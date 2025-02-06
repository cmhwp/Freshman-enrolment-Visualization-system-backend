import pandas as pd
import numpy as np
from app.models.student import Student
from app.models.score import Score
from app.models.class_info import ClassInfo
from sqlalchemy import func, case, and_
from app import db

class ScoreAnalysis:
    @staticmethod
    def calculate_statistics(scores):
        df = pd.DataFrame(scores)
        stats = {
            'mean': df['total_score'].mean(),
            'median': df['total_score'].median(),
            'std': df['total_score'].std(),
            'max': df['total_score'].max(),
            'min': df['total_score'].min()
        }
        return stats
    
    @staticmethod
    def score_distribution(scores, bins=10):
        df = pd.DataFrame(scores)
        hist, bins = np.histogram(df['total_score'], bins=bins)
        return {
            'counts': hist.tolist(),
            'bins': bins.tolist()
        }
    
    @staticmethod
    def subject_analysis(scores):
        df = pd.DataFrame(scores)
        subjects = ['chinese', 'math', 'english', 'physics', 'chemistry', 'biology']
        analysis = {}
        for subject in subjects:
            analysis[subject] = {
                'mean': df[subject].mean(),
                'excellent_rate': (df[subject] >= 90).mean()
            }
        return analysis 

def calculate_total_score(scores):
    """计算总分"""
    return sum([
        scores.chinese,
        scores.math,
        scores.english,
        scores.physics,
        scores.chemistry,
        scores.biology
    ])

def get_major_rankings(student_id):
    """获取专业排名相关数据"""
    student = Student.query.get(student_id)
    if not student:
        raise ValueError("Student not found")
        
    class_id = student.class_id
    
    # 获取该专业所有学生的成绩
    major_scores = db.session.query(
        Student, 
        Score.total_score.label('total')
    ).join(Score).filter(Student.class_id == class_id).all()
    
    if not major_scores:
        raise ValueError("No scores found for this major")
    
    # 计算排名、平均分、最高分等
    scores_list = [score.total for score in major_scores]
    student_score = next((score.total for score in major_scores 
                         if score.Student.id == student_id), None)
    
    if student_score is None:
        raise ValueError("Student score not found")
    
    return {
        'major_name': student.class_info.major,
        'rank': sorted(scores_list, reverse=True).index(student_score) + 1,
        'total': len(scores_list),
        'average': round(sum(scores_list) / len(scores_list), 2),
        'highest': max(scores_list)
    }

def get_score_distribution(student_id):
    """获取分数分布数据"""
    student = Student.query.get(student_id)
    if not student:
        raise ValueError("Student not found")
        
    class_id = student.class_id
    
    # 定义分数段
    ranges = ['<500', '500-550', '550-600', '600-650', '650-700', '>700']
    
    # 使用 case 语句统计各分数段的学生数量
    count_cases = [
        case(
            (and_(Score.total_score < 500), 1),
            (and_(Score.total_score >= 500, Score.total_score < 550), 1),
            (and_(Score.total_score >= 550, Score.total_score < 600), 1),
            (and_(Score.total_score >= 600, Score.total_score < 650), 1),
            (and_(Score.total_score >= 650, Score.total_score < 700), 1),
            (and_(Score.total_score >= 700), 1),
        )
    ]
    
    # 查询各分数段的学生数量
    distribution = db.session.query(
        func.sum(case(
            [(Score.total_score < 500, 1)], 
            else_=0
        )).label('<500'),
        func.sum(case(
            [(and_(Score.total_score >= 500, Score.total_score < 550), 1)], 
            else_=0
        )).label('500-550'),
        func.sum(case(
            [(and_(Score.total_score >= 550, Score.total_score < 600), 1)], 
            else_=0
        )).label('550-600'),
        func.sum(case(
            [(and_(Score.total_score >= 600, Score.total_score < 650), 1)], 
            else_=0
        )).label('600-650'),
        func.sum(case(
            [(and_(Score.total_score >= 650, Score.total_score < 700), 1)], 
            else_=0
        )).label('650-700'),
        func.sum(case(
            [(Score.total_score >= 700, 1)], 
            else_=0
        )).label('>700')
    ).join(Student).filter(Student.class_id == class_id).first()
    
    # 转换查询结果为列表
    counts = [getattr(distribution, range_label.replace('-', '_')) or 0 
             for range_label in ranges]
    
    return {
        'ranges': ranges,
        'counts': counts
    }

def get_gender_admission_ratio():
    """获取录取性别比例"""
    total_students = Student.query.count()
    male_count = Student.query.filter_by(gender='M').count()
    female_count = Student.query.filter_by(gender='F').count()
    
    return {
        'male': male_count / total_students,
        'female': female_count / total_students
    }

def get_school_ranking(student_id):
    """获取学校排名数据"""
    student = Student.query.get(student_id)
    if not student:
        raise ValueError("Student not found")
    
    # 获取所有学生的总分并排序
    all_scores = db.session.query(
        Student,
        Score.total_score.label('total')
    ).join(Score).all()
    
    if not all_scores:
        raise ValueError("No scores found")
    
    scores_list = [score.total for score in all_scores]
    student_score = next((score.total for score in all_scores 
                         if score.Student.id == student_id), None)
    
    if student_score is None:
        raise ValueError("Student score not found")
    
    rank = sorted(scores_list, reverse=True).index(student_score) + 1
    
    return {
        'rank': rank,
        'total': len(scores_list),
        'percentile': round((len(scores_list) - rank) / len(scores_list) * 100, 2)
    } 