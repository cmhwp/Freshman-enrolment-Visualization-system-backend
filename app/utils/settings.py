from app.extensions import db
from app.models.settings import Settings
from flask import current_app

def get_settings():
    """获取系统设置，如果不存在则创建默认设置"""
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)
        db.session.commit()
    return settings

def get_setting(key):
    """获取单个设置项"""
    settings = get_settings()
    return getattr(settings, key, None)

def update_setting(key, value):
    """更新单个设置项"""
    settings = get_settings()
    if hasattr(settings, key):
        setattr(settings, key, value)
        db.session.commit()
        return True
    return False 