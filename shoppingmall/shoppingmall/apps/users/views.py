from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, HttpRequest
from django.views import View


class RegisterView(View):
    """user register view"""
    def get(self, request: HttpRequest):
        return render(request, 'register.html')
