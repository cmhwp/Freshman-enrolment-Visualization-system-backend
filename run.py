from app import create_app, db
from app.models import User, SystemSettings

app = create_app()

def init_db():
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        # 检查是否已存在管理员账号
        admin = User.query.filter_by(role='admin').first()
        if not admin:
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
            settings = SystemSettings(
                site_name='新生入学可视化系统',
                site_description='欢迎使用新生入学可视化系统',
                maintenance_mode=False,
                allow_registration=True
            )
            db.session.add(settings)
            
            try:
                db.session.commit()
                print('Default admin account created successfully.')
                print('Username: admin')
                print('Password: admin123')
            except Exception as e:
                db.session.rollback()
                print(f'Error creating default admin account: {str(e)}')

if __name__ == '__main__':
    init_db()  # 初始化数据库和默认数据
    app.run(debug=True) 