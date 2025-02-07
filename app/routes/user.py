from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Student
from app import db
from werkzeug.security import check_password_hash

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取用户信息"""
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['user_id'])
        
        if not user:
            return jsonify({"message": "User not found"}), 404
            
        profile = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "contact": user.contact,
            "province": user.province,
            "class_id": user.class_id
        }
        
        # 如果是学生，添加性别信息
        if user.role == 'student' and user.student_profile:
            profile['gender'] = user.student_profile.gender
            
        return jsonify({"success": True, "data": profile}), 200
        
    except Exception as e:
        print(f"Get profile error: {str(e)}")
        return jsonify({"message": "Failed to get profile"}), 500

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新用户信息"""
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['user_id'])
        
        if not user:
            return jsonify({"message": "User not found"}), 404
            
        data = request.get_json()
        
        # 更新基本信息
        if 'name' in data:
            user.name = data['name']
        if 'contact' in data:
            user.contact = data['contact']
        if 'province' in data:
            user.province = data['province']
            
        # 如果是学生，更新性别
        if user.role == 'student' and 'gender' in data and user.student_profile:
            user.student_profile.gender = data['gender']
            
        db.session.commit()
        return jsonify({"success": True, "message": "Profile updated successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Update profile error: {str(e)}")
        return jsonify({"message": "Failed to update profile"}), 500

@user_bp.route('/password', methods=['PUT'])
@jwt_required()
def update_password():
    """更新密码"""
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['user_id'])
        
        if not user:
            return jsonify({"message": "User not found"}), 404
            
        data = request.get_json()
        
        if not all(k in data for k in ('old_password', 'new_password')):
            return jsonify({"message": "Missing password fields"}), 400
            
        if not user.check_password(data['old_password']):
            return jsonify({"message": "Current password is incorrect"}), 400
            
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({"success": True, "message": "Password updated successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Update password error: {str(e)}")
        return jsonify({"message": "Failed to update password"}), 500 