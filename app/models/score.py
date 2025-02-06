from app import db
from datetime import datetime

class Score(db.Model):
    __tablename__ = 'scores'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    total_score = db.Column(db.Float, nullable=False)
    chinese = db.Column(db.Float)
    math = db.Column(db.Float)
    english = db.Column(db.Float)
    physics = db.Column(db.Float)
    chemistry = db.Column(db.Float)
    biology = db.Column(db.Float)
    province_rank = db.Column(db.Integer)
    major_rank = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 