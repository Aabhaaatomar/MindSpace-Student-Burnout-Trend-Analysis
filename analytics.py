import pandas as pd
import numpy as np
from models import StudentDetail, db

def get_dashboard_metrics():
    """
    Calculate high-level KPI metrics from database records.
    """
    # Load all records into DataFrame
    students = db.session.query(StudentDetail).all()
    df = pd.DataFrame([s.to_dict() for s in students])
    
    if df.empty:
        return {
            'total_students': 0,
            'avg_stress': 0.0,
            'avg_burnout': 0.0,
            'avg_sleep': 0.0,
            'avg_study': 0.0,
            'avg_screen': 0.0,
            'avg_attendance': 0.0,
            'high_risk_pct': 0.0,
            'medium_risk_pct': 0.0,
            'low_risk_pct': 0.0,
            'healthy_students': 0,
            'high_risk_count': 0
        }

    total = len(df)
    avg_stress = float(df['stress_level'].mean())
    avg_burnout = float(df['burnout_score'].mean())
    avg_sleep = float(df['sleep_hours'].mean())
    avg_study = float(df['study_hours'].mean())
    avg_screen = float(df['screen_time'].mean())
    avg_attendance = float(df['attendance'].mean())
    
    # Calculate counts based on burnout category
    cat_counts = df['burnout_category'].value_counts()
    high_count = int(cat_counts.get('High', 0))
    med_count = int(cat_counts.get('Medium', 0))
    low_count = int(cat_counts.get('Low', 0))
    
    high_pct = (high_count / total) * 100 if total > 0 else 0
    med_pct = (med_count / total) * 100 if total > 0 else 0
    low_pct = (low_count / total) * 100 if total > 0 else 0
    
    # "Healthy" is Low Burnout & Stress level <= 4
    healthy_students = int(df[(df['burnout_category'] == 'Low') & (df['stress_level'] <= 4)].shape[0])

    return {
        'total_students': total,
        'avg_stress': round(avg_stress, 2),
        'avg_burnout': round(avg_burnout, 2),
        'avg_sleep': round(avg_sleep, 2),
        'avg_study': round(avg_study, 2),
        'avg_screen': round(avg_screen, 2),
        'avg_attendance': round(avg_attendance, 2),
        'high_risk_pct': round(high_pct, 1),
        'medium_risk_pct': round(med_pct, 1),
        'low_risk_pct': round(low_pct, 1),
        'healthy_students': healthy_students,
        'high_risk_count': high_count
    }

def get_chart_data():
    """
    Process records and generate structured JSON responses for Chart.js.
    """
    students = db.session.query(StudentDetail).all()
    df = pd.DataFrame([s.to_dict() for s in students])
    
    if df.empty:
        return {}

    charts = {}

    # 1. Burnout Category Distribution (Donut)
    burnout_dist = df['burnout_category'].value_counts()
    charts['burnout_distribution'] = {
        'labels': list(burnout_dist.index),
        'data': [int(v) for v in burnout_dist.values]
    }

    # 2. Stress Level vs Burnout Score (Scatter Plot)
    # Take a sample of up to 100 points for visualization speed and clarity
    scatter_df = df.sample(min(len(df), 150), random_state=42)
    charts['stress_vs_burnout'] = [
        {'x': float(row['stress_level']), 'y': float(row['burnout_score']), 'name': str(row['name'])}
        for _, row in scatter_df.iterrows()
    ]

    # 3. Sleep Hours vs Burnout Score (Scatter)
    charts['sleep_vs_burnout'] = [
        {'x': float(row['sleep_hours']), 'y': float(row['burnout_score']), 'name': str(row['name'])}
        for _, row in scatter_df.iterrows()
    ]

    # 4. Department-wise Burnout and Stress (Grouped Bar)
    dept_df = df.groupby('department')[['burnout_score', 'stress_level']].mean().reset_index()
    charts['department_analysis'] = {
        'labels': list(dept_df['department']),
        'burnout': [round(float(v), 2) for v in dept_df['burnout_score']],
        'stress': [round(float(v), 2) for v in dept_df['stress_level']]
    }

    # 5. Academic Year-wise Burnout Trends (Line Chart)
    year_df = df.groupby('academic_year')['burnout_score'].mean().sort_index().reset_index()
    charts['year_analysis'] = {
        'labels': [f"Year {int(y)}" for y in year_df['academic_year']],
        'data': [round(float(v), 2) for v in year_df['burnout_score']]
    }

    # 6. Gender-wise Burnout Score (Pie)
    gender_df = df.groupby('gender')['burnout_score'].mean().reset_index()
    charts['gender_analysis'] = {
        'labels': list(gender_df['gender']),
        'data': [round(float(v), 2) for v in gender_df['burnout_score']]
    }

    # 7. Stress Level Counts (Bar/Histogram)
    stress_counts = df['stress_level'].value_counts().sort_index()
    charts['stress_distribution'] = {
        'labels': [str(int(k)) for k in stress_counts.index],
        'data': [int(v) for v in stress_counts.values]
    }

    # 8. Sleep Analysis (Histogram)
    sleep_bins = pd.cut(df['sleep_hours'], bins=[0, 5, 6, 7, 8, 9, 12], labels=['<5 hrs', '5-6 hrs', '6-7 hrs', '7-8 hrs', '8-9 hrs', '9+ hrs'])
    sleep_counts = sleep_bins.value_counts().sort_index()
    charts['sleep_distribution'] = {
        'labels': list(sleep_counts.index.astype(str)),
        'data': [int(v) for v in sleep_counts.values]
    }

    # 9. Correlation Matrix (Heatmap)
    corr_cols = ['study_hours', 'sleep_hours', 'stress_level', 'screen_time', 'attendance', 'mental_fatigue', 'physical_activity', 'burnout_score']
    corr_matrix = df[corr_cols].corr()
    charts['correlation_matrix'] = {
        'labels': [c.replace('_', ' ').title() for c in corr_cols],
        'data': [[round(float(corr_matrix.iloc[i, j]), 2) for j in range(len(corr_cols))] for i in range(len(corr_cols))]
    }

    # 10. Study Hours vs Burnout Score (Scatter/Trend)
    charts['study_vs_burnout'] = [
        {'x': float(row['study_hours']), 'y': float(row['burnout_score']), 'name': str(row['name'])}
        for _, row in scatter_df.iterrows()
    ]

    return charts
