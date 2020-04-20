import os

SECRET_KEY = os.getenv('SECRET_KEY', '9qeYcNLM2CFcp55RaGlwtzpXupeQAFWD')
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:gWeih$o1!TyyuOurTDdxi1d9@cdb-ck8fb4oz.gz.tencentcdb.com:10017/weixin'
SQLALCHEMY_TRACK_MODIFICATIONS = False  # 关闭对模型修改的监控
SQLALCHEMY_POOL_RECYCLE = 300
SQLALCHEMY_POOL_SIZE = 10
APPID = 'wx1473cc2c07952e8c' #微信appid
APPSECRET = '9bc486a4cf102993ab95d6b0b01e0a09' #微信secret
TOKEN = 'my123' #微信token