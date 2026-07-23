import os
import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, confusion_matrix
from config import Config

# Features used for the prediction model
FEATURE_COLS = [
    'study_hours', 
    'sleep_hours', 
    'stress_level', 
    'screen_time', 
    'attendance', 
    'mental_fatigue', 
    'physical_activity'
]

def train_model(csv_path):
    """
    Train a Random Forest model on the student burnout dataset.
    Returns evaluation metrics (accuracy, confusion matrix, feature importance).
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset CSV not found at {csv_path}")

    # Load and clean dataset for training
    df = pd.read_csv(csv_path)
    df.dropna(subset=FEATURE_COLS + ['burnout_category'], inplace=True)
    df.drop_duplicates(inplace=True)

    X = df[FEATURE_COLS]
    y = df['burnout_category']

    # Split dataset
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train Random Forest Classifier
    model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, class_weight='balanced')
    model.fit(X_train_scaled, y_train)

    # Evaluate model
    y_pred = model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    
    # Confusion matrix
    classes = sorted(list(y.unique())) # 'High', 'Low', 'Medium' (typically sorted alphabetically)
    cm = confusion_matrix(y_test, y_pred, labels=classes)
    
    # Format confusion matrix for UI display
    cm_dict = {
        'labels': classes,
        'values': cm.tolist()
    }

    # Feature Importance
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    feature_importance = [
        {'feature': FEATURE_COLS[i].replace('_', ' ').title(), 'importance': float(importances[i])}
        for i in indices
    ]

    # Save scaler and model
    with open(Config.MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    with open(Config.SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)

    # Save metadata
    metadata = {
        'accuracy': float(accuracy),
        'confusion_matrix': cm_dict,
        'feature_importance': feature_importance,
        'sample_size': len(df)
    }
    
    metadata_path = os.path.join(Config.BASE_DIR, 'model_metadata.pkl')
    with open(metadata_path, 'wb') as f:
        pickle.dump(metadata, f)

    return metadata

def get_model_metadata():
    """
    Retrieve accuracy and evaluation metrics of the trained model.
    """
    metadata_path = os.path.join(Config.BASE_DIR, 'model_metadata.pkl')
    if os.path.exists(metadata_path):
        with open(metadata_path, 'rb') as f:
            return pickle.load(f)
    return None

def predict_burnout(features_dict):
    """
    Make predictions using the serialized model and scaler.
    """
    # Load model and scaler
    if not os.path.exists(Config.MODEL_PATH) or not os.path.exists(Config.SCALER_PATH):
        # Trigger retraining dynamically
        csv_path = os.path.join(Config.DATASET_DIR, 'student_burnout.csv')
        if os.path.exists(csv_path):
            train_model(csv_path)
        else:
            return {'error': 'Model not trained and dataset CSV is missing.'}

    with open(Config.MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    with open(Config.SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)

    # Parse and format input features
    input_data = []
    for col in FEATURE_COLS:
        val = features_dict.get(col, 0)
        try:
            input_data.append(float(val))
        except (ValueError, TypeError):
            input_data.append(0.0)

    # Reshape and scale input data
    input_array = np.array([input_data])
    scaled_array = scaler.transform(input_array)

    # Predict class & confidence
    prediction = model.predict(scaled_array)[0]
    probabilities = model.predict_proba(scaled_array)[0]
    
    classes = model.classes_
    class_probs = {classes[i]: float(probabilities[i]) for i in range(len(classes))}
    confidence = float(class_probs.get(prediction, 0.0))

    return {
        'prediction': prediction,
        'confidence': confidence,
        'probabilities': class_probs
    }
