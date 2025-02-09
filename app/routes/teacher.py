from app.extensions import db
from flask import Blueprint, jsonify, request, g
from app.utils.decorators import teacher_required
from app.models.class_info import ClassInfo
from app.models.system_log import SystemLog

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/classes', methods=['POST'])
@teacher_required
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
            
        # 创建班级，自动设置当前教师为班主任
        class_info = ClassInfo(
            name=data['name'],
            major=data['major'],
            department=data['department'],
            year=data['year'],
            capacity=data['capacity'],
            teacher_id=g.user_id  # 设置当前教师为班主任
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