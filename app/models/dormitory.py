from app.extensions import db
from datetime import datetime

class DormitoryBuilding(db.Model):
    """宿舍楼模型"""
    __tablename__ = 'dormitory_buildings'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # 宿舍楼名称
    gender = db.Column(db.String(1))  # M-男生宿舍, F-女生宿舍
    description = db.Column(db.String(200))  # 描述
    rooms = db.relationship('DormitoryRoom', backref='building', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'description': self.description,
            'roomCount': len(self.rooms)
        }

class DormitoryRoom(db.Model):
    """宿舍房间模型"""
    __tablename__ = 'dormitory_rooms'

    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), nullable=False)  # 房间号
    building_id = db.Column(db.Integer, db.ForeignKey('dormitory_buildings.id'), nullable=False)
    capacity = db.Column(db.Integer, default=4)  # 房间容量
    description = db.Column(db.String(200))  # 描述
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    @property
    def occupancy(self):
        """计算当前入住人数"""
        return DormitoryAssignment.query.filter_by(
            room_id=self.id,
            status='active'
        ).count()

    def to_dict(self):
        return {
            'id': self.id,
            'buildingId': self.building_id,
            'buildingName': self.building.name,
            'roomNumber': self.room_number,
            'capacity': self.capacity,
            'description': self.description,
            'occupancy': self.occupancy
        }

class DormitoryAssignment(db.Model):
    """宿舍分配记录"""
    __tablename__ = 'dormitory_assignments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('dormitory_rooms.id'), nullable=False)
    check_in_date = db.Column(db.DateTime, default=datetime.now)  # 入住时间
    check_out_date = db.Column(db.DateTime)  # 退宿时间
    status = db.Column(db.String(20), default='active')  # active-在住, inactive-已退宿
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    student = db.relationship('Student', backref=db.backref('dormitory_assignment', uselist=False))
    room = db.relationship('DormitoryRoom', backref='residents')

    def to_dict(self):
        return {
            'id': self.id,
            'studentId': self.student_id,
            'roomId': self.room_id,
            'checkInDate': self.check_in_date.isoformat() if self.check_in_date else None,
            'checkOutDate': self.check_out_date.isoformat() if self.check_out_date else None,
            'status': self.status
        } 