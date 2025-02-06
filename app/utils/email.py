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
    try:
        code = generate_verification_code()
        print(f"Generated code for {email}: {code}")
        
        # 将验证码存储到Redis，设置5分钟过期
        key = f"email_verify:{email}"
        redis_client.setex(key, timedelta(minutes=5), code)
        
        # 验证是否成功存储
        stored_code = redis_client.get(key)
        print(f"Stored code in Redis: {stored_code}")
        
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
        print(f"Verification email sent to {email}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise e

def verify_email_code(email, code):
    """验证邮箱验证码"""
    key = f"email_verify:{email}"
    stored_code = redis_client.get(key)
    
    print(f"Verifying code for {email}")
    print(f"Stored code: {stored_code}")
    print(f"Received code: {code}")
    
    if not stored_code:
        print("No code found in Redis")
        return False
    
    if stored_code == code:
        print("Code verified successfully")
        redis_client.delete(key)
        return True
    
    print("Code verification failed")
    return False 