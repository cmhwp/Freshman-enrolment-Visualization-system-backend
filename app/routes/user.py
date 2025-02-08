from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Student, SystemLog
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
            
        user_data = user.to_dict()
        if user.role == 'student' and user.student_profile:
            user_data['student_profile'] = user.student_profile.to_dict()
            
        return jsonify({
            "success": True,
            "data": user_data
        })
        
    except Exception as e:
        print(f"Get profile error: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

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
        changed_fields = []
        
        # 更新基本信息
        if 'name' in data and data['name'] != user.name:
            changed_fields.append(f"姓名: {user.name} -> {data['name']}")
            user.name = data['name']
        if 'contact' in data and data['contact'] != user.contact:
            changed_fields.append(f"联系方式: {user.contact} -> {data['contact']}")
            user.contact = data['contact']
        if 'province' in data and data['province'] != user.province:
            changed_fields.append(f"省份: {user.province} -> {data['province']}")
            user.province = data['province']
        # 更新性别
        if 'gender' in data and data['gender'] != user.gender:
            changed_fields.append(f"性别: {user.gender} -> {data['gender']}")
            user.gender = data['gender']
            
        db.session.commit()
        
        # 记录操作日志
        if changed_fields:
            log = SystemLog(
                user_id=user.id,
                type='update_profile',
                content=f'更新个人信息: {", ".join(changed_fields)}',
                ip_address=request.remote_addr
            )
            db.session.add(log)
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
        
        # 记录密码修改日志
        log = SystemLog(
            user_id=user.id,
            type='update_password',
            content='修改密码',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Password updated successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Update password error: {str(e)}")
        return jsonify({"message": "Failed to update password"}), 500 