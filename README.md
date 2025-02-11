# 新生入学可视化系统

一个基于 Flask 的新生入学管理系统，提供新生报到、班级管理、成绩管理等功能。

## 功能特点

- 多角色权限管理（管理员、教师、学生）
- 新生报到管理
- 班级管理
- 学生成绩管理
- 宿舍分配
- 待办事项管理
- 数据可视化分析
- Excel导入导出

## 技术栈

- Backend: Flask + SQLAlchemy + JWT
- Database: MySQL
- Cache: Redis
- Task Queue: APScheduler

## 安装部署

1. 克隆项目
```bash
git clone https://github.com/yourusername/student-enrollment-system.git
cd student-enrollment-system
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库等信息
```

5. 初始化数据库
```bash
flask db upgrade
python run.py
```

6. 运行服务
```bash
flask run
```

## 默认账号

- 管理员：admin/admin123
- 教师：teacher1/123456
- 学生：自行注册

## API 文档

主要API路由：

- 认证相关: `/api/auth/*`
- 学生相关: `/api/student/*`
- 教师相关: `/api/teacher/*`
- 管理员相关: `/api/admin/*`
- 用户相关: `/api/user/*`
- 统计相关: `/api/stats/*`
- 宿舍相关: `/api/dormitory/*`
- 待办相关: `/api/todo/*`

## 开发团队

- 后端开发: [我不是干脆面]
- 前端开发: [Front-end Developer]

## License

MIT 