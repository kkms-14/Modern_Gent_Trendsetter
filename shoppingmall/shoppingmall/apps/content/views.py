from django.http import HttpRequest
from django.shortcuts import render
from django.views import View

from content.models import ContentCategory
from content.utils import get_categories


# Create your views here.
class IndexView(View):
    def get(self, request: HttpRequest):
        # 查询分类数据
        categories = get_categories()

        # 查询广告数据
        contents = {}
        content_categories = ContentCategory.objects.all()
        for cat in content_categories:
            contents[cat.key] = cat.content_set.all().order_by("sequence")
        # 组织广告数据
        context = {
            "categories": categories,
            "contents": contents
        }
        return render(request, "index.html", context)
