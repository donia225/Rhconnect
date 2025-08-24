import os
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, '..', '..', 'ml_models', 'svm_model.pkl')
encoder_path = os.path.join(BASE_DIR, '..', '..', 'ml_models', 'label_encoder.pkl')

svm_model = joblib.load(os.path.abspath(model_path))
label_encoder = joblib.load(os.path.abspath(encoder_path))
