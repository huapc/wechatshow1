from flask import request, jsonify, abort
from app import app, db
from sqlalchemy import and_, or_, union
from models import *
import requests
import hashlib
from config.response import ResMsg
from config.code import ResponseCode, ResponseMessage
import json
from sqlalchemy import func
from util import *
from wechatpy import parse_message
from wechatpy import WeChatClient
from wechatpy.replies import TextReply
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import datetime

@app.route('/api/v1.0/wechat/login')
def get_userinfo():
    appid = app.config['APPID']
    openid = request.args.get('openid')
    token = request.args.get('token')
    secret = app.config['APPSECRET']
    s = Serializer(app.config["SECRET_KEY"])
    try:
        # 转换为字典
        data = s.loads(token)
    except Exception:
        res = ResMsg(code=ResponseCode.INVALID_PARAMETER, msg=ResponseMessage.FAIL)
        return (res.data)
    if openid:
        user = User.query.filter_by(openid=openid).first()
        if user:
            res = ResMsg()
            user_dict = dict(nickname=user.nickname, headimgurl=user.headimgurl, openid=user.openid,ismember=user.ismember)
            res.update(data=user_dict)
            return jsonify(res.data)
        else:
            client = WeChatClient(appid, secret)
            userinfo = client.user.get(openid)
            user = User(openid=userinfo['openid'], nickname=userinfo['nickname'], sex=userinfo['sex'],
                   province=userinfo['province'], city=userinfo['city'], country=userinfo['country'],
                  headimgurl=userinfo['headimgurl'])
            db.session.add(user)
            db.session.commit()
            user = User.query.filter_by(openid=openid).first()
            res = ResMsg()
            user_dict = dict(nickname=user.nickname, headimgurl=user.headimgurl, openid=user.openid,ismember=user.ismember)
            res.update(data=user_dict)
            return jsonify(res.data)

    else:
        res = ResMsg(code=ResponseCode.INVALID_PARAMETER, msg=ResponseMessage.FAIL)
        return(res.data)

@app.route('/api/v1.0/wechat/search-tag')
def search_tag():
    #'0-18', '18-25', '26-32', '33-39', '40-46', '46-80'
    "Authorization"
    openid = request.headers.get('Authorization')
    if openid is None:
        openid = request.args.get('openid')
    user = User.query.filter_by(openid=openid).first()
    search_tag = [{'name':'性别', 'data': [{'value': '男', 'tag': 'sex1'}, {'value': '女', 'tag': 'sex2'}]},
                  {'name':'粉丝数','data':[{'value':'500-5000','tag':'follower_num1'},{'value':'100-500','tag':'follower_num2'},{'value':'10-100','tag':'follower_num3'},
                                        {'value':'1-10','tag':'follower_num4'},{'value':'0-1','tag':'follower_num5'}]},
                  {'name': '标签', 'data': [{'value': user.kol_tag1, 'tag': 'tag1'}, {'value': user.kol_tag2, 'tag': 'tag2'},
                                          {'value': user.kol_tag3, 'tag': 'tag3'}]},
                  {'name':'粉丝年龄', 'data': [{'value': '0-18', 'tag': 'fans_age'}, {'value': '18-25', 'tag': 'fans_age'},{'value': '26-32', 'tag': 'fans_age'},
                                           {'value': '33-39', 'tag': 'fans_age'},{'value': '40-46', 'tag': 'fans_age'},{'value': '46-80', 'tag': 'fans_age'}]},
                  {'name': '手机品牌信息', 'data': [{'value': '小米', 'tag': 'fans_phone'}, {'value': '苹果', 'tag': 'fans_phone'},{'value': '华为', 'tag': 'fans_phone'},{'value': 'oppo', 'tag': 'fans_phone'},
                                              {'value': 'vivo', 'tag': 'fans_phone'},{'value': '其他', 'tag': 'fans_phone'}]},
                  {'name': '地域分布', 'data': [{'value': '一线城市', 'tag': 'fans_city'}, {'value': '二线城市', 'tag': 'fans_city'},{'value': '三线城市', 'tag': 'fans_city'}]},
                ]
    res = ResMsg()
    res.update(data=search_tag)
    return jsonify(res.data)

@app.route('/api/v1.0/wechat/kol-list')
def kollist():
    openid = request.headers['Authorization']
    user = User.query.filter_by(openid=openid).first()
    args_dict = request.args.to_dict()
    if args_dict:
        task_filter = []
        for k, v in args_dict.items():
            if v in ['男','女']:
                if request.args.get('sex1') and request.args.get('sex2') is None:
                    task_filter.append(KolList.sex == '男')
                if request.args.get('sex2') and request.args.get('sex1') is None:
                    task_filter.append(KolList.sex == '女')
                if request.args.get('sex1') and request.args.get('sex2'):
                    task_filter.append(or_(KolList.sex == '男', KolList.sex == '女'))
            if v in [user.kol_tag1,user.kol_tag2,user.kol_tag3]:
                #100
                if request.args.get('tag1') and request.args.get('tag2') is None and request.args.get('tag3') is None:
                    task_filter.append(KolList.tag == (request.args.get('tag1')))
                #010
                if request.args.get('tag2') and request.args.get('tag1') is None and request.args.get('tag3') is None:
                    task_filter.append(KolList.tag == (request.args.get('tag2')))
                #001
                if request.args.get('tag3') and request.args.get('tag1') is None and request.args.get('tag2') is None:
                    task_filter.append(KolList.tag == (request.args.get('tag3')))
                #110
                if request.args.get('tag1') and request.args.get('tag2') and request.args.get('tag3') is None:
                    task_filter.append(or_(KolList.tag == request.args.get('tag1'), KolList.tag == request.args.get('tag2')))
                #101
                if request.args.get('tag1') and request.args.get('tag2') is None and request.args.get('tag3'):
                    task_filter.append(or_(KolList.tag == request.args.get('tag1'), KolList.tag == request.args.get('tag3')))
                #011
                if request.args.get('tag1') is None and request.args.get('tag2') and request.args.get('tag3'):
                    task_filter.append(or_(KolList.tag == request.args.get('tag2'), KolList.tag == request.args.get('tag3')))
                #111
                if request.args.get('tag1') and request.args.get('tag2') and request.args.get('tag3'):
                    task_filter.append(or_(KolList.tag == request.args.get('tag1'), KolList.tag == request.args.get('tag2'),KolList.tag == request.args.get('tag2')))
        follower_num = request.args.get('follower_num')
        if follower_num:
            min_max = follower_num.split('-')
            min = int(min_max[0])
            max = int(min_max[1])
            task_filter.append(and_(KolList.follower_num > min * 10000, KolList.follower_num <= max * 10000))
        kol_all = KolList.query.filter(*task_filter).order_by(KolList.follower_num.desc()).limit(100).all()
        data = []
        for kol in kol_all:
            info = {'userid': kol.userid, "nickname": kol.nickname, "sex": kol.sex,
                    "follower_num": kol.follower_num, "age": kol.age, "tag": kol.tag,
                    "video_count": kol.video_count,
                    "cooperate_index": kol.cooperate_index, "douyin_id": kol.douyin_id,
                    "growth_index": kol.growth_index, "spread_index": kol.spread_index,
                    "total_video_count": kol.fans_attribute.total_video_count, "cp_index": kol.cp_index,
                    "star_map_index": kol.star_map_index, "shopping_index": kol.shopping_index,"avatar":kol.fans_attribute.avatar}
            data.append(info)
        res = ResMsg()
        res.update(data=data)
        return jsonify(res.data)
    else:
        #默认查询
        kols = KolList.query.order_by(KolList.follower_num.desc()).limit(100).all()
        data = []
        for kol in kols:
            info = {'userid': kol.userid, "nickname": kol.nickname, "sex": kol.sex,
                    "follower_num": kol.follower_num, "age": kol.age, "tag": kol.tag,
                    "video_count": kol.video_count,
                    "cooperate_index": kol.cooperate_index, "douyin_id": kol.douyin_id,
                    "growth_index": kol.growth_index, "spread_index": kol.spread_index,
                    "total_video_count": kol.fans_attribute.total_video_count, "cp_index": kol.cp_index,
                    "star_map_index": kol.star_map_index, "shopping_index": kol.shopping_index,"avatar":kol.fans_attribute.avatar}
            data.append(info)
        res = ResMsg()
        res.update(data=data)
        return jsonify(res.data)
@app.route('/api/v1.0/wechat/fans-portrait')
def fans_portrait():
    args_dict = request.args.to_dict()
    if args_dict:
        # 基础合集
        kol_all = KolList.query.filter(KolList.sex == '').limit(100)
        for k, v in args_dict.items():
            if v in ['iPhone','OPPO','vivo','others','huawei','xiaomi']:
                kols_fans = db.session.query(KolList).join(PhoneAgeInfo, KolList.userid == PhoneAgeInfo.userid).order_by(eval(f'PhoneAgeInfo.{v}')).limit(100)
            if v in ['less_18', 'age_18_25', 'age_26_32','age_33_39','age_40_46','greater_46']:
                kols_fans = db.session.query(KolList).join(PhoneAgeInfo,KolList.userid == PhoneAgeInfo.userid).order_by(eval(f'PhoneAgeInfo.{v}')).limit(100)
            if v in ['one_city', 'two_city', 'three_city']:
                kols_fans = db.session.query(KolList).join(PhoneAgeInfo,KolList.userid == PhoneAgeInfo.userid).order_by(eval(f'PhoneAgeInfo.{v}')).limit(100)
            kol_all = kol_all.union(kols_fans)
        kol_all = kol_all.order_by(KolList.follower_num.desc()).limit(100).all()
        data = []
        for kol in kol_all:
            info = {'userid': kol.userid, "nickname": kol.nickname, "sex": kol.sex,
                    "follower_num": kol.follower_num, "age": kol.age, "tag": kol.tag,
                    "video_count": kol.video_count,
                    "cooperate_index": kol.cooperate_index, "douyin_id": kol.douyin_id,
                    "growth_index": kol.growth_index, "spread_index": kol.spread_index,
                    "total_video_count": kol.fans_attribute.total_video_count, "cp_index": kol.cp_index,
                    "star_map_index": kol.star_map_index, "shopping_index": kol.shopping_index,"avatar":kol.fans_attribute.avatar}
            data.append(info)
        res = ResMsg()
        res.update(data=data)
        return jsonify(res.data)
    else:
        # 默认查询
        kols = KolList.query.order_by(KolList.follower_num.desc()).limit(100).all()
        data = []
        for kol in kols:
            info = {'userid': kol.userid, "nickname": kol.nickname, "sex": kol.sex,
                    "follower_num": kol.follower_num, "age": kol.age, "tag": kol.tag,
                    "video_count": kol.video_count,
                    "cooperate_index": kol.cooperate_index, "douyin_id": kol.douyin_id,
                    "growth_index": kol.growth_index, "spread_index": kol.spread_index,
                    "total_video_count": kol.fans_attribute.total_video_count, "cp_index": kol.cp_index,
                    "star_map_index": kol.star_map_index, "shopping_index": kol.shopping_index,"avatar":kol.fans_attribute.avatar}
            data.append(info)
        res = ResMsg()
        res.update(data=data)
        return jsonify(res.data)

@app.route('/api/v1.0/wechat/kol-detail')
def kol_detail():
    userid = request.args.get('userid')
    if userid is not None:
        fans_attribute = FansAttribute.query.filter_by(userid=userid).first()
        info = {"avg_play":float(fans_attribute.avg_play),
                "avg_like":float(fans_attribute.avg_like),
                "avg_comment":int(fans_attribute.avg_comment),
                "total_video_count": int(fans_attribute.total_video_count),
                "video_count_15": int(fans_attribute.video_count_15),
                "video_count_30": int(fans_attribute.video_count_30),
                "avg_interaction_15":int(fans_attribute.avg_interaction_15),
                "avg_interaction_30":int(fans_attribute.avg_interaction_30),
                "total_video_avg_interaction":fans_attribute.total_video_avg_interaction,
                "iPhone": fans_attribute.kol.phone_age_info.iPhone,
                "OPPO":fans_attribute.kol.phone_age_info.OPPO,
                "vivo": fans_attribute.kol.phone_age_info.vivo,
                "huawei":fans_attribute.kol.phone_age_info.huawei,
                "xiaomi":fans_attribute.kol.phone_age_info.xiaomi,
                "others":fans_attribute.kol.phone_age_info.others,"less_18":fans_attribute.kol.phone_age_info.less_18,
                "age_18_25":fans_attribute.kol.phone_age_info.age_18_25,"age_26_32":fans_attribute.kol.phone_age_info.age_26_32,
                "age_33_39":fans_attribute.kol.phone_age_info.age_33_39,"age_40_46":fans_attribute.kol.phone_age_info.age_40_46,
                "greater_46":fans_attribute.kol.phone_age_info.greater_46,
                "male":fans_attribute.kol.phone_age_info.male,"female":fans_attribute.kol.phone_age_info.female,
                "one_city":int(fans_attribute.kol.phone_age_info.one_city),"two_city": int(fans_attribute.kol.phone_age_info.two_city),
                "three_city":int(fans_attribute.kol.phone_age_info.three_city),"mcn_name":fans_attribute.kol.mcn_name
                }
        region_dict = fans_attribute.kol.region.__dict__
        region_dict.pop('_sa_instance_state')
        info.update(region_dict)
        res = ResMsg()
        res.update(data=info)
        return jsonify(res.data)

@app.route('/api/v1.0/wechat/cmm-list')
def cmm():
    #cmmall = CmmAll.query.filter(CmmAll.rank <= 100).all()
    cmmall = CmmAll.query.order_by(CmmAll.rank.asc()).limit(100).all()
    data = []
    for cmm in cmmall:
        info = {"promotion_id":cmm.promotion_id,"author_number": cmm.author_number, "brand_name": cmm.brand_name,
                "day_order_count": cmm.day_order_count,"platform": cmm.platform,"coupon_price":cmm.coupon_price,"image":cmm.image,
                "market_price":cmm.market_price,"money":cmm.money,"month_conversion_rate":cmm.month_conversion_rate,"order_count":cmm.order_count}
        data.append(info)
    res = ResMsg()
    res.update(data=data)
    return jsonify(res.data)

@app.route('/api/v1.0/wechat/cmm-detail')
def cmm_detail():
    promotion_id = request.args.get('promotion_id')
    if promotion_id:
        cmm_detail = CmmAll.query.filter_by(promotion_id=promotion_id).first()
        header = Header.query.filter_by(promotion_id=promotion_id).first()
        age_sex_region = AgeSexRegion.query.filter_by(promotion_id=promotion_id).first()
        basic = Basic.query.filter_by(promotion_id=promotion_id).first()
        # info = {'author_number':cmm_detail.author_number,'brand_name':cmm_detail.brand_name,'coupon_price':cmm_detail.coupon_price}
        cmm_dict = cmm_detail.__dict__
        header_dict = header.__dict__
        age_sex_region_dict = age_sex_region.__dict__
        basic_dict = basic.__dict__

        cmm_dict.pop('_sa_instance_state')
        header_dict.pop('_sa_instance_state')
        age_sex_region_dict.pop('_sa_instance_state')
        basic_dict.pop('_sa_instance_state')
        code = basic_dict['basic']
        code = eval(code.strip("'"))
        basic_dict['basic'] = code

        cmm_dict.update(header_dict)
        cmm_dict.update(age_sex_region_dict)
        cmm_dict.update(basic_dict)

        res = ResMsg()
        res.update(data=cmm_dict)

        '''
        if age_sex_region_dict:
            age_sex_region_dict.pop('_sa_instance_state')
        if header is not None:
            header_dict = header.__dict__
            cmm_dict.pop('_sa_instance_state')
            header_dict.pop('_sa_instance_state')
            cmm_dict.update(header_dict)
            res = ResMsg()
            res.update(data=cmm_dict)
        else:
            cmm_dict.pop('_sa_instance_state')
            res = ResMsg()
            res.update(data=cmm_dict)
        '''

        return jsonify(res.data)

#微信服务器验证
@app.route('/api/v1.0/wechat', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        xml = bytes.decode(request.data)
        msg = parse_message(xml)
        openid = msg.source
        s = Serializer(app.config["SECRET_KEY"], expires_in=600)
        token = s.dumps({"openid": openid}).decode("ascii")
        content = f'http://wxclub.qitenggroup.com?openid={openid}&token={token}'
        #短网址
        appid = 'wx72a2bac687b9a16c'
        secret = 'dfb9975abb1fff18bc3a7b0273988d60'
        client = WeChatClient(appid, secret)
        res = client.misc.short_url(content)
        content=res['short_url']

        tips = '点击链接查看详情,如无权限请联系您对应的业务员开通'
        reply = TextReply(content=(tips+content), message=msg)
        xml = reply.render()
        return xml
    else:
        token = app.config['TOKEN']
        signature = request.args.get('signature')
        timestamp = request.args.get('timestamp')
        nonce = request.args.get('nonce')
        echostr = request.args.get('echostr')

        list = [token, timestamp, nonce]
        list.sort()
        tmp_str = ''.join(list).encode('utf-8')
        sign = hashlib.sha1(tmp_str).hexdigest()

        if signature != sign:
            abort(403)
        else:
            return echostr

#后台管理
@app.route('/api/v1.0/wechat/admin/login', methods=['POST'])
def admin_login():
    username = request.json['username']
    password = request.json['password']

    if username == 'admin' and password == '123':
        access_token = generate_access_token(user_name=username)
        data = {"access_token": access_token.decode("utf-8"),'isLogin': True}
        res = ResMsg()
        res.update(data=data)
        return jsonify(res.data)
    else:
        data = {'isLogin': False}
        res = ResMsg()
        res.update(data=data)
        return jsonify(res.data)

@app.route('/api/v1.0/wechat/admin/users', methods=['GET','POST'])
def admin_users():
    if request.method == 'GET':
        users = User.query.all()
        data = []
        for user in users:
            info = {'nickname':user.nickname,'sex':user.sex,'headimgurl':user.headimgurl,'openid':user.openid,
                    'kol_tag1':user.kol_tag1,'kol_tag2':user.kol_tag2,'kol_tag3':user.kol_tag3, 'isMenber':user.ismember,
                    'audit':user.audit,'mobile':user.mobile,'category':user.category,'shopurl':user.shopurl,'expiredate':user.expiredate,
                    'name':user.name,'supplier':user.supplier,'expiredate':user.expiredate,'signdate':user.signdate,'shop':user.shop}
            data.append(info)
        res = ResMsg()
        res.update(data=data)
        return jsonify(res.data)
    else:
        #提交主管审核
        audit = request.json['audit']
        openid = request.json['openid']
        kol_tag1 = request.json['kol_tag1']
        kol_tag2 = request.json['kol_tag2']
        kol_tag3 = request.json['kol_tag3']
        mobile = request.json['mobile']
        expiredate = request.json['expiredate']
        shop = request.json['shop']
        supplier = request.json['supplier']
        name = request.json['name']
        user = User.query.filter_by(openid=openid).first()
        user.audit = audit
        user.kol_tag1 = kol_tag1
        user.kol_tag2 = kol_tag2
        user.kol_tag3 = kol_tag3
        user.expiredate = expiredate
        user.shop = shop
        user.mobile = mobile
        user.supplier = supplier
        user.name = name
        db.session.commit()
        res = ResMsg()
        return jsonify(res.data)
@app.route('/api/v1.0/wechat/admin/lead-users', methods=['GET','POST'])
def lead_users():
    if request.method == 'GET':
        users = User.query.all()
        data = []
        for user in users:
            info = {'nickname':user.nickname,'sex':user.sex,'headimgurl':user.headimgurl,'openid':user.openid,
                    'kol_tag1':user.kol_tag1,'kol_tag2':user.kol_tag2,'kol_tag3':user.kol_tag3, 'isMenber':user.ismember,
                    'audit':user.audit,'mobile':user.mobile,'category':user.category,'shopurl':user.shopurl,'expiredate':user.expiredate,
                    'name':user.name,'supplier':user.supplier,'expiredate':user.expiredate,'signdate':user.signdate,'shop':user.shop}
            data.append(info)
        res = ResMsg()
        res.update(data=data)
        return jsonify(res.data)
    else:
        #审核
        ismember = request.json['ismember']
        openid = request.json['openid']
        kol_tag1 = request.json['kol_tag1']
        kol_tag2 = request.json['kol_tag2']
        kol_tag3 = request.json['kol_tag3']
        user = User.query.filter_by(openid=openid).first()
        user.ismember = ismember
        user.kol_tag1 = kol_tag1
        user.kol_tag2 = kol_tag2
        user.kol_tag3 = kol_tag3
        db.session.commit()
        res = ResMsg()
        return jsonify(res.data)
@app.route('/api/v1.0/wechat/admin/tags', methods=['GET'])
def admin_tags():
    tags = KolList.query.with_entities(KolList.tag).distinct().all()
    info = []
    for tag in tags:
        info.append(tag)
    res = ResMsg()
    res.update(data=info)
    return jsonify(res.data)

#客户修改标签,每月3次
@app.route('/api/v1.0/wechat/update-tags', methods=['POST'])
def update_tags():
    openid = request.json['openid']
    kol_tag1 = request.json['kol_tag1']
    kol_tag2 = request.json['kol_tag2']
    kol_tag3 = request.json['kol_tag3']

    user = User.query.filter_by(openid=openid).first()
    update_time = user.tag_update_time
    update_time_month = update_time.month
    now_time_month = datetime.datetime.now().month

    if update_time_month == now_time_month:
        if user.update_num <= 3:
            user.kol_tag1 = kol_tag1
            user.kol_tag2 = kol_tag2
            user.kol_tag3 = kol_tag3
            user.update_num = user.update_num + 1
            db.session.commit()
            res = ResMsg()
            return jsonify(res.data)
        else:
            res = ResMsg(code=ResponseCode.INVALID_PARAMETER, msg=ResponseMessage.FAIL)
            return (res.data)
    else:
        user.kol_tag1 = kol_tag1
        user.kol_tag2 = kol_tag2
        user.kol_tag3 = kol_tag3
        user.update_num = 1
        db.session.commit()
        res = ResMsg()
        return jsonify(res.data)


