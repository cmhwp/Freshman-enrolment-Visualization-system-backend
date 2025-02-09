from app.extensions import db
from .user import User
from .student import Student
from .class_info import ClassInfo
from .system_log import SystemLog
from .settings import Settings
from .score import Score
from .teacher import Teacher
from .dormitory import DormitoryBuilding, DormitoryRoom, DormitoryAssignment

__all__ = ['User', 'Student', 'ClassInfo', 'SystemLog', 'Settings', 'Score', 'Teacher', 'DormitoryBuilding', 'DormitoryRoom', 'DormitoryAssignment'] 