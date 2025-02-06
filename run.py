from app import create_app, db
from app.models.user import User
from app.models.score import Score
from app.models.operation_log import OperationLog
from app.models.class_info import ClassInfo
from app.models.student import Student

app = create_app()

# 创建所有数据库表
def init_db():
    with app.app_context():
        # 删除所有表（如果存在）
        db.drop_all()
        # 创建所有表
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    init_db()  # 初始化数据库
    app.run(debug=True) 