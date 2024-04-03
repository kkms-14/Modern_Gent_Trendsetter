def get_breadcrumbs(category):
    """
    获取分类的面包屑导航数据
    :param category:
    :return:
    """
    cat2 = category.parent
    cat1 = cat2.parent
    bread_crumbs = {
        "cat1": {
            "name": cat1.name,
            "url": cat1.goodschannel_set.all()[0].url
        },
        "cat2": cat2,
        "cat3": category
    }
    return bread_crumbs
