import os

SECRET_KEY = os.getenv('SECRET_KEY', '9qeYcNLM2CFcp55RaGlwtzpXupeQAFWD')
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://qtuser:Qt@wx123!@172.16.23.6:3306/star_library'
#SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:gWeih$o1!TyyuOurTDdxi1d9@cdb-ck8fb4oz.gz.tencentcdb.com:10017/weixin'
SQLALCHEMY_DATABASE_URI =  'mysql+pymysql://root:gWeih$o1!TyyuOurTDdxi1d9@cdb-ck8fb4oz.gz.tencentcdb.com:10017/star_library'
SQLALCHEMY_TRACK_MODIFICATIONS = False  # 关闭对模型修改的监控
SQLALCHEMY_POOL_RECYCLE = 300
SQLALCHEMY_POOL_SIZE = 10
APPID = 'wx6f962ffc76231591' #微信appid
APPSECRET = 'a2bc01bcdefa53588285cdad598f9440' #微信secret
TOKEN = 'qiteng181111' #微信token