from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='student', nullable=False)  # 'admin' or 'student'
    department = db.Column(db.String(100), nullable=True)
    semester = db.Column(db.String(20), nullable=True)
    profile_pic = db.Column(db.String(100), default='default.png', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class StudentDetail(db.Model):
    __tablename__ = 'student_details'
    
    id = db.Column(db.Integer, primary_key=True)
    student_uid = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    academic_year = db.Column(db.Integer, nullable=False)  # 1, 2, 3, 4
    study_hours = db.Column(db.Float, nullable=False)      # hours/day
    sleep_hours = db.Column(db.Float, nullable=False)      # hours/day
    stress_level = db.Column(db.Float, nullable=False)     # 1-10 scale
    screen_time = db.Column(db.Float, nullable=False)      # hours/day
    attendance = db.Column(db.Float, nullable=False)       # 0-100 percentage
    mental_fatigue = db.Column(db.Float, nullable=False)   # 0.0 - 1.0 scale
    physical_activity = db.Column(db.Float, nullable=False) # hours/week
    burnout_score = db.Column(db.Float, nullable=False)    # 0.0 - 1.0 score
    burnout_category = db.Column(db.String(20), nullable=False) # 'Low', 'Medium', 'High'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'student_uid': self.student_uid,
            'name': self.name,
            'gender': self.gender,
            'age': self.age,
            'department': self.department,
            'academic_year': self.academic_year,
            'study_hours': self.study_hours,
            'sleep_hours': self.sleep_hours,
            'stress_level': self.stress_level,
            'screen_time': self.screen_time,
            'attendance': self.attendance,
            'mental_fatigue': self.mental_fatigue,
            'physical_activity': self.physical_activity,
            'burnout_score': self.burnout_score,
            'burnout_category': self.burnout_category,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    def __repr__(self):
        return f"<StudentDetail {self.student_uid} - {self.name}>"


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True)
    
    # Relationship to user
    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))

    def __repr__(self):
        return f"<AuditLog {self.action} at {self.timestamp}>"


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True) # None for global/system
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info', nullable=False) # 'info', 'warning', 'success', 'reminder'
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

    def __repr__(self):
        return f"<Notification {self.title} read={self.is_read}>"
