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
        return jsonify({"message": str(e)}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        
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
            
        # 创建用户
        user = User(
            username=data['username'],
            email=data['email'],
            role=data['role'],
            name=data['name'],
            contact=data.get('contact'),
            province=data.get('province'),
            is_active=True
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        
        # 如果是学生角色，创建学生记录
        if data['role'] == 'student':
            student = Student(
                user_id=user.id,
                gender=data.get('gender')
            )
            db.session.add(student)
            
        db.session.commit()
        
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        db.session.rollback()
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