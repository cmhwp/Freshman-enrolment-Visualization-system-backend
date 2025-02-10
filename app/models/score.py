from app.extensions import db
from datetime import datetime

class Score(db.Model):
    """高考成绩模型"""
    __tablename__ = 'scores'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)  # 高考年份
    total_score = db.Column(db.Float, nullable=False)  # 总分
    chinese = db.Column(db.Float)  # 语文
    math = db.Column(db.Float)    # 数学
    english = db.Column(db.Float)  # 英语
    physics = db.Column(db.Float)  # 物理
    chemistry = db.Column(db.Float)  # 化学
    biology = db.Column(db.Float)  # 生物
    province_rank = db.Column(db.Integer)  # 省排名
    major_rank = db.Column(db.Integer)    # 专业排名
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())
    
    # 关联关系
    student = db.relationship('Student', backref='score')
    
    def to_dict(self):
        return {
            'id': self.id,
            'studentId': self.student_id,
            'studentName': self.student.user.name,
            'studentNumber': self.student.student_id,
            'year': self.year,
            'totalScore': self.total_score,
            'chinese': self.chinese,
            'math': self.math,
            'english': self.english,
            'physics': self.physics,
            'chemistry': self.chemistry,
            'biology': self.biology,
            'provinceRank': self.province_rank,
            'majorRank': self.major_rank,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        } 