from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, Response, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length
from models import db, StudentDetail, AuditLog, User, Notification
from decorators import admin_required
from prediction import train_model
from utils import export_students_csv, export_students_excel, export_students_pdf, generate_student_uid
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Form for adding/editing students
class StudentForm(FlaskForm):
    name = StringField('Student Name', validators=[DataRequired(), Length(min=2, max=100)])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Non-Binary', 'Non-Binary')], validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=15, max=100)])
    department = SelectField('Department', choices=[
        ('Computer Science', 'Computer Science'),
        ('Mechanical Engineering', 'Mechanical Engineering'),
        ('Electrical Engineering', 'Electrical Engineering'),
        ('Business Analytics', 'Business Analytics'),
        ('Psychology', 'Psychology')
    ], validators=[DataRequired()])
    academic_year = SelectField('Academic Year', choices=[('1', 'Year 1'), ('2', 'Year 2'), ('3', 'Year 3'), ('4', 'Year 4')], coerce=int, validators=[DataRequired()])
    study_hours = FloatField('Study Hours/Day', validators=[DataRequired(), NumberRange(min=0.0, max=24.0)])
    sleep_hours = FloatField('Sleep Hours/Day', validators=[DataRequired(), NumberRange(min=0.0, max=24.0)])
    stress_level = FloatField('Stress Level (1-10)', validators=[DataRequired(), NumberRange(min=1.0, max=10.0)])
    screen_time = FloatField('Screen Time/Day (Hours)', validators=[DataRequired(), NumberRange(min=0.0, max=24.0)])
    attendance = FloatField('Attendance (%)', validators=[DataRequired(), NumberRange(min=0.0, max=100.0)])
    mental_fatigue = FloatField('Mental Fatigue Score (0.0-1.0)', validators=[DataRequired(), NumberRange(min=0.0, max=1.0)])
    physical_activity = FloatField('Physical Activity/Week (Hours)', validators=[DataRequired(), NumberRange(min=0.0, max=168.0)])
    submit = SubmitField('Save Student Record')


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Admin Landing Dashboard
    # Get basic counts for analytics cards
    total_students = StudentDetail.query.count()
    high_risk = StudentDetail.query.filter_by(burnout_category='High').count()
    med_risk = StudentDetail.query.filter_by(burnout_category='Medium').count()
    
    # Audit log
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    # System info
    db_size = "N/A"
    db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    if os.path.exists(db_path):
        db_size = f"{os.path.getsize(db_path) / 1024 / 1024:.2f} MB"
        
    return render_template('admin_dashboard.html', 
                           total_students=total_students, 
                           high_risk=high_risk, 
                           med_risk=med_risk,
                           recent_logs=recent_logs,
                           db_size=db_size)


@admin_bp.route('/students', methods=['GET'])
@login_required
@admin_required
def students():
    # Data Management Dashboard with Paginated/Filtered records
    page = request.args.get('page', 1, type=int)
    search_q = request.args.get('search', '', type=str)
    dept_filter = request.args.get('department', '', type=str)
    risk_filter = request.args.get('risk', '', type=str)
    
    query = StudentDetail.query
    
    if search_q:
        query = query.filter(
            (StudentDetail.name.ilike(f"%{search_q}%")) | 
            (StudentDetail.student_uid.ilike(f"%{search_q}%"))
        )
    if dept_filter:
        query = query.filter_by(department=dept_filter)
    if risk_filter:
        query = query.filter_by(burnout_category=risk_filter)
        
    # Order by ID descending
    query = query.order_by(StudentDetail.id.desc())
    
    # Paginate (15 items per page)
    pagination = query.paginate(page=page, per_page=15, error_out=False)
    students_list = pagination.items
    
    # Get distinct departments for filter dropdown
    depts = [d[0] for d in db.session.query(StudentDetail.department).distinct().all()]
    
    return render_template('data_management.html', 
                           students=students_list, 
                           pagination=pagination,
                           search=search_q,
                           dept_filter=dept_filter,
                           risk_filter=risk_filter,
                           depts=depts)


@admin_bp.route('/students/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_student():
    form = StudentForm()
    if form.validate_on_submit():
        # Calculate burnout score and category before saving
        stress = form.stress_level.data
        fatigue = form.mental_fatigue.data
        sleep = form.sleep_hours.data
        attendance = form.attendance.data
        
        # Consistent formula with synthetic generator
        burnout_val = (stress * 0.35 / 10) + (fatigue * 0.35) + ((10.0 - sleep) * 0.15 / 10) + ((100 - attendance) * 0.15 / 100)
        burnout_score = min(1.0, max(0.0, round(burnout_val, 2)))
        
        if burnout_score < 0.40:
            burnout_category = "Low"
        elif burnout_score < 0.70:
            burnout_category = "Medium"
        else:
            burnout_category = "High"

        # Unique student ID
        seq = StudentDetail.query.count() + 1
        uid = generate_student_uid(seq)
        
        student = StudentDetail(
            student_uid=uid,
            name=form.name.data,
            gender=form.gender.data,
            age=form.age.data,
            department=form.department.data,
            academic_year=form.academic_year.data,
            study_hours=form.study_hours.data,
            sleep_hours=form.sleep_hours.data,
            stress_level=form.stress_level.data,
            screen_time=form.screen_time.data,
            attendance=form.attendance.data,
            mental_fatigue=form.mental_fatigue.data,
            physical_activity=form.physical_activity.data,
            burnout_score=burnout_score,
            burnout_category=burnout_category
        )
        db.session.add(student)
        db.session.commit()
        
        # Log action
        log = AuditLog(user_id=current_user.id, action="Create Student Record", details=f"Added student {uid} ({form.name.data})")
        db.session.add(log)
        db.session.commit()
        
        flash(f"Student record {uid} created successfully!", "success")
        return redirect(url_for('admin.students'))
        
    return render_template('student_form.html', form=form, title="Add Student Record")


@admin_bp.route('/students/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_student(id):
    student = StudentDetail.query.get_or_404(id)
    form = StudentForm(obj=student)
    
    if form.validate_on_submit():
        # Calculate burnout score and category
        stress = form.stress_level.data
        fatigue = form.mental_fatigue.data
        sleep = form.sleep_hours.data
        attendance = form.attendance.data
        
        burnout_val = (stress * 0.35 / 10) + (fatigue * 0.35) + ((10.0 - sleep) * 0.15 / 10) + ((100 - attendance) * 0.15 / 100)
        burnout_score = min(1.0, max(0.0, round(burnout_val, 2)))
        
        if burnout_score < 0.40:
            burnout_category = "Low"
        elif burnout_score < 0.70:
            burnout_category = "Medium"
        else:
            burnout_category = "High"

        # Apply edits
        student.name = form.name.data
        student.gender = form.gender.data
        student.age = form.age.data
        student.department = form.department.data
        student.academic_year = form.academic_year.data
        student.study_hours = form.study_hours.data
        student.sleep_hours = form.sleep_hours.data
        student.stress_level = form.stress_level.data
        student.screen_time = form.screen_time.data
        student.attendance = form.attendance.data
        student.mental_fatigue = form.mental_fatigue.data
        student.physical_activity = form.physical_activity.data
        student.burnout_score = burnout_score
        student.burnout_category = burnout_category
        
        db.session.commit()
        
        # Log action
        log = AuditLog(user_id=current_user.id, action="Update Student Record", details=f"Edited student {student.student_uid} ({student.name})")
        db.session.add(log)
        db.session.commit()
        
        flash(f"Student record {student.student_uid} updated successfully!", "success")
        return redirect(url_for('admin.students'))
        
    return render_template('student_form.html', form=form, title=f"Edit Student: {student.student_uid}")


@admin_bp.route('/students/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_student(id):
    student = StudentDetail.query.get_or_404(id)
    uid = student.student_uid
    name = student.name
    
    db.session.delete(student)
    db.session.commit()
    
    # Log action
    log = AuditLog(user_id=current_user.id, action="Delete Student Record", details=f"Removed student {uid} ({name})")
    db.session.add(log)
    db.session.commit()
    
    flash(f"Student record {uid} has been deleted.", "warning")
    return redirect(url_for('admin.students'))


@admin_bp.route('/export/csv', methods=['GET'])
@login_required
@admin_required
def export_csv():
    dept = request.args.get('department', '')
    risk = request.args.get('risk', '')
    
    query = StudentDetail.query
    if dept:
        query = query.filter_by(department=dept)
    if risk:
        query = query.filter_by(burnout_category=risk)
        
    csv_data = export_students_csv(query.all())
    
    filename = f"student_burnout_report_{datetime.now().strftime('%Y%m%d')}.csv"
    
    # Audit Log
    log = AuditLog(user_id=current_user.id, action="Export CSV Data", details=f"Exported student data list to CSV")
    db.session.add(log)
    db.session.commit()
    
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )


@admin_bp.route('/export/excel', methods=['GET'])
@login_required
@admin_required
def export_excel():
    dept = request.args.get('department', '')
    risk = request.args.get('risk', '')
    
    query = StudentDetail.query
    if dept:
        query = query.filter_by(department=dept)
    if risk:
        query = query.filter_by(burnout_category=risk)
        
    xlsx_data = export_students_excel(query.all())
    
    filename = f"student_burnout_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    # Audit Log
    log = AuditLog(user_id=current_user.id, action="Export Excel Data", details=f"Exported student data list to Excel")
    db.session.add(log)
    db.session.commit()
    
    import io
    return send_file(
        io.BytesIO(xlsx_data),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )


@admin_bp.route('/export/pdf', methods=['GET'])
@login_required
@admin_required
def export_pdf():
    dept = request.args.get('department', '')
    risk = request.args.get('risk', '')
    
    query = StudentDetail.query
    if dept:
        query = query.filter_by(department=dept)
    if risk:
        query = query.filter_by(burnout_category=risk)
        
    title = "Burnout Summary Report"
    if dept:
        title += f" ({dept})"
    if risk:
        title += f" - {risk} Risk"
        
    pdf_data = export_students_pdf(query.all(), title_name=title)
    
    filename = f"student_burnout_report_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    # Audit Log
    log = AuditLog(user_id=current_user.id, action="Export PDF Report", details=f"Exported student report to PDF")
    db.session.add(log)
    db.session.commit()
    
    import io
    return send_file(
        io.BytesIO(pdf_data),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )


@admin_bp.route('/ml/retrain', methods=['POST'])
@login_required
@admin_required
def retrain():
    # Retrain model trigger
    csv_path = os.path.join(current_app.config['DATASET_DIR'], 'student_burnout.csv')
    try:
        metrics = train_model(csv_path)
        flash(f"ML Model retrained successfully! Accuracy: {metrics['accuracy']*100:.2f}%", "success")
        
        # Log action
        log = AuditLog(user_id=current_user.id, action="Retrain ML Model", 
                       details=f"Retrained RF classifier. Accuracy: {metrics['accuracy']:.4f}")
        db.session.add(log)
        
        notif = Notification(
            title="ML Model Updated",
            message=f"Model successfully retrained by administrator. New testing accuracy: {metrics['accuracy']*100:.2f}%.",
            type="info"
        )
        db.session.add(notif)
        db.session.commit()
    except Exception as e:
        flash(f"Error during retraining: {str(e)}", "danger")
        
    return redirect(url_for('admin.dashboard'))
