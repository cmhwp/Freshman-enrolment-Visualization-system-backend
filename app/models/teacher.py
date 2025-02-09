from app.extensions import db
from datetime import datetime

class Teacher(db.Model):
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    department = db.Column(db.String(64))
    title = db.Column(db.String(64))
    research_area = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())
    


    # 建立与User模型的关系
    user = db.relationship('User', backref=db.backref('teacher_profile', uselist=False))

    def to_dict(self):
        return {
            'id': self.id,
            'department': self.department,
            'title': self.title,
            'research_area': self.research_area
        } 