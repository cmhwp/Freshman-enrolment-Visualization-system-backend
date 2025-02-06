from app import db

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    gender = db.Column(db.String(1))  # 'M' 或 'F'
    
    # 修改关系定义，移除循环依赖
    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    scores = db.relationship('Score', backref='student', lazy=True) 