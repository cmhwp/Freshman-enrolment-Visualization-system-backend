from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from flask_apscheduler import APScheduler
from redis import Redis
from .config import Config

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
scheduler = APScheduler()
redis_client = Redis(
    host=Config.REDIS_HOST, 
    port=Config.REDIS_PORT, 
    decode_responses=True
) 