from goods.models import GoodsChannelGroup


def get_categories():
    """
    按分类列表的效果构建分类数据
    [
        {
            "channels": [
                {
                    "id": "",
                    "name": "",
                    "url": "",
                },
            ],
            "sub_cats": [
                {
                    "id": "",
                    "name": "",
                    "sub_cats": [
                        {
                            "id": "",
                            "name": "",
                        },
                    ],
                },
            ]
        },
        {
        }
    ]
    :return:
    """
    categories = []
    groups = GoodsChannelGroup.objects.all().order_by("id")
    for group in groups:
        channel_group = {
            "channels": [],
            "sub_cats": []
        }
        categories.append(channel_group)
        # 填充频道列表, 遍历频道组里所有频道数据, 构建频道对应的字典数据
        for channel in group.goodschannel_set.all().order_by("sequence"):
            channel_dict = {
                "id": channel.id,
                "name": channel.category.name,
                "url": channel.url,
            }
            channel_group["channels"].append(channel_dict)

            # 填充二级分类列表
            # 遍历所有的频道数据, 找到频道下面的一级分类,
            # 查询一级分类下面的所有二级分类, 使用二级分类列表构建字典数据插入列表中
            for cat2 in channel.category.subs.all():
                cat2_dict = {
                    "id": cat2.id,
                    "name": cat2.name,
                    "sub_cats": [],
                }
                for cat3 in cat2.subs.all():
                    cat3_dict = {
                        "id": cat3.id,
                        "name": cat3.name,
                    }
                    cat2_dict["sub_cats"].append(cat3_dict)
                channel_group["sub_cats"].append(cat2_dict)
    return categories
