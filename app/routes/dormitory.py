from flask import Blueprint, jsonify, request, g
from app.extensions import db
from app.utils.decorators import admin_required
from app.models.dormitory import DormitoryBuilding, DormitoryRoom, DormitoryAssignment
from app.models.student import Student
from app.models.user import User
from app.models.system_log import SystemLog
from datetime import datetime

dormitory_bp = Blueprint('dormitory', __name__)

@dormitory_bp.route('/buildings', methods=['GET'])
@admin_required
def get_buildings():
    """获取所有宿舍楼"""
    try:
        buildings = DormitoryBuilding.query.all()
        return jsonify({
            'success': True,
            'data': [building.to_dict() for building in buildings]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@dormitory_bp.route('/buildings', methods=['POST'])
@admin_required
def create_building():
    """创建宿舍楼"""
    try:
        data = request.get_json()
        building = DormitoryBuilding(
            name=data['name'],
            gender=data['gender'],
            description=data.get('description')
        )
        db.session.add(building)
        
        # 记录日志
        log = SystemLog(
            user_id=g.user_id,
            type='create_building',
            content=f'创建宿舍楼: {building.name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': building.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@dormitory_bp.route('/rooms', methods=['POST'])
@admin_required
def create_room():
    """创建宿舍房间"""
    try:
        data = request.get_json()
        building_id = data.get('buildingId')
        room_number = data.get('roomNumber')
        capacity = data.get('capacity', 4)
        description = data.get('description')

        # 验证必要参数
        if not all([building_id, room_number]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400

        # 检查宿舍楼是否存在
        building = DormitoryBuilding.query.get(building_id)
        if not building:
            return jsonify({
                'success': False,
                'message': '宿舍楼不存在'
            }), 404

        # 检查房间号是否已存在
        existing_room = DormitoryRoom.query.filter_by(
            building_id=building_id,
            room_number=room_number
        ).first()
        if existing_room:
            return jsonify({
                'success': False,
                'message': '房间号已存在'
            }), 400

        # 创建房间
        room = DormitoryRoom(
            building_id=building_id,
            room_number=room_number,
            capacity=capacity,
            description=description
        )
        db.session.add(room)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'id': room.id,
                'buildingId': room.building_id,
                'roomNumber': room.room_number,
                'capacity': room.capacity,
                'description': room.description,
                'occupancy': 0
            }
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error creating room: {str(e)}")  # 添加错误日志
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@dormitory_bp.route('/rooms/<int:building_id>', methods=['GET'])
@admin_required
def get_rooms(building_id):
    """获取指定宿舍楼的所有房间"""
    try:
        rooms = DormitoryRoom.query.filter_by(building_id=building_id).all()
        return jsonify({
            'success': True,
            'data': [room.to_dict() for room in rooms]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@dormitory_bp.route('/assign', methods=['POST'])
@admin_required
def assign_room():
    """分配宿舍"""
    try:
        data = request.get_json()
        student_id = data['studentId']
        room_id = data['roomId']
        
        # 检查学生性别和宿舍楼性别是否匹配
        student = Student.query.get_or_404(student_id)
        room = DormitoryRoom.query.get_or_404(room_id)
        
        if student.user.gender != room.building.gender:
            return jsonify({
                'success': False,
                'message': '学生性别与宿舍楼不匹配'
            }), 400
            
        # 检查房间容量
        if len(room.residents) >= room.capacity:
            return jsonify({
                'success': False,
                'message': '该宿舍已满'
            }), 400
            
        # 创建分配记录
        assignment = DormitoryAssignment(
            student_id=student_id,
            room_id=room_id
        )
        db.session.add(assignment)
        
        log = SystemLog(
            user_id=g.user_id,
            type='assign_room',
            content=f'分配宿舍: {student.user.name} -> {room.building.name}-{room.room_number}',
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

@dormitory_bp.route('/unassigned-students', methods=['GET'])
@admin_required
def get_unassigned_students():
    """获取未分配宿舍的学生"""
    try:
        building_id = request.args.get('buildingId', type=int)
        if not building_id:
            return jsonify({
                'success': False,
                'message': '请指定宿舍楼'
            }), 400
            
        # 获取宿舍楼性别
        building = DormitoryBuilding.query.get_or_404(building_id)
        print(f"Building gender: {building.gender}")  # 打印宿舍楼性别
        
        # 获取已分配宿舍的学生ID
        assigned_ids = db.session.query(DormitoryAssignment.student_id)\
            .filter(DormitoryAssignment.status == 'active').all()
        assigned_ids = [id[0] for id in assigned_ids]
        print(f"Assigned student IDs: {assigned_ids}")  # 打印已分配宿舍的学生ID
        
        # 查询所有已报到的学生
        all_reported = db.session.query(Student, User)\
            .join(User)\
            .filter(
                Student.status == 'reported',
                User.gender == building.gender
            ).all()
        print(f"Total reported students with matching gender: {len(all_reported)}")  # 打印符合条件的学生总数
        
        # 查询未分配宿舍且性别匹配的学生
        students = db.session.query(Student, User)\
            .join(User)\
            .filter(
                ~Student.id.in_(assigned_ids) if assigned_ids else True,  # 如果没有已分配的学生，不使用 in_ 条件
                User.gender == building.gender,
                Student.status == 'reported'
            ).all()
        
        print(f"Unassigned students found: {len(students)}")  # 打印未分配宿舍的学生数量
        db.session.commit()
        student_list = [{
            'id': student.id,
            'name': user.name,
            'studentId': student.student_id,
            'major': student.major,
            'gender': user.gender
        } for student, user in students]
        
        return jsonify({
            'success': True,
            'data': student_list
        })
        
    except Exception as e:
        print(f"Error in get_unassigned_students: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@dormitory_bp.route('/room-details', methods=['GET'])
@admin_required
def get_room_details():
    """获取指定宿舍的详细信息"""
    try:
        building_id = request.args.get('buildingId', type=int)
        room_number = request.args.get('roomNumber')
        
        if not all([building_id, room_number]):
            return jsonify({
                'success': False,
                'message': '请指定宿舍楼和房间号'
            }), 400
            
        # 获取房间信息
        room = DormitoryRoom.query.filter_by(
            building_id=building_id,
            room_number=room_number
        ).first_or_404()
            
        # 获取该宿舍的所有学生
        students = db.session.query(Student, User, DormitoryAssignment)\
            .join(User)\
            .join(DormitoryAssignment)\
            .filter(
                DormitoryAssignment.room_id == room.id,
                DormitoryAssignment.status == 'active'
            ).all()
            
        student_list = [{
            'id': student.id,
            'name': user.name,
            'studentId': student.student_id,
            'major': student.major,
            'gender': user.gender,
            'assignmentId': assignment.id
        } for student, user, assignment in students]
        
        return jsonify({
            'success': True,
            'data': {
                'id': room.id,
                'buildingId': room.building_id,
                'roomNumber': room.room_number,
                'building': room.building.name,
                'room': room.room_number,
                'occupancy': len(student_list),
                'capacity': room.capacity,
                'students': student_list
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@dormitory_bp.route('/buildings/<int:building_id>', methods=['PUT'])
@admin_required
def update_building(building_id):
    """修改宿舍楼信息"""
    try:
        building = DormitoryBuilding.query.get_or_404(building_id)
        data = request.get_json()
        
        # 更新信息
        if 'name' in data and data['name'] != building.name:
            # 检查名称是否重复
            if DormitoryBuilding.query.filter_by(name=data['name']).first():
                return jsonify({
                    'success': False,
                    'message': '宿舍楼名称已存在'
                }), 400
            building.name = data['name']
            
        if 'gender' in data:
            building.gender = data['gender']
        if 'description' in data:
            building.description = data['description']
        # 记录日志
        log = SystemLog(
            user_id=g.user_id,
            type='update_building',
            content=f'更新宿舍楼: {building.name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': building.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@dormitory_bp.route('/buildings/<int:building_id>', methods=['DELETE'])
@admin_required
def delete_building(building_id):
    """删除宿舍楼"""
    try:
        building = DormitoryBuilding.query.get_or_404(building_id)
        
        # 检查是否有学生入住
        rooms_with_students = DormitoryRoom.query.join(DormitoryAssignment)\
            .filter(
                DormitoryRoom.building_id == building_id,
                DormitoryAssignment.status == 'active'
            ).first()
            
        if rooms_with_students:
            return jsonify({
                'success': False,
                'message': '该宿舍楼还有学生入住，无法删除'
            }), 400
            
        # 删除所有房间
        DormitoryRoom.query.filter_by(building_id=building_id).delete()
        db.session.delete(building)
        # 记录日志
        log = SystemLog(
            user_id=g.user_id,
            type='delete_building',
            content=f'删除宿舍楼: {building.name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '宿舍楼删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@dormitory_bp.route('/rooms/<int:room_id>', methods=['PUT'])
@admin_required
def update_room(room_id):
    """修改房间信息"""
    try:
        room = DormitoryRoom.query.get_or_404(room_id)
        data = request.get_json()
        
        if 'roomNumber' in data and data['roomNumber'] != room.room_number:
            # 检查房间号是否重复
            if DormitoryRoom.query.filter_by(
                building_id=room.building_id,
                room_number=data['roomNumber']
            ).first():
                return jsonify({
                    'success': False,
                    'message': '房间号已存在'
                }), 400
            room.room_number = data['roomNumber']
            
        if 'capacity' in data:
            # 检查新容量是否小于当前入住人数
            current_occupancy = DormitoryAssignment.query.filter_by(
                room_id=room_id,
                status='active'
            ).count()
            if data['capacity'] < current_occupancy:
                return jsonify({
                    'success': False,
                    'message': '新容量小于当前入住人数'
                }), 400
            room.capacity = data['capacity']
            
        if 'description' in data:
            room.description = data['description']
        # 记录日志
        log = SystemLog(
            user_id=g.user_id,
            type='update_room',
            content=f'更新宿舍房间: {room.building.name}-{room.room_number}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': room.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@dormitory_bp.route('/rooms/<int:room_id>', methods=['DELETE'])
@admin_required
def delete_room(room_id):
    """删除房间"""
    try:
        room = DormitoryRoom.query.get_or_404(room_id)
        
        # 检查是否有学生入住
        if DormitoryAssignment.query.filter_by(
            room_id=room_id,
            status='active'
        ).first():
            return jsonify({
                'success': False,
                'message': '该房间还有学生入住，无法删除'
            }), 400
            
        db.session.delete(room)
        # 记录日志
        log = SystemLog(
            user_id=g.user_id,
            type='delete_room',
            content=f'删除宿舍房间: {room.building.name}-{room.room_number}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '房间删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@dormitory_bp.route('/assignments/<int:assignment_id>/checkout', methods=['POST'])
@admin_required
def checkout(assignment_id):
    """学生退宿"""
    try:
        assignment = DormitoryAssignment.query.get_or_404(assignment_id)
        
        if assignment.status != 'active':
            return jsonify({
                'success': False,
                'message': '该学生已退宿'
            }), 400
            
        assignment.status = 'inactive'
        assignment.check_out_date = datetime.now()
        
        # 记录日志
        log = SystemLog(
            user_id=g.user_id,
            type='checkout',
            content=f'学生退宿: {assignment.student.user.name} 从 {assignment.room.building.name}-{assignment.room.room_number}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '退宿成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@dormitory_bp.route('/assignments/<int:assignment_id>/change', methods=['POST'])
@admin_required
def change_room(assignment_id):
    """调整学生宿舍"""
    try:
        data = request.get_json()
        new_room_id = data.get('newRoomId')
        
        if not new_room_id:
            return jsonify({
                'success': False,
                'message': '请指定新宿舍'
            }), 400
            
        assignment = DormitoryAssignment.query.get_or_404(assignment_id)
        new_room = DormitoryRoom.query.get_or_404(new_room_id)
        
        # 检查新宿舍是否已满
        if len(new_room.residents) >= new_room.capacity:
            return jsonify({
                'success': False,
                'message': '新宿舍已满'
            }), 400
            
        # 检查性别是否匹配
        if assignment.student.user.gender != new_room.building.gender:
            return jsonify({
                'success': False,
                'message': '学生性别与新宿舍楼不匹配'
            }), 400
            
        # 创建新的分配记录
        new_assignment = DormitoryAssignment(
            student_id=assignment.student_id,
            room_id=new_room_id
        )
        
        # 更新原记录状态
        assignment.status = 'inactive'
        assignment.check_out_date = datetime.now()
        
        db.session.add(new_assignment)
        
        # 记录日志
        log = SystemLog(
            user_id=g.user_id,
            type='change_room',
            content=f'调整宿舍: {assignment.student.user.name} 从 {assignment.room.building.name}-{assignment.room.room_number} 到 {new_room.building.name}-{new_room.room_number}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '宿舍调整成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500 