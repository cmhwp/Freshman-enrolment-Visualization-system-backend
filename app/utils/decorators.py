from functools import wraps
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask import jsonify

def role_required(roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            current_user = get_jwt_identity()
            if current_user['role'] not in roles:
                return jsonify({"msg": "Unauthorized access"}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper

# 添加具体角色的装饰器
def student_required(f):
    return role_required(['student'])(f)

def teacher_required(f):
    return role_required(['teacher'])(f)

def admin_required(f):
    return role_required(['admin'])(f)

# 多角色装饰器
def teacher_or_admin_required(f):
    return role_required(['teacher', 'admin'])(f) 