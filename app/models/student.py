from app import db

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    gender = db.Column(db.String(1))  # 'M' 或 'F'
    
    # 关联关系
    user = db.relationship('User', backref='student_profile', uselist=False)
    scores = db.relationship('Score', backref='student', lazy=True) 