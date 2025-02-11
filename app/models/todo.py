from app.extensions import db
from datetime import datetime

class Todo(db.Model):
    __tablename__ = 'todos'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text) # 任务内容
    status = db.Column(db.String(20), default='pending')  # pending, completed, rejected
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    comment = db.Column(db.Text)  # 教师反馈

    student = db.relationship('Student', backref='todos')
    teacher = db.relationship('Teacher', backref='todos')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'status': self.status,
            'student_id': self.student_id,
            'teacher_id': self.teacher_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'comment': self.comment,
            'student': self.student.user.name if self.student else None,
            'teacher': self.teacher.user.name if self.teacher else None
        } 