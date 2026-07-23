import os
from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from models import db, User, Notification
from routes import main_bp
from admin import admin_bp
from utils import clean_and_load_dataset, seed_default_users
from prediction import train_model

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Database Initialization
    db.init_app(app)

    # Login Manager setup
    login_manager = LoginManager()
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    # Custom Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    # Context processors to make notifications available globally to layouts
    @app.context_processor
    def inject_global_data():
        from flask_login import current_user
        unread_notifs_count = 0
        latest_notifs = []
        if current_user.is_authenticated:
            unread_notifs_count = Notification.query.filter(
                (Notification.user_id == current_user.id) | (Notification.user_id.is_(None)),
                Notification.is_read == False
            ).count()
            latest_notifs = Notification.query.filter(
                (Notification.user_id == current_user.id) | (Notification.user_id.is_(None))
            ).order_by(Notification.created_at.desc()).limit(5).all()
        return dict(
            unread_notifs_count=unread_notifs_count,
            latest_notifications=latest_notifs
        )

    # Application Startup tasks: Database setup, Seeding & ML Training
    with app.app_context():
        # Ensure directories exist
        os.makedirs(app.config['DATASET_DIR'], exist_ok=True)
        os.makedirs(app.config['REPORTS_DIR'], exist_ok=True)
        os.makedirs(app.config['UPLOADS_DIR'], exist_ok=True)

        db.create_all()
        
        # Seed Admin and Student logins
        seed_default_users()
        
        # Seed student dataset from bundled CSV (or create synthetic first if missing)
        csv_path = os.path.join(app.config['DATASET_DIR'], 'student_burnout.csv')
        if not os.path.exists(csv_path):
            from utils import generate_synthetic_csv
            generate_synthetic_csv(csv_path)
            
        clean_and_load_dataset(csv_path)
        
        # Train ML Model on start
        if not os.path.exists(app.config['MODEL_PATH']):
            print("ML model not found. Training model...")
            train_model(csv_path)
            print("ML model trained successfully!")

    return app

app = create.app()

if __name__ == '__main__':
    app.run(debug=True)
