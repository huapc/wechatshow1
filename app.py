from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from util import JSONEncoder

app = Flask(__name__)
app.json_encoder = JSONEncoder

CORS(app)
app.config.from_pyfile('config/settings.py')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from views import *
from admin_views import *

