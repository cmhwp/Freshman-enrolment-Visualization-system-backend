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
from sqlalchemy import func, case
from app.models.class_info import ClassInfo

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
    """获取专业排名"""
    try:
        student = Student.query.get(g.user_id)
        if not student or not student.score:
            return jsonify({
                'success': False,
                'message': '未找到成绩记录'
            }), 404
            
        # 获取同专业的所有成绩
        major_scores = Score.query.join(Student)\
            .filter(Student.major == student.major)\
            .order_by(Score.total_score.desc())\
            .all()
            
        # 计算当前排名
        current_rank = 1
        for i, score in enumerate(major_scores, 1):
            if score.student_id == student.id:
                current_rank = i
                break
                
        return jsonify({
            'success': True,
            'data': {
                'currentRank': current_rank,
                'totalStudents': len(major_scores)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@student_bp.route('/school-ranking', methods=['GET'])
@student_required
def get_school_ranking():
    """获取学校排名"""
    try:
        student = Student.query.get(g.user_id)
        if not student or not student.score:
            return jsonify({
                'success': False,
                'message': '未找到成绩记录'
            }), 404
            
        # 获取所有成绩并排序
        all_scores = Score.query\
            .order_by(Score.total_score.desc())\
            .all()
            
        # 计算当前排名
        current_rank = 1
        for i, score in enumerate(all_scores, 1):
            if score.student_id == student.id:
                current_rank = i
                break
                
        return jsonify({
            'success': True,
            'data': {
                'currentRank': current_rank,
                'totalStudents': len(all_scores)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@student_bp.route('/score-analysis', methods=['GET'])
@student_required
def get_score_analysis():
    """获取成绩分析"""
    try:
        student = Student.query.get(g.user_id)
        if not student or not student.score:
            return jsonify({
                'success': False,
                'message': '未找到成绩记录'
            }), 404
            
        # 计算专业平均分
        avg_scores = db.session.query(
            func.avg(Score.chinese).label('chinese'),
            func.avg(Score.math).label('math'),
            func.avg(Score.english).label('english'),
            func.avg(Score.physics).label('physics'),
            func.avg(Score.chemistry).label('chemistry'),
            func.avg(Score.biology).label('biology')
        ).join(Student)\
        .filter(Student.major == student.major)\
        .first()
        
        # 计算各科目排名
        subject_ranks = {}
        for subject in ['chinese', 'math', 'english', 'physics', 'chemistry', 'biology']:
            scores = Score.query.join(Student)\
                .filter(Student.major == student.major)\
                .order_by(getattr(Score, subject).desc())\
                .all()
                
            for i, score in enumerate(scores, 1):
                if score.student_id == student.id:
                    subject_ranks[subject] = i
                    break
                    
        return jsonify({
            'success': True,
            'data': {
                'averageScores': {
                    'chinese': float(avg_scores.chinese or 0),
                    'math': float(avg_scores.math or 0),
                    'english': float(avg_scores.english or 0),
                    'physics': float(avg_scores.physics or 0),
                    'chemistry': float(avg_scores.chemistry or 0),
                    'biology': float(avg_scores.biology or 0)
                },
                'subjectRanks': subject_ranks
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@student_bp.route('/score-distribution', methods=['GET'])
@student_required
def get_score_distribution():
    """获取分数段分布数据"""
    try:
        student = Student.query.get(g.user_id)
        if not student:
            return jsonify({
                'success': False,
                'message': '未找到学生信息'
            }), 404

        # 修改 case 语句的写法
        province_distribution = db.session.query(
            case(
                (Score.total_score >= 700, '750-700'),
                (Score.total_score >= 650, '699-650'),
                (Score.total_score >= 600, '649-600'),
                (Score.total_score >= 550, '599-550'),
                (Score.total_score >= 500, '549-500'),
                else_='<500'
            ).label('score_range'),
            func.count('*').label('count')
        ).group_by('score_range').all()

        # 修改专业分数分布查询
        major_distribution = db.session.query(
            case(
                (Score.total_score >= 700, '750-700'),
                (Score.total_score >= 650, '699-650'),
                (Score.total_score >= 600, '649-600'),
                (Score.total_score >= 550, '599-550'),
                (Score.total_score >= 500, '549-500'),
                else_='<500'
            ).label('score_range'),
            func.count('*').label('count')
        ).join(Student).filter(
            Student.major == student.major
        ).group_by('score_range').all()

        # 转换查询结果为字典
        province_dict = {str(range_): count for range_, count in province_distribution}
        major_dict = {str(range_): count for range_, count in major_distribution}

        # 确保所有分数段都有值，没有的设为0
        score_ranges = ['750-700', '699-650', '649-600', '599-550', '549-500', '<500']
        for range_ in score_ranges:
            if range_ not in province_dict:
                province_dict[range_] = 0
            if range_ not in major_dict:
                major_dict[range_] = 0

        return jsonify({
            'success': True,
            'data': {
                'province': province_dict,
                'major': major_dict
            }
        })
    except Exception as e:
        print(f"Error in score distribution: {str(e)}")  # 添加错误日志
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

@student_bp.route('/score', methods=['GET'])
@student_required
def get_score():
    """获取学生个人成绩"""
    try:
        score = Score.query.filter_by(student_id=g.user_id).first()
        if not score:
            return jsonify({
                'success': False,
                'message': '未找到成绩记录'
            }), 404
            
        return jsonify({
            'success': True,
            'data': score.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@student_bp.route('/transfer', methods=['POST'])
def transfer_student():
    try:
        data = request.get_json()
        student = Student.query.get_or_404(data['student_id'])
        old_class_id = student.class_id
        new_class_id = data['new_class_id']
        
        if old_class_id:
            old_class = ClassInfo.query.get(old_class_id)
            old_class.assigned_students -= 1
            
        new_class = ClassInfo.query.get(new_class_id)
        new_class.assigned_students += 1
        student.class_id = new_class_id
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '学生转班成功'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Transfer error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
