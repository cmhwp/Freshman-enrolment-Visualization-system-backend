import pandas as pd
import numpy as np
from app.models.student import Student
from app.models.score import Score
from app.models.class_info import ClassInfo
from sqlalchemy import func, case, and_
from app import db
from typing import List, Dict, Any
from openai import OpenAI
import os
from dotenv import load_dotenv
import time
from functools import wraps
import random

load_dotenv()  # 加载环境变量

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

def get_score_distribution(scores: List[Score]) -> Dict[str, int]:
    """计算成绩分布"""
    ranges = ['<300', '300-360', '360-420', '420-480', '480-540', '≥540']
    distribution = {range_: 0 for range_ in ranges}
    
    for score in scores:
        total = score.total_score  # 修改为正确的属性名
        if total < 300:
            distribution['<300'] += 1
        elif total < 360:
            distribution['300-360'] += 1
        elif total < 420:
            distribution['360-420'] += 1
        elif total < 480:
            distribution['420-480'] += 1
        elif total < 540:
            distribution['480-540'] += 1
        else:
            distribution['≥540'] += 1
            
    return distribution

def calculate_subject_scores(scores: List[Score]) -> Dict[str, Dict[str, float]]:
    """计算各科目成绩统计"""
    subjects = ['chinese', 'math', 'english', 'physics', 'chemistry', 'biology']
    subject_names = {
        'chinese': '语文',
        'math': '数学',
        'english': '英语',
        'physics': '物理',
        'chemistry': '化学',
        'biology': '生物'
    }
    
    result = {}
    for subject in subjects:
        scores_list = [getattr(score, subject) for score in scores if getattr(score, subject) is not None]
        if scores_list:
            avg = float(np.mean(scores_list))  # 确保转换为Python float
            std = float(np.std(scores_list))
            max_score = float(max(scores_list))
            min_score = float(min(scores_list))
            
            # 计算得分率
            full_score = 150 if subject in ['chinese', 'math', 'english'] else 100
            score_rate = (avg / full_score) * 100
            
            result[subject_names[subject]] = {
                'average': round(avg, 1),
                'standardDeviation': round(std, 1),
                'max': round(max_score, 1),
                'min': round(min_score, 1),
                'scoreRate': round(score_rate, 1)
            }
    
    return result

def calculate_score_trends(class_id: int) -> List[Dict[str, Any]]:
    """计算成绩趋势"""
    # 获取最近6次考试的平均分趋势
    trends = db.session.query(
        Score.year,
        func.avg(Score.totalScore).label('average'),
        func.count(Score.id).label('count')
    ).join(Student)\
    .filter(Student.class_id == class_id)\
    .group_by(Score.year)\
    .order_by(Score.year.desc())\
    .limit(6)\
    .all()
    
    return [{
        'year': trend.year,
        'average': round(float(trend.average), 1),
        'count': trend.count
    } for trend in trends]

def retry_with_backoff(retries=3, backoff_in_seconds=1):
    """重试装饰器，带有指数退避"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        raise e
                    else:
                        x += 1
                        # 计算延迟时间：基础时间 * (1.5 ~ 2.5) * 重试次数
                        sleep_time = (backoff_in_seconds * (1.5 + random.random())) * x
                        print(f"Retrying in {sleep_time:.2f} seconds...")
                        time.sleep(sleep_time)
        return wrapper
    return decorator

@retry_with_backoff(retries=3, backoff_in_seconds=2)  # 增加重试间隔
def call_ai_api(client, messages, temperature=0.3):
    """调用 AI API 的函数，带有重试机制"""
    try:
        return client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=messages,
            temperature=temperature,
            timeout=60  # 增加到60秒
        )
    except Exception as e:
        print(f"API Call Error: {str(e)}")
        raise e

def generate_ai_analysis(
    scores: List[Score],
    distribution: Dict[str, int],
    subject_scores: Dict[str, Dict[str, float]],
    class_info: Any
) -> str:
    """生成AI分析报告"""
    try:
        # 准备分析数据
        analysis_data = {
            "班级信息": {
                "班级名称": class_info.class_name,
                "专业": class_info.major,
                "年级": class_info.year
            },
            "成绩分布": distribution,
            "各科成绩": subject_scores,
            "总人数": len(scores)
        }
        
        # 从环境变量获取API密钥
        api_key = os.getenv('MOONSHOT_API_KEY')
        if not api_key:
            raise ValueError("Missing MOONSHOT_API_KEY in environment variables")
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1",
        )
        
        prompt = f'''
        请根据以下高考成绩数据生成一份详细的分析报告。

        班级信息：
        - 班级：{analysis_data["班级信息"]["班级名称"]}
        - 专业：{analysis_data["班级信息"]["专业"]}
        - 年级：{analysis_data["班级信息"]["年级"]}
        - 总人数：{analysis_data["总人数"]}人

        成绩分布：
        {analysis_data["成绩分布"]}

        各科目成绩情况：
        {analysis_data["各科成绩"]}

        请使用Markdown格式生成一份完整的分析报告，包含以下几个部分：

        # 整体表现分析

        分析班级的整体成绩情况...

        # 各科目表现分析

        分析各科目的具体表现，包括优势科目和薄弱科目...

        # 成绩分布特点

        分析成绩的分布情况...

        # 存在的问题和短板

        指出存在的主要问题...

        # 针对性的改进建议

        提供具体的改进建议...

        注意：
        1. 使用Markdown语法来组织内容
        2. 可以使用表格、列表、加粗等Markdown格式
        3. 建议要具体且可操作
        '''
        
        messages = [
            {"role": "system", "content": "你是一个专业的教育分析师，擅长分析学生成绩数据并提供教学建议。请使用Markdown格式输出分析报告。"},
            {"role": "user", "content": prompt}
        ]

        # 使用重试机制调用 API
        completion = call_ai_api(client, messages)
        
        # 直接返回Markdown文本
        return completion.choices[0].message.content

    except Exception as e:
        print(f"AI Analysis Error: {str(e)}")
        # 如果AI分析失败，返回基础分析的Markdown文本
        return f'''
# 基础分析报告

由于技术原因({str(e)})，暂时无法生成AI分析报告。以下是基础统计分析：

## 班级基本信息
- 班级：{class_info.class_name}
- 总人数：{len(scores)}人

## 成绩分布
{distribution}
```

## 各科目成绩情况
{subject_scores}
```

## 成绩趋势
{calculate_score_trends(class_info.class_id)}
```

## 基础分析

分析班级的整体成绩情况...

## 各科目表现分析

分析各科目的具体表现，包括优势科目和薄弱科目...

## 成绩分布特点

分析成绩的分布情况...

## 存在的问题和短板

指出存在的主要问题...

## 针对性的改进建议

提供具体的改进建议...

## 建议查看详细的数据图表了解具体情况

可以稍后重试AI分析
```
'''

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