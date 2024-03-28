import random

from django.http import HttpResponse, HttpRequest, JsonResponse
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from redis import Redis

from shoppingmall.libs.captcha.captcha import captcha

from shoppingmall.utils import constants

from shoppingmall.utils.response_code import RETCODE

from shoppingmall.libs.ronglian_sms_sdk.Sms import send_sms_code


# Create your views here.
class ImageCodeView(View):
    def get(self, request, uuid):
        code, code_text, code_image = captcha.generate_captcha()
        connection: Redis = get_redis_connection('image_code')
        connection.setex(uuid, constants.image_code_redis_expire, code_text)
        return HttpResponse(code_image, content_type='image/jpg')


class SMSCodeView(View):
    def get(self, request: HttpRequest, mobile):
        # 接收参数
        image_code: str = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')
        # 校验参数
        if not all([image_code, uuid]):
            return JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少必传参数'})
        # 创建连接到redis的对象
        img_conn: Redis = get_redis_connection('image_code')
        image_code_redis = img_conn.get(uuid)
        if image_code_redis is None:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '图形验证码已失效'})
        image_code_redis = image_code_redis.decode()
        img_conn.delete(uuid)
        if image_code.lower() != image_code_redis.lower():
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '图形验证码错误'})

        sms_code = "%04d" % random.randint(0, 9999)
        sms_conn: Redis = get_redis_connection('sms_code')
        sms_conn.setex(mobile, constants.SMS_CODE_REDIS_EXPIRE, sms_code)
        ret = send_sms_code([mobile], sms_code)
        if ret:
            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
        else:
            return JsonResponse({'code': RETCODE.SMSCODERR, 'errmsg': '短信发送失败'})
