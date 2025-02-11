from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from redis import Redis
from .config import Config
from flask_apscheduler import APScheduler
from app.tasks.enrollment import check_enrollment_deadline
from .extensions import db, jwt, mail, scheduler, redis_client

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化插件
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app)
    
    # 初始化调度器
    scheduler.init_app(app)
    
    # 添加定时任务
    @scheduler.task('interval', id='check_enrollment_deadline', seconds=10)
    def check_enrollment_task():
        with app.app_context():
            check_enrollment_deadline()

    
    scheduler.start()
    
    # 注册蓝图
    from .routes import auth_bp, student_bp, teacher_bp, admin_bp, user_bp, stats_bp, dormitory_bp, todo_bp 
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(student_bp, url_prefix='/api/student')
    app.register_blueprint(teacher_bp, url_prefix='/api/teacher')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')
    app.register_blueprint(dormitory_bp, url_prefix='/api/dormitory')
    app.register_blueprint(todo_bp, url_prefix='/api/todo')
    return app 