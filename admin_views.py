from flask import request, jsonify
from app import app, db
from models import *
from config.response import ResMsg
from config.code import ResponseCode, ResponseMessage
from util import *
import demjson

@app.route('/api/v1.0/admin/kol-list')
def kol_list():
    page = int(request.args.get('page', 1))
    # 每页条数
    per_page = int(request.args.get('per_page', 15))

    tag = request.args.get('tag')
    sex = request.args.get('sex')
    age = request.args.get('age')
    follower_num = request.args.get('follower_num')
    map = []
    if tag:
        map.append(KolList.tag == tag)
    if sex:
        map.append(KolList.sex == sex)
    if age:
        age_list = age.split('-')
        min_age = age_list[0]
        max_age = age_list[0]
        map.append(KolList.age.between(min_age,max_age))
    if follower_num:
        follower_num_list = follower_num.split('-')
        min = int(follower_num_list[0]) * 10000
        max = int(follower_num_list[1]) * 10000
        map.append(KolList.follower_num.between(min, max))
    paginate = KolList.query.filter(*map).order_by(KolList.follower_num.desc()).paginate(page, per_page, error_out=False)
    for i in paginate.items:
        avatar = FansAttribute.query.get(i.userid).avatar
        i.__setattr__('avatar',avatar)
    data = construct_page_data(paginate)
    res = ResMsg()
    res.update(data=data)
    return jsonify(res.data)

@app.route('/api/v1.0/admin/kol-tag')
def kol_tag():
    tags = KolList.query.with_entities(KolList.tag).distinct().all()
    list = []
    for t in tags:
        list.append(t[0])
    data = {'tags': list}
    res = ResMsg()
    res.update(data=data)
    return jsonify(res.data)

@app.route('/api/v1.0/admin/fansattribute')
def fansattribute():
    userid = request.args.get('userid')
    fansattribute = FansAttribute.query.get(userid)
    data = model_to_dict(fansattribute)
    res = ResMsg()
    res.update(data=data)
    return jsonify(res.data)

@app.route('/api/v1.0/admin/phoneageinfo')
def phoneageinfo():
    userid = request.args.get('userid')
    phoneageinfo = PhoneAgeInfo.query.get(userid)
    data = phoneageinfo.__dict__
    data.pop('_sa_instance_state')
    res = ResMsg()
    res.update(data=data)
    return jsonify(res.data)

@app.route('/api/v1.0/admin/region')
def region():
    userid = request.args.get('userid')
    region = Region.query.get(userid)
    data = model_to_dict(region)
    res = ResMsg()
    res.update(data=data)
    return jsonify(res.data)

@app.route('/api/v1.0/admin/kol-search')
def kol_search():
    nickname = request.args.get('nickname')
    kol = KolList.query.filter_by(nickname=nickname)
    data = model_to_dict(kol)
    res = ResMsg()
    res.update(data=data)
    return jsonify(res.data)

@app.route('/api/v1.0/admin/cmm-list')
def cmm_list():
    page = int(request.args.get('page', 1))
    # 每页条数
    per_page = int(request.args.get('per_page', 15))
    tag = request.args.get('tag')
    map = []
    if tag:
        map.append(CmmAll.category == tag)

    paginate = CmmAll.query.filter(*map).paginate(page, per_page, error_out=False)
    data = construct_page_data(paginate)
    res = ResMsg()
    res.update(data=data)
    return jsonify(res.data)


@app.route('/api/v1.0/admin/cmm-header')
def cmm_header():
    promotion_id = request.args.get('promotion_id')
    header = Header.query.get(promotion_id)
    data = model_to_dict(header)
    star_list = data['star_list']
    star_list = star_list.strip("'")
    data['star_list'] = demjson.decode(star_list)
    res = ResMsg()
    res.update(data=data)
    return jsonify(res.data)

@app.route('/api/v1.0/admin/cmm-agesexregion')
def agesexregion():
    promotion_id = request.args.get('promotion_id')
    agesexregion = AgeSexRegion.query.get(promotion_id)
    data = model_to_dict(agesexregion)
    res = ResMsg()
    res.update(data=data)
    return jsonify(res.data)

@app.route('/api/v1.0/admin/cmm-tag')
def cmm_tag():
    tags = CmmAll.query.with_entities(CmmAll.category).distinct().all()
    list = []
    for t in tags:
        list.append(t[0])
    data = {'tags': list}
    res = ResMsg()
    res.update(data=data)
    return jsonify(res.data)




