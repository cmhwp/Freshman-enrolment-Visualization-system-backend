from app.extensions import db
from datetime import datetime

class SystemLog(db.Model):
    __tablename__ = 'system_logs'

    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    type = db.Column(db.String(50))  # 操作类型
    content = db.Column(db.Text)  # 操作内容
    ip_address = db.Column(db.String(50))  # IP地址
    created_at = db.Column(db.DateTime, default=datetime.now())
    

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'content': self.content,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 