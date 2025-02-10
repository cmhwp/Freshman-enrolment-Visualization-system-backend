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

@teacher_bp.route('/scores/template', methods=['GET'])
@teacher_required
def get_score_template():
    """获取成绩导入模板"""
    try:
        template_path = create_student_score_template()
        return send_file(
            template_path,
            as_attachment=True,
            download_name='student_score_template.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@teacher_bp.route('/scores/import', methods=['POST'])
@teacher_required
def import_scores():
    """导入学生成绩"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '没有上传文件'
            }), 400
            
        file = request.files['file']
        if not file.filename.endswith('.xlsx'):
            return jsonify({
                'success': False,
                'message': '请上传Excel文件(.xlsx)'
            }), 400
            
        result = process_student_score_excel(file)
        
        # 记录导入日志
        log = SystemLog(
            user_id=g.user_id,
            type='import_scores',
            content=f'导入学生成绩：成功{result["success"]}条，失败{result["failed"]}条',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': result
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


