import json
import re

from django import http
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import DatabaseError
from django.shortcuts import render, redirect

# Create your views here.
from django.http import HttpResponse, HttpRequest, JsonResponse, HttpResponseForbidden
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection

from shoppingmall.utils.response_code import RETCODE
from users.models import User, Address


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

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        response = redirect('/')
        response.set_cookie('username', user.username, max_age=60 * 60 * 24 * 14)

        return response


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


class LoginView(View):
    def get(self, request):
        """打开登陆页面"""
        return render(request, 'login.html')

    def post(self, request):
        """提交登陆数据"""
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        if not all([username, password, remembered]):
            return HttpResponseForbidden('缺少必须的参数')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输⼊5-20个字符的⽤户名')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输⼊8-20位的密码')

        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'login.html', {'loginerror': '用户名或密码错误'})

        login(request, user)
        if remembered != 'on':
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(None)

        next_path = request.GET.get('next', reverse('contents:index'))
        response = redirect(next_path)
        response.set_cookie('username', user.username, max_age=60 * 60 * 24 * 14)
        return response


class LogoutView(View):
    def get(self, request):
        logout(request)
        response = redirect(reverse('contents:index'))
        response.delete_cookie('username')
        return response


class UserCenterView(LoginRequiredMixin, View):
    def get(self, request):
        context = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active
        }
        return render(request, 'user_center_info.html', context)


class AddressView(View):
    def get(self, request):
        return render(request, 'user_center_address.html')

    def post(self, request):
        data_dict = json.loads(request.body.decode())
        title = data_dict.get('title')
        receiver = data_dict.get('receiver')
        province_id = data_dict.get('province_id')
        city_id = data_dict.get('city_id')
        district_id = data_dict.get('district_id')
        place = data_dict.get('place')
        mobile = data_dict.get('mobile')
        tel = data_dict.get('tel')
        email = data_dict.get('email')

        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return HttpResponseForbidden('缺少信息')
        if not re.match(r'^1[345789]\d{9}$', mobile):
            return HttpResponseForbidden('手机号格式错误')
        if tel and not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
            return HttpResponseForbidden('电话格式错误')
        if email and re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return HttpResponseForbidden('邮箱格式错误')
        if not title:
            title = receiver

        try:
            address: Address = Address.objects.create(
                title=title,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                telephone=tel,
                email=email,
                user=request.user
            )
        except Exception:
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '新增地址失败'})

        address_dict = {
            'id': address,
            'title': title,
            'receiver': receiver,
            'province': address.province.name,
            'province_id': address.province_id,
            'city': address.city.name,
            'city_id': address.city_id,
            'district': address.district.name,
            'district_id': address.district_id,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.telephone,
            'email': address.email,
        }
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'address': address_dict})


