from flask import Blueprint, request, jsonify
from app.models.user import User
from app.models.student import Student
from app import db
from app.utils.email import send_verification_email, verify_email_code
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required
)
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "Auth blueprint is working!"}), 200

@auth_bp.route('/send-verification', methods=['POST'])
def send_verification():
    """发送邮箱验证码"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({"message": "Email is required"}), 400
            
        if User.query.filter_by(email=email).first():
            return jsonify({"message": "Email already registered"}), 400
            
        send_verification_email(email)
        return jsonify({"message": "Verification code sent"}), 200
    except Exception as e:
        print(f"Send verification error: {str(e)}")  # 开发时查看具体错误
        return jsonify({"message": "Failed to send verification code"}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        print("Received registration data:", data)  # 添加调试日志
        
        # 验证必要字段
        required_fields = ['username', 'email', 'password', 'role', 'name', 'verification_code']
        for field in required_fields:
            if field not in data:
                return jsonify({"message": f"{field} is required"}), 400
        
        # 验证用户名和邮箱是否已存在
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"message": "Username already exists"}), 400
            
        if User.query.filter_by(email=data['email']).first():
            return jsonify({"message": "Email already registered"}), 400
            
        # 验证邮箱验证码
        if not verify_email_code(data['email'], data['verification_code']):
            return jsonify({"message": "Invalid or expired verification code"}), 400
            
        try:
            # 创建用户
            user = User(
                username=data['username'],
                email=data['email'],
                role=data['role'],
                name=data['name'],
                contact=data.get('contact'),
                province=data.get('province'),
                is_active=True  # 确保设置为 True
            )
            user.set_password(data['password'])
            
            db.session.add(user)
            db.session.flush()  # 获取用户ID
            
            # 如果是学生角色，创建学生记录
            if data['role'] == 'student':
                student = Student(
                    user_id=user.id,
                    gender=data.get('gender')
                )
                db.session.add(student)
            
            db.session.commit()
            print("User registered successfully:", user.id)  # 添加调试日志
            return jsonify({"message": "Registration successful"}), 201
            
        except Exception as e:
            db.session.rollback()
            print("Database error:", str(e))  # 添加调试日志
            return jsonify({"message": "Database error occurred"}), 500
            
    except Exception as e:
        print("Registration error:", str(e))  # 添加调试日志
        return jsonify({"message": str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        
        # 支持用户名或邮箱登录
        user = User.query.filter(
            (User.username == data.get('username')) | 
            (User.email == data.get('username'))
        ).first()
        
        if not user or not user.check_password(data.get('password')):
            return jsonify({"message": "Invalid username or password"}), 401
            
        if not user.is_active:
            return jsonify({"message": "Account is not activated"}), 401
            
        # 生成访问令牌和刷新令牌
        access_token = create_access_token(
            identity={'user_id': user.id, 'role': user.role}
        )
        refresh_token = create_refresh_token(
            identity={'user_id': user.id, 'role': user.role}
        )
        
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "name": user.name
            }
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    try:
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user)
        return jsonify({
            "access_token": access_token
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@auth_bp.route('/send-reset-code', methods=['POST'])
def send_reset_code():
    """发送重置密码的验证码"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({"success": False, "message": "邮箱不能为空"}), 400
            
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"success": False, "message": "该邮箱未注册"}), 404
            
        # 发送验证码
        send_verification_email(email)
        return jsonify({
            "success": True, 
            "message": "重置密码验证码已发送到您的邮箱"
        }), 200
        
    except Exception as e:
        print(f"Send reset code error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "发送验证码失败，请稍后重试"
        }), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """重置密码"""
    try:
        data = request.get_json()
        email = data.get('email')
        verification_code = data.get('verification_code')
        new_password = data.get('new_password')
        
        if not all([email, verification_code, new_password]):
            return jsonify({
                "success": False,
                "message": "请填写完整信息"
            }), 400
            
        # 验证邮箱是否存在
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                "success": False,
                "message": "该邮箱未注册"
            }), 404
            
        # 验证验证码
        if not verify_email_code(email, verification_code):
            return jsonify({
                "success": False,
                "message": "验证码错误或已过期"
            }), 400
            
        # 更新密码
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "密码重置成功，请使用新密码登录"
        }), 200
        
    except Exception as e:
        print(f"Reset password error: {str(e)}")
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "重置密码失败，请稍后重试"
        }), 500 