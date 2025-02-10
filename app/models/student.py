from app.extensions import db
from datetime import datetime

class Student(db.Model):
    """学生模型"""
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class_info.id'))
    major = db.Column(db.String(50))
    admission_year = db.Column(db.Integer)
    admission_date = db.Column(db.DateTime)
    graduation_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending-待报到, reported-已报到, unreported-未报到
    report_time = db.Column(db.DateTime) # 报到时间
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())


    # 删除原有的宿舍字段
    # dormitory_building = db.Column(db.String(50))
    # dormitory_room = db.Column(db.String(20))

    # 建立与User模型的关系
    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    
    def to_dict(self):
        data = {
            'id': self.id,
            'userId': self.user_id,
            'studentId': self.student_id,
            'major': self.major,
            'classId': self.class_id,
            'admissionYear': self.admission_year,
            'admissionDate': self.admission_date.isoformat() if self.admission_date else None,
            'graduationDate': self.graduation_date.isoformat() if self.graduation_date else None,
            'status': self.status,

            'reportTime': self.report_time.isoformat() if self.report_time else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
        


        # 添加宿舍信息
        if hasattr(self, 'dormitory_assignment') and self.dormitory_assignment:
            assignment = self.dormitory_assignment
            data['dormitory'] = {
                'buildingName': assignment.room.building.name,
                'roomNumber': assignment.room.room_number,
                'checkInDate': assignment.check_in_date.isoformat() if assignment.check_in_date else None
            }
            
        return data 