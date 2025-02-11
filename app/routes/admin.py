from flask import Blueprint, jsonify, request, g, send_file
from app.utils.decorators import admin_required
from app.models.user import User
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.system_log import SystemLog
from app.models.settings import Settings
from app.models.class_info import ClassInfo
from app.extensions import db
from sqlalchemy import or_, case, func, and_
from app.utils.excel import process_teacher_excel
import os
from app.utils.template import create_teacher_template
from datetime import datetime, timedelta
from app.utils.template import create_student_template
from app.utils.excel import process_student_excel

admin_bp = Blueprint('admin', __name__)

# 学生管理
@admin_bp.route('/students', methods=['GET'])
@admin_required
def get_students():
    """获取学生列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('pageSize', 10, type=int)
        search = request.args.get('search', '')
        major = request.args.get('major', '')
        status = request.args.get('status', '')
        
        # 构建查询
        query = User.query.join(Student).filter(User.role == 'student')
        
        # 搜索条件
        if search:
            query = query.filter(or_(
                User.name.like(f'%{search}%'),
                User.email.like(f'%{search}%'),
                Student.student_id.like(f'%{search}%')  # 添加学号搜索
            ))
            
        if major:
            query = query.filter(Student.major == major)
            
        if status:
            query = query.filter(Student.status == status)
            
        # 分页
        pagination = query.paginate(page=page, per_page=per_page)
        
        # 转换为列表
        students = []
        for user in pagination.items:
            student_data = user.to_dict()
            student = user.student_profile
            if student:
                student_data.update({
                    'student_id': student.student_id,
                    'major': student.major,
                    'status': student.status,
                    'admission_date': student.admission_date.strftime('%Y-%m-%d') if student.admission_date else None,
                    'graduation_date': student.graduation_date.strftime('%Y-%m-%d') if student.graduation_date else None
                })
            students.append(student_data)
            
        return jsonify({
            'success': True,
            'data': {
                'list': students,
                'total': pagination.total
            }
        })
        
    except Exception as e:
        print(f"Get students error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/students/<int:id>', methods=['PUT'])
@admin_required
def update_student(id):
    """更新学生信息"""
    try:
        data = request.get_json()
        user = User.query.get_or_404(id)
        student = Student.query.filter_by(user_id=id).first()
        
        if not student:
            return jsonify({
                'success': False,
                'message': '学生不存在'
            }), 404
            
        # 更新基本信息
        if 'name' in data:
            user.name = data['name']
        if 'gender' in data:
            user.gender = data['gender']
        if 'contact' in data:
            user.contact = data['contact']
            
        # 更新学生特有信息
        if 'major' in data:
            student.major = data['major']
        if 'status' in data:  # 添加状态更新
            student.status = data['status']
            
        db.session.commit()
        
        # 返回更新后的完整信息
        student_data = user.to_dict()
        student_data.update({
            'student_id': student.student_id,
            'major': student.major,
            'status': student.status,
            'admission_date': student.admission_date.strftime('%Y-%m-%d') if student.admission_date else None,
            'graduation_date': student.graduation_date.strftime('%Y-%m-%d') if student.graduation_date else None
        })
        # 记录操作日志
        log = SystemLog(
            user_id=g.user_id,
            type='update_student',
            content=f'更新学生信息: {user.name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '更新成功',
            'data': student_data
        })

        
    except Exception as e:
        db.session.rollback()
        print(f"Update student error: {str(e)}")  # 添加错误日志
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/students/<int:id>', methods=['DELETE'])
@admin_required
def delete_student(id):
    """删除学生信息"""
    try:
        user = User.query.get_or_404(id)
        student = Student.query.filter_by(user_id=id).first()
        
        if not student:
            return jsonify({
                'success': False,
                'message': '学生不存在'
            }), 404
            
        # 记录删除日志
        log = SystemLog(
            user_id=g.user_id,
            type='delete_student',
            content=f'删除学生: {user.name}（学号：{student.student_id}）',
            ip_address=request.remote_addr
        )
        
        # 删除学生信息和用户信息
        db.session.delete(student)
        db.session.delete(user)
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Delete student error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 操作日志
@admin_bp.route('/logs', methods=['GET'])
@admin_required
def get_system_logs():
    """获取系统操作日志"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 10, type=int)
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        log_type = request.args.get('type')
        
        query = SystemLog.query
        
        if start_date:
            query = query.filter(SystemLog.created_at >= start_date)
        if end_date:
            query = query.filter(SystemLog.created_at <= end_date)
        if log_type:
            query = query.filter(SystemLog.type == log_type)
            
        pagination = query.order_by(SystemLog.created_at.desc()).paginate(
            page=page,
            per_page=page_size,
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'list': [log.to_dict() for log in pagination.items],
                'total': pagination.total
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500



@admin_bp.route('/teachers', methods=['GET'])
@admin_required
def get_teacher_list():
    """获取教师列表"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 10))
        search = request.args.get('search', '')
        department = request.args.get('department')

        # 构建查询
        query = User.query.filter_by(role='teacher')
        
        # 搜索条件
        if search:
            query = query.filter(
                db.or_(
                    User.username.like(f'%{search}%'),
                    User.name.like(f'%{search}%'),
                    User.email.like(f'%{search}%')
                )
            )
            
        if department:
            query = query.filter(User.department == department)

        # 分页
        pagination = query.paginate(
            page=page,
            per_page=page_size,
            error_out=False
        )

        return jsonify({
            'success': True,
            'data': {
                'list': [user.to_dict() for user in pagination.items],
                'total': pagination.total
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/teachers/<int:id>', methods=['PUT'])
@admin_required
def update_teacher(id):
    """更新教师信息"""
    try:
        data = request.get_json()
        user = User.query.filter_by(id=id, role='teacher').first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': '教师不存在'
            }), 404
        
        # 更新用户基本信息
        if 'name' in data:
            user.name = data['name']
        if 'gender' in data:
            user.gender = data['gender']
        if 'contact' in data:
            user.contact = data['contact']
        
        # 更新教师信息
        if 'teacher_profile' in data:
            teacher = user.teacher_profile
            if not teacher:
                teacher = Teacher(user=user)
                db.session.add(teacher)
            
            profile_data = data['teacher_profile']
            if 'department' in profile_data:
                teacher.department = profile_data['department']
            if 'title' in profile_data:
                teacher.title = profile_data['title']
            if 'research_area' in profile_data:
                teacher.research_area = profile_data['research_area']
        
        # 记录操作日志
        log = SystemLog(
            user_id=g.user_id,
            type='update_teacher',
            content=f'更新教师信息: {user.name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '更新成功'
        })
        
    except Exception as e:
        print(f"Update teacher error: {str(e)}")  # 打印错误信息
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '更新失败，请检查输入数据'
        }), 500

@admin_bp.route('/teachers/<int:id>', methods=['DELETE'])
@admin_required
def delete_teacher(id):
    """删除教师信息"""
    try:
        user = User.query.get_or_404(id)
        teacher = Teacher.query.filter_by(user_id=id).first()
        
        if not teacher:
            return jsonify({
                'success': False,
                'message': '教师不存在'
            }), 404
            
        # 检查是否有关联的班级
        managed_classes = ClassInfo.query.filter_by(teacher_id=id).all()
        if managed_classes:
            # 解除班级关联
            for class_info in managed_classes:
                class_info.teacher_id = None
            
        # 记录删除日志
        log = SystemLog(
            user_id=g.user_id,
            type='delete_teacher',
            content=f'删除教师: {user.name}',
            ip_address=request.remote_addr
        )
        
        # 先删除教师信息，再删除用户信息
        db.session.delete(teacher)
        db.session.delete(user)
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Delete teacher error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 添加系统设置相关路由
@admin_bp.route('/settings', methods=['GET'])
@admin_required
def get_settings():
    """获取系统设置"""
    try:
        settings = Settings.query.first()
        if not settings:
            settings = Settings()  # 创建默认设置
            db.session.add(settings)
            db.session.commit()
            
        return jsonify({
            'success': True,
            'data': settings.to_dict()
        })
        
    except Exception as e:
        print(f"Get settings error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/settings', methods=['PUT'])
@admin_required
def update_settings():
    """更新系统设置"""
    try:
        data = request.get_json()
        settings = Settings.query.first()
        
        if not settings:
            settings = Settings()
            db.session.add(settings)
        
        # 更新设置
        settings.update_from_dict(data)
        
        # 记录操作日志
        log = SystemLog(
            user_id=g.user_id,
            type='update_settings',
            content=f'更新系统设置',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '设置更新成功'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Update settings error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/teachers', methods=['POST'])
@admin_required
def create_teacher():
    """创建教师账号"""
    try:
        data = request.get_json()
        
        # 创建用户基本信息
        user = User(
            username=data['username'],
            email=data['email'],
            role='teacher',
            name=data['name'],
            gender=data.get('gender'),  # 新增
            province=data.get('province'),  # 新增
            is_active=True
        )
        user.set_password(data['password'])
        
        # 创建教师信息
        teacher = Teacher(
            user=user,
            department=data['teacher_profile']['department'],
            title=data['teacher_profile'].get('title'),
            research_area=data['teacher_profile'].get('research_area')
        )
        
        db.session.add(user)
        db.session.add(teacher)
        
        # 记录操作日志
        log = SystemLog(
            user_id=g.user_id,
            type='create_teacher',
            content=f'创建教师账号: {user.username}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '创建成功',
            'data': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Create teacher error: {str(e)}")  # 添加错误日志
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@admin_bp.route('/classes', methods=['POST'])
@admin_required
def create_class():
    """创建班级"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['name', 'major', 'department', 'year', 'capacity']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'message': '缺少必需字段'
            }), 400
            
        # 创建班级
        class_info = ClassInfo(
            name=data['name'],
            major=data['major'],
            department=data['department'],
            year=data['year'],
            capacity=data['capacity'],
            teacher_id=data.get('teacher_id')  # 可选字段
        )
        
        db.session.add(class_info)
        
        # 记录操作日志
        log = SystemLog(
            user_id=g.user_id,
            type='create_class',
            content=f'创建班级: {class_info.name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '班级创建成功',
            'data': class_info.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/teachers/import', methods=['POST'])
@admin_required
def import_teachers():
    """批量导入教师"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '没有上传文件'
            }), 400

        file = request.files['file']
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({
                'success': False,
                'message': '请上传Excel文件'
            }), 400

        result = process_teacher_excel(file)
        
        # 记录操作日志
        log = SystemLog(
            user_id=g.user_id,
            type='import_teachers',
            content=f'批量导入教师: 成功{result["success"]}条，失败{result["failed"]}条',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '导入完成',
            'data': result
        })

    except Exception as e:
        print(f"Import teachers error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/teachers/template', methods=['GET'])
@admin_required
def download_teacher_template():
    """下载教师导入模板"""
    try:
        template_path = create_teacher_template()
        return send_file(
            template_path,
            as_attachment=True,
            download_name='教师导入模板.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        current_app.logger.error(f"Template download error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 新生报到相关路由
@admin_bp.route('/enrollment/stats', methods=['GET'])
@admin_required
def get_enrollment_stats():
    """获取新生报到统计"""
    try:
        settings = get_settings()
        current_year = datetime.now().year
        
        # 获取总人数
        total_count = db.session.query(Student).filter(
            Student.admission_year == current_year
        ).count()
        
        # 获取已报到人数
        reported_count = db.session.query(Student).filter(
            Student.admission_year == current_year,
            Student.status == 'reported'
        ).count()
        
        # 按专业统计
        major_stats = db.session.query(
            Student.major,
            func.count().label('total'),
            func.sum(
                case(
                    (Student.status == 'reported', 1),
                    else_=0
                )
            ).label('reported')
        ).filter(
            Student.admission_year == current_year
        ).group_by(Student.major).all()
        
        # 按省份统计
        province_stats = db.session.query(
            User.province,
            func.count().label('count')
        ).join(
            Student, Student.user_id == User.id
        ).filter(
            Student.admission_year == current_year
        ).group_by(User.province).all()
        
        return jsonify({
            'success': True,
            'data': {
                'totalCount': total_count,
                'reportedCount': reported_count,
                'unreportedCount': total_count - reported_count,
                'reportRate': reported_count / total_count if total_count > 0 else 0,
                'byMajor': [{
                    'major': stat.major or '未分配',
                    'total': stat.total,
                    'reported': stat.reported,
                    'rate': stat.reported / stat.total if stat.total > 0 else 0
                } for stat in major_stats],
                'byProvince': [{
                    'province': stat.province or '未知',
                    'count': stat.count,
                    'percentage': stat.count / total_count if total_count > 0 else 0
                } for stat in province_stats]
            }
        })
    except Exception as e:
        print(f"Enrollment stats error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/enrollment/trend', methods=['GET'])
@admin_required
def get_enrollment_trend():
    """获取每日报到趋势"""
    try:
        start_date = request.args.get('startDate', 
            (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date = request.args.get('endDate', 
            datetime.now().strftime('%Y-%m-%d'))
        
        # 转换日期字符串为datetime对象
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        
        # 按日期统计报到人数
        daily_stats = db.session.query(
            func.date(Student.report_time).label('date'),
            func.count().label('count')
        ).filter(
            Student.report_time.between(start_datetime, end_datetime),
            Student.status == 'reported'
        ).group_by(
            func.date(Student.report_time)
        ).order_by('date').all()
        
        # 计算累计人数
        result = []
        accumulative = 0
        
        # 确保每天都有数据
        current_date = start_datetime
        while current_date <= end_datetime:
            date_str = current_date.strftime('%Y-%m-%d')
            day_count = 0
            
            # 查找当天的统计数据
            for stat in daily_stats:
                if stat.date.strftime('%Y-%m-%d') == date_str:
                    day_count = stat.count
                    break
            
            accumulative += day_count
            result.append({
                'date': date_str,
                'count': day_count,
                'accumulative': accumulative
            })
            
            current_date += timedelta(days=1)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        print(f"Enrollment trend error: {str(e)}")  # 添加错误日志
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/dormitory/assign', methods=['POST'])
@admin_required
def assign_dormitories():
    """批量分配宿舍"""
    try:
        data = request.get_json()
        student_ids = data.get('studentIds', [])
        building = data.get('building')
        room = data.get('room')
        
        if not all([student_ids, building, room]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
            
        # 检查宿舍是否可用
        existing = Student.query.filter_by(
            dormitory_building=building,
            dormitory_room=room
        ).count()
        
        if existing >= 4:  # 假设每个宿舍最多4人
            return jsonify({
                'success': False,
                'message': '该宿舍已满'
            }), 400
            
        # 分配宿舍
        for student_id in student_ids:
            student = Student.query.get(student_id)
            if student:
                student.dormitory_building = building
                student.dormitory_room = room
        # 记录操作日志
        log = SystemLog(
            user_id=g.user_id,
            type='assign_dormitories',
            content=f'批量分配宿舍: {building} {room}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '宿舍分配成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/students/template', methods=['GET'])
@admin_required
def get_student_template():
    """获取学生导入模板"""
    try:
        template_path = create_student_template()
        return send_file(
            template_path,
            as_attachment=True,
            download_name='student_import_template.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/students/import', methods=['POST'])
@admin_required
def import_students():
    """导入学生"""
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
            
        result = process_student_excel(file)
        
        # 记录导入日志
        log = SystemLog(
            user_id=g.user_id,
            type='import_students',
            content=f'导入学生: 成功{result["success"]}条，失败{result["failed"]}条',
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