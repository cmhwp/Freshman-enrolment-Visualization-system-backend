from app import db

class ClassInfo(db.Model):
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    major = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    
    # 反向引用
    students = db.relationship('User', backref='class_info', lazy=True) 