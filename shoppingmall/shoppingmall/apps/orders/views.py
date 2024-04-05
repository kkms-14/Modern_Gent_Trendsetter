import json
from decimal import Decimal

from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import render

# Create your views here.
from django.utils import timezone
from django.views import View
from django_redis import get_redis_connection
from redis import Redis

from goods.models import SKU
from orders.models import OrderInfo, OrderGoods
from users.models import Address
from shoppingmall.utils import constants
from shoppingmall.utils.mixin import LoginRequiredMixin
from shoppingmall.utils.response_code import RETCODE


class OrderSettlementView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest):
        # 1.提取参数
        # 2.校验参数
        # 3.处理逻辑
        user = request.user
        # 3.1. 查询当前用户的地址数据
        try:
            addresses = Address.objects.filter(user=user, is_delete=False)
        except Address.DoesNotExist:
            addresses = None

        # 3.2. 查询当前用户的购物车中选中的商品
        connection: Redis = get_redis_connection("carts")
        carts_sku_count = connection.hgetall("carts_%s" % user.id)
        carts_sku_selected = connection.smembers("selected_%s" % user.id)
        carts_sku_count_selected = {}  # 保存所有选中的商品的数量和id
        for sku_id in carts_sku_selected:
            carts_sku_count_selected[int(sku_id)] = int(carts_sku_count[sku_id])

        # 3.3. 组织数据
        total_count = 0
        total_amount = Decimal(0.00)
        skus = SKU.objects.filter(id__in=carts_sku_count_selected.keys())
        for sku in skus:
            sku.count = carts_sku_count_selected[sku.id]
            sku.amount = carts_sku_count_selected[sku.id] * sku.price
            total_count += carts_sku_count_selected[sku.id]
            total_amount += carts_sku_count_selected[sku.id] * sku.price

        context = {
            "addresses": addresses,
            "skus": skus,
            "total_count": total_count,
            "total_amount": total_amount,
            "freight": Decimal(20.00),
            "payment_amount": Decimal(20.00) + total_amount,
            "default_address_id": user.default_address_id,
        }
        # 4.返回响应
        return render(request, "place_order.html", context)


class OrderCommitView(View):
    """提交订单"""

    def post(self, request: HttpRequest):
        # 1.提取参数
        data = json.loads(request.body.decode())
        address_id = data.get("address_id")
        pay_method = data.get("pay_method")

        # 2.校验参数
        if not all([address_id, pay_method]):
            return HttpResponseForbidden("缺少必须参数")

        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return HttpResponseForbidden("地址不存在")

        if pay_method not in OrderInfo.PAY_METHODS_ENUM.values():
            return HttpResponseForbidden("支付方式选择错误")

        # 3.处理逻辑
        with transaction.atomic():
            user = request.user
            # 3.1.构建订单的基本信息，插入数据库
            # order_id 使用 当前时间的 年月日时分秒 + 9位用户id 来构建
            order_id = timezone.localtime().strftime("%Y%m%d%H%M%S") + "%09d" % user.id
            sid = transaction.savepoint()
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                address=address,
                total_count=0,
                total_amount=0,
                freight=Decimal("20.00"),
                pay_method=pay_method,
                status=OrderInfo.ORDER_STATUS_ENUM["UNPAID"] if pay_method == OrderInfo.PAY_METHODS_ENUM["ALIPAY"] else
                OrderInfo.ORDER_STATUS_ENUM["UNSEND"],
            )
            # 3.2.构建订单的商品数据，插入数据库
            connection: Redis = get_redis_connection("carts")
            carts_sku_count = connection.hgetall("carts_%s" % user.id)
            carts_sku_selected = connection.smembers("selected_%s" % user.id)

            for sku_id in carts_sku_selected:
                while True:
                    sku = SKU.objects.get(id=int(sku_id))
                    count = int(carts_sku_count[sku_id])
                    # 3.2.1 查询商品的库存信息，判断库存是否足够
                    if sku.stock < count:
                        transaction.savepoint_rollback(sid)
                        return JsonResponse({"code": RETCODE.STOCKERR, "errmsg": "商品库存不足"})

                    import time
                    time.sleep(5)

                    # 3.2.2 操作库存和销量数据
                    # sku.stock -= count
                    # sku.sales += count
                    # sku.save()
                    new_stock = sku.stock - count
                    new_sales = sku.sales + count
                    result = SKU.objects.filter(id=sku_id, stock=sku.stock).update(stock=new_stock, sales=new_sales)
                    if result == 0:
                        # 商品被其他人同时下单，重新下单该商品
                        continue

                    sku.spu.sales += count
                    sku.spu.save()

                    # 3.2.3 构建订单的商品数据，插入数据库
                    OrderGoods.objects.create(
                        order=order,
                        sku=sku,
                        count=count,
                        price=sku.price,
                    )

                    # 3.2.4 计算订单商品总数和总费用
                    order.total_count += count
                    order.total_amount += count * sku.price
                    # 下单商品成功，对下一个商品进行下单
                    break

            order.total_amount += order.freight
            order.save()
            transaction.savepoint_commit(sid)

        # 3.2.5 删除购物车中已经结算过的商品
        connection.hdel("carts_%s" % user.id, *carts_sku_selected)
        connection.srem("selected_%s" % user.id, *carts_sku_selected)
        # 4.返回响应
        return JsonResponse({"code": RETCODE.OK, "errmsg": "OK", "order_id": order_id})


class OrderSuccessView(View):
    def get(self, request: HttpRequest):
        order_id = request.GET.get("order_id")
        pay_method = request.GET.get("pay_method")
        payment_amount = request.GET.get("payment_amount")

        context = {
            "order_id": order_id,
            "pay_method": pay_method,
            "payment_amount": payment_amount,
        }
        return render(request, "order_success.html", context)


class UserOrderInfoView(LoginRequiredMixin, View):
    """显示用户的订单列表"""

    def get(self, request: HttpRequest, page_num):
        user = request.user
        orders = user.orderinfo_set.all().order_by("-create_time")

        page_num = int(page_num)
        paginator = Paginator(orders, constants.ORDER_LIST_LIMIT)
        page_orders = paginator.page(page_num)

        for order in page_orders:
            order.pay_method_name = OrderInfo.PAY_METHOD_CHOICES[order.pay_method-1][1]
            order.status_name = OrderInfo.ORDER_STATUS_CHOICES[order.status-1][1]

        context = {
            "orders": page_orders,
            "page_num": page_num,
            "page_total": paginator.num_pages,
        }
        return render(request, "user_center_order.html", context)
