from app.extensions import db
from app.models.student import Student
from app.models.settings import Settings
from app.models.system_log import SystemLog
from datetime import datetime
from sqlalchemy import and_
from flask import current_app

def check_enrollment_deadline():
    """检查报到截止时间，更新未报到学生状态"""
    try:
        settings = Settings.query.first()
        if not settings or not settings.enrollment_deadline:
            return
            
        now = datetime.now()
        if now >= settings.enrollment_deadline:
            # 查找所有待报到的学生
            pending_students = Student.query.filter(
                and_(
                    Student.status == 'pending',
                    Student.admission_year == now.year  # 只处理当年的新生
                )
            ).all()
            
            # 更新状态
            updated_count = 0
            for student in pending_students:
                student.status = 'unreported'
                updated_count += 1
            
            if updated_count > 0:
                # 记录系统日志
                log = SystemLog(
                    user_id=None,  # 系统自动操作
                    type='system_auto',
                    content=f'系统自动更新{updated_count}名未报到学生状态',
                    ip_address='127.0.0.1'
                )
                db.session.add(log)
                db.session.commit()
                
    except Exception as e:
        print(f"Check enrollment deadline error: {str(e)}")
        db.session.rollback() 