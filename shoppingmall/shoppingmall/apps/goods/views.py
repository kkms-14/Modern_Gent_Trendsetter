import json
from datetime import datetime

from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection
from redis import Redis

from content.utils import get_categories
from goods.models import GoodsCategory, SKU, GoodsVisitCount
from goods.utils import get_breadcrumbs
from shoppingmall.utils import constants
from shoppingmall.utils.response_code import RETCODE

from shoppingmall.utils.dict_str_transform import base64_dict_loads


class GoodsListView(View):
    def get(self, request: HttpRequest, category_id, page_num):
        # 1.提取参数
        sort = request.GET.get("sort", "default")
        # 2.校验参数
        if sort not in ["default", "price", "hot"]:
            return HttpResponseForbidden("sort参数错误")
        # 3.处理逻辑
        # 3.1查询分类数据
        categories = get_categories()
        # 3.2查询面包屑导航栏数据
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return HttpResponseForbidden("category_id不存在")
        bread_crumbs = get_breadcrumbs(category)
        # 3.3查询商品列表数据
        # 3.3.1 查询指定分类的商品列表sku数据
        skus: QuerySet = SKU.objects.filter(category=category, is_launched=True)
        # 3.3.2 按指定的排序方式对查询结果进行排序
        if sort == "price":
            sort_field = "price"
        elif sort == "hot":
            sort_field = "-sales"
        else:
            sort_field = "create_time"
        skus_ordered = skus.order_by(sort_field)
        # 3.3.3 对排序结果进行分页
        paginator = Paginator(skus_ordered, 5)
        page_skus = paginator.page(page_num)

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
        context = {
            "categories": categories,
            "bread_crumbs": bread_crumbs,
            "skus": page_skus,
            "category": category,
            "page_num": page_num,
            "sort": sort,
            "page_total": paginator.num_pages,
            "carts": carts
        }
        return render(request, "list.html", context)


class HotGoodsView(View):
    def get(self, request, category_id):
        # 1.提取参数
        # 2.校验参数
        # 3.处理逻辑
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({"code": RETCODE.PARAMERR, "errmsg": "分类不存在"})
        skus = SKU.objects.filter(category=category, is_launched=True).order_by("-sales")
        # 4.返回响应
        hot_skus = []
        for sku in skus:
            hot_skus.append({
                "id": sku.id,
                "default_image_url": sku.default_image.url,
                "name": sku.name,
                "price": sku.price
            })
        return JsonResponse({
            "code": RETCODE.OK,
            "errmsg": "OK",
            "hot_skus": hot_skus[:2]
        })


class DetailView(View):
    def get(self, request: HttpRequest, sku_id):
        # 1.查询数据
        # 1.1 商品分类列表
        categories = get_categories()
        # 1.2 商品SKU信息(详情信息)
        try:
            sku_current = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            render(request, "404.html")
        # 1.3 面包屑导航
        bread_crumbs = get_breadcrumbs(sku_current.category)

        # 1.4 SKU规格信息 sku_current-spu-多个规格-多个规格选项
        specs = sku_current.spu.specs.all().order_by("id")
        # 为当前页面的每个规格选项找到 sku_id
        # 1.4.1 找到 sku_current 属于的 spu 下面的所有的 skus
        skus = sku_current.spu.sku_set.all()
        # 1.4.2 给每个 sku_current 找到所元组有的选项的id，用选项id构建一个元组，
        # 把元组和 sku_id 对应关系保存在字典里面，把元组作为 key，把 sku_id 作为 value
        options_sku_map = {}
        for sku in skus:
            option_ids = []
            for sku_option in sku.specs.all().order_by("spec_id"):
                option_ids.append(sku_option.option_id)
            options_sku_map[tuple(option_ids)] = sku.id
            # 获取当前选中的sku商品的选项值的id构建的列表
            if sku.id == sku_current.id:
                option_ids_current = option_ids

        # 1.4.3 为当前页面里的每个选项产生 选项id 构建的元组，到上面的字典你们查询当前选项对应的sku_id
        for index, spec in enumerate(specs):
            spec.option_list = []
            for option in spec.options.all():
                option_ids_temple = option_ids_current[:]
                option_ids_temple[index] = option.id
                option.sku_id = options_sku_map.get(tuple(option_ids_temple), 0)
                spec.option_list.append(option)

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
        # print(carts)

        # 2.组织数据
        context = {
            "categories": categories,
            "bread_crumbs": bread_crumbs,
            "sku": sku_current,
            "specs": specs,
            "carts": carts,
        }
        # 3.返回响应
        return render(request, "detail.html", context)


class StatisticsCategoryCountView(View):
    def post(self, request: HttpRequest, category_id):
        # 1.提取参数
        # 2.校验参数
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({"code": RETCODE.PARAMERR, "errmsg": "分类不存在"})
        # 3.处理逻辑
        now = datetime.now()
        today_date = datetime(now.year, now.month, now.day)
        try:
            count = GoodsVisitCount.objects.get(category=category, date=today_date)
        except GoodsVisitCount.DoesNotExist:
            count = GoodsVisitCount(category=category)
        count.count += 1
        count.save()

        # 4.返回响应
        return JsonResponse({"code": RETCODE.OK, "errmsg": "OK"})


class UserBrowserHistoryView(View):
    def post(self, request: HttpRequest):
        # 1.提取参数
        data_json = request.body.decode()
        data_dict: dict = json.loads(data_json)
        sku_id = data_dict.get("sku_id")
        # 2.校验参数
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({"code": RETCODE.PARAMERR, "errmsg": "商品不存在"})
        # 3.处理逻辑
        # 把 sku_id 保存在 redis 中, 先去重, 再存储, 再裁减
        conn: Redis = get_redis_connection("history")
        user_id = request.user.id
        # 去重
        conn.lrem("history_%s" % user_id, 0, sku_id)
        # 存储
        conn.lpush("history_%s" % user_id, sku_id)
        # 裁减
        conn.ltrim("history_%s" % user_id, 0, 5)

        # 4.返回响应
        return JsonResponse({"code": RETCODE.OK, "errmsg": "OK"})

    def get(self, request: HttpRequest):
        # 1.获取参数
        # 2.校验参数
        # 3.处理逻辑
        # 查询用户的浏览记录数据，组织数据
        conn: Redis = get_redis_connection("history")
        sku_ids = conn.lrange("history_%s" % request.user.id, 0, 4)
        sku_list = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=int(sku_id))
            sku_list.append({
                "id": sku.id,
                "name": sku.name,
                "default_image_url": sku.default_image.url,
                "price": sku.price,
            })
        # 4.返回响应
        return JsonResponse({"code": RETCODE.OK, "errmsg": "ok", "skus": sku_list})
