from datetime import datetime, timedelta

import jwt

key = "zkpfw*%$qjrfono@sdko34@%"


def generate_access_token(user_name: str = "", algorithm: str = 'HS256', exp: float = 2):
    """
    生成access_token
    :param user_name: 自定义部分
    :param algorithm:加密算法
    :param exp:过期时间
    :return:token
    """

    now = datetime.utcnow()
    exp_datetime = now + timedelta(hours=exp)
    access_payload = {
        'exp': exp_datetime,
        'flag': 1,  # 标识是否为一次性token，0是，1不是
        'iat': now,  # 开始时间
        'iss': 'qin',  # 签名
        'user_name': user_name  # 自定义部分
    }
    access_token = jwt.encode(access_payload, key, algorithm=algorithm)
    return access_token


def generate_refresh_token(user_name: str = "", algorithm: str = 'HS256', fresh: float = 30):
    """
    生成refresh_token

    :param user_name: 自定义部分
    :param algorithm:加密算法
    :param fresh:过期时间
    :return:token
    """
    now = datetime.utcnow()
    # 刷新时间为30天
    exp_datetime = now + timedelta(days=fresh)
    refresh_payload = {
        'exp': exp_datetime,
        'flag': 1,  # 标识是否为一次性token，0是，1不是
        'iat': now,  # 开始时间
        'iss': 'qin',  # 签名，
        'user_name': user_name  # 自定义部分
    }

    refresh_token = jwt.encode(refresh_payload, key, algorithm=algorithm)
    return refresh_token

def decode_auth_token(token: str):
    """
    解密token
    :param token:token字符串
    :return:
    """
    try:
        # 取消过期时间验证
        # payload = jwt.decode(token, key, options={'verify_exp': False})
        payload = jwt.decode(token, key=key, )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, jwt.InvalidSignatureError):
        return ""
    else:
        return payload

def identify(auth_header: str):
    """
    用户鉴权
    :return:
    """
    if auth_header:
        payload = decode_auth_token(auth_header)
        if not payload:
            return False
        if "user_name" in payload and "flag" in payload:
            if payload["flag"] == 1:
                # 用来获取新access_token的refresh_token无法获取数据
                return False
            elif payload["flag"] == 0:
                return payload["user_name"]
            else:
                # 其他状态暂不允许
                return False
        else:
            return False
    else:
        return False

from functools import wraps

def login_required(f):
    """
    登陆保护，验证用户是否登陆
    :param f:
    :return:
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", default=None)
        if not token:
            return "请登陆"
        user_name = identify(token)
        if not user_name:
             return "请登陆"
        # 获取到用户并写入到session中,方便后续使用
        session["user_name"] = user_name
        return f(*args, **kwargs)
    return wrapper

def model_to_dict(result):
    '''
    查询结果转换为字典
    :param result:
    :return:
    '''
    from collections import Iterable
    # 转换完成后，删除  '_sa_instance_state' 特殊属性
    try:
        if isinstance(result, Iterable):
            tmp = [dict(zip(res.__dict__.keys(), res.__dict__.values())) for res in result]
            for t in tmp:
                t.pop('_sa_instance_state')
        else:
            tmp = dict(zip(result.__dict__.keys(), result.__dict__.values()))
            tmp.pop('_sa_instance_state')
        return tmp
    except BaseException as e:
        print(e.args)
        raise TypeError('Type error of parameter')

def construct_page_data(data):
    '''
    分页需要返回的数据
    :param data:
    :return:
    '''
    page = {"page_no": data.page,  # 当前页数
            "page_size": data.per_page,  # 每页显示的属性
            "tatal_page": data.pages,  # 总共的页数
            "tatal_count": data.total,  # 查询返回的记录总数
            "is_first_page": True if data.page == 1 else False,  # 是否第一页
            "is_last_page": False if data.has_next else True  # 是否最后一页
            }
    # result = menu_to_dict(data.items)
    result = model_to_dict(data.items)
    data = {"page": page, "list": result}
    return data

import datetime
import decimal
import uuid

from flask.json import JSONEncoder as BaseJSONEncoder


class JSONEncoder(BaseJSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            # 格式化时间
            return o.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(o, datetime.date):
            # 格式化日期
            return o.strftime('%Y-%m-%d')
        if isinstance(o, decimal.Decimal):
            # 格式化高精度数字
            return str(o)
        if isinstance(o, uuid.UUID):
            # 格式化uuid
            return str(o)
        if isinstance(o, bytes):
            # 格式化字节数据
            return o.decode("utf-8")
        return super(JSONEncoder, self).default(o)