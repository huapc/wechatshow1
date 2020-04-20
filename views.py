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

@app.route('/login')
def get_userinfo():
    appid = app.config['APPID']
    code = request.args.get('code')
    secret = app.config['APPSECRET']
    if code:
        access_token_url = f'https://api.weixin.qq.com/sns/oauth2/access_token?appid={appid}&secret={secret}&code={code}&grant_type=authorization_code'
        r = requests.get(access_token_url)
        access_json = r.json()
        access_token = access_json['access_token']
        openid = access_json['openid']
        if access_token:
            user = User.query.filter_by(openid=openid).first()
            if user is None:
                user_info_url = f'https://api.weixin.qq.com/sns/userinfo?access_token={access_token}&openid={openid}&lang=zh_CN'
                r = requests.get(user_info_url)
                r.encoding = 'utf-8'
                userinfo = r.json()
                user = User(openid=userinfo['openid'], nickname=userinfo['nickname'], sex=userinfo['sex'],
                       province=userinfo['province'], city=userinfo['city'], country=userinfo['country'],
                      headimgurl=userinfo['headimgurl'])
                db.session.add(user)
                db.session.commit()
            else:
                user_info_url = f'https://api.weixin.qq.com/sns/userinfo?access_token={access_token}&openid={openid}&lang=zh_CN'
                r = requests.get(user_info_url)
                r.encoding = 'utf-8'
                userinfo = r.json()
                print(userinfo)
                user.nickname = userinfo['nickname']
                user.sex = userinfo['sex']
                user.province = userinfo['province']
                user.city = userinfo['city']
                user.country = userinfo['country']
                user.headimgurl = userinfo['headimgurl']
                db.session.commit()
            user = User.query.filter_by(openid=openid).first()
            res = ResMsg()
            user_dict = dict(nickname=user.nickname,headimgurl=user.headimgurl,openid=user.openid,ismember=user.ismember)
            res.update(data=user_dict)
            return jsonify(res.data)
    else:
        res = ResMsg(code=ResponseCode.INVALID_PARAMETER, msg=ResponseMessage.FAIL)
        return(res.data)

@app.route('/search-tag')
def search_tag():
    #'0-18', '18-25', '26-32', '33-39', '40-46', '46-80'
    search_tag = [{'name':'性别', 'data': [{'value': '男', 'tag': 'sex1'}, {'value': '女', 'tag': 'sex2'}]},
                  {'name':'粉丝数','data':[{'value':'500-5000','tag':'follower_num1'},{'value':'100-500','tag':'follower_num2'},{'value':'10-100','tag':'follower_num3'},
                                        {'value':'1-10','tag':'follower_num4'},{'value':'0-1','tag':'follower_num5'}]},
                  {'name': '标签', 'data': [{'value': '美女', 'tag': 'tag1'}, {'value': '汽车知识', 'tag': 'tag2'},
                                          {'value': '剧情', 'tag': 'tag3'},{'value': '舞蹈', 'tag': 'tag4'},
                                          {'value': '搞笑', 'tag': 'tag5'},{'value': '歌曲演唱', 'tag': 'tag6'},]},
                  {'name':'粉丝年龄', 'data': [{'value': '0-18', 'tag': 'fans_age'}, {'value': '18-25', 'tag': 'fans_age'},{'value': '26-32', 'tag': 'fans_age'},
                                           {'value': '33-39', 'tag': 'fans_age'},{'value': '40-46', 'tag': 'fans_age'},{'value': '46-80', 'tag': 'fans_age'}]},
                  {'name': '手机品牌信息', 'data': [{'value': '小米', 'tag': 'fans_phone'}, {'value': '苹果', 'tag': 'fans_phone'},{'value': '华为', 'tag': 'fans_phone'},{'value': 'oppo', 'tag': 'fans_phone'},
                                              {'value': 'vivo', 'tag': 'fans_phone'},{'value': '其他', 'tag': 'fans_phone'}]},
                  {'name': '地域分布', 'data': [{'value': '一线城市', 'tag': 'fans_city'}, {'value': '二线城市', 'tag': 'fans_city'},{'value': '三线城市', 'tag': 'fans_city'}]},
                ]
    res = ResMsg()
    res.update(data=search_tag)
    return jsonify(res.data)

@app.route('/kol-list')
def kollist():
    args_dict = request.args.to_dict()
    for k,v in args_dict.items():
        print(k,v)
    if args_dict:
        #基础合集
        kol_all = KolList.query.filter(KolList.sex == '').limit(100)
        for k, v in args_dict.items():
            if k in ['sex1','sex2']:
                kols = KolList.query.filter(KolList.sex == v).order_by(KolList.follower_num.desc()).limit(100)
            if k in ['美女','汽车知识','舞蹈']:
                kols = KolList.query.filter(KolList.tag == v).order_by(KolList.follower_num.desc()).limit(100)
            if k in ['500-5000', '100-500','10-100','0-10']:
                min_max = v.split('-')
                min = int(min_max[0])
                max = int(min_max[1])
                kols = KolList.query.filter(and_(KolList.follower_num > min * 10000, KolList.follower_num <= max * 10000)).order_by(KolList.follower_num.desc()).limit(100)
            if k in ['one_city', 'two_city', 'three_city']:
                kols = KolList.query.order_by(KolList.phone_age_info.one_city).limit(100)
            kol_all = kol_all.union(kols)
        kol_all = kol_all.order_by(KolList.follower_num.desc()).limit(100).all()
        data = []
        for kol in kol_all:
            info = {'userid': kol.userid, "nickname": kol.nickname, "sex": kol.sex,
                    "follower_num": kol.follower_num, "age": kol.age, "tag": kol.tag,
                    "video_count": kol.video_count,
                    "cooperate_index": kol.cooperate_index, "douyin_id": kol.douyin_id,
                    "growth_index": kol.growth_index, "spread_index": kol.spread_index,
                    "total_video_count": kol.fans_attribute.total_video_count, "cp_index": kol.cp_index,
                    "star_map_index": kol.star_map_index, "shopping_index": kol.shopping_index}
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
                    "star_map_index": kol.star_map_index, "shopping_index": kol.shopping_index}
            data.append(info)
        res = ResMsg()
        res.update(data=data)
        return jsonify(res.data)

    sex1 = request.args.get('sex1')
    sex2 = request.args.get('sex2')

    follower_num1 = request.args.get('follower_num1')
    follower_num2 = request.args.get('follower_num2')
    follower_num3 = request.args.get('follower_num3')
    follower_num4 = request.args.get('follower_num4')
    follower_num5 = request.args.get('follower_num5')
    min_max1 = follower_num1.split('-')
    min1 = int(min_max1[0])
    max1 = int(min_max1[1])
    min_max2 = follower_num2.split('-')
    min2 = int(min_max2[0])
    max2 = int(min_max2[1])
    min_max3 = follower_num3.split('-')
    min3 = int(min_max3[0])
    max3 = int(min_max3[1])
    min_max4 = follower_num4.split('-')
    min4 = int(min_max4[0])
    max4 = int(min_max4[1])
    min_max5 = follower_num5.split('-')
    min5 = int(min_max5[0])
    max5 = int(min_max5[1])

    tag1 = request.args.get('tag1')
    tag2 = request.args.get('tag2')
    tag3 = request.args.get('tag3')
    tag4 = request.args.get('tag4')
    tag5 = request.args.get('tag5')
    tag6 = request.args.get('tag6')
    tag7 = request.args.get('tag7')
    tag8 = request.args.get('tag8')
    tag9 = request.args.get('tag9')
    tag10 = request.args.get('tag10')
    tag11 = request.args.get('tag11')
    tag12 = request.args.get('tag12')
    tag13 = request.args.get('tag13')
    tag14 = request.args.get('tag14')

    """
    fans_age1 = request.args.get('fans_age1')
    fans_age2 = request.args.get('fans_age2')
    fans_age3 = request.args.get('fans_age3')
    fans_age4 = request.args.get('fans_age4')
    fans_age5 = request.args.get('fans_age5')
    fans_age6 = request.args.get('fans_age6')

    fans_phone1 = request.args.get('fans_phone1')
    fans_phone2 = request.args.get('fans_phone2')
    fans_phone3 = request.args.get('fans_phone3')
    fans_phone4 = request.args.get('fans_phone4')
    fans_phone5 = request.args.get('fans_phone5')

    fans_city1 = request.args.get('fans_city1')
    fans_city2 = request.args.get('fans_city2')
    fans_city3 = request.args.get('fans_city3')


    age_min_max1 = fans_age1.split('-')
    age_min1 = int(age_min_max1[0])
    age_max1 = int(age_min_max1[1])
    age_min_max2 = fans_age2.split('-')
    age_min2 = int(age_min_max2[0])
    age_max2 = int(age_min_max2[1])
    age_min_max3 = fans_age3.split('-')
    age_min3 = int(age_min_max3[0])
    age_max3 = int(age_min_max3[1])
    age_min_max4 = fans_age4.split('-')
    age_min4 = int(age_min_max4[0])
    age_max4 = int(age_min_max4[1])
    age_min_max5 = fans_age5.split('-')
    age_min5 = int(age_min_max5[0])
    age_max5 = int(age_min_max5[1])
    age_min_max6 = fans_age6.split('-')
    age_min6 = int(age_min_max6[0])
    age_max6 = int(age_min_max6[1])


    task_filter = [
        or_(
            KolList.sex == sex1,
            KolList.sex == sex2,
        ),
        or_(
            and_(
                KolList.follower_num > min1 * 10000,
                KolList.follower_num <= max1 *10000
            ),
            and_(
                KolList.follower_num > min2 *10000,
                KolList.follower_num <= max2 *10000
            ),
            and_(
                KolList.follower_num > min3 * 10000,
                KolList.follower_num <= max3 * 10000
            ),
            and_(
                KolList.follower_num > min4 * 10000,
                KolList.follower_num <= max4 * 10000
            ),
            and_(
                KolList.follower_num > min5 * 10000,
                KolList.follower_num <= max5 * 10000
            ),
        ),
        or_(
            KolList.tag == tag1,
            KolList.tag == tag2,
            KolList.tag == tag3,
            KolList.tag == tag4,
            KolList.tag == tag5,
            KolList.tag == tag6,
            KolList.tag == tag7,
            KolList.tag == tag8,
            KolList.tag == tag9,
            KolList.tag == tag10,
            KolList.tag == tag12,
            KolList.tag == tag13,
            KolList.tag == tag13,
            KolList.tag == tag14
        ),
    ]
    kols = KolList.query.filter(*task_filter).order_by(KolList.follower_num.desc()).limit(100).all()
    # '0-18','18-25','26-32','33-39','40-46','46-80'
    fans_ages = [fans_age1,fans_age2,fans_age3,fans_age4,fans_age5,fans_age6]
    kols_fans_all = db.session.query(KolList).join(PhoneAgeInfo, KolList.userid == PhoneAgeInfo.userid).filter(and_(*task_filter)).order_by(PhoneAgeInfo.age_18_25)
    for fans_age in fans_ages:
        if fans_age:
            if fans_age == '0-18':
                kols_fans = db.session.query(KolList).join(PhoneAgeInfo, KolList.userid == PhoneAgeInfo.userid).filter(and_(*task_filter)).order_by(PhoneAgeInfo.age_18_25)
                kols_fans_all.union(kols_fans)
            if fans_age == '18-25':
                kols_fans = db.session.query(KolList).join(PhoneAgeInfo, KolList.userid == PhoneAgeInfo.userid).filter(and_(*task_filter)).order_by(PhoneAgeInfo.age_18_25)
                kols_fans_all.union(kols_fans)
            if fans_age == '26-32':
                kols_fans = db.session.query(KolList).join(PhoneAgeInfo, KolList.userid == PhoneAgeInfo.userid).filter(and_(*task_filter)).order_by(PhoneAgeInfo.age_26_32)
                kols_fans_all.union(kols_fans)
            if fans_age == '33-39':
                kols_fans = db.session.query(KolList).join(PhoneAgeInfo, KolList.userid == PhoneAgeInfo.userid).filter(and_(*task_filter)).order_by(PhoneAgeInfo.age_33_39)
                kols_fans_all.union(kols_fans)
            if fans_age == '40-46':
                kols_fans = db.session.query(KolList).join(PhoneAgeInfo, KolList.userid == PhoneAgeInfo.userid).filter(and_(*task_filter)).order_by(PhoneAgeInfo.age_40_46)
                kols_fans_all.union(kols_fans)
            if fans_age == '46-80':
                kols_fans = db.session.query(KolList).join(PhoneAgeInfo, KolList.userid == PhoneAgeInfo.userid).filter(and_(*task_filter)).order_by(PhoneAgeInfo.greater_46)
                kols_fans_all.union(kols_fans)
    data = []
    kols_fans_all = kols_fans.order_by().limit(100).all()
    print()
    for kol in kols_fans_all:
        info = {'userid': kol.userid, "nickname": kol.nickname, "sex": kol.sex,
                "follower_num": kol.follower_num, "age": kol.age, "tag": kol.tag,
                "video_count": kol.video_count,
                "cooperate_index": kol.cooperate_index, "douyin_id": kol.douyin_id,
                "growth_index": kol.growth_index, "spread_index": kol.spread_index,
                "total_video_count": kol.fans_attribute.total_video_count, "cp_index": kol.cp_index,
                "star_map_index": kol.star_map_index, "shopping_index": kol.shopping_index}
        data.append(info)
    res = ResMsg()
    res.update(data=data)
    return jsonify(res.data)

    if fans_phone is not None:
        if fans_phone == '苹果':
            kols_fans = db.session.query(KolList).join(PhoneAgeInfo, KolList.userid == PhoneAgeInfo.userid).filter(and_(*task_filter)).order_by(PhoneAgeInfo.iPhone).limit(100).all()
            data = []
            for kol in kols_fans:
                info = {'userid': kol.userid, "nickname": kol.nickname, "sex": kol.sex,
                        "follower_num": kol.follower_num, "age": kol.age, "tag": kol.tag,
                        "video_count": kol.video_count,
                        "cooperate_index": kol.cooperate_index, "douyin_id": kol.douyin_id,
                        "growth_index": kol.growth_index, "spread_index": kol.spread_index,
                        "total_video_count": kol.fans_attribute.total_video_count, "cp_index": kol.cp_index,
                        "star_map_index": kol.star_map_index, "shopping_index": kol.shopping_index}
                data.append(info)
            res = ResMsg()
            res.update(data=data)
            return jsonify(res.data)
        if fans_phone == '小米':
            kols_fans = db.session.query(KolList).join(PhoneAgeInfo, KolList.userid == PhoneAgeInfo.userid).filter(and_(*task_filter)).order_by(PhoneAgeInfo.xiaomi).limit(100).all()
            data = []
            for kol in kols_fans:
                info = {'userid': kol.userid, "nickname": kol.nickname, "sex": kol.sex,
                        "follower_num": kol.follower_num, "age": kol.age, "tag": kol.tag,
                        "video_count": kol.video_count,
                        "cooperate_index": kol.cooperate_index, "douyin_id": kol.douyin_id,
                        "growth_index": kol.growth_index, "spread_index": kol.spread_index,
                        "total_video_count": kol.fans_attribute.total_video_count, "cp_index": kol.cp_index,
                        "star_map_index": kol.star_map_index, "shopping_index": kol.shopping_index}
                data.append(info)
            res = ResMsg()
            res.update(data=data)
            return jsonify(res.data)
        if fans_phone == '华为':
            kols_fans = db.session.query(KolList).join(PhoneAgeInfo, KolList.userid == PhoneAgeInfo.userid).filter(and_(*task_filter)).order_by(PhoneAgeInfo.huawei).limit(100).all()
            data = []
            for kol in kols_fans:
                info = {'userid': kol.userid, "nickname": kol.nickname, "sex": kol.sex,
                        "follower_num": kol.follower_num, "age": kol.age, "tag": kol.tag,
                        "video_count": kol.video_count,
                        "cooperate_index": kol.cooperate_index, "douyin_id": kol.douyin_id,
                        "growth_index": kol.growth_index, "spread_index": kol.spread_index,
                        "total_video_count": kol.fans_attribute.total_video_count, "cp_index": kol.cp_index,
                        "star_map_index": kol.star_map_index, "shopping_index": kol.shopping_index}
                data.append(info)
            res = ResMsg()
            res.update(data=data)
            return jsonify(res.data)
        if fans_phone == 'oppo':
            kols_fans = db.session.query(KolList).join(PhoneAgeInfo, KolList.userid == PhoneAgeInfo.userid).filter(and_(*task_filter)).order_by(PhoneAgeInfo.OPPO).limit(100).all()
            data = []
            for kol in kols_fans:
                info = {'userid': kol.userid, "nickname": kol.nickname, "sex": kol.sex,
                        "follower_num": kol.follower_num, "age": kol.age, "tag": kol.tag,
                        "video_count": kol.video_count,
                        "cooperate_index": kol.cooperate_index, "douyin_id": kol.douyin_id,
                        "growth_index": kol.growth_index, "spread_index": kol.spread_index,
                        "total_video_count": kol.fans_attribute.total_video_count, "cp_index": kol.cp_index,
                        "star_map_index": kol.star_map_index, "shopping_index": kol.shopping_index}
                data.append(info)
            res = ResMsg()
            res.update(data=data)
            return jsonify(res.data)
        if fans_phone == 'vivo':
            kols_fans = db.session.query(KolList).join(PhoneAgeInfo, KolList.userid == PhoneAgeInfo.userid).filter(and_(*task_filter)).order_by(PhoneAgeInfo.vivo).limit(100).all()
            data = []
            for kol in kols_fans:
                info = {'userid': kol.userid, "nickname": kol.nickname, "sex": kol.sex,
                        "follower_num": kol.follower_num, "age": kol.age, "tag": kol.tag,
                        "video_count": kol.video_count,
                        "cooperate_index": kol.cooperate_index, "douyin_id": kol.douyin_id,
                        "growth_index": kol.growth_index, "spread_index": kol.spread_index,
                        "total_video_count": kol.fans_attribute.total_video_count, "cp_index": kol.cp_index,
                        "star_map_index": kol.star_map_index, "shopping_index": kol.shopping_index}
                data.append(info)
            res = ResMsg()
            res.update(data=data)
            return jsonify(res.data)
        if fans_phone == '其他':
            kols_fans = db.session.query(KolList).join(PhoneAgeInfo, KolList.userid == PhoneAgeInfo.userid).filter(and_(*task_filter)).order_by(PhoneAgeInfo.others).limit(100).all()
            data = []
            for kol in kols_fans:
                info = {'userid': kol.userid, "nickname": kol.nickname, "sex": kol.sex,
                        "follower_num": kol.follower_num, "age": kol.age, "tag": kol.tag,
                        "video_count": kol.video_count,
                        "cooperate_index": kol.cooperate_index, "douyin_id": kol.douyin_id,
                        "growth_index": kol.growth_index, "spread_index": kol.spread_index,
                        "total_video_count": kol.fans_attribute.total_video_count, "cp_index": kol.cp_index,
                        "star_map_index": kol.star_map_index, "shopping_index": kol.shopping_index}
                data.append(info)
            res = ResMsg()
            res.update(data=data)
            return jsonify(res.data)

    if fans_city is not None:
        if fans_city == '一线城市':
            kols_fans = db.session.query(KolList).join(PhoneAgeInfo, KolList.userid == PhoneAgeInfo.userid).filter(
                and_(*task_filter)).order_by(PhoneAgeInfo.one_city).limit(100).all()
            data = []
            for kol in kols_fans:
                info = {'userid': kol.userid, "nickname": kol.nickname, "sex": kol.sex,
                        "follower_num": kol.follower_num, "age": kol.age, "tag": kol.tag,
                        "video_count": kol.video_count,
                        "cooperate_index": kol.cooperate_index, "douyin_id": kol.douyin_id,
                        "growth_index": kol.growth_index, "spread_index": kol.spread_index,
                        "total_video_count": kol.fans_attribute.total_video_count, "cp_index": kol.cp_index,
                        "star_map_index": kol.star_map_index, "shopping_index": kol.shopping_index}
                data.append(info)
            res = ResMsg()
            res.update(data=data)
            return jsonify(res.data)
        if fans_city == '二线城市':
            kols_fans = db.session.query(KolList).join(PhoneAgeInfo, KolList.userid == PhoneAgeInfo.userid).filter(
                and_(*task_filter)).order_by(PhoneAgeInfo.two_city).limit(100).all()
            data = []
            for kol in kols_fans:
                info = {'userid': kol.userid, "nickname": kol.nickname, "sex": kol.sex,
                        "follower_num": kol.follower_num, "age": kol.age, "tag": kol.tag,
                        "video_count": kol.video_count,
                        "cooperate_index": kol.cooperate_index, "douyin_id": kol.douyin_id,
                        "growth_index": kol.growth_index, "spread_index": kol.spread_index,
                        "total_video_count": kol.fans_attribute.total_video_count, "cp_index": kol.cp_index,
                        "star_map_index": kol.star_map_index, "shopping_index": kol.shopping_index}
                data.append(info)
            res = ResMsg()
            res.update(data=data)
            return jsonify(res.data)
        if fans_city == '三线城市':
            kols_fans = db.session.query(KolList).join(PhoneAgeInfo, KolList.userid == PhoneAgeInfo.userid).filter(
                and_(*task_filter)).order_by(PhoneAgeInfo.three_city).limit(100).all()
            data = []
            for kol in kols_fans:
                info = {'userid': kol.userid, "nickname": kol.nickname, "sex": kol.sex,
                        "follower_num": kol.follower_num, "age": kol.age, "tag": kol.tag,
                        "video_count": kol.video_count,
                        "cooperate_index": kol.cooperate_index, "douyin_id": kol.douyin_id,
                        "growth_index": kol.growth_index, "spread_index": kol.spread_index,
                        "total_video_count": kol.fans_attribute.total_video_count, "cp_index": kol.cp_index,
                        "star_map_index": kol.star_map_index, "shopping_index": kol.shopping_index}
                data.append(info)
            res = ResMsg()
            res.update(data=data)
            return jsonify(res.data)

    data = []
    for kol in kols:
        info = {'userid': kol.userid,"nickname": kol.nickname,"sex":kol.sex,"follower_num": kol.follower_num, "age": kol.age, "tag": kol.tag,"video_count":kol.video_count,
                "cooperate_index":kol.cooperate_index,"douyin_id":kol.douyin_id,"growth_index":kol.growth_index,"spread_index":kol.spread_index,
                "total_video_count":kol.fans_attribute.total_video_count,"cp_index":kol.cp_index,"star_map_index":kol.star_map_index,"shopping_index":kol.shopping_index,
                'iPhone':kol.phone_age_info.iPhone,'OPPO':kol.phone_age_info.OPPO,'vivo':kol.phone_age_info.vivo,'huawei':kol.phone_age_info.huawei,'xiaomi':kol.phone_age_info.xiaomi,
                'others':kol.phone_age_info.others,'less_18':kol.phone_age_info.less_18,'age_18_25':kol.phone_age_info.age_18_25,'age_26_32':kol.phone_age_info.age_26_32,
                'age_33_39':kol.phone_age_info.age_33_39,'age_40_46':kol.phone_age_info.age_40_46,'greater_46':kol.phone_age_info.greater_46,
                'one_city':int(kol.phone_age_info.one_city),'two_city':int(kol.phone_age_info.two_city),'three_city':int(kol.phone_age_info.three_city)}
        data.append(info)
    res = ResMsg()
    res.update(data=data)
    return jsonify(res.data)
    """

@app.route('/kol-detail')
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

@app.route('/cmm-list')
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

@app.route('/cmm-detail')
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
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        print(bytes.decode(request.data))
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