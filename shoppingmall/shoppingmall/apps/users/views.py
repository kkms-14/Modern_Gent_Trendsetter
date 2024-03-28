import re

from django import http
from django.contrib.auth import login
from django.db import DatabaseError
from django.shortcuts import render, redirect

# Create your views here.
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.views import View
from django_redis import get_redis_connection

from shoppingmall.utils.response_code import RETCODE
from users.models import User


class RegisterView(View):
    """user register view"""

    def get(self, request: HttpRequest):
        """展示用户注册页面"""
        return render(request, 'register.html')

    def post(self, request: HttpRequest):
        """提交用户注册数据"""
        # 1
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        sms_code = request.POST.get('sms_code')
        allow = request.POST.get('allow')

        # 2
        if not all([username, password, password2, mobile, sms_code, allow]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输⼊5-20个字符的⽤户名')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输⼊8-20位的密码')
        if password != password2:
            return http.HttpResponseForbidden('两次输⼊的密码不⼀致')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输⼊正确的⼿机号码')
        if allow != 'on':
            return http.HttpResponseForbidden('请勾选⽤户协议')
        connection = get_redis_connection('sms_code')
        sms_code_redis = connection.get(mobile)
        if sms_code_redis is None:
            return render(request, 'register.html', {'register_errmsg': "短信验证码无效"})
        if sms_code != sms_code_redis.decode():
            return render(request, 'register.html', {'register_errmsg': "短信验证码错误"})

        # 3
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError as e:
            return render(request, 'register.html', {'register_errmsg': "服务器错误"})

        login(request, user)

        return redirect('/')


class UsernameCountView(View):
    def get(self, request: HttpRequest, username: str):
        count = 0
        try:
            count = User.objects.filter(username=username).count()
        except DatabaseError as e:
            ret = {
                "code": RETCODE.DBERR,
                "errmsg": '查询失败',
                "count": 0
            }

        ret = {
            "code": RETCODE.OK,
            "errmsg": 'OK',
            "count": count
        }
        return JsonResponse(ret)


class MobileCountView(View):
    def get(self, request: HttpRequest, mobile):
        count = 0
        try:
            count = User.objects.filter(mobile=mobile).count()
        except DatabaseError as e:
            data = {
                "code": RETCODE.DBERR,
                "errmsg": '查询失败',
                "count": 0
            }
        data = {
            "code": RETCODE.OK,
            "errmsg": 'OK',
            "count": count
        }
        return JsonResponse(data)