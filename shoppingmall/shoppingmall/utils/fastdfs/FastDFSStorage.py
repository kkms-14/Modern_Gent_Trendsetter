from django.conf import settings
from django.core.files.storage import Storage


class FastDFSFileStorages(Storage):

    def url(self, name):
        return settings.FDFS_BASE_PATH + name
