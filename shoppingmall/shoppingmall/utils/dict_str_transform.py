import base64
import pickle


def dict_base64_dumps(data_dict):
    """
    把字典数据转换为 base64 编码后的字符串
    :param data_dict:
    :return:
    """
    data_bytes = pickle.dumps(data_dict)
    data_b64 = base64.b64encode(data_bytes)
    return data_b64.decode()


def base64_dict_loads(data_b64_str):
    """
    把 base64 编码后的字符串数据转换为字典数据
    :param data_b64_str:
    :return:
    """
    data_b64 = data_b64_str.encode()
    data_bytes = base64.b64decode(data_b64)
    data_dict = pickle.loads(data_bytes)
    return data_dict
