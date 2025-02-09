from app import create_app
from app.models import User, Settings, Student, ClassInfo, SystemLog, DormitoryBuilding, DormitoryRoom, DormitoryAssignment
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
                provinces = ['beijing', 'shanghai', 'guangdong', 'jiangsu', 'zhejiang', 'sichuan', 'hubei', 'shanxi']
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

if __name__ == '__main__':
    init_db()  # 初始化数据库和默认数据
    app.run(debug=True) 