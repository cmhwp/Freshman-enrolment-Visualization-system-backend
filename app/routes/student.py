from flask import Blueprint, jsonify, request, g
from app.utils.decorators import student_required, login_required
from app.models.score import Score
from app.models.student import Student
from app.extensions import db
from app.utils.analysis import (
    calculate_total_score,
    get_major_rankings,
    get_score_distribution,
    get_gender_admission_ratio,
    get_school_ranking
)
from app.models.system_log import SystemLog
from app.models.user import User
from datetime import datetime

student_bp = Blueprint('student', __name__)

@student_bp.route('/scores', methods=['GET'])
@student_required
def get_student_scores():
    """获取学生个人成绩详情"""
    try:
        student_id = g.user_id
        scores = Score.query.filter_by(student_id=student_id).first()
        
        if not scores:
            return jsonify({
                'success': False,
                'message': '未找到成绩数据'
            }), 404
            
        # 记录查询日志
        log = SystemLog(
            user_id=student_id,
            type='view_scores',
            content='查看个人成绩',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
            
        return jsonify({
            'success': True,
            'data': {
                'total_score': scores.total_score,
                'chinese': scores.chinese,
                'math': scores.math,
                'english': scores.english,
                'physics': scores.physics,
                'chemistry': scores.chemistry,
                'biology': scores.biology,
                'province_rank': scores.province_rank,
                'major_rank': scores.major_rank
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@student_bp.route('/major-ranking', methods=['GET'])
@student_required
def get_major_ranking():
    """获取专业排名信息"""
    try:
        student_id = g.user_id
        
        # 获取专业排名数据
        ranking_data = get_major_rankings(student_id)
        
        return jsonify({
            'success': True,
            'data': {
                'major_name': ranking_data['major_name'],
                'student_rank': ranking_data['rank'],
                'total_students': ranking_data['total'],
                'average_score': ranking_data['average'],
                'highest_score': ranking_data['highest']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@student_bp.route('/score-distribution', methods=['GET'])
@student_required
def get_class_distribution():
    """获取班级分数分布和录取性别比例"""
    try:
        student_id = g.user_id
        
        # 获取分数分布数据
        score_distribution = get_score_distribution(student_id)
        gender_ratio = get_gender_admission_ratio()
        
        return jsonify({
            'success': True,
            'data': {
                'score_distribution': {
                    'ranges': score_distribution['ranges'],
                    'counts': score_distribution['counts']
                },
                'gender_ratio': {
                    'male': gender_ratio['male'],
                    'female': gender_ratio['female']
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@student_bp.route('/school-ranking', methods=['GET'])
@student_required
def get_student_school_ranking():
    """获取学生在学校的总体排名"""
    try:
        student_id = g.user_id
        
        # 获取学校排名数据
        ranking_data = get_school_ranking(student_id)
        
        return jsonify({
            'success': True,
            'data': {
                'school_rank': ranking_data['rank'],
                'total_students': ranking_data['total'],
                'percentile': ranking_data['percentile']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@student_bp.route('/report', methods=['POST'])
@login_required
def student_report():
    """学生报到"""
    try:
        # 获取当前用户
        user = User.query.get(g.user_id)
        if not user or user.role != 'student':
            return jsonify({
                'success': False,
                'message': '只有学生可以报到'
            }), 403
            
        # 获取学生信息
        student = Student.query.filter_by(user_id=g.user_id).first()
        if not student:
            return jsonify({
                'success': False,
                'message': '学生信息不存在'
            }), 404
            
        # 检查报到状态
        if student.status == 'reported':
            return jsonify({
                'success': False,
                'message': '您已经完成报到'
            }), 400
            
        # 更新报到状态
        student.status = 'reported'
        student.report_time = datetime.now()
        
        # 记录报到日志
        log = SystemLog(
            user_id=g.user_id,
            type='student_report',
            content=f'学生 {user.name} 完成报到',
            ip_address=request.remote_addr
        )
        
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '报到成功'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Report error: {str(e)}")  # 添加错误日志
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
