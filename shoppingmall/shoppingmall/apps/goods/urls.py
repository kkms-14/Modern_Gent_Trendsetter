from django.conf.urls import url

from goods import views

urlpatterns = [
    url(r"^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$", views.GoodsListView.as_view(), name="goods_list"),
    url(r"^hot/(?P<category_id>\d+)/$", views.HotGoodsView.as_view(), name="hot_goods"),
    url(r"^detail/(?P<sku_id>\d+)/$", views.DetailView.as_view(), name="detail"),
    url(r"^detail/visit/(?P<category_id>\d+)/$", views.StatisticsCategoryCountView.as_view(), name="count"),
    url(r"^browse_histories/$", views.UserBrowserHistoryView.as_view(), name="history"),
]
