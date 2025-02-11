from app.extensions import db
from datetime import datetime

import json

class AnalysisReport(db.Model):
    __tablename__ = 'analysis_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class_info.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    report_data = db.Column(db.JSON, nullable=False)  # 存储JSON格式的报告数据
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 添加关系
    teacher = db.relationship('User', backref='analysis_reports')
    class_info = db.relationship('ClassInfo', backref='analysis_reports')
    
    def to_dict(self):
        return {
            'id': self.id,
            'class_id': self.class_id,
            'teacher_id': self.teacher_id,
            'report_data': self.report_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 