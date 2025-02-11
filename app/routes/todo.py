from flask import Blueprint, jsonify, request, g
from app.models.todo import Todo
from app.extensions import db
from app.utils.decorators import login_required, teacher_required, student_required
from datetime import datetime
from app.models import Student, ClassInfo, Teacher
from app.models.user import User
from flask_jwt_extended import get_jwt_identity

todo_bp = Blueprint('todo', __name__)

@todo_bp.route('/todos', methods=['GET'])
@login_required
def get_todos():
    """获取待办事项列表"""
    current_user = get_jwt_identity()
    user = User.query.get(current_user['user_id'])
    try:
        if user.role == 'teacher':
            # 确保教师存在
            teacher = Teacher.query.filter_by(user_id=user.id).first()
            if not teacher:
                return jsonify({
                    'success': False,
                    'message': '教师信息不存在'
                }), 404

            # 教师获取其负责班级学生的所有待办，并包含学生和班级信息
            todos = Todo.query\
                .join(Student, Todo.student_id == Student.id)\
                .join(ClassInfo, Student.class_id == ClassInfo.id)\
                .filter(Todo.teacher_id == teacher.id)\
                .add_columns(ClassInfo.class_name)\
                .order_by(Todo.created_at.desc())\
                .all()
                
            # 构造返回数据
            todo_list = []
            for todo, class_name in todos:
                todo_dict = todo.to_dict()
                todo_dict['class_name'] = class_name
                todo_list.append(todo_dict)
                
            return jsonify({
                'success': True,
                'data': todo_list
            })
            
        elif user.role == 'student':
            # 确保学生存在
            student = Student.query.filter_by(user_id=user.id).first()
            if not student:
                return jsonify({
                    'success': False,
                    'message': '学生信息不存在'
                }), 404

            # 学生只能获取自己的待办
            todos = Todo.query.filter_by(student_id=student.id)\
                .order_by(Todo.created_at.desc())\
                .all()
                
            return jsonify({
                'success': True,
                'data': [todo.to_dict() for todo in todos]
            })
        else:
            return jsonify({
                'success': False,
                'message': '无权限访问'
            }), 403
            
    except Exception as e:
        print(f"Error in get_todos: {str(e)}")  # 添加错误日志
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@todo_bp.route('/todos', methods=['POST'])
@student_required
def create_todo():
    """创建待办事项"""
    current_user = get_jwt_identity()
    user = User.query.get(current_user['user_id'])
    try:
        data = request.get_json()
        if not data or not data.get('title') or not data.get('content'):
            return jsonify({
                'success': False,
                'message': '请提供完整信息'
            }), 400

        # 获取学生和班级信息
        student = Student.query.filter_by(user_id=user.id).first()
        if not student:
            return jsonify({
                'success': False,
                'message': '学生信息不存在'
            }), 404
            
        # 获取班级和教师信息
        class_info = ClassInfo.query.get(student.class_id)
        if not class_info:
            return jsonify({
                'success': False,
                'message': '未找到班级信息'
            }), 404
            
        # 获取教师信息
        teacher = Teacher.query.filter_by(user_id=class_info.teacher_id).first()
        if not teacher:
            return jsonify({
                'success': False,
                'message': '未找到班级教师'
            }), 404

        todo = Todo(
            title=data['title'],
            content=data['content'],
            status='pending',
            student_id=student.id,
            teacher_id=teacher.id
        )
        
        db.session.add(todo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': todo.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@todo_bp.route('/todos/<int:todo_id>', methods=['PUT'])
@login_required
def update_todo(todo_id):
    """更新待办事项"""
    current_user = get_jwt_identity()
    user = User.query.get(current_user['user_id'])
    try:
        todo = Todo.query.get_or_404(todo_id)
        data = request.get_json()
        
        # 验证权限
        if user.role == 'student':
            student = Student.query.filter_by(user_id=user.id).first()
            if not student or todo.student_id != student.id:
                return jsonify({
                    'success': False,
                    'message': '无权操作此待办事项'
                }), 403
            
        elif user.role == 'teacher':
            teacher = Teacher.query.filter_by(user_id=user.id).first()
            if not teacher or todo.teacher_id != teacher.id:
                return jsonify({
                    'success': False,
                    'message': '无权操作此待办事项'
                }), 403
        
        # 更新字段
        if user.role == 'teacher':
            # 教师可以更新状态和评论
            todo.status = data.get('status', todo.status)
            todo.comment = data.get('comment', todo.comment)
        else:
            # 学生可以更新标题、内容
            if todo.status == 'pending':  # 只能在待处理状态下修改
                todo.title = data.get('title', todo.title)
                todo.content = data.get('content', todo.content)
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': todo.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@todo_bp.route('/todos/<int:todo_id>', methods=['DELETE'])
@login_required
def delete_todo(todo_id):
    """删除待办事项"""
    current_user = get_jwt_identity()
    user = User.query.get(current_user['user_id'])
    try:
        todo = Todo.query.get_or_404(todo_id)
        
        # 验证权限
        if user.role == 'student':
            student = Student.query.filter_by(user_id=user.id).first()
            if not student or todo.student_id != student.id:
                return jsonify({
                    'success': False,
                    'message': '无权删除此待办事项'
                }), 403
            
        elif user.role == 'teacher':
            teacher = Teacher.query.filter_by(user_id=user.id).first()
            if not teacher or todo.teacher_id != teacher.id:
                return jsonify({
                    'success': False,
                    'message': '无权删除此待办事项'
                }), 403
        
        db.session.delete(todo)
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