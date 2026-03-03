"""
Agrinova - Main Flask Application
Created by Parth Dshiphale
"""

import os
import logging
from flask import Flask, jsonify, render_template, request, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from datetime import datetime, timedelta
import joblib
import numpy as np

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, 
            static_folder='../frontend',
            template_folder='../frontend',
            static_url_path='')

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'agrinova-secret-key-parth-dshiphale')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///agrinova.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Initialize extensions
CORS(app, resources={r"/api/*": {"origins": "*"}})
db = SQLAlchemy(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load AI Models
try:
    logger.info("🌾 Loading Agrinova AI Models...")
    ensemble_model = joblib.load('backend/models/saved_models/ensemble_model.pkl')
    label_encoder = joblib.load('backend/models/saved_models/label_encoder.pkl')
    scaler = joblib.load('backend/models/saved_models/scaler.pkl')
    logger.info("✅ AI Models loaded successfully!")
except Exception as e:
    logger.error(f"❌ Error loading models: {e}")
    ensemble_model = None
    label_encoder = None
    scaler = None

# Import blueprints
from api.crop_recommend import crop_bp
from api.weather import weather_bp
from api.mandi_prices import mandi_bp
from api.schemes import schemes_bp
from api.chatbot import chatbot_bp

# Register blueprints
app.register_blueprint(crop_bp, url_prefix='/api/crop')
app.register_blueprint(weather_bp, url_prefix='/api/weather')
app.register_blueprint(mandi_bp, url_prefix='/api/mandi')
app.register_blueprint(schemes_bp, url_prefix='/api/schemes')
app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')

# Database Models
class User(db.Model):
    """User model for farmers"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(15), unique=True)
    language = db.Column(db.String(10), default='en')
    state = db.Column(db.String(50))
    district = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class CropHistory(db.Model):
    """Track user's crop recommendations"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    soil_n = db.Column(db.Float)
    soil_p = db.Column(db.Float)
    soil_k = db.Column(db.Float)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    ph = db.Column(db.Float)
    rainfall = db.Column(db.Float)
    recommended_crop = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Serve dashboard page"""
    return render_template('pages/dashboard.html')

@app.route('/about')
def about():
    """Serve about page"""
    return render_template('pages/about.html')

@app.route('/contact')
def contact():
    """Serve contact page"""
    return render_template('pages/contact.html')

@app.route('/api/health')
def health_check():
    """API health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'app': 'Agrinova',
        'created_by': 'Parth Dshiphale',
        'timestamp': datetime.now().isoformat(),
        'ai_model_loaded': ensemble_model is not None
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Create database tables
with app.app_context():
    db.create_all()
    logger.info("✅ Database tables created")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)