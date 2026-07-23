import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mindspace-super-secret-key-12345!')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'mindspace.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Custom directories
    DATASET_DIR = os.path.join(BASE_DIR, 'dataset')
    REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
    UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
    
    # Model configuration
    MODEL_PATH = os.path.join(BASE_DIR, 'burnout_model.pkl')
    SCALER_PATH = os.path.join(BASE_DIR, 'burnout_scaler.pkl')
