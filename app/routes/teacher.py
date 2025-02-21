from app.extensions import db
from flask import Blueprint, jsonify, request, g, send_file
from app.utils.decorators import teacher_required, login_required
from app.models.class_info import ClassInfo
from app.models.student import Student
from app.models.score import Score
from app.models.system_log import SystemLog
from app.models.user import User
from datetime import datetime
from app.utils.template import create_student_score_template
from app.utils.excel import process_student_score_excel
from app.models.settings import Settings
from app.schemas import StudentSchema
from app.models.teacher import Teacher
from flask_jwt_extended import get_jwt_identity
from app.utils.analysis import (
    get_score_distribution,
    calculate_subject_scores,
    calculate_score_trends,
    generate_ai_analysis
)
from sqlalchemy import func
from app.models.analysis_report import AnalysisReport
import json
from io import BytesIO

teacher_bp = Blueprint('teacher', __name__)

# 班级管理相关API
@teacher_bp.route('/classes', methods=['GET'])
@teacher_required
def get_classes():
    """获取教师负责的班级列表"""
    try:
        classes = ClassInfo.query.filter_by(teacher_id=g.user_id).all()
        return jsonify({
            'success': True,
            'data': [class_info.to_dict() for class_info in classes],
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@teacher_bp.route('/classes/<int:class_id>', methods=['GET'])
@teacher_required
def get_class_details(class_id):
    """获取班级详情"""
    try:
        class_info = ClassInfo.query.get_or_404(class_id)
        if class_info.teacher_id != g.user_id:
            return jsonify({
                'success': False,
                'message': '无权访问该班级'
            }), 403
            
        # 获取班级学生信息
        students = Student.query.filter_by(class_id=class_id).all()
        student_list = []
        for student in students:
            # 性别转换
            gender_map = {
                'M': '男',
                'F': '女'
            }
            student_data = {
                'id': student.id,
                'name': student.user.name,
                'student_id': student.student_id,
                'gender': gender_map.get(student.user.gender, '未知'),  # 转换性别显示
                'status': student.status,
                'admission_year': student.admission_year,
                'report_time': student.report_time.isoformat() if student.report_time else None,
                'contact': student.user.contact,
                'email': student.user.email,
                'province': student.user.province
            }
            student_list.append(student_data)
            
        # 构建返回数据
        class_data = class_info.to_dict()
        class_data['students'] = student_list
            
        return jsonify({
            'success': True,
            'data': class_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@teacher_bp.route('/classes/<int:class_id>', methods=['PUT'])
@teacher_required
def update_class(class_id):
    """更新班级信息"""
    try:
        class_info = ClassInfo.query.get_or_404(class_id)
        if class_info.teacher_id != g.user_id:
            return jsonify({
                'success': False,
                'message': '无权修改该班级'
            }), 403

        data = request.get_json()
        
        # 更新班级信息
        class_info.class_name = data.get('class_name', class_info.class_name)
        class_info.department = data.get('department', class_info.department)
        class_info.major = data.get('major', class_info.major)
        class_info.year = data.get('year', class_info.year)
        class_info.capacity = data.get('capacity', class_info.capacity)
        
        # 重新计算已分配学生数量
        class_info.assigned_students = Student.query.filter_by(class_id=class_id).count()
        
        db.session.commit()

        # 记录日志
        log = SystemLog(
            user_id=g.user_id,
            type='update_class',
            content=f'更新班级信息：{class_info.class_name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '更新成功',
            'data': class_info.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 成绩管理相关API
@teacher_bp.route('/scores', methods=['GET'])
@teacher_required
def get_scores():
    """获取学生成绩列表"""
    try:
        # 获取教师管理的班级的所有学生成绩
        scores = Score.query.join(Student, Score.student_id == Student.id)\
            .join(ClassInfo, Student.class_id == ClassInfo.id)\
            .filter(ClassInfo.teacher_id == g.user_id)\
            .all()
            
        return jsonify({
            'success': True,
            'data': [score.to_dict() for score in scores]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@teacher_bp.route('/classes/<int:class_id>/score-template', methods=['GET'])
@teacher_required
def get_score_template(class_id):
    """获取成绩导入模板"""
    try:
        # 验证班级权限
        class_info = ClassInfo.query.filter_by(
            id=class_id,
            teacher_id=g.user_id
        ).first()
        
        if not class_info:
            return jsonify({
                'success': False,
                'message': '未找到班级信息'
            }), 404
    
        # 创建模板
        wb = create_student_score_template(class_id, g.user_id)
        
        # 保存到内存
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{class_info.class_name}-成绩导入模板.xlsx'
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
        }), 500

@teacher_bp.route('/classes/<int:class_id>/scores/import', methods=['POST'])
@teacher_required
def import_scores(class_id):
    """导入成绩"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '未上传文件'
            }), 400
            
        file = request.files['file']
        if not file.filename.endswith('.xlsx'):
            return jsonify({
                'success': False,
                'message': '请上传Excel文件(.xlsx)'
            }), 400

        # 处理导入
        results = process_student_score_excel(file.read(), class_id, g.user_id)
        
        return jsonify({
            'success': True,
            'data': results
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

#在settingInfo获取departmentOptions和majorOptions
@teacher_bp.route('/options', methods=['GET'])
@login_required
def get_options():
    """获取部门和专业选项"""
    try:
        # 从系统设置获取选项
        settings = Settings.query.first()
        if not settings:
            return jsonify({
                'success': False,
                'message': '系统设置未初始化'
            }), 500
            
        # 获取当前所有班级的年级选项
        years = db.session.query(ClassInfo.year)\
            .distinct()\
            .order_by(ClassInfo.year.desc())\
            .all()
        year_options = [year[0] for year in years]
            
        return jsonify({
            'success': True,
            'data': {
                'departments': settings.departments,  # 院系选项
                'majors': settings.majors,          # 专业选项
                'years': year_options
            }
        })
    except Exception as e:

        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
#创建班级
@teacher_bp.route('/classes', methods=['POST'])
@teacher_required
def create_class():
    """创建班级"""
    #获取当前登录用户
    user = User.query.get(g.user_id)
    if not user:
        return jsonify({
            'success': False,
            'message': '用户不存在'
        }), 404
    try:
        data = request.get_json()
        class_name = data.get('class_name')
        department = data.get('department')
        major = data.get('major')
        year = data.get('year')
        capacity = data.get('capacity') 
        teacher_id = user.id
        
        # 检查班级是否已存在
        existing_class = ClassInfo.query.filter_by(class_name=class_name).first()
        if existing_class:
            return jsonify({
                'success': False,
                'message': '班级已存在' 
            }), 400
        
        # 创建新班级
        new_class = ClassInfo(
            class_name=class_name,
            department=department,
            major=major,
            year=year,
            capacity=capacity,
            teacher_id=teacher_id
        )
        

        db.session.add(new_class)   
        db.session.commit()
        
        # 记录日志
        log = SystemLog(
            user_id=g.user_id,
            type='create_class',
            content=f'创建班级：{class_name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit() 
        
        return jsonify({
            'success': True,
            'message': '班级创建成功',
            'data': new_class.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
#删除班级
@teacher_bp.route('/classes/<int:class_id>', methods=['DELETE'])
@teacher_required   
def delete_class(class_id):
    """删除班级"""
    try:
        class_info = ClassInfo.query.get_or_404(class_id)
        if class_info.teacher_id != g.user_id:
            return jsonify({
                'success': False,
                'message': '无权删除该班级'
            }), 403
        
        db.session.delete(class_info)
        db.session.commit() 
        
        return jsonify({
            'success': True,
            'message': '班级删除成功'
        })
    except Exception as e:  
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500 

# 获取未分配班级的学生列表
@teacher_bp.route('/unassigned-students', methods=['GET'])
@teacher_required
def get_unassigned_students():
    """获取未分配班级的学生列表"""
    try:
        # 查询未分配班级的学生
        students = Student.query.join(User).filter(Student.class_id.is_(None)).all()
        
        # 转换为列表数据
        student_list = []
        for student in students:
            student_data = {
                'id': student.id,
                'name': student.user.name,
                'student_id': student.student_id,
                'major': student.major,
                'status': student.status,
                'gender': student.user.gender,
                'contact': student.user.contact,
                'email': student.user.email
            }
            student_list.append(student_data)
            
        return jsonify({
            'success': True,
            'data': student_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 分配学生到班级
@teacher_bp.route('/class/<int:class_id>/assign-students', methods=['POST'])
@login_required
def assign_students(class_id):
    try:
        data = request.get_json()
        student_ids = data.get('student_ids', [])
        
        # 检查班级是否存在
        class_obj = ClassInfo.query.get(class_id)
        if not class_obj:
            return jsonify({
                'success': False,
                'message': '班级不存在'
            }), 404
            
        # 检查班级容量
        current_student_count = Student.query.filter_by(class_id=class_id).count()
        if current_student_count + len(student_ids) > class_obj.capacity:
            return jsonify({
                'success': False,
                'message': '超出班级容量限制'
            }), 400
            
        # 分配学生到班级
        students = Student.query.filter(Student.id.in_(student_ids)).all()
        for student in students:
            if student.class_id is not None:
                return jsonify({
                    'success': False,
                    'message': f'学生 {student.name} 已经分配了班级'
                }), 400
            student.class_id = class_id
            
        # 更新班级已分配学生数量
        class_obj.assigned_students = current_student_count + len(students)
        
        # 记录日志
        log = SystemLog(
            user_id=g.user_id,
            type='assign_students',
            content=f'分配学生到班级：{class_id}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '分配成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 从班级移除学生
@teacher_bp.route('/class/<int:class_id>/remove-students', methods=['POST'])
@login_required
def remove_students(class_id):
    try:
        data = request.get_json()
        student_ids = data.get('student_ids', [])
        
        # 检查班级是否存在
        class_obj = ClassInfo.query.get(class_id)
        if not class_obj:
            return jsonify({
                'success': False,
                'message': '班级不存在'
            }), 404
            
        # 移除学生的班级分配
        students = Student.query.filter(
            Student.id.in_(student_ids),
            Student.class_id == class_id
        ).all()
        
        if not students:
            return jsonify({
                'success': False,
                'message': '未找到要移除的学生'
            }), 404
            
        for student in students:
            student.class_id = None
            
        # 更新班级已分配学生数量
        class_obj.assigned_students = max(0, class_obj.assigned_students - len(students))
            
        db.session.commit()
        
        # 记录日志
        log = SystemLog(
            user_id=g.user_id,
            type='remove_students',
            content=f'从班级移除学生：{class_id}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '移除成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    

# 获取班级成绩
@teacher_bp.route('/classes/<int:class_id>/scores', methods=['GET'])
@teacher_required
def get_class_scores(class_id):
    try:
        # 检查班级是否存在且属于当前教师
        class_info = ClassInfo.query.filter_by(
            id=class_id,
            teacher_id=g.user_id
        ).first_or_404()
        
        # 获取班级学生的成绩
        scores = Score.query.join(Student).filter(
            Student.class_id == class_id
        ).all()
        
        return jsonify({
            'success': True,
            'data': [score.to_dict() for score in scores]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 更新班级成绩
@teacher_bp.route('/classes/<int:class_id>/scores', methods=['POST'])
@teacher_required
def update_class_scores(class_id):
    try:
        data = request.get_json()
        scores = data.get('scores', [])
        
        # 检查班级是否存在且属于当前教师
        class_info = ClassInfo.query.filter_by(
            id=class_id,
            teacher_id=g.user_id
        ).first_or_404()
        
        # 批量更新成绩
        for score_data in scores:
            score = Score.query.get(score_data['id'])
            if score:
                for key, value in score_data.items():
                    if key != 'id':
                        setattr(score, key, value)
                        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '成绩更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@teacher_bp.route('/scores/<int:score_id>', methods=['PUT'])
@teacher_required
def update_score(score_id):
    """更新学生成绩"""
    try:
        # 获取成绩记录
        score = Score.query.get_or_404(score_id)
        
        # 检查是否有权限修改（只能修改自己班级学生的成绩）
        student = Student.query.get(score.student_id)
        if not student or student.class_id not in [c.id for c in ClassInfo.query.filter_by(teacher_id=g.user_id).all()]:
            return jsonify({
                'success': False,
                'message': '无权修改该学生成绩'
            }), 403
            
        # 获取更新数据
        data = request.get_json()
        
        # 更新成绩
        score.chinese = data.get('chinese', score.chinese)
        score.math = data.get('math', score.math)
        score.english = data.get('english', score.english)
        score.physics = data.get('physics', score.physics)
        score.chemistry = data.get('chemistry', score.chemistry)
        score.biology = data.get('biology', score.biology)
        
        # 重新计算总分
        score.total_score = (
            score.chinese +
            score.math +
            score.english +
            score.physics +
            score.chemistry +
            score.biology
        )
        
        # 记录日志
        log = SystemLog(
            user_id=g.user_id,
            type='update_score',
            content=f'更新学生成绩：{student.user.name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '成绩更新成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@teacher_bp.route('/scores/<int:score_id>', methods=['DELETE'])
@teacher_required
def delete_score(score_id):
    """删除学生成绩"""
    try:
        # 获取成绩记录
        score = Score.query.get_or_404(score_id)
        
        # 检查是否有权限删除（只能删除自己班级学生的成绩）
        student = Student.query.get(score.student_id)
        if not student or student.class_id not in [c.id for c in ClassInfo.query.filter_by(teacher_id=g.user_id).all()]:
            return jsonify({
                'success': False,
                'message': '无权删除该学生成绩'
            }), 403
            
        # 记录日志
        log = SystemLog(
            user_id=g.user_id,
            type='delete_score',
            content=f'删除学生成绩：{student.user.name}',
            ip_address=request.remote_addr
        )
        
        # 删除成绩
        db.session.delete(score)
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '成绩删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@teacher_bp.route('/classes/<int:class_id>/analysis', methods=['GET', 'POST'])
@teacher_required
def analyze_class_scores(class_id):
    """获取或生成班级成绩分析报告"""
    try:
        # 验证班级是否存在且属于当前教师
        class_info = ClassInfo.query.filter_by(
            id=class_id, 
            teacher_id=g.user_id
        ).first()
        
        if not class_info:
            return jsonify({
                'success': False,
                'message': '未找到班级信息'
            }), 404

        # GET请求 - 获取已有的分析报告
        if request.method == 'GET':
            existing_report = AnalysisReport.query.filter_by(class_id=class_id).first()
            if existing_report:
                return jsonify({
                    'success': True,
                    'data': existing_report.report_data,
                    'created_at': existing_report.created_at.isoformat()
                })
            return jsonify({
                'success': True,
                'data': None
            })

        # POST请求 - 生成新的分析报告
        scores = Score.query.join(Student)\
            .filter(Student.class_id == class_id)\
            .all()
            
        if not scores:
            return jsonify({
                'success': False,
                'message': '暂无成绩数据'
            }), 404

        # 1. 计算成绩分布
        score_distribution = get_score_distribution(scores)
        
        # 2. 计算各科目成绩情况
        subject_scores = calculate_subject_scores(scores)
        
        # 3. 生成AI分析报告
        report_content = generate_ai_analysis(
            scores=scores,
            distribution=score_distribution,
            subject_scores=subject_scores,
            class_info=class_info
        )

        # 4. 处理报告内容格式
        if isinstance(report_content, str):
            if report_content.startswith('```markdown'):
                report_content = report_content.replace('```markdown', '', 1)
            if report_content.startswith('```'):
                report_content = report_content.replace('```', '', 1)
            if report_content.endswith('```'):
                report_content = report_content[:-3]
            report_content = report_content.strip()

        # 5. 保存或更新分析报告
        existing_report = AnalysisReport.query.filter_by(class_id=class_id).first()
        if existing_report:
            existing_report.report_data = report_content
            existing_report.updated_at = datetime.now()
        else:
            new_report = AnalysisReport(
                class_id=class_id,
                teacher_id=g.user_id,
                report_data=report_content
            )
            db.session.add(new_report)
        #记录日志
        log = SystemLog(
            user_id=g.user_id,
            type='generate_analysis_report',
            content=f'生成班级成绩分析报告：{class_id}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': report_content
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error in analyze_class_scores: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'生成分析报告失败: {str(e)}'
        }), 500

@teacher_bp.route('/classes/<int:class_id>/analysis/history', methods=['GET'])
@teacher_required
def get_analysis_history(class_id):
    """获取班级历史分析报告"""
    try:
        report = AnalysisReport.query.filter_by(class_id=class_id).first()
        print(report.to_dict())
        if not report:
            return jsonify({
                'success': False,
                'message': '未找到分析报告'
            }), 404
        
        return jsonify({
            'success': True,
            'data': report.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@teacher_bp.route('/students/report-status', methods=['GET'])
@teacher_required
def get_students_report_status():
    """获取教师管理班级的学生报到情况"""
    current_user = get_jwt_identity()
    user = User.query.get(current_user['user_id'])
    try:
        # 获取当前教师信息
        teacher = Teacher.query.filter_by(user_id=user.id).first()
        if not teacher:
            return jsonify({
                'success': False,
                'message': '教师信息不存在'
            }), 404

        # 获取教师管理的班级的所有学生
        students = Student.query\
            .join(User, Student.user_id == User.id)\
            .join(ClassInfo, Student.class_id == ClassInfo.id)\
            .filter(ClassInfo.teacher_id == user.id)\
            .add_columns(
                ClassInfo.class_name,
                Student.student_id,
                Student.report_time,
                Student.status
            )\
            .all()

        # 构造返回数据
        student_list = [{
            'id': student.Student.id,
            'name': student.Student.user.name,
            'student_number': student.student_id,
            'class_name': student.class_name,
            'report_time': student.report_time.isoformat() if student.report_time else None,
            'status': student.status
        } for student in students]

        # 统计数据
        total = len(student_list)
        reported = sum(1 for s in student_list if s['status'] == 'reported')
        unreported = total - reported

        return jsonify({
            'success': True,
            'data': {
                'students': student_list,
                'statistics': {
                    'total': total,
                    'reported': reported,
                    'unreported': unreported,
                    'report_rate': f"{(reported/total*100):.1f}%" if total > 0 else "0%"
                }
            }
        })

    except Exception as e:
        print(f"Error in get_students_report_status: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@teacher_bp.route('/students/<int:student_id>/report-status', methods=['PUT'])
@teacher_required
def update_student_report_status(student_id):
    """更新学生报到状态"""
    current_user = get_jwt_identity()
    user = User.query.get(current_user['user_id'])
    try:
        # 获取当前教师信息
        teacher = Teacher.query.filter_by(user_id=user.id).first()
        if not teacher:
            return jsonify({
                'success': False,
                'message': '教师信息不存在'
            }), 404

        # 获取学生信息并验证权限
        student = Student.query\
            .join(ClassInfo, Student.class_id == ClassInfo.id)\
            .filter(
                Student.id == student_id,
                ClassInfo.teacher_id == user.id
            ).first()

        if not student:
            return jsonify({
                'success': False,
                'message': '无权操作此学生或学生不存在'
            }), 404

        data = request.get_json()
        new_status = data.get('status')
        if new_status not in ['reported', 'unreported']:
            return jsonify({
                'success': False,
                'message': '无效的报到状态'
            }), 400

        # 更新状态
        student.status = new_status
        if new_status == 'reported':
            student.report_time = datetime.now()
        else:
            student.report_time = None
        #记录日志
        log = SystemLog(
            user_id=user.id,
            type='update_student_report_status',
            content=f'{user.name}更新学生报到状态：{student.user.name}',
            ip_address=request.remote_addr
        )   
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '更新成功'
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error in update_student_report_status: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

