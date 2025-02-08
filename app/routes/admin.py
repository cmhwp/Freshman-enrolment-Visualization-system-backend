from flask import Blueprint, jsonify, request, g
from app.utils.decorators import admin_required
from app.models.user import User
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.system_log import SystemLog
from app.models.settings import SystemSettings
from app.models.class_info import ClassInfo
from app import db

admin_bp = Blueprint('admin', __name__)

# 学生管理
@admin_bp.route('/students', methods=['GET'])
@admin_required
def get_student_list():
    """获取学生列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 10, type=int)
        search = request.args.get('search', '')
        major = request.args.get('major', '')
        province = request.args.get('province', '')
        
        query = User.query.filter_by(role='student')
        
        if search:
            query = query.filter(
                (User.name.like(f'%{search}%')) |
                (User.username.like(f'%{search}%'))
            )
        
        if major:
            query = query.join(Student).filter(Student.major == major)
            
        if province:
            query = query.filter(User.province == province)
            
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

@admin_bp.route('/students/<int:id>', methods=['PUT'])
@admin_required
def update_student(id):
    """更新学生信息"""
    try:
        student = User.query.filter_by(id=id, role='student').first()
        if not student:
            return jsonify({
                'success': False,
                'message': '学生不存在'
            }), 404
            
        data = request.get_json()
        for key, value in data.items():
            if hasattr(student, key):
                setattr(student, key, value)
                
        db.session.commit()
        
        # 添加操作日志
        log = SystemLog(
            user_id=g.user_id,
            type='update_student',
            content=f'更新学生信息: {student.username}',
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

# 在现有代码后添加教师管理相关路由

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
        teacher = User.query.filter_by(id=id, role='teacher').first()
        if not teacher:
            return jsonify({
                'success': False,
                'message': '教师不存在'
            }), 404
            
        data = request.get_json()
        for key, value in data.items():
            if hasattr(teacher, key):
                setattr(teacher, key, value)
                
        db.session.commit()
        
        # 添加操作日志
        log = SystemLog(
            user_id=g.user_id,
            type='update_teacher',
            content=f'更新教师信息: {teacher.username}',
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
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/teachers/<int:id>', methods=['DELETE'])
@admin_required
def delete_teacher(id):
    """删除教师"""
    try:
        teacher = User.query.filter_by(id=id, role='teacher').first()
        if not teacher:
            return jsonify({
                'success': False,
                'message': '教师不存在'
            }), 404
            
        username = teacher.username  # 保存用户名用于日志记录
        db.session.delete(teacher)
        db.session.commit()
        
        # 添加操作日志
        log = SystemLog(
            user_id=g.user_id,
            type='delete_teacher',
            content=f'删除教师用户: {username}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
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
        settings = SystemSettings.query.first()
        if not settings:
            settings = SystemSettings()  # 创建默认设置
            db.session.add(settings)
            db.session.commit()
            
        return jsonify({
            'success': True,
            'data': settings.to_dict()
        })
        
    except Exception as e:
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
        settings = SystemSettings.query.first()
        
        if not settings:
            settings = SystemSettings()
            db.session.add(settings)
            
        # 记录修改的字段
        changed_fields = []
        for key, value in data.items():
            if hasattr(settings, key):
                old_value = getattr(settings, key)
                if old_value != value:
                    setattr(settings, key, value)
                    changed_fields.append(f"{key}: {old_value} -> {value}")
                
        db.session.commit()
        
        # 添加操作日志
        if changed_fields:
            log = SystemLog(
                user_id=g.user_id,
                type='update_settings',
                content=f'更新系统设置: {", ".join(changed_fields)}',
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