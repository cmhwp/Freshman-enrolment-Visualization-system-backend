from marshmallow import Schema, fields

class StudentSchema(Schema):
    """学生信息序列化模式"""
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    student_id = fields.Str(required=True)
    major = fields.Str()
    admission_year = fields.Int()
    admission_date = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    graduation_date = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    status = fields.Str()
    report_time = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')

    # 关联的用户信息
    user = fields.Nested('UserSchema', only=('id', 'name', 'email', 'gender', 'contact'))

class UserSchema(Schema):
    """用户信息序列化模式"""
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    email = fields.Str(required=True)
    role = fields.Str(required=True)
    name = fields.Str()
    gender = fields.Str()
    contact = fields.Str()
    province = fields.Str()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')

class TeacherSchema(Schema):
    """教师信息序列化模式"""
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    department = fields.Str()
    title = fields.Str()
    research_area = fields.Str()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')

    # 关联的用户信息
    user = fields.Nested('UserSchema', only=('id', 'name', 'email', 'gender', 'contact'))

class ClassSchema(Schema):
    """班级信息序列化模式"""
    id = fields.Int(dump_only=True)
    class_name = fields.Str(required=True)
    major = fields.Str()
    department = fields.Str()
    year = fields.Int()
    capacity = fields.Int()
    assigned_students = fields.Int()
    teacher_id = fields.Int()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')

    # 关联的教师和学生信息
    teacher = fields.Nested('UserSchema', only=('id', 'name'))
    students = fields.Nested('StudentSchema', many=True)

class ScoreSchema(Schema):
    """成绩信息序列化模式"""
    id = fields.Int(dump_only=True)
    student_id = fields.Int(required=True)
    year = fields.Int(required=True)
    total_score = fields.Float(required=True)
    chinese = fields.Float()
    math = fields.Float()
    english = fields.Float()
    physics = fields.Float()
    chemistry = fields.Float()
    biology = fields.Float()
    province_rank = fields.Int()
    major_rank = fields.Int()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')

    # 关联的学生信息
    student = fields.Nested('StudentSchema', only=('id', 'student_id', 'user.name')) 