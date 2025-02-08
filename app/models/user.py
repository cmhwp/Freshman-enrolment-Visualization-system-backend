from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    role = db.Column(db.String(20), nullable=False)  # student, teacher, admin
    name = db.Column(db.String(64))
    gender = db.Column(db.String(1))  # 'M' 或 'F'
    contact = db.Column(db.String(64))
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id', ondelete='SET NULL'), nullable=True)
    province = db.Column(db.String(64))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())
    
    # 修改关系定义，明确指定外键
    class_info = db.relationship(
        'ClassInfo',
        foreign_keys=[class_id],
        backref=db.backref('users', lazy='dynamic'),
        lazy='joined'
    )
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        base_dict = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'name': self.name,
            'gender': self.gender,
            'contact': self.contact,
            'province': self.province,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # 如果是教师，添加教师特有信息
        if self.role == 'teacher' and hasattr(self, 'teacher_profile') and self.teacher_profile:
            base_dict.update({
                'department': self.teacher_profile.department,
                'title': self.teacher_profile.title,
                'research_area': self.teacher_profile.research_area
            })
        
        # 如果是学生，添加学生特有信息
        if self.role == 'student' and hasattr(self, 'student_profile') and self.student_profile:
            base_dict.update({
                'student_id': self.student_profile.student_id,
                'major': self.student_profile.major,
                'admission_date': self.student_profile.admission_date.isoformat() if self.student_profile.admission_date else None,
                'graduation_date': self.student_profile.graduation_date.isoformat() if self.student_profile.graduation_date else None,
                'status': self.student_profile.status
            })
        
        return base_dict