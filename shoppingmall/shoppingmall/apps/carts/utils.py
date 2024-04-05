from django.http import HttpRequest, HttpResponse
from django_redis import get_redis_connection
from redis import Redis

from shoppingmall.utils.dict_str_transform import base64_dict_loads


def merge_cart(request: HttpRequest, response: HttpResponse):
    """合并购物车数据"""
    # 1. 从 cookie 中获取购物车数据
    carts_str = request.COOKIES.get("carts")
    if not carts_str:
        return response
    carts_dict = base64_dict_loads(carts_str)
    # 2. 把购物车数据合并到 redis 购物车中
    carts_sku_count = {}
    carts_selected = []
    carts_not_selected = []
    for sku_id in carts_dict.keys():
        carts_sku_count[sku_id] = carts_dict[sku_id]["count"]
        if carts_dict[sku_id]["selected"]:
            carts_selected.append(sku_id)
        else:
            carts_not_selected.append(sku_id)

    user = request.user
    connection: Redis = get_redis_connection("carts")
    connection.hmset("carts_%s" % user.id, carts_sku_count)
    if carts_selected:
        connection.sadd("selected_%s" % user.id, *carts_selected)
    if carts_not_selected:
        connection.srem("selected_%s" % user.id, *carts_not_selected)

    # 3. 删除cookie中的购物车数据
    response.delete_cookie("carts")
    return response
