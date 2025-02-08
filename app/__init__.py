from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from redis import Redis
from .config import Config
db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
redis_client = Redis(
    host=Config.REDIS_HOST, 
    port=Config.REDIS_PORT, 
    decode_responses=True
)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化插件
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app)
    
    
    # 注册蓝图
    from .routes import auth_bp, student_bp, teacher_bp, admin_bp, user_bp ,stats_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(student_bp, url_prefix='/api/student')
    app.register_blueprint(teacher_bp, url_prefix='/api/teacher')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')
    
    return app 