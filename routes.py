from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from models import db, User, StudentDetail, Notification, AuditLog
from recommendation import get_recommendations
from prediction import predict_burnout, get_model_metadata
from analytics import get_dashboard_metrics
from utils import generate_student_uid
import random

# Blueprint initialization
main_bp = Blueprint('main', __name__)

# List of motivational quotes
QUOTES = [
    "You don't have to carry it all. Taking breaks is part of the process.",
    "Rest is not laziness, it's a necessity for sustainability.",
    "Your health is your real wealth. School is important, but you come first.",
    "An empty lantern provides no light. Take time to fill your lamp.",
    "Self-care is how you take your power back.",
    "It's okay to slow down. Just don't stop taking care of yourself."
]

# Forms definition
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters")])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    department = SelectField('Department', choices=[
        ('Computer Science', 'Computer Science'),
        ('Mechanical Engineering', 'Mechanical Engineering'),
        ('Electrical Engineering', 'Electrical Engineering'),
        ('Business Analytics', 'Business Analytics'),
        ('Psychology', 'Psychology')
    ], validators=[DataRequired()])
    semester = SelectField('Current Semester', choices=[
        ('Semester 1', 'Semester 1'),
        ('Semester 2', 'Semester 2'),
        ('Semester 3', 'Semester 3'),
        ('Semester 4', 'Semester 4'),
        ('Semester 5', 'Semester 5'),
        ('Semester 6', 'Semester 6'),
        ('Semester 7', 'Semester 7'),
        ('Semester 8', 'Semester 8')
    ], validators=[DataRequired()])
    submit = SubmitField('Create Account')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please choose a different one.')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Reset Link')

class ProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    department = SelectField('Department', choices=[
        ('Computer Science', 'Computer Science'),
        ('Mechanical Engineering', 'Mechanical Engineering'),
        ('Electrical Engineering', 'Electrical Engineering'),
        ('Business Analytics', 'Business Analytics'),
        ('Psychology', 'Psychology')
    ])
    semester = SelectField('Semester', choices=[
        ('Semester 1', 'Semester 1'),
        ('Semester 2', 'Semester 2'),
        ('Semester 3', 'Semester 3'),
        ('Semester 4', 'Semester 4'),
        ('Semester 5', 'Semester 5'),
        ('Semester 6', 'Semester 6'),
        ('Semester 7', 'Semester 7'),
        ('Semester 8', 'Semester 8')
    ])
    new_password = PasswordField('New Password (leave blank to keep current)', validators=[Length(max=50)])
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('new_password')])
    submit = SubmitField('Update Profile')

class PredictionForm(FlaskForm):
    study_hours = FloatField('Study Hours / Day', validators=[DataRequired(), NumberRange(0, 24)])
    sleep_hours = FloatField('Sleep Hours / Day', validators=[DataRequired(), NumberRange(0, 24)])
    stress_level = IntegerField('Stress Level (1 - 10)', validators=[DataRequired(), NumberRange(1, 10)])
    screen_time = FloatField('Screen Time / Day (Hours)', validators=[DataRequired(), NumberRange(0, 24)])
    attendance = FloatField('Attendance (%)', validators=[DataRequired(), NumberRange(0, 100)])
    mental_fatigue = FloatField('Mental Fatigue Score (0.0 - 1.0)', validators=[DataRequired(), NumberRange(0.0, 1.0)])
    physical_activity = FloatField('Physical Activity / Week (Hours)', validators=[DataRequired(), NumberRange(0, 100)])
    submit = SubmitField('Analyze Burnout Risk')


# --- Routes ---

@main_bp.route('/')
def index():
    # Landing page. Load metrics for stats section if database contains records.
    metrics = get_dashboard_metrics()
    return render_template('landing.html', metrics=metrics)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f"Welcome back, {user.name}!", "success")
            
            # Log action
            log = AuditLog(user_id=user.id, action="User Login", details=f"Logged in as {user.role}")
            db.session.add(log)
            db.session.commit()
            
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('main.dashboard'))
        else:
            flash("Invalid email or password.", "danger")
            
    return render_template('login.html', form=form)

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            email=form.email.data,
            role="student",
            department=form.department.data,
            semester=form.semester.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('main.login'))
        
    return render_template('register.html', form=form)

@main_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        # Simulated reset
        flash("Password reset link sent! Check your email inbox.", "success")
        return redirect(url_for('main.login'))
    return render_template('forgot_password.html', form=form)

@main_bp.route('/logout')
@login_required
def logout():
    log = AuditLog(user_id=current_user.id, action="User Logout", details="Logged out successfully")
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('main.index'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # If the user is admin, redirect to admin panel
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
        
    metrics = get_dashboard_metrics()
    quote = random.choice(QUOTES)
    
    # Try to find user's details if they are registered as a student in the preloaded details.
    # Otherwise, generate mock/simulated recommendations based on average values.
    student_details = StudentDetail.query.filter(StudentDetail.name.ilike(f"%{current_user.name}%")).first()
    
    if student_details:
        recs = get_recommendations(student_details)
        student_data = student_details
    else:
        # Default mock student attributes for recommendations
        mock_student = {
            'study_hours': 5.2,
            'sleep_hours': 6.8,
            'stress_level': 6.0,
            'screen_time': 5.5,
            'attendance': 88.5,
            'mental_fatigue': 0.55,
            'physical_activity': 2.5,
            'burnout_category': 'Medium'
        }
        recs = get_recommendations(mock_student)
        student_data = mock_student

    # Get recent global system notifications + user-specific ones
    notifications = Notification.query.filter(
        (Notification.user_id == current_user.id) | (Notification.user_id.is_(None))
    ).order_by(Notification.created_at.desc()).limit(5).all()

    return render_template('dashboard.html', metrics=metrics, quote=quote, recs=recs, student_data=student_data, notifications=notifications)

@main_bp.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    form = PredictionForm()
    prediction_result = None
    recs = None
    
    # Pre-populate student metrics if they exist in the DB matching the current user name
    student_details = StudentDetail.query.filter(StudentDetail.name.ilike(f"%{current_user.name}%")).first()
    if request.method == 'GET' and student_details:
        form.study_hours.data = student_details.study_hours
        form.sleep_hours.data = student_details.sleep_hours
        form.stress_level.data = int(student_details.stress_level)
        form.screen_time.data = student_details.screen_time
        form.attendance.data = student_details.attendance
        form.mental_fatigue.data = student_details.mental_fatigue
        form.physical_activity.data = student_details.physical_activity

    if form.validate_on_submit():
        features = {
            'study_hours': form.study_hours.data,
            'sleep_hours': form.sleep_hours.data,
            'stress_level': form.stress_level.data,
            'screen_time': form.screen_time.data,
            'attendance': form.attendance.data,
            'mental_fatigue': form.mental_fatigue.data,
            'physical_activity': form.physical_activity.data
        }
        
        prediction_result = predict_burnout(features)
        
        # Merge target class and features to get personalized recommendations
        rec_data = features.copy()
        rec_data['burnout_category'] = prediction_result.get('prediction', 'Low')
        recs = get_recommendations(rec_data)
        
        # Log calculation
        log = AuditLog(user_id=current_user.id, action="Burnout Prediction", 
                       details=f"Predicted Class: {rec_data['burnout_category']} (Conf: {prediction_result.get('confidence', 0):.2f})")
        db.session.add(log)
        db.session.commit()
        
    model_meta = get_model_metadata()
    
    return render_template('predict.html', form=form, result=prediction_result, recs=recs, model_meta=model_meta)

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    
    if request.method == 'GET':
        form.name.data = current_user.name
        form.department.data = current_user.department
        form.semester.data = current_user.semester
        
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.department = form.department.data
        current_user.semester = form.semester.data
        
        if form.new_password.data:
            current_user.set_password(form.new_password.data)
            
        db.session.commit()
        
        # Log profile change
        log = AuditLog(user_id=current_user.id, action="Profile Update", details="Updated personal data and preferences")
        db.session.add(log)
        db.session.commit()
        
        flash("Your profile has been updated successfully!", "success")
        return redirect(url_for('main.profile'))
        
    return render_template('profile.html', form=form)

@main_bp.route('/notifications/read/<int:id>', methods=['POST'])
@login_required
def read_notification(id):
    notif = Notification.query.get_or_404(id)
    if notif.user_id and notif.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@main_bp.route('/api/charts-data')
@login_required
def api_charts_data():
    from analytics import get_chart_data
    data = get_chart_data()
    return jsonify(data)
