from .auth import auth_bp
from .student import student_bp
from .teacher import teacher_bp
from .admin import admin_bp
from .user import user_bp

__all__ = ['auth_bp', 'student_bp', 'teacher_bp', 'admin_bp', 'user_bp']

# 创建其他空的蓝图文件 