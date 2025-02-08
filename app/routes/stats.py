from flask import Blueprint, jsonify, g, current_app
from app.models.user import User
from app.models.class_info import ClassInfo
from app.models.system_log import SystemLog
from app.utils.decorators import login_required
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from app import db
from flask_jwt_extended import get_jwt_identity
from app.models.student import Student

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_overview():
    """获取统计概览"""
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['user_id'])
        
        # 基础统计数据
        stats = {
            'studentCount': User.query.filter_by(role='student').count(),
            'teacherCount': User.query.filter_by(role='teacher').count(),
            'classCount': ClassInfo.query.count(),
            'todayVisits': SystemLog.query.filter(
                SystemLog.created_at >= datetime.now().date()
            ).count()
        }
        
        # 根据用户角色返回不同的统计信息
        if user.role == 'student':
            student = Student.query.filter_by(user_id=user.id).first()
            if student:
                stats['student_profile'] = {
                    'student_id': student.student_id,
                    'major': student.major,
                    'status': student.status
                }
        elif user.role == 'teacher':
            stats['managedClasses'] = ClassInfo.query.filter_by(teacher_id=user.id).count()
            stats['todoCount'] = 0  # 可以添加待办事项统计
            
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        print(f"Get overview error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@stats_bp.route('/last-login', methods=['GET'])
@login_required
def get_last_login():
    """获取上次登录时间"""
    try:
        last_login = SystemLog.query.filter_by(
            user_id=g.user_id,
            type='login'
        ).order_by(SystemLog.created_at.desc()).offset(1).first()
        
        return jsonify({
            'success': True,
            'data': {
                'lastLoginTime': last_login.created_at.isoformat() if last_login else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500 