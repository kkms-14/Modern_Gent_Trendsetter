import json

from django.http import HttpRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection
from redis import Redis

from goods.models import SKU
from shoppingmall.utils import constants
from shoppingmall.utils.dict_str_transform import base64_dict_loads, dict_base64_dumps
from shoppingmall.utils.response_code import RETCODE


class CartsView(View):
    def post(self, request: HttpRequest):
        """添加商品到购物车中"""
        # 1.提取参数
        data_dict = json.loads(request.body.decode())
        sku_id = data_dict.get("sku_id")
        count = data_dict.get("count")
        selected = data_dict.get("selected", True)

        # 2.校验参数
        if not all([sku_id, count]):
            return HttpResponseForbidden("缺少必须参数")
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return HttpResponseForbidden("商品不存在")
        count = int(count)
        if count < 1:
            return HttpResponseForbidden("商品数量不能小于1")
        elif count > sku.stock:
            return JsonResponse({"code": RETCODE.PARAMERR, "errmsg": "商品库存不足"})
        # 3.处理逻辑
        user = request.user
        if user.is_authenticated:
            # 用户登录修改 redis 中的购物车数据
            connection: Redis = get_redis_connection("carts")
            connection.hincrby("carts_%s" % user.id, sku_id, count)
            connection.sadd("selected_%s" % user.id, sku_id)
            return JsonResponse({"code": RETCODE.OK, "errmsg": "添加购物车成功"})
        else:
            # 用户未登录修改 cookie 中的购物车数据
            # 1.获取 cookie 中的购物车字符串数据，转换为 python 字典类型的数据
            carts_str = request.COOKIES.get("carts")
            if carts_str:
                carts_dict = base64_dict_loads(carts_str)
            else:
                carts_dict = {}
            # 2.修改购物车中的商品的数量
            if sku_id in carts_dict:
                old_count = carts_dict[sku_id]["count"]
                count += old_count
            carts_dict[sku_id] = {
                "count": count,
                "selected": selected
            }
            # 3.把购物车数据转换为字符串，写入 cookie
            carts_str = dict_base64_dumps(carts_dict)
            response = JsonResponse({"code": RETCODE.OK, "errmsg": "添加购物车成功"})
            response.set_cookie("carts", carts_str, constants.CARTS_COOKIE_EXPIRES)
            return response

    def get(self, request: HttpRequest):
        """展示购物车页面"""
        # 1.提取参数
        # 2.校验参数
        # 3.处理逻辑
        # 查询购物车数据
        user = request.user
        if user.is_authenticated:
            # 登录的用户购物车数据从 redis 里面查询
            connection: Redis = get_redis_connection("carts")
            carts_sku_count = connection.hgetall("carts_%s" % user.id)
            carts_sku_selected = connection.smembers("selected_%s" % user.id)
            carts_dict = {}
            for sku_id, count in carts_sku_count.items():
                carts_dict[int(sku_id)] = {
                    "count": int(count),
                    "selected": sku_id in carts_sku_selected
                }
        else:
            # 未登录的用户购物车数据从 cookie 里面查询
            carts_str = request.COOKIES.get("carts")
            if carts_str:
                carts_dict = base64_dict_loads(carts_str)
            else:
                carts_dict = {}
        # 组织购物车数据
        # [
        #     {
        #       "name":"",
        #       "price":"",
        #       "image":"",
        #       "selected":"",
        #       "count":"",
        #       "acount":"",
        #       "id":"",
        #     },
        # ]
        carts = []
        skus = SKU.objects.filter(id__in=carts_dict.keys())
        for sku in skus:
            carts.append({
                "id": sku.id,
                "name": sku.name,
                "price": str(sku.price),
                "default_image_url": sku.default_image.url,
                "selected": str(carts_dict[sku.id]["selected"]),
                "count": carts_dict[sku.id]["count"],
                "amount": str(carts_dict[sku.id]["count"] * sku.price),
            })
        # 4.返回响应
        # 渲染购物车页面
        context = {"carts": carts}
        return render(request, "cart.html", context)

    def put(self, request: HttpRequest):
        """修改购物车数据"""
        # 1.提取参数
        data = json.loads(request.body.decode())
        sku_id = data.get("sku_id")
        count = data.get("count")
        selected = data.get("selected")

        # 2.校验参数
        if not all([sku_id, count]):
            return HttpResponseForbidden("缺少必须参数")

        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return HttpResponseForbidden("商品不存在")
        count = int(count)
        if count < 1:
            return HttpResponseForbidden("商品数量不能小于1")
        elif count > sku.stock:
            return JsonResponse({"code": RETCODE.PARAMERR, "errmsg": "商品库存不足"})

        if selected:
            if not isinstance(selected, bool):
                return HttpResponseForbidden("参数格式错误")
        # 3.处理逻辑
        user = request.user
        if user.is_authenticated:
            # 用户已经登录，修改 redis 中的数据
            connection: Redis = get_redis_connection("carts")
            connection.hset("carts_%s" % user.id, sku_id, count)
            if selected:
                connection.sadd("selected_%s" % user.id, sku_id)
            else:
                connection.srem("selected_%s" % user.id, sku_id)
            cart_sku = {
                "name": sku.name,
                "price": sku.price,
                "default_image_url": sku.default_image.url,
                "selected": selected,
                "count": count,
                "acount": sku.price * count,
                "id": sku.id,
            }
            return JsonResponse({"code": RETCODE.OK, "errmsg": "OK", "cart_sku": cart_sku})
        else:
            # 用户没有登录，修改 cookie 里面的购物车数据
            carts_str = request.COOKIES.get("carts", "{}")
            carts_dict = base64_dict_loads(carts_str)
            carts_dict[sku_id] = {
                "count": count,
                "selected": selected
            }
            carts_str = dict_base64_dumps(carts_dict)
            cart_sku = {
                "name": sku.name,
                "price": sku.price,
                "default_image_url": sku.default_image.url,
                "selected": selected,
                "count": count,
                "acount": sku.price * count,
                "id": sku.id,
            }
            response = JsonResponse({"code": RETCODE.OK, "errmsg": "OK", "cart_sku": cart_sku})
            response.set_cookie("carts", carts_str, constants.CARTS_COOKIE_EXPIRES)
            return response

    def delete(self, request: HttpRequest):
        """删除购物车中的商品"""
        # 1.提取参数
        data = json.loads(request.body.decode())
        sku_id = data.get("sku_id")

        # 2.校验参数
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return HttpResponseForbidden("商品不存在")
        # 3.处理逻辑
        user = request.user
        if user.is_authenticated:
            # 用户登录状态删除 redis 中购物车中的商品
            connection: Redis = get_redis_connection("carts")
            connection.hdel("carts_%s" % user.id, sku_id)
            connection.srem("selected_%s" % user.id, sku_id)
            return JsonResponse({"code": RETCODE.OK, "errmsg": "ok"})
        else:
            # 用户没有登录删除 cookie 中购物车中的商品
            carts_str = request.COOKIES.get("carts", "{}")
            carts_dict = base64_dict_loads(carts_str)
            if sku_id in carts_dict:
                del carts_dict[sku_id]
            carts_str = dict_base64_dumps(carts_dict)
            response = JsonResponse({"code": RETCODE.OK, "errmsg": "ok"})
            response.set_cookie("carts", carts_str, constants.CARTS_COOKIE_EXPIRES)
            return response


class CartsSelectAllView(View):
    def put(self, request: HttpRequest):
        """全部选中或取消选中购物车商品"""
        # 1.提取参数
        data = json.loads(request.body.decode())
        selected = data.get("selected", True)

        # 2.校验参数
        if selected:
            if not isinstance(selected, bool):
                return HttpResponseForbidden("参数格式错误")

        # 3.处理逻辑
        user = request.user
        if user.is_authenticated:
            connection: Redis = get_redis_connection("carts")
            carts_sku_count = connection.hgetall("carts_%s" % user.id)
            if selected:
                connection.sadd("selected_%s" % user.id, *carts_sku_count.keys())
            else:
                connection.srem("selected_%s" % user.id, *carts_sku_count.keys())

            return JsonResponse({"code": RETCODE.OK, "errmsg": "ok"})
        else:
            carts_str = request.COOKIES.get("carts", "{}")
            carts_dict = base64_dict_loads(carts_str)
            for sku_id in carts_dict.keys():
                carts_dict[sku_id]["selected"] = True
            carts_str = dict_base64_dumps(carts_dict)
            response = JsonResponse({"code": RETCODE.OK, "errmsg": "ok"})
            response.set_cookie("carts", carts_str, constants.CARTS_COOKIE_EXPIRES)
            return response