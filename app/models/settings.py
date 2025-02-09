from app.extensions import db
from datetime import datetime

class Settings(db.Model):
    """系统设置模型"""
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    system_name = db.Column(db.String(100), default='新生入学可视化系统')
    version = db.Column(db.String(20), default='1.0.0')
    allow_register = db.Column(db.Boolean, default=True)
    require_email_verification = db.Column(db.Boolean, default=True)
    student_id_prefix = db.Column(db.String(10), default='2024')
    default_student_status = db.Column(db.String(20), default='pending')
    majors = db.Column(db.JSON, default=lambda: [
        '计算机科学与技术',
        '软件工程',

        '信息安全',
        '人工智能',
        '数据科学与大数据技术'
    ])
    departments = db.Column(db.JSON, default=lambda: [
        '计算机学院',
        '信息工程学院',
        '电子工程学院',
        '自动化学院'
    ])
    enrollment_deadline = db.Column(db.DateTime)  # 报到截止时间
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())


    def to_dict(self):
        return {
            'systemName': self.system_name,
            'version': self.version,
            'allowRegister': self.allow_register,
            'requireEmailVerification': self.require_email_verification,
            'studentIdPrefix': self.student_id_prefix,
            'defaultStudentStatus': self.default_student_status,
            'majors': self.majors,
            'departments': self.departments,
            'enrollmentDeadline': self.enrollment_deadline.isoformat() if self.enrollment_deadline else None,
        }

    def update_from_dict(self, data):
        """从字典更新设置"""
        mapping = {
            'systemName': 'system_name',
            'version': 'version',
            'allowRegister': 'allow_register',
            'requireEmailVerification': 'require_email_verification',
            'studentIdPrefix': 'student_id_prefix',
            'defaultStudentStatus': 'default_student_status',
            'majors': 'majors',
            'departments': 'departments',
            'enrollmentDeadline': 'enrollment_deadline',
        }
        
        for key, value in data.items():
            if key in mapping and hasattr(self, mapping[key]):
                setattr(self, mapping[key], value) 