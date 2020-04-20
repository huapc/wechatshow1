from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config.from_pyfile('config/settings.py')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from views import *

