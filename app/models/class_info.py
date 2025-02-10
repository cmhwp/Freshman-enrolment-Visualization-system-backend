from app.extensions import db
from datetime import datetime

class ClassInfo(db.Model):
    __tablename__ = 'class_info'
    
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(50), nullable=False)  # 班级名称
    major = db.Column(db.String(64))  # 专业
    department = db.Column(db.String(64))  # 院系
    year = db.Column(db.Integer)  # 年级
    capacity = db.Column(db.Integer)  # 班级容量
    assigned_students = db.Column(db.Integer, default=0)  # 已分配学生数量
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 班主任ID
    
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())
    
    # 简化关系定义
    students = db.relationship(
        'User',
        primaryjoin="and_(User.class_id==ClassInfo.id, User.role=='student')",
        back_populates='class_info',
        overlaps="class_members",
        viewonly=True  # 只读关系
    )
    
    teacher = db.relationship(
        'User',
        primaryjoin="and_(User.id==ClassInfo.teacher_id, User.role=='teacher')",
        back_populates='managed_classes',
        foreign_keys='ClassInfo.teacher_id'
    )
    
    # 主要的关系定义
    class_members = db.relationship(
        'User',
        back_populates='class_info',
        foreign_keys='User.class_id',
        overlaps="students,student_class"  # 声明重叠的关系
    )
    
    def to_dict(self, with_students=False):
        data = {
            'id': self.id,
            'class_name': self.class_name,
            'department': self.department,
            'major': self.major,
            'year': self.year,
            'capacity': self.capacity,
            'teacher_id': self.teacher_id,
            'assigned_students': self.assigned_students,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if with_students:
            data['students'] = [student.to_dict() for student in self.students]
        
        return data

    # 反向引用由 User 模型定义，这里不需要定义
    # students = db.relationship('User', backref='class_info', lazy=True) 