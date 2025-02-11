from app import create_app
from app.models import User, Settings, Student, ClassInfo, SystemLog, DormitoryBuilding, DormitoryRoom, DormitoryAssignment, Score, Teacher
from app import db
from datetime import datetime, timedelta
import random
from werkzeug.security import generate_password_hash

app = create_app()

def init_db():
    with app.app_context():
        db.create_all()  # 重新创建表
        
        # 检查是否已存在管理员账号
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            try:
                # 创建默认管理员账号
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    name='系统管理员',
                    role='admin',
                    is_active=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                
                # 创建默认系统设置
                settings = Settings(
                    system_name='新生入学可视化系统',
                    version='1.0.0',
                    allow_register=True,
                    require_email_verification=True,
                    majors=[
                        '计算机科学与技术',
                        '软件工程',
                        '人工智能',
                        '数据科学',
                        '网络工程'
                    ],
                    departments=[
                        '计算机学院',
                        '信息工程学院',
                        '电子工程学院',
                        '自动化学院'
                    ]
                )
                db.session.add(settings)
                
                # 创建默认宿舍楼
                building_m = DormitoryBuilding(name='A栋', gender='M', description='男生宿舍')
                building_f = DormitoryBuilding(name='B栋', gender='F', description='女生宿舍')
                db.session.add(building_m)
                db.session.add(building_f)
                db.session.flush()  # 获取building的id
                
                # 为每栋楼创建房间
                for building in [building_m, building_f]:
                    for floor in range(1, 7):  # 6层
                        for room in range(1, 11):  # 每层10间
                            room_number = f'{floor}0{room}' if room < 10 else f'{floor}{room}'
                            dorm_room = DormitoryRoom(
                                room_number=room_number,
                                building_id=building.id,
                                capacity=4
                            )
                            db.session.add(dorm_room)
                
                # 创建测试学生数据
                provinces = ['北京市', '上海市', '广东省', '江苏省', '浙江省', '四川省', '湖北省', '山西省']
                statuses = ['pending', 'reported', 'unreported']
                current_year = datetime.now().year

                for i in range(100):  # 创建100个测试学生
                    gender = random.choice(['M', 'F'])
                    user = User(
                        username=f'student{i+1}',
                        email=f'student{i+1}@example.com',
                        name=f'学生{i+1}',
                        role='student',
                        gender=gender,
                        province=random.choice(provinces),
                        contact=f'138{random.randint(10000000, 99999999)}',
                        is_active=True,
                        password_hash=generate_password_hash('123456')
                    )
                    db.session.add(user)
                    db.session.flush()  # 获取user.id

                    status = random.choice(statuses)
                    report_time = None
                    if status == 'reported':
                        days_ago = random.randint(0, 30)
                        report_time = datetime.now() - timedelta(days=days_ago)

                    student = Student(
                        user_id=user.id,
                        student_id=f'2024{str(i+1).zfill(4)}',
                        major=random.choice(settings.majors),
                        admission_year=current_year,
                        status=status,
                        report_time=report_time
                    )
                    db.session.add(student)
                    
                    # 如果学生已报到，分配宿舍
                    if status == 'reported':
                        # 获取对应性别的宿舍楼
                        building = building_m if gender == 'M' else building_f
                        # 随机选择一个房间
                        rooms = DormitoryRoom.query.filter_by(building_id=building.id).all()
                        room = random.choice(rooms)
                        
                        # 创建宿舍分配记录
                        assignment = DormitoryAssignment(
                            student_id=student.id,
                            room_id=room.id,
                            check_in_date=report_time
                        )
                        db.session.add(assignment)

                    # 添加报到日志
                    if status == 'reported':
                        log = SystemLog(
                            user_id=user.id,
                            type='student_report',
                            content=f'学生 {user.name} 完成报到',
                            ip_address='127.0.0.1',
                            created_at=report_time
                        )
                        db.session.add(log)

                db.session.commit()
                print('初始化数据成功！')
                print('管理员账号: admin')
                print('密码: admin123')
                
            except Exception as e:
                db.session.rollback()
                print(f'Error creating initial data: {str(e)}')

def create_score_data():
    """创建成绩测试数据"""
    with app.app_context():
        try:
            # 为现有的学生添加成绩数据
            students = Student.query.all()
            for student in students:
                # 检查是否已有成绩
                existing_score = Score.query.filter_by(student_id=student.id).first()
                if existing_score:
                    continue
                    
                # 创建随机成绩
                score = Score(
                    student_id=student.id,
                    year=2024,
                    total_score=0,  # 稍后计算
                    chinese=random.randint(90, 150),
                    math=random.randint(90, 150),
                    english=random.randint(90, 150),
                    physics=random.randint(60, 100),
                    chemistry=random.randint(60, 100),
                    biology=random.randint(60, 100),
                    created_at=datetime.now()
                )
                
                # 计算总分
                score.total_score = (
                    score.chinese + 
                    score.math + 
                    score.english + 
                    score.physics + 
                    score.chemistry + 
                    score.biology
                )
                
                db.session.add(score)
            
            db.session.commit()
            
            # 计算并更新排名
            update_rankings()
            
            print("成绩测试数据创建完成!")
            
        except Exception as e:
            db.session.rollback()
            print(f'Error creating score data: {str(e)}')

def update_rankings():
    """更新所有学生的排名"""
    try:
        # 更新省排名
        scores = Score.query.order_by(Score.total_score.desc()).all()
        for rank, score in enumerate(scores, 1):
            score.province_rank = rank
        
        # 更新专业排名
        students = Student.query.all()
        majors = set(student.major for student in students)
        
        for major in majors:
            major_scores = Score.query.join(Student).filter(
                Student.major == major
            ).order_by(Score.total_score.desc()).all()
            
            for rank, score in enumerate(major_scores, 1):
                score.major_rank = rank
        
        db.session.commit()
        print("排名更新完成!")
        
    except Exception as e:
        db.session.rollback()
        print(f'Error updating rankings: {str(e)}')

def create_class_data():
    """创建班级测试数据"""
    with app.app_context():
        try:
            # 创建一些教师账号
            teachers_data = [
                {
                    'username': 'teacher1',
                    'email': 'teacher1@example.com',
                    'name': '张老师',
                    'department': '计算机学院'
                },
                {
                    'username': 'teacher2',
                    'email': 'teacher2@example.com',
                    'name': '李老师',
                    'department': '软件学院'
                },
                {
                    'username': 'teacher3',
                    'email': 'teacher3@example.com',
                    'name': '王老师',
                    'department': '人工智能学院'
                }
            ]
            
            teacher_ids = []
            for teacher_data in teachers_data:
                existing_teacher = User.query.filter_by(username=teacher_data['username']).first()
                if not existing_teacher:
                    # 创建 User 记录
                    teacher_user = User(
                        username=teacher_data['username'],
                        email=teacher_data['email'],
                        role='teacher',
                        name=teacher_data['name'],
                        gender='M',
                        contact=f'138{random.randint(10000000, 99999999)}'
                    )
                    teacher_user.set_password('123456')
                    db.session.add(teacher_user)
                    db.session.flush()  # 获取 user.id
                    
                    # 创建 Teacher 记录
                    teacher = Teacher(
                        user_id=teacher_user.id,
                        title='教授',  # 职称
                        research_area='计算机科学'  # 研究方向
                    )
                    db.session.add(teacher)
                    db.session.flush()
                    teacher_ids.append(teacher_user.id)
                else:
                    # 检查是否已有 Teacher 记录
                    teacher = Teacher.query.filter_by(user_id=existing_teacher.id).first()
                    if not teacher:
                        teacher = Teacher(
                            user_id=existing_teacher.id,
                            title='教授',
                            research_area='计算机科学'
                        )
                        db.session.add(teacher)
                    teacher_ids.append(existing_teacher.id)

            # 创建班级
            classes_data = [
                {
                    'class_name': '2024计算机1班',
                    'major': '计算机科学与技术',
                    'department': '计算机学院',
                    'teacher_id': teacher_ids[0]
                },
                {
                    'class_name': '2024软件1班',
                    'major': '软件工程',
                    'department': '软件学院',
                    'teacher_id': teacher_ids[1]
                },
                {
                    'class_name': '2024人工智能1班',
                    'major': '人工智能',
                    'department': '人工智能学院',
                    'teacher_id': teacher_ids[2]
                }
            ]

            for class_data in classes_data:
                existing_class = ClassInfo.query.filter_by(class_name=class_data['class_name']).first()
                if not existing_class:
                    class_info = ClassInfo(
                        class_name=class_data['class_name'],
                        major=class_data['major'],
                        department=class_data['department'],
                        year=2024,
                        capacity=40,
                        teacher_id=class_data['teacher_id']
                    )
                    db.session.add(class_info)
            
            db.session.commit()
            
            # 将现有学生随机分配到班级
            classes = ClassInfo.query.all()
            students = Student.query.filter_by(class_id=None).all()
            
            for student in students:
                random_class = random.choice(classes)
                student.class_id = random_class.id
                student.major = random_class.major  # 更新学生专业以匹配班级
                random_class.assigned_students += 1  # 更新已分配学生数量
            
            db.session.commit()
            print("班级测试数据创建完成!")
            
        except Exception as e:
            db.session.rollback()
            print(f'Error creating class data: {str(e)}')

if __name__ == '__main__':
    # #检查是否已存在管理员账号
    with app.app_context():
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            init_db()  # 初始化数据库和默认数据
            create_class_data()  # 创建班级测试数据
            create_score_data()  # 创建成绩测试数据
    # init_db()  # 初始化数据库和默认数据
    # create_class_data()  # 创建班级测试数据
    # create_score_data()  # 创建成绩测试数据
    app.run(debug=True) 