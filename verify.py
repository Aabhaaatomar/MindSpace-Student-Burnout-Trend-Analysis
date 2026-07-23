import os
import sys

def verify_system():
    print("==================================================")
    print("MindSpace - Starting Backend Integrity Verification")
    print("==================================================")

    # 1. Imports check
    try:
        from app import create_app
        from models import db, User, StudentDetail, AuditLog
        from prediction import predict_burnout, get_model_metadata
        from utils import export_students_pdf, export_students_excel, export_students_csv
        print("[SUCCESS] Core modules imported successfully.")
    except Exception as e:
        print(f"[FAIL] Dependency import error: {str(e)}")
        sys.exit(1)

    # 2. Flask Application Context instantiation
    try:
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        print("[SUCCESS] Flask app initialized.")
    except Exception as e:
        print(f"[FAIL] Flask instantiation failed: {str(e)}")
        sys.exit(1)

    with app.app_context():
        # 3. Database Check
        try:
            total_students = StudentDetail.query.count()
            users_count = User.query.count()
            print(f"[SUCCESS] Database connected. Found {total_students} student details and {users_count} user accounts.")
            
            if total_students < 500:
                print(f"[FAIL] Student records count is low: {total_students} (Expected > 500)")
                sys.exit(1)
            
            admin_user = User.query.filter_by(email="admin@mindspace.edu").first()
            if not admin_user or admin_user.role != 'admin':
                print("[FAIL] Default Admin user was not seeded properly.")
                sys.exit(1)
            
            student_user = User.query.filter_by(email="student@mindspace.edu").first()
            if not student_user or student_user.role != 'student':
                print("[FAIL] Default Student user was not seeded properly.")
                sys.exit(1)
                
            print("[SUCCESS] Default credentials (admin@mindspace.edu & student@mindspace.edu) confirmed.")
        except Exception as e:
            print(f"[FAIL] Database verification failed: {str(e)}")
            sys.exit(1)

        # 4. Machine Learning Model Check
        try:
            metadata = get_model_metadata()
            if not metadata:
                print("[FAIL] Model metadata not found in PKL file.")
                sys.exit(1)
            
            print(f"[SUCCESS] Classifier metadata retrieved. Accuracy: {metadata['accuracy']*100:.2f}%. Sample Size: {metadata['sample_size']} rows.")
            
            # Print feature importances
            print("Feature Importances:")
            for fi in metadata['feature_importance'][:3]:
                print(f"  - {fi['feature']}: {fi['importance']:.4f}")
                
            # Perform prediction inference check
            test_features = {
                'study_hours': 8.0,
                'sleep_hours': 5.0,
                'stress_level': 8.0,
                'screen_time': 9.0,
                'attendance': 75.0,
                'mental_fatigue': 0.85,
                'physical_activity': 1.0
            }
            pred_res = predict_burnout(test_features)
            print(f"[SUCCESS] ML Prediction inference output: {pred_res['prediction']} Burnout (Confidence: {pred_res['confidence']:.4f})")
            
            if pred_res['prediction'] not in ['High', 'Medium', 'Low']:
                print(f"[FAIL] Invalid prediction class output: {pred_res['prediction']}")
                sys.exit(1)
                
        except Exception as e:
            print(f"[FAIL] Machine learning pipeline checks failed: {str(e)}")
            sys.exit(1)

        # 5. File Exporters Check
        try:
            queryset = StudentDetail.query.limit(10).all()
            
            # CSV Check
            csv_data = export_students_csv(queryset)
            if not csv_data or "Student ID" not in csv_data:
                print("[FAIL] CSV exporter generated invalid content.")
                sys.exit(1)
                
            # Excel Check
            excel_data = export_students_excel(queryset)
            if not excel_data or len(excel_data) < 1000:
                print("[FAIL] Excel exporter generated invalid content size.")
                sys.exit(1)
                
            # PDF Check
            pdf_data = export_students_pdf(queryset)
            if not pdf_data or len(pdf_data) < 1000:
                print("[FAIL] PDF exporter generated invalid content size.")
                sys.exit(1)
                
            print("[SUCCESS] Report Exporters (CSV, Excel, PDF) validated successfully.")
        except Exception as e:
            print(f"[FAIL] Exporter validations encountered errors: {str(e)}")
            sys.exit(1)

    print("==================================================")
    print("MindSpace - System Integrity Verification PASSED!")
    print("==================================================")

if __name__ == '__main__':
    verify_system()
