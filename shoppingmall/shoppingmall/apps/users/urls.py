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
    url(r'^addresses/(?P<address_id>\d+)/$', views.AddressView.as_view(), name='addresses_update_delete'),
    url(r'^addresses/(?P<address_id>\d+)/default/$', views.DefaultAddressView.as_view(),
        name='addresses_default'),
    url(r'^addresses/(?P<address_id>\d+)/title/$', views.AddressTitleView.as_view(),
        name='addresses_title'),
    url(r'^password/$', views.PasswordView.as_view(), name='password'),
]
