import json
import logging
from shoppingmall.libs.ronglian_sms_sdk import SmsSDK

# 说明： 主账号， 登陆云通讯⽹站后， 可在"控制台-应⽤"中看到开发者主账号ACCOUNT SID
accId = '2c94811c8cd4da0a018e84404ad64a31'

# 说明： 主账号Token， 登陆云通讯⽹站后， 可在控制台-应⽤中看到开发者主账号AUTH TOKEN
accToken = '801b86b949b2402f82cd0936d28dc82f'

# 请使⽤管理控制台⾸⻚的APPID或⾃⼰创建应⽤的APPID
appId = '2c94811c8cd4da0a018e84404c534a38'


def send_sms_code(mobiles, code):
    """
       使用容联云通讯发送短信验证码
       :param mobiles: 接收短信的手机号列表
       :param code: 短信验证码
       :return:
    """
    sdk = SmsSDK(accId, accToken, appId)
    tid = '1'  # 您的验证码为{1}，请于{2}内正确输入，如非本人操作，请忽略此短信。
    mobile = ",".join(mobiles)
    datas = (code, '5')
    logging.getLogger("django").info(code)  #打印短信验证码
    resp = sdk.sendMessage(tid, mobile, datas)
    resp = json.loads(resp)
    if resp.get("statusCode") == "000000":
        return True
    else:
        return False


if __name__ == '__main__':
    send_sms_code(["13699109260"], "9999")

    # mobile = "18580494008"
    # code = "123456"
    # send_sms_code([mobile], code)
