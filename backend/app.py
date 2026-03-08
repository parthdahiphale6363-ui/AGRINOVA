"""
Agrinova - AI Powered Farming Assistant
Created by Parth Dahiphale
Uses Claude AI for accurate crop recommendations
"""

import os
import requests
import json
import random
from io import BytesIO
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from datetime import datetime
import sys
import logging

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

print("=== STARTING AGRINOVA APP ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")

# Check for missing dependencies
try:
    import flask
    print(f"✅ Flask version: {flask.__version__}")
    import flask_cors
    print("✅ Flask-CORS imported")
    import requests
    print(f"✅ Requests version: {requests.__version__}")
    import joblib
    print(f"✅ Joblib version: {joblib.__version__}")
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    raise

try:
    app = Flask(__name__, 
                static_folder='../frontend',
                template_folder='../frontend',
                static_url_path='')
    print("✅ Flask app created successfully")
except Exception as e:
    print(f"❌ Failed to create Flask app: {e}")
    raise

app.config['SECRET_KEY'] = 'agrinova-secret-key-parth-2026'
CORS(app)

# ============================================
# GEMINI API CONFIGURATION (COMPLETELY FREE!)
# ============================================
GEMINI_API_KEY = "AIzaSyCMSjnoiIUzoZfuVeYcJlOFIG5Lo-i8SDU"  # Your Gemini key
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# ============================================
# INPUT VALIDATION RANGES (Scientifically valid)
# ============================================
VALID_RANGES = {
    'nitrogen':    {'min': 0,   'max': 300,  'unit': 'kg/ha', 'label': 'Nitrogen'},
    'phosphorus':  {'min': 0,   'max': 300,  'unit': 'kg/ha', 'label': 'Phosphorus'},
    'potassium':   {'min': 0,   'max': 300,  'unit': 'kg/ha', 'label': 'Potassium'},
    'temperature': {'min': 0,   'max': 50,   'unit': '°C',    'label': 'Temperature'},
    'humidity':    {'min': 0,   'max': 100,  'unit': '%',     'label': 'Humidity'},
    'ph':          {'min': 0,   'max': 14,   'unit': '',      'label': 'pH'},
    'rainfall':    {'min': 0,   'max': 500,  'unit': 'mm',    'label': 'Rainfall'},
}

# Crop database
CROP_INFO = {
    'rice':      {'name': 'Rice',      'icon': '🌾', 'season': 'Kharif (June-October)',       'water': 'High (1200-1500 mm)',   'soil': 'Clay loam, alluvial',    'temp': '20-35°C'},
    'wheat':     {'name': 'Wheat',     'icon': '🌾', 'season': 'Rabi (November-April)',        'water': 'Medium (450-650 mm)',   'soil': 'Loamy, clay loam',       'temp': '15-25°C'},
    'maize':     {'name': 'Maize',     'icon': '🌽', 'season': 'All seasons',                  'water': 'Medium (500-800 mm)',   'soil': 'Well-drained loamy',     'temp': '22-30°C'},
    'cotton':    {'name': 'Cotton',    'icon': '🌿', 'season': 'Kharif (May-September)',       'water': 'Medium (700-1000 mm)',  'soil': 'Black cotton soil',      'temp': '25-35°C'},
    'groundnut': {'name': 'Groundnut', 'icon': '🥜', 'season': 'Kharif & Rabi',               'water': 'Low (350-500 mm)',      'soil': 'Sandy loam',             'temp': '24-30°C'},
    'sugarcane': {'name': 'Sugarcane', 'icon': '🎋', 'season': 'All seasons',                  'water': 'High (1500-2500 mm)',   'soil': 'Deep loamy',             'temp': '20-35°C'},
    'potato':    {'name': 'Potato',    'icon': '🥔', 'season': 'Rabi (October-February)',      'water': 'Medium (400-600 mm)',   'soil': 'Sandy loam',             'temp': '15-25°C'},
    'onion':     {'name': 'Onion',     'icon': '🧅', 'season': 'Rabi & Kharif',               'water': 'Medium (350-500 mm)',   'soil': 'Well-drained loamy',     'temp': '20-30°C'},
    'tomato':    {'name': 'Tomato',    'icon': '🍅', 'season': 'All seasons',                  'water': 'Medium (400-600 mm)',   'soil': 'Well-drained loamy',     'temp': '20-27°C'},
    'chickpea':  {'name': 'Chickpea',  'icon': '🫘', 'season': 'Rabi (October-March)',         'water': 'Low (300-450 mm)',      'soil': 'Sandy loam to clay loam','temp': '15-25°C'},
    'lentil':    {'name': 'Lentil',    'icon': '🫘', 'season': 'Rabi (October-March)',         'water': 'Low (250-400 mm)',      'soil': 'Loamy',                  'temp': '15-25°C'},
    'mustard':   {'name': 'Mustard',   'icon': '🌻', 'season': 'Rabi (October-March)',         'water': 'Low (250-400 mm)',      'soil': 'Sandy loam to loam',     'temp': '10-25°C'},
    'soybean':   {'name': 'Soybean',   'icon': '🫘', 'season': 'Kharif (June-October)',        'water': 'Medium (500-800 mm)',   'soil': 'Well-drained loamy',     'temp': '20-30°C'},
    'banana':    {'name': 'Banana',    'icon': '🍌', 'season': 'All seasons',                  'water': 'High (1200-2200 mm)',   'soil': 'Rich loamy',             'temp': '26-35°C'},
    'mango':     {'name': 'Mango',     'icon': '🥭', 'season': 'Perennial (harvest Apr-Jul)',  'water': 'Medium (900-1000 mm)',  'soil': 'Deep loamy alluvial',    'temp': '24-30°C'},
}

# Government Schemes
GOVERNMENT_SCHEMES = [
    {'id': 1, 'name': 'PM-KISAN',           'icon': '💰', 'description': 'Income support of ₹6000 per year',  'benefit': '₹2000 every 4 months',      'eligibility': 'All landholding farmer families', 'apply_link': 'https://pmkisan.gov.in',          'documents': ['Aadhaar Card', 'Land Records']},
    {'id': 2, 'name': 'PM Fasal Bima Yojana','icon': '🛡️','description': 'Crop insurance scheme',             'benefit': 'Insurance at nominal premium','eligibility': 'All farmers',                    'apply_link': 'https://pmfby.gov.in',            'documents': ['Land Records', 'Bank Account']},
    {'id': 3, 'name': 'Kisan Credit Card',   'icon': '💳', 'description': 'Credit up to ₹3 lakh',             'benefit': 'Low interest loans',           'eligibility': 'All farmers',                    'apply_link': 'https://www.kcc.gov.in',          'documents': ['Aadhaar', 'Land Records']},
    {'id': 4, 'name': 'Soil Health Card',    'icon': '🧪', 'description': 'Free soil testing',                'benefit': 'Fertilizer recommendations',   'eligibility': 'All farmers',                    'apply_link': 'https://soilhealth.dac.gov.in',   'documents': ['Land Records']},
]

# Market Prices
MARKET_PRICES = [
    {'commodity': 'Basmati Rice',  'market': 'Azadpur Mandi', 'state': 'Delhi',       'min': 3500, 'max': 4500, 'modal': 4000},
    {'commodity': 'Common Rice',   'market': 'Azadpur Mandi', 'state': 'Delhi',       'min': 2200, 'max': 2800, 'modal': 2500},
    {'commodity': 'Wheat',         'market': 'Khanna Mandi',  'state': 'Punjab',      'min': 2400, 'max': 2700, 'modal': 2550},
    {'commodity': 'Maize',         'market': 'Gultekdi',      'state': 'Maharashtra', 'min': 1800, 'max': 2100, 'modal': 1950},
    {'commodity': 'Cotton',        'market': 'APMC Gujarat',  'state': 'Gujarat',     'min': 5800, 'max': 6300, 'modal': 6050},
    {'commodity': 'Potato',        'market': 'Azadpur Mandi', 'state': 'Delhi',       'min': 1200, 'max': 1600, 'modal': 1400},
    {'commodity': 'Onion',         'market': 'Azadpur Mandi', 'state': 'Delhi',       'min': 1500, 'max': 2000, 'modal': 1750},
]


# ============================================
# INPUT VALIDATION
# ============================================
def validate_soil_input(data):
    errors = {}
    validated = {}
    for field, rules in VALID_RANGES.items():
        raw = data.get(field)
        if raw is None or str(raw).strip() == '':
            errors[field] = f"{rules['label']} is required."
            continue
        try:
            value = float(raw)
        except (ValueError, TypeError):
            errors[field] = f"{rules['label']} must be a number."
            continue
        if value < rules['min'] or value > rules['max']:
            errors[field] = (
                f"{rules['label']} must be between {rules['min']} and "
                f"{rules['max']} {rules['unit']}. Got: {value}."
            )
        else:
            validated[field] = value
    return (len(errors) == 0), errors, validated


# ============================================
# CLAUDE AI RECOMMENDATION
# ============================================
def get_gemini_recommendation(soil_data):
    api_key = GEMINI_API_KEY or os.environ.get('GEMINI_API_KEY', '')
    
    print(f"🔑 API Key present: {'Yes' if api_key else 'No'}")
    
    if not api_key:
        print("⚠️ No Gemini API key found, using rule-based")
        return get_intelligent_recommendation(soil_data)
    
    n, p, k = soil_data['nitrogen'], soil_data['phosphorus'], soil_data['potassium']
    t, h = soil_data['temperature'], soil_data['humidity']
    ph, r = soil_data['ph'], soil_data['rainfall']
    
    prompt = f"""You are an expert agronomist for Indian farming conditions.
Analyze these soil and climate parameters and recommend the best crops:

- Nitrogen (N): {n} kg/ha
- Phosphorus (P): {p} kg/ha
- Potassium (K): {k} kg/ha
- Temperature: {t}°C
- Humidity: {h}%
- Soil pH: {ph}
- Rainfall: {r} mm/month

Respond ONLY with a valid JSON object (no other text):
{{
  "primary_crop": "<best crop name>",
  "confidence": <0.0 to 1.0>,
  "alternatives": [
    {{"crop": "<name1>", "confidence": 0.85, "icon": "<emoji>"}},
    {{"crop": "<name2>", "confidence": 0.75, "icon": "<emoji>"}},
    {{"crop": "<name3>", "confidence": 0.65, "icon": "<emoji>"}},
    {{"crop": "<name4>", "confidence": 0.55, "icon": "<emoji>"}},
    {{"crop": "<name5>", "confidence": 0.45, "icon": "<emoji>"}}
  ],
  "tips": ["<tip1>", "<tip2>", "<tip3>", "<tip4>"],
  "reasoning": "<2-3 sentence scientific explanation>"
}}"""

    try:
        print("🌐 Calling Gemini API...")
        response = requests.post(
            f"{GEMINI_API_URL}?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 1000,
                    "responseMimeType": "application/json"
                }
            },
            timeout=15
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['candidates'][0]['content']['parts'][0]['text']
            
            # Parse JSON response
            try:
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    recommendation = json.loads(json_match.group())
                else:
                    recommendation = json.loads(content)
                
                recommendation['ai_source'] = 'Gemini AI'
                print("✅ Gemini API response received")
                return recommendation
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")
                return get_intelligent_recommendation(soil_data)
        else:
            print(f"❌ Gemini API error: {response.text}")
            return get_intelligent_recommendation(soil_data)
            
    except Exception as e:
        print(f"❌ Gemini API exception: {e}")
        return get_intelligent_recommendation(soil_data)


# ============================================
# RULE-BASED FALLBACK (Accurate weighted scoring)
# ============================================
def get_intelligent_recommendation(soil_data):
    n, p, k = soil_data['nitrogen'], soil_data['phosphorus'], soil_data['potassium']
    t, h    = soil_data['temperature'], soil_data['humidity']
    ph, r   = soil_data['ph'], soil_data['rainfall']

    def range_score(val, low, high, weight=25):
        if low <= val <= high:
            return weight
        margin = max((high - low) * 0.3, 5)
        if val < low:
            return max(0, weight * (1 - (low - val) / margin))
        return max(0, weight * (1 - (val - high) / margin))

    # (temp_min, temp_max, rain_min, rain_max, ph_min, ph_max,
    #  n_min, n_max, p_min, p_max, k_min, k_max, hum_min, hum_max)
    crop_params = {
        'Rice':      (20,35, 150,500, 5.5,7.5,  80,200,  30, 80,  30, 80,  70,95),
        'Wheat':     (10,25,  25,100, 6.0,7.5,  60,150,  40,100,  40,100,  40,70),
        'Maize':     (18,30,  50,150, 5.5,7.5,  60,140,  35, 75,  35, 80,  50,80),
        'Cotton':    (25,40,  50,100, 6.0,8.0,  50,120,  25, 65,  25, 65,  40,70),
        'Groundnut': (24,33,  35, 90, 6.0,7.0,  30, 80,  30, 75,  25, 65,  45,70),
        'Sugarcane': (20,35, 150,500, 6.0,7.5, 100,250,  25, 60,  25, 60,  65,90),
        'Potato':    (10,25,  30, 75, 5.0,6.5,  60,140,  50,100,  60,120,  60,80),
        'Onion':     (15,30,  25, 65, 6.0,7.0,  40, 90,  35, 80,  40, 80,  40,70),
        'Tomato':    (18,28,  40, 90, 6.0,7.0,  50,110,  45, 90,  40, 85,  50,75),
        'Chickpea':  (10,28,  20, 55, 6.0,8.0,  30, 80,  40, 90,  20, 55,  30,60),
        'Lentil':    (10,25,  20, 50, 6.0,8.0,  25, 70,  35, 85,  20, 55,  35,60),
        'Mustard':   ( 8,25,  20, 50, 6.0,7.5,  40,100,  30, 70,  30, 70,  30,60),
        'Soybean':   (20,30,  50,125, 6.0,7.5,  30, 80,  40, 90,  30, 80,  55,80),
        'Banana':    (26,38, 100,300, 5.5,7.0, 100,200,  30, 80,  30, 80,  70,90),
        'Mango':     (20,35,  50,125, 5.5,7.5,  40, 90,  25, 60,  25, 60,  40,70),
    }
    icons = {
        'Rice':'🌾','Wheat':'🌾','Maize':'🌽','Cotton':'🌿','Groundnut':'🥜',
        'Sugarcane':'🎋','Potato':'🥔','Onion':'🧅','Tomato':'🍅','Chickpea':'🫘',
        'Lentil':'🫘','Mustard':'🌻','Soybean':'🫘','Banana':'🍌','Mango':'🥭'
    }

    crop_scores = {}
    for crop, (tl,th,rl,rh,pl,ph_,nl,nh,phl,phh,kl,kh,hl,hh) in crop_params.items():
        score  = range_score(t,  tl, th,   25)
        score += range_score(r,  rl, rh,   22)
        score += range_score(ph, pl, ph_,  18)
        score += range_score(n,  nl, nh,   12)
        score += range_score(p,  phl, phh, 10)
        score += range_score(k,  kl, kh,   10)
        score += range_score(h,  hl, hh,    8)
        crop_scores[crop] = round(min(score, 97), 1)

    sorted_crops = sorted(crop_scores.items(), key=lambda x: x[1], reverse=True)
    primary_crop, primary_score = sorted_crops[0]
    primary_confidence = round(primary_score / 100, 2)

    alternatives = [
        {'crop': c, 'confidence': round(s / 100, 2), 'icon': icons.get(c, '🌱')}
        for c, s in sorted_crops[1:6]
    ]

    tips_map = {
        'Rice':      ["Maintain 2-5 cm standing water during early growth","Use SRI method to save water","Apply urea in 3 split doses","Monitor for blast and BPH pests"],
        'Wheat':     ["Sow between Nov 1-20 for best yield","Irrigate at crown root initiation stage","Apply nitrogen in 3 splits","Watch for yellow rust disease"],
        'Maize':     ["Ensure well-drained field before sowing","Plant in rows 60 cm apart","Apply zinc sulfate if deficient","Scout for fall armyworm regularly"],
        'Cotton':    ["Use high-density planting for better yield","Apply boron at flowering stage","Monitor for bollworm and whitefly","Avoid waterlogging at any stage"],
        'Groundnut': ["Ensure good drainage to avoid aflatoxin","Apply gypsum at pegging stage","Inoculate seeds with Rhizobium","Harvest before excess moisture"],
        'Sugarcane': ["Use ratoon management for 2nd year crop","Apply trash mulching to conserve moisture","Control early shoot borer","Stagger planting for year-round supply"],
        'Potato':    ["Use certified disease-free seed tubers","Ridge up soil at 30 DAP","Apply fungicide for late blight prevention","Cure harvested potatoes before storage"],
        'Onion':     ["Transplant seedlings 45 days after sowing","Avoid excess nitrogen near harvest","Apply potash to improve bulb quality","Stop irrigation 2 weeks before harvest"],
        'Tomato':    ["Stake or cage plants for support","Apply calcium to prevent blossom end rot","Use drip irrigation for consistency","Rotate crops to prevent soil diseases"],
        'default':   ["Test soil before each season","Use certified seeds from reliable sources","Practice crop rotation every season","Monitor for pests and diseases regularly"],
    }
    tips = tips_map.get(primary_crop, tips_map['default'])
    reasoning = (
        f"With N:{n}, P:{p}, K:{k} kg/ha, pH:{ph}, temperature:{t}°C and rainfall:{r}mm, "
        f"{primary_crop} is the most suitable crop ({primary_confidence*100:.0f}% match). "
        f"The soil chemistry and climate closely align with its ideal growing conditions."
    )

    return {
        'primary_crop': primary_crop,
        'confidence': primary_confidence,
        'alternatives': alternatives,
        'tips': tips,
        'reasoning': reasoning,
        'ai_source': 'Agri-Intelligence AI'
    }


# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/recommend-crop', methods=['POST'])
def recommend_crop():
    try:
        data = request.json or {}

        is_valid, errors, validated = validate_soil_input(data)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': 'Invalid input values. Please check your entries.',
                'validation_errors': errors
            }), 400

        print(f"📊 Processing soil data: {validated}")
        recommendation = get_gemini_recommendation(validated)

        primary_crop = recommendation['primary_crop']
        primary_key  = primary_crop.lower()
        primary_info = None
        for key, info in CROP_INFO.items():
            if key == primary_key or info['name'].lower() == primary_key:
                primary_info = info
                break
        if not primary_info:
            primary_info = {'name': primary_crop, 'icon': '🌱', 'season': 'Contact local agriculture officer', 'water': 'Varies', 'soil': 'Varies', 'temp': 'Varies'}

        recommendations = [
            {'rank': i+1, 'crop': alt['crop'], 'confidence': alt['confidence'], 'icon': alt.get('icon','🌱')}
            for i, alt in enumerate(recommendation.get('alternatives', [])[:5])
        ]

        return jsonify({
            'success': True,
            'ai_source': recommendation.get('ai_source', 'Agri-Intelligence AI'),
            'primary': {
                'crop': primary_info['name'],
                'confidence': recommendation['confidence'],
                'icon': primary_info['icon'],
                'details': {
                    'season': primary_info.get('season','Contact local officer'),
                    'water_requirement': primary_info.get('water','Varies'),
                    'soil_type': primary_info.get('soil','Varies'),
                    'temperature_range': primary_info.get('temp','Varies'),
                    'tips': recommendation.get('tips',[])
                }
            },
            'recommendations': recommendations,
            'reasoning': recommendation.get('reasoning','Based on scientific soil analysis.')
        })

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/weather')
def weather():
    lat = request.args.get('lat', '28.6139')
    lon = request.args.get('lon', '77.2090')
    location_name = "Delhi, India"
    try:
        geo_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        geo_response = requests.get(geo_url, headers={'User-Agent': 'Agrinova'}, timeout=3)
        geo_data = geo_response.json()
        if 'address' in geo_data:
            city  = geo_data['address'].get('city') or geo_data['address'].get('town') or geo_data['address'].get('village')
            state = geo_data['address'].get('state')
            if city and state:
                location_name = f"{city}, {state}"
    except:
        pass
    return jsonify({
        'current': {
            'temperature': random.randint(25, 32),
            'humidity':    random.randint(60, 80),
            'wind_speed':  random.randint(5, 15),
            'condition':   random.choice(['Sunny', 'Partly Cloudy', 'Cloudy', 'Clear']),
            'icon':        random.choice(['☀️', '⛅', '☁️', '☀️']),
            'location':    location_name
        },
        'forecast': [
            {'day': 'Mon', 'max_temp': 32, 'min_temp': 22, 'condition': 'Sunny',         'icon': '☀️'},
            {'day': 'Tue', 'max_temp': 31, 'min_temp': 21, 'condition': 'Partly Cloudy', 'icon': '⛅'},
            {'day': 'Wed', 'max_temp': 30, 'min_temp': 20, 'condition': 'Cloudy',        'icon': '☁️'},
            {'day': 'Thu', 'max_temp': 29, 'min_temp': 19, 'condition': 'Light Rain',    'icon': '🌧️'},
            {'day': 'Fri', 'max_temp': 28, 'min_temp': 18, 'condition': 'Rain',          'icon': '🌧️'},
            {'day': 'Sat', 'max_temp': 29, 'min_temp': 19, 'condition': 'Cloudy',        'icon': '☁️'},
            {'day': 'Sun', 'max_temp': 31, 'min_temp': 21, 'condition': 'Sunny',         'icon': '☀️'},
        ]
    })


@app.route('/api/mandi-prices')
def mandi_prices():
    prices_with_trends = []
    for price in MARKET_PRICES:
        p = price.copy()
        p['trend'] = random.choice(['up', 'down', 'stable'])
        p['change_percent'] = random.randint(1, 8)
        prices_with_trends.append(p)
    return jsonify(prices_with_trends)


@app.route('/api/schemes')
def get_schemes():
    return jsonify(GOVERNMENT_SCHEMES)


@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    data    = request.json
    message = data.get('message', '').lower()
    responses = {
        'hello':  '👋 Namaste! I\'m Agrinova AI. Created by Parth Dahiphale.',
        'hi':     '👋 Namaste! How can I help?',
        'crop':   '🌱 Our AI analyzes soil and climate for accurate recommendations.',
        'weather':'🌤️ Check Weather section for forecasts. Use location for accuracy!',
        'scheme': '🏛️ See Schemes section for government schemes with apply links.',
        'price':  '💰 Market section shows live mandi prices from across India.',
        'soil':   '🧪 Enter N, P, K, pH values for best recommendations.',
        'thank':  '🙏 You\'re welcome! Happy farming!'
    }
    response = "I can help with crops, weather, schemes, and prices. What do you need?"
    for key, value in responses.items():
        if key in message:
            response = value
            break
    return jsonify({'response': response})


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌾 AGRINOVA - AI POWERED FARMING ASSISTANT")
    print("="*60)
    print(f"👤 Created by: Parth Dahiphale")
    api_key = GEMINI_API_KEY or os.environ.get('GEMINI_API_KEY', '')
    print(f"🤖 AI Engine: {'Gemini AI (Free)' if api_key else 'Agri-Intelligence AI (Rule-based)'}")
    print(f"📍 Server: http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, port=5000)


# ============================================
# VERCEL SERVERLESS HANDLER
# ============================================
def handler(event, context):
    """
    Vercel serverless handler for AWS Lambda.
    Converts Lambda event to WSGI and returns Vercel-formatted response.
    """
    from io import BytesIO
    from werkzeug.serving import WSGIRequestHandler
    
    # Build WSGI environ dict
    environ = {
        'REQUEST_METHOD': event.get('httpMethod', 'GET'),
        'SCRIPT_NAME': '',
        'PATH_INFO': event.get('path', '/'),
        'QUERY_STRING': event.get('rawQueryString', ''),
        'CONTENT_TYPE': event.get('headers', {}).get('content-type', ''),
        'CONTENT_LENGTH': event.get('headers', {}).get('content-length', '0'),
        'SERVER_NAME': event.get('headers', {}).get('host', 'localhost'),
        'SERVER_PORT': '443',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': BytesIO(event.get('body', '').encode() if isinstance(event.get('body'), str) else event.get('body', b'')),
        'wsgi.errors': None,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }
    
    # Add headers to environ
    headers = event.get('headers', {})
    for key, value in headers.items():
        key = 'HTTP_' + key.upper().replace('-', '_')
        if key not in ('HTTP_CONTENT_TYPE', 'HTTP_CONTENT_LENGTH'):
            environ[key] = value
    
    # Capture response
    response_data = {'status': '200 OK', 'headers': [], 'body': []}
    
    def start_response(status, response_headers, exc_info=None):
        response_data['status'] = status
        response_data['headers'] = response_headers
        return lambda x: None
    
    # Call Flask WSGI app
    app_iter = app.wsgi_app(environ, start_response)
    
    try:
        for data in app_iter:
            response_data['body'].append(data)
    finally:
        if hasattr(app_iter, 'close'):
            app_iter.close()
    
    # Parse status code
    status_code = int(response_data['status'].split(' ')[0])
    
    # Convert headers to dict
    headers_dict = {}
    for name, value in response_data['headers']:
        headers_dict[name] = value
    
    # Combine body
    body = b''.join(response_data['body'])
    if isinstance(body, bytes):
        body = body.decode('utf-8', errors='replace')
    
    return {
        'statusCode': status_code,
        'headers': headers_dict,
        'body': body,
        'isBase64Encoded': False
    }