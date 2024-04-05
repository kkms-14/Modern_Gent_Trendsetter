from django.http import HttpRequest
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from redis import Redis

from content.models import ContentCategory
from content.utils import get_categories
from goods.models import SKU
from shoppingmall.utils.dict_str_transform import base64_dict_loads


# Create your views here.
class IndexView(View):
    def get(self, request: HttpRequest):
        # 查询分类数据
        categories = get_categories()

        # 查询广告数据
        contents = {}
        content_categories = ContentCategory.objects.all()
        for cat in content_categories:
            contents[cat.key] = cat.content_set.all().order_by("sequence")
        # 组织广告数据

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
        print(carts)
        context = {
            "categories": categories,
            "contents": contents,
            "carts": carts
        }
        return render(request, "index.html", context)
