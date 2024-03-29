from django.contrib.auth.models import AbstractUser
from django.db import models

from shoppingmall.utils.models import BaseModel


# Create your models here.
class User(AbstractUser):
    """⾃定义⽤户模型类"""
    mobile = models.CharField(max_length=11, unique=True, verbose_name='⼿机号')
    email_active = models.BooleanField(default=False, verbose_name='邮箱激活状态')
    default_address = models.ForeignKey('Address', related_name='users', null=True, blank=True,
                                        on_delete=models.SET_NULL, verbose_name='默认收货地址')

    class Meta:
        db_table = 'tb_user'
        verbose_name = '⽤户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username


class Address(BaseModel):
    title = models.CharField(max_length=20, verbose_name='地址标题')
    receiver = models.CharField(max_length=20, verbose_name='收件人')
    province = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='province_address',
                                 verbose_name='省')
    city = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='city_address', verbose_name='市')
    district = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='district_address',
                                 verbose_name='区')
    place = models.CharField(max_length=100, verbose_name='详细地址')
    mobile = models.CharField(max_length=11, verbose_name='手机号码')
    telephone = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')
    email = models.CharField(max_length=50, null=True, blank=True, default='', verbose_name='电子邮箱')
    is_delete = models.BooleanField(default=False, verbose_name='逻辑删除')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='用户')

    class Meta:
        db_table = 'tb_addresses'
        verbose_name = '收货地址'
        ordering = ['-update_time']
