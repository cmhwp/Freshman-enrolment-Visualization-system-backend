from app import create_app, db
from app.models import User, Student, Score, ClassInfo, OperationLog

app = create_app()

# 创建所有数据库表
def init_db():
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        # 创建默认的班级信息
        default_class = ClassInfo(
            name="默认班级",
            year=2024,  # 使用 year 而不是 grade
            major="计算机科学与技术"
        )
        db.session.add(default_class)
        db.session.commit()
        print("Database tables created successfully!")

if __name__ == '__main__':
    init_db()  # 初始化数据库
    app.run(debug=True) 