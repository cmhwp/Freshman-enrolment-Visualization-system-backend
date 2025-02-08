from app import db
from datetime import datetime

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    student_id = db.Column(db.String(20), unique=True)  # 学号
    major = db.Column(db.String(64))  # 专业
    admission_date = db.Column(db.Date)  # 入学日期
    graduation_date = db.Column(db.Date)  # 预计毕业日期
    status = db.Column(db.String(20), default='active')  # 学籍状态：active, graduated, suspended
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())
    

    # 建立与User模型的关系
    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'major': self.major,
            'gender': self.user.gender,
            'admission_date': self.admission_date.isoformat() if self.admission_date else None,
            'graduation_date': self.graduation_date.isoformat() if self.graduation_date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 