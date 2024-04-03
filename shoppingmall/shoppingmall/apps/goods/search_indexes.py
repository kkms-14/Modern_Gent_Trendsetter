from haystack import indexes

from goods.models import SKU


class SKUIndexModel(indexes.SearchIndex, indexes.Indexable):
    """SKU索引数据模型类"""

    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return SKU

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_launched=True)