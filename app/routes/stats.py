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
from app.models.teacher import Teacher
from app.models.dormitory import DormitoryRoom, DormitoryAssignment

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_overview():
    """获取系统概览数据"""
    try:
        # 获取当前用户
        current_user = get_jwt_identity()
        user = User.query.get(current_user['user_id'])

        # 获取学生总数和各状态数量
        total_students = Student.query.count()
        reported_count = Student.query.filter_by(status='reported').count()
        unreported_count = Student.query.filter_by(status='unreported').count()
        pending_count = Student.query.filter_by(status='pending').count()


        # 获取教师总数
        total_teachers = Teacher.query.count()

        # 获取宿舍统计
        total_rooms = DormitoryRoom.query.count()
        occupied_rooms = db.session.query(DormitoryRoom)\
            .join(DormitoryAssignment)\
            .filter(DormitoryAssignment.status == 'active')\
            .distinct().count()

        # 获取专业分布
        major_stats = db.session.query(
            Student.major,
            db.func.count(Student.id).label('count')
        ).group_by(Student.major).all()
        
        major_distribution = [{
            'major': item[0],
            'count': item[1]
        } for item in major_stats]

        # 获取省份分布（包含更多学生信息）
        province_stats = db.session.query(
            User.province,
            Student.major,
            Student.student_id,
            User.name,
            User.gender,
            Student.status,
            db.func.count(User.id).label('count')
        ).join(Student)\
        .group_by(
            User.province,
            Student.major,
            Student.student_id,
            User.name,
            User.gender,
            Student.status
        ).all()
        
        province_distribution = [{
            'province': item[0] or '未知',
            'major': item[1],
            'studentId': item[2],
            'name': item[3],
            'gender': '男' if item[4] == 'M' else '女',
            'status': {
                'reported': '已报到',
                'unreported': '未报到',
                'pending': '待报到'
            }.get(item[5], '未知'),
            'count': item[6]
        } for item in province_stats]

        # 按省份分组统计
        province_summary = {}
        for item in province_distribution:
            province = item['province']
            if province not in province_summary:
                province_summary[province] = 0
            province_summary[province] += item['count']

        province_stats = [
            {'province': k, 'count': v}
            for k, v in province_summary.items()
        ]
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
                    'report_time': student.report_time.isoformat() if student.report_time else None,
                    'status': student.status,
                }
                print(stats['student_profile'])
        elif user.role == 'teacher':
            stats['managedClasses'] = ClassInfo.query.filter_by(teacher_id=user.id).count()

            stats['todoCount'] = 0  # 可以添加待办事项统计
        return jsonify({
            'success': True,
            'data': {
                'studentStats': {
                    'total': total_students,
                    'reported': reported_count,
                    'unreported': unreported_count,
                    'pending': pending_count
                },
                'teacherCount': total_teachers,
                'dormitoryStats': {
                    'total': total_rooms,
                    'occupied': occupied_rooms,
                    'available': total_rooms - occupied_rooms
                },
                'majorDistribution': major_distribution,
                'provinceDistribution': province_stats,
                'studentDetails': province_distribution,
                'stats': stats
            }
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