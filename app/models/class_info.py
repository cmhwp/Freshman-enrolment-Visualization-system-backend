from app import db
from datetime import datetime

class ClassInfo(db.Model):
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 班级名称
    major = db.Column(db.String(100), nullable=False)  # 专业
    department = db.Column(db.String(100), nullable=False)  # 所属院系
    year = db.Column(db.Integer, nullable=False)  # 入学年份
    capacity = db.Column(db.Integer)  # 班级容量
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 班主任ID
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())
    

    # 只保留教师关系定义
    teacher = db.relationship(
        'User',
        foreign_keys=[teacher_id],
        backref=db.backref('managed_classes', lazy='dynamic')
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'major': self.major,
            'department': self.department,
            'year': self.year,
            'capacity': self.capacity,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.name if self.teacher else None,
            'student_count': self.users.filter_by(role='student').count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    # 反向引用由 User 模型定义，这里不需要定义
    # students = db.relationship('User', backref='class_info', lazy=True) 