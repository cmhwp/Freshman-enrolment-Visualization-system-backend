from app import db
from datetime import datetime

class SystemSettings(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), default='新生入学可视化系统')
    site_description = db.Column(db.Text)
    maintenance_mode = db.Column(db.Boolean, default=False)
    allow_registration = db.Column(db.Boolean, default=True)
    score_visible = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'site_name': self.site_name,
            'site_description': self.site_description,
            'maintenance_mode': self.maintenance_mode,
            'allow_registration': self.allow_registration,
            'score_visible': self.score_visible,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 