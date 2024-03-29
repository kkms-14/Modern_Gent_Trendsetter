from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    url(r'^register/$', views.RegisterView.as_view(), name='register'),
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameCountView.as_view(),
        name='username_count'),
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view(),
        name='mobile_count'),
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    url(r'^info/$', views.UserCenterView.as_view(), name='info'),
    url(r'^addresses/$', views.AddressView.as_view(), name='addresses'),
    url(r'^addresses/create/$', views.AddressView.as_view(), name='addresses_create'),
]
