from django.conf.urls import url

from carts import views

urlpatterns = [
    url(r"^carts/$", views.CartsView.as_view(), name="carts"),
    url(r"^carts/selection/$", views.CartsSelectAllView.as_view(), name="carts_select_all"),

]