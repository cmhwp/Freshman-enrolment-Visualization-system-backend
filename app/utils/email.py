from flask_mail import Message
from app import mail
import random
import string
from datetime import datetime, timedelta
from app import redis_client

def generate_verification_code():
    """生成6位验证码"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email):
    """发送验证码邮件"""
    code = generate_verification_code()
    
    # 将验证码存储到Redis，设置5分钟过期
    key = f"email_verify:{email}"
    redis_client.setex(key, timedelta(minutes=5), code)
    
    msg = Message(
        '学生成绩管理系统 - 邮箱验证',
        sender='cmh22408@163.com',
        recipients=[email]
    )
    

    msg.body = f'''您好！
    
您的验证码是：{code}

该验证码将在5分钟后过期，请尽快完成验证。

如果这不是您的操作，请忽略此邮件。

此致
学生成绩管理系统团队
'''
    
    mail.send(msg)
    return True

def verify_email_code(email, code):
    """验证邮箱验证码"""
    key = f"email_verify:{email}"
    stored_code = redis_client.get(key)
    
    if not stored_code:
        return False
        
    # 验证成功后删除验证码
    if stored_code.decode('utf-8') == code:
        redis_client.delete(key)
        return True
        
    return False 