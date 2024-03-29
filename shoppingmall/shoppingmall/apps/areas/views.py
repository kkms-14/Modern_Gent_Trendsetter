from django.core.cache import cache
from django.http import JsonResponse, HttpRequest
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from redis import Redis

from areas.models import Area
from shoppingmall.utils.response_code import RETCODE


# Create your views here.
# class AreasView(View):
#     def get(self, request):
#         area_id = request.GET.get('area_id')
#         if not area_id:
#             try:
#                 provinces = Area.objects.filter(parent__isnull=True)
#                 province_list = []
#                 for province in provinces:
#                     province_list.append({'id': province.id, 'name': province})
#             except Exception:
#                 return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '省份数据错误'})
#             return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
#         else:
#             pass
#
#         pass
class AreasView(View):

    def get(self, request: HttpRequest):
        area_id = request.GET.get('area_id')
        # 判断 area_id是否存在
        # 如果前端没有传入area_id，表示用户需要省份数据，那么查询arent_id等于nul 的数据
        cnn: Redis = get_redis_connection('default')
        if not area_id:
            province_list = cache.get('province_list')
            print(province_list)
            if not province_list:
                try:
                    province_model = Area.objects.filter(parent__isnull=True)
                    province_list = []
                    for province in province_model:
                        province_list.append({
                            'id': province.id,
                            'name': province.name
                        })
                except Exception:
                    return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '省份数据错误'})
                cache.set('province_list', province_list, 60 * 2)

            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
        else:

            # 如果前端传入了area_id，表示用户需要市或区数据，那么查询 parent_id等于area_id 数据
            sub_data = cache.get('sub_' + str(area_id))
            if not sub_data:
                sub_model_list = Area.objects.filter(parent=area_id)
                parent: Area = Area.objects.get(id=area_id)
                # sub_model_list = parent.subs.all()
                subs = []
                for sub in sub_model_list:
                    subs.append(
                        {
                            'id': sub.id,
                            'name': sub.name
                        })
                sub_data = {
                    "id": parent.id,
                    "name": parent.name,
                    "subs": subs
                }
                cache.set('sub_' + str(area_id), sub_data, 60 * 2)
            # print(sub_model_list)
            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', "sub_data": sub_data})
