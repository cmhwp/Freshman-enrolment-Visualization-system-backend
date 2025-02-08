from functools import wraps
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask import jsonify, g

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
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user = get_jwt_identity()
            
            if not current_user or 'user_id' not in current_user:
                return jsonify({
                    'success': False,
                    'message': '无法获取用户信息'
                }), 401
                
            # 检查用户角色
            if current_user.get('role') != 'student':
                return jsonify({
                    'success': False,
                    'message': '只有学生可以访问此接口'
                }), 403
                
            # 将用户ID存储在g对象中
            g.user_id = current_user['user_id']
            
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 401
            
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user = get_jwt_identity()
            
            if not current_user or 'user_id' not in current_user:
                return jsonify({
                    'success': False,
                    'message': '无法获取用户信息'
                }), 401
                
            # 检查用户角色
            if current_user.get('role') != 'teacher':
                return jsonify({
                    'success': False,
                    'message': '只有教师可以访问此接口'
                }), 403
                
            # 将用户ID存储在g对象中
            g.user_id = current_user['user_id']
            
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 401
            
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user = get_jwt_identity()
            
            if not current_user or 'user_id' not in current_user:
                return jsonify({
                    'success': False,
                    'message': '无法获取用户信息'
                }), 401
                
            # 检查用户角色
            if current_user.get('role') != 'admin':
                return jsonify({
                    'success': False,
                    'message': '只有管理员可以访问此接口'
                }), 403
                
            # 将用户ID存储在g对象中
            g.user_id = current_user['user_id']
            
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 401
            
    return decorated_function

# 多角色装饰器
def teacher_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user = get_jwt_identity()
            
            if not current_user or 'user_id' not in current_user:
                return jsonify({
                    'success': False,
                    'message': '无法获取用户信息'
                }), 401
                
            # 检查用户角色
            if current_user.get('role') not in ['teacher', 'admin']:
                return jsonify({
                    'success': False,
                    'message': '只有教师或管理员可以访问此接口'
                }), 403
                
            # 将用户ID存储在g对象中
            g.user_id = current_user['user_id']
            
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 401
            
    return decorated_function 
# 仅登录装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user = get_jwt_identity()
            
            if not current_user or 'user_id' not in current_user:
                return jsonify({
                    'success': False,
                    'message': '无法获取用户信息'
                }), 401
            
            # 将用户信息存储在g对象中
            g.user_id = current_user['user_id']
            g.user_role = current_user['role']
            
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 401
            
    return decorated_function

