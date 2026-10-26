from flask import Flask, jsonify, request, render_template, session, redirect, send_file
from flask_cors import CORS
import sqlite3
import os
import pandas as pd
import numpy as np
import json
import re
from datetime import datetime
import requests
from urllib.parse import urlparse
from werkzeug.security import generate_password_hash, check_password_hash
from ml_engine import ml_engine

app = Flask(__name__)
app.secret_key = "supersecretkey123"
CORS(app)

# Database and folder configuration
DATABASE = "users.db"
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Store data in memory
data_store = []
current_crop = None

# Configuration - REPLACE WITH YOUR ACTUAL N8N WEBHOOK URL
N8N_WEBHOOK_URL = "https://sanjas2406.app.n8n.cloud/webhook-test/2699c6a5-f0b8-4bad-9401-6461f69344f4"
# Fallback to local if n8n fails
USE_N8N = True  # Set to False to use local CSV only


# ---------------- DATABASE INIT ----------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()


# ---------------- HOME ROUTE (LOGIN PAGE) ----------------
@app.route("/")
def home():
    # Always show login page, never auto-redirect to dashboard
    return render_template("index.html")   # Always show login page


# ---------------- DASHBOARD PAGE (PROTECTED) ----------------
@app.route("/dashboard")
def dashboard():
    # If not logged in → redirect to login page
    if "user_id" not in session:
        return redirect("/")
    return render_template("dashboard.html", email=session.get("email", ""))


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    first_name = data.get("fName")
    last_name = data.get("lName")
    email = data.get("email")
    password = data.get("password")

    if not all([first_name, last_name, email, password]):
        return jsonify({"success": False})

    hashed_password = generate_password_hash(password)

    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("""
            INSERT INTO users (first_name, last_name, email, password)
            VALUES (?, ?, ?, ?)
        """, (first_name, last_name, email, hashed_password))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except sqlite3.IntegrityError:
        return jsonify({"success": False})


# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()

    if user and check_password_hash(user[4], password):
        session["user_id"] = user[0]
        session["email"] = user[3]
        return jsonify({"success": True})

    return jsonify({"success": False})


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")   # After logout go to login page


# ---------------- AGRICULTURE DASHBOARD API ROUTES ----------------
def load_csv_from_data_folder():
    """Load CSV from data folder in code"""
    print("📂 Loading CSV from data folder...")
    
    csv_paths = [
        'data/agriculture_data.csv',
        'uploads/agriculture_data.csv',
        'agriculture_data.csv',
        'data.csv'
    ]
    
    for csv_path in csv_paths:
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                print(f"✅ Loaded CSV from {csv_path}: {len(df)} records")
                return process_csv_dataframe(df)
            except Exception as e:
                print(f"❌ Error loading {csv_path}: {str(e)}")
    
    print("⚠️ No CSV file found, using sample data from example...")
    return generate_sample_data_from_example()


def process_csv_dataframe(df):
    """Process pandas DataFrame into standardized format"""
    processed_data = []
    
    print(f"🔍 Processing DataFrame with columns: {df.columns.tolist()}")
    print(f"🔍 DataFrame shape: {df.shape}")
    
    # Clean column names
    df.columns = df.columns.str.strip().str.lower()
    
    # Try to fix common column name issues
    column_fixes = {
        'yield_t_pe': 'yield_t_per_ha',
        'price_per': 'price_per_qtl', 
        'profit_per': 'profit_per_ha',
        'yield_t_per': 'yield_t_per_ha',
        'price_qtl': 'price_per_qtl',
        'profit_ha': 'profit_per_ha',
        'yield (t/ha)': 'yield_t_per_ha',
        'price (€/qtl)': 'price_per_qtl',
        'profit (€/ha)': 'profit_per_ha',
        'ucpi score': 'ucpi_score',
        'ai profit score': 'ai_profit_score'
    }
    
    # Apply column name fixes
    for old_name, new_name in column_fixes.items():
        if old_name in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)
    
    # Handle merged columns
    for col in list(df.columns):
        if ' ' in col:
            # Check if it's a merged column like "ucpi_score ai_profit_score"
            if 'ucpi' in col.lower() and 'ai' in col.lower() and 'profit' in col.lower():
                print(f"⚠️ Found potentially merged column: {col}")
                # Try to extract the first value
                try:
                    # Create a copy of the column and split
                    temp_series = df[col].astype(str).str.split().str[0]
                    # Extract numeric value
                    df['ucpi_score'] = temp_series.str.extract(r'(\d+\.?\d*)').astype(float)
                    print(f"✅ Extracted ucpi_score from merged column")
                except:
                    pass
    
    # Enhanced column mapping for different CSV formats
    column_mapping = {
        'crop': ['crop', 'crop_name', 'cropname', 'crop type', 'crop_type'],
        'state': ['state', 'state_name', 'statename', 'state name', 'region'],
        'season': ['season', 'session', 'crop_season', 'season_name', 'period'],
        'yield_t_per_ha': ['yield_t_per_ha', 'yield', 'yield_per_ha', 'yield_ha', 'yield (t/ha)', 'yield_t/ha', 'yield_t_per', 'yieldtperha', 'yield_t_pe'],
        'price_per_qtl': ['price_per_qtl', 'price', 'price_qtl', 'price_per_unit', 'price (rs/qtl)', 'price/qtl', 'priceperqtl', 'price_per', 'price (€/qtl)'],
        'profit_per_ha': ['profit_per_ha', 'profit', 'profit_ha', 'profit_per_hectare', 'profit (rs/ha)', 'profit/ha', 'profitperha', 'profit_per', 'profit (€/ha)'],
        'ucpi_score': ['ucpi_score', 'ucpi', 'score', 'ucpi_rating', 'ucpi score', 'rating'],
        'ai_profit_score': ['ai_profit_score', 'ai_profit', 'ai_score', 'ai_rating', 'ai profit score', 'ai_score', 'aiprofit', 'ai profit', 'al_profit_score']
    }
    
    # Create reverse mapping
    reverse_mapping = {}
    for target_col, possible_names in column_mapping.items():
        for name in possible_names:
            reverse_mapping[name] = target_col
    
    # Process each row
    for index, row in df.iterrows():
        try:
            item = {}
            
            # Map columns
            for col in df.columns:
                col_lower = col.lower().strip()
                if col_lower in reverse_mapping:
                    target_field = reverse_mapping[col_lower]
                    value = row[col]
                    
                    # Handle NaN values
                    if pd.isna(value):
                        if target_field in ['yield_t_per_ha', 'price_per_qtl', 'profit_per_ha', 'ucpi_score', 'ai_profit_score']:
                            value = 0.0
                        else:
                            value = ''
                    
                    # Convert numeric fields
                    if target_field in ['yield_t_per_ha', 'price_per_qtl', 'profit_per_ha', 'ucpi_score', 'ai_profit_score']:
                        try:
                            if isinstance(value, str):
                                # Remove currency symbols and non-numeric except decimal point
                                value = str(value).replace('₹', '').replace('€', '').replace('$', '').replace(',', '')
                                value = re.sub(r'[^\d.-]', '', value)
                                if value == '' or value == '-':
                                    value = '0'
                            value = float(value) if value else 0.0
                        except Exception as e:
                            print(f"⚠️ Error converting '{value}' to float for {target_field}: {e}")
                            value = 0.0
                        item[target_field] = value
                    else:
                        item[target_field] = str(value).strip() if value else ''
            
            # Calculate profit if missing but yield and price exist
            if ('profit_per_ha' not in item or item.get('profit_per_ha', 0) == 0) and \
               'yield_t_per_ha' in item and 'price_per_qtl' in item:
                try:
                    yield_val = item.get('yield_t_per_ha', 0)
                    price_val = item.get('price_per_qtl', 0)
                    
                    if isinstance(yield_val, str):
                        yield_val = float(re.sub(r'[^\d.-]', '', yield_val)) if yield_val else 0
                    if isinstance(price_val, str):
                        price_val = float(re.sub(r'[^\d.-]', '', price_val)) if price_val else 0
                    
                    if yield_val > 0 and price_val > 0:
                        calculated_profit = yield_val * price_val * 10
                        item['profit_per_ha'] = round(calculated_profit, 2)
                except:
                    item['profit_per_ha'] = 0.0
            
            # Ensure all required fields exist
            required_fields = ['crop', 'state', 'season', 'yield_t_per_ha', 'price_per_qtl', 'profit_per_ha', 'ucpi_score', 'ai_profit_score']
            for field in required_fields:
                if field not in item:
                    if field in ['yield_t_per_ha', 'price_per_qtl', 'profit_per_ha', 'ucpi_score', 'ai_profit_score']:
                        item[field] = 0.0
                    else:
                        item[field] = ''
            
            # Only add if we have crop and state
            if item['crop'] and item['state']:
                item['id'] = len(processed_data) + 1
                processed_data.append(item)
                
        except Exception as e:
            print(f"⚠️ Error processing row {index}: {str(e)}")
            continue
    
    print(f"✅ Successfully processed {len(processed_data)} records")
    
    # Show some statistics
    if processed_data:
        crop_counts = {}
        for item in processed_data:
            crop = item['crop']
            crop_counts[crop] = crop_counts.get(crop, 0) + 1
        
        print(f"📊 Crop distribution: {crop_counts}")
    
    return processed_data


def generate_sample_data_from_example():
    """Generate sample data based on the provided example structure"""
    # Based on the example data structure from images
    example_data = []
    
    # Example crops from the dataset
    crops = ['Rice', 'Onion', 'Potato', 'Maize', 'Cucumber', 'Wheat', 'Chili', 'Tomato']
    states = ['Odisha', 'Madhya Pradesh', 'Tamil Nadu', 'Bihar', 'Rajasthan', 'Punjab', 
              'Karnataka', 'Uttar Pradesh', 'West Bengal', 'Assam', 'Kerala', 'Gujarat',
              'Maharashtra', 'Telangana', 'Andhra Pradesh', 'Haryana']
    seasons = ['Kharif', 'Rabi', 'Zaid']
    
    # Generate 3000 sample records
    record_id = 1
    for _ in range(3000):
        crop = np.random.choice(crops)
        state = np.random.choice(states)
        season = np.random.choice(seasons)
        
        # Crop-specific parameters based on example data
        if crop == 'Rice':
            yield_val = round(np.random.uniform(3.0, 5.0), 2)
            price_val = round(np.random.uniform(2000, 3000), 2)
            profit_val = yield_val * price_val * 10  # Calculate profit
            ucpi_val = round(np.random.uniform(70, 80), 2)
            ai_val = round(profit_val * np.random.uniform(0.3, 0.7), 2)
        elif crop == 'Onion':
            yield_val = round(np.random.uniform(15, 30), 2)
            price_val = round(np.random.uniform(800, 1200), 2)
            profit_val = yield_val * price_val * 10
            ucpi_val = round(np.random.uniform(35, 65), 2)
            ai_val = round(profit_val * np.random.uniform(0.2, 0.6), 2)
        elif crop == 'Potato':
            yield_val = round(np.random.uniform(15, 30), 2)
            price_val = round(np.random.uniform(500, 800), 2)
            profit_val = yield_val * price_val * 10
            ucpi_val = round(np.random.uniform(50, 70), 2)
            ai_val = round(profit_val * np.random.uniform(0.3, 0.6), 2)
        elif crop == 'Wheat':
            yield_val = round(np.random.uniform(3.5, 5.0), 2)
            price_val = round(np.random.uniform(1800, 2600), 2)
            profit_val = yield_val * price_val * 10
            ucpi_val = round(np.random.uniform(60, 80), 2)
            ai_val = round(profit_val * np.random.uniform(0.4, 0.7), 2)
        elif crop == 'Tomato':
            yield_val = round(np.random.uniform(25, 55), 2)
            price_val = round(np.random.uniform(800, 1500), 2)
            profit_val = yield_val * price_val * 10
            ucpi_val = round(np.random.uniform(50, 70), 2)
            ai_val = round(profit_val * np.random.uniform(0.3, 0.5), 2)
        elif crop == 'Chili':
            yield_val = round(np.random.uniform(2.0, 3.0), 2)
            price_val = round(np.random.uniform(3000, 5000), 2)
            profit_val = yield_val * price_val * 10
            ucpi_val = round(np.random.uniform(70, 85), 2)
            ai_val = round(profit_val * np.random.uniform(0.4, 0.8), 2)
        else:
            yield_val = round(np.random.uniform(5, 40), 2)
            price_val = round(np.random.uniform(500, 2000), 2)
            profit_val = yield_val * price_val * 10
            ucpi_val = round(np.random.uniform(50, 75), 2)
            ai_val = round(profit_val * np.random.uniform(0.3, 0.6), 2)
        
        example_data.append({
            'id': record_id,
            'crop': crop,
            'state': state,
            'season': season,
            'yield_t_per_ha': yield_val,
            'price_per_qtl': price_val,
            'profit_per_ha': round(profit_val, 2),
            'ucpi_score': ucpi_val,
            'ai_profit_score': round(ai_val, 2)
        })
        record_id += 1
    
    print(f"📊 Generated {len(example_data)} sample records")
    return example_data


# Load data on startup
data_store = load_csv_from_data_folder()


@app.route('/fetch-n8n-data', methods=['POST'])
def fetch_n8n_data():
    """Fetch data from n8n or use local data"""
    global data_store, current_crop
    
    # Check if user is logged in for API access
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first",
            "redirect": "/"
        })
    
    try:
        data = request.json
        crop_name = data.get('crop', '').strip()
        state_filter = data.get('state', '').strip()
        season_filter = data.get('season', '').strip()
        
        print(f"🌱 Searching for crop: {crop_name}")
        current_crop = crop_name
        
        # Try n8n first if enabled
        n8n_data = None
        if USE_N8N and N8N_WEBHOOK_URL and crop_name:
            try:
                print(f"🔗 Calling n8n webhook for crop: {crop_name}")
                payload = {
                    "crop": crop_name,
                    "state": state_filter,
                    "season": season_filter,
                    "timestamp": datetime.now().isoformat()
                }
                
                response = requests.post(
                    N8N_WEBHOOK_URL,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    n8n_data = response.json()
                    print(f"✅ Received data from n8n: {len(n8n_data) if isinstance(n8n_data, list) else 'unknown'}")
                    
                    # Process n8n response
                    if isinstance(n8n_data, list):
                        processed_n8n = []
                        for item in n8n_data:
                            processed_item = {
                                'id': len(processed_n8n) + 1,
                                'crop': str(item.get('crop', item.get('Crop', crop_name))).strip(),
                                'state': str(item.get('state', item.get('State', ''))).strip(),
                                'season': str(item.get('season', item.get('Season', ''))).strip(),
                                'yield_t_per_ha': float(item.get('yield_t_per_ha', item.get('yield', 0))),
                                'price_per_qtl': float(item.get('price_per_qtl', item.get('price', 0))),
                                'profit_per_ha': float(item.get('profit_per_ha', item.get('profit', 0))),
                                'ucpi_score': float(item.get('ucpi_score', item.get('ucpi', 0))),
                                'ai_profit_score': float(item.get('ai_profit_score', item.get('ai_profit', 0)))
                            }
                            processed_n8n.append(processed_item)
                        
                        if processed_n8n:
                            # IMPORTANT: For n8n, we use ONLY the data returned by n8n
                            filtered_data = processed_n8n
                            source = "n8n"
                            print(f"🔄 Using {len(processed_n8n)} records from n8n for {crop_name}")
                        else:
                            # If n8n returned empty, fall back to local
                            print("⚠️ n8n returned empty data, falling back to local")
                            n8n_data = None
                else:
                    print(f"❌ n8n returned status {response.status_code}")
                    n8n_data = None
                    
            except Exception as n8n_error:
                print(f"⚠️ n8n error: {str(n8n_error)}")
                n8n_data = None
        
        # If n8n didn't provide data, use local data
        if n8n_data is None:
            print("🔄 Using local data store")
            source = "local"
            
            # Filter data based on criteria from local data store
            filtered_data = []
            
            if crop_name:
                # Find EXACT crop name matches first
                exact_matches = [item for item in data_store 
                               if item['crop'].lower() == crop_name.lower()]
                
                if exact_matches:
                    filtered_data = exact_matches
                    print(f"✅ Found {len(exact_matches)} exact matches for {crop_name}")
                else:
                    # If no exact matches, find partial matches
                    filtered_data = [item for item in data_store 
                                   if crop_name.lower() in item['crop'].lower()]
                    print(f"✅ Found {len(filtered_data)} partial matches for {crop_name}")
            else:
                filtered_data = data_store.copy()
        
        # Apply state and season filters if provided
        if state_filter:
            filtered_data = [item for item in filtered_data 
                           if state_filter.lower() in item['state'].lower()]
        
        if season_filter:
            filtered_data = [item for item in filtered_data 
                           if season_filter.lower() == item['season'].lower()]
        
        if not filtered_data:
            return jsonify({
                "success": False,
                "message": f"No data found for crop: {crop_name}",
                "source": source
            })
        
        print(f"📊 Final filtered data: {len(filtered_data)} records")
        
        # Calculate statistics
        stats = calculate_statistics(filtered_data)
        
        # Get top 5 states by profit
        top_states_data = get_top_states_by_profit(filtered_data)
        
        # Prepare chart data
        chart_data = prepare_chart_data(filtered_data, top_states_data)
        
        return jsonify({
            "success": True,
            "message": f"Found {len(filtered_data)} records for {crop_name}",
            "source": source,
            "data": filtered_data,
            "stats": stats,
            "top_states": top_states_data,
            "charts": chart_data,
            "total_records": len(filtered_data)
        })
        
    except Exception as e:
        print(f"❌ Error in fetch_n8n_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": str(e),
            "source": "error"
        })


def calculate_statistics(data):
    """Calculate statistics for the data"""
    if not data:
        return {}
    
    profits = [item['profit_per_ha'] for item in data]
    ucpi_scores = [item['ucpi_score'] for item in data]
    ai_scores = [item['ai_profit_score'] for item in data]
    yields = [item['yield_t_per_ha'] for item in data]
    prices = [item['price_per_qtl'] for item in data]
    
    # Get crop name from first item
    crop_name = data[0]['crop'] if data else "Unknown"
    
    return {
        'total_records': len(data),
        'crop_name': crop_name,
        'unique_states': len(set([item['state'] for item in data])),
        'unique_seasons': len(set([item['season'] for item in data])),
        'avg_profit': round(np.mean(profits) if profits else 0, 2),
        'max_profit': round(max(profits) if profits else 0, 2),
        'min_profit': round(min(profits) if profits else 0, 2),
        'avg_ucpi': round(np.mean(ucpi_scores) if ucpi_scores else 0, 2),
        'avg_ai_score': round(np.mean(ai_scores) if ai_scores else 0, 2),
        'avg_yield': round(np.mean(yields) if yields else 0, 2),
        'avg_price': round(np.mean(prices) if prices else 0, 2)
    }


def get_top_states_by_profit(data):
    """Get top 5 states by profit for the given crop data"""
    if not data:
        return []
    
    # Group by state and calculate average profit
    state_profits = {}
    for item in data:
        state = item['state']
        if state not in state_profits:
            state_profits[state] = []
        state_profits[state].append(item['profit_per_ha'])
    
    # Calculate average profit per state
    state_avg_profits = []
    for state, profits in state_profits.items():
        if profits:
            avg_profit = sum(profits) / len(profits)
            state_avg_profits.append({
                'state': state,
                'avg_profit': round(avg_profit, 2),
                'record_count': len(profits),
                'max_profit': round(max(profits), 2),
                'min_profit': round(min(profits), 2)
            })
    
    # Sort by average profit (descending) and take top 5
    state_avg_profits.sort(key=lambda x: x['avg_profit'], reverse=True)
    return state_avg_profits[:5]


def prepare_chart_data(full_data, top_states):
    """Prepare data for charts based on the full dataset and top states"""
    if not top_states:
        return {
            'profit_chart': {'labels': [], 'datasets': []},
            'ucpi_chart': {'labels': [], 'datasets': []},
            'ai_chart': {'labels': [], 'datasets': []}
        }
    
    # Profit chart - use top states data
    profit_labels = [state['state'] for state in top_states]
    profit_data = [state['avg_profit'] for state in top_states]
    
    # Generate colors
    colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
    
    profit_chart = {
        'labels': profit_labels,
        'datasets': [{
            'label': 'Average Profit (₹/ha)',
            'data': profit_data,
            'backgroundColor': colors[:len(top_states)],
            'borderColor': '#fff',
            'borderWidth': 2
        }]
    }
    
    # For UCPI and AI charts - calculate actual averages from full data
    ucpi_data = []
    ai_data = []
    
    for state_info in top_states:
        state_name = state_info['state']
        # Get all records for this state
        state_records = [item for item in full_data if item['state'] == state_name]
        
        if state_records:
            avg_ucpi = sum([item['ucpi_score'] for item in state_records]) / len(state_records)
            avg_ai = sum([item['ai_profit_score'] for item in state_records]) / len(state_records)
            ucpi_data.append(round(avg_ucpi, 2))
            ai_data.append(round(avg_ai, 2))
        else:
            ucpi_data.append(0)
            ai_data.append(0)
    
    ucpi_chart = {
        'labels': profit_labels,
        'datasets': [{
            'label': 'UCPI Score',
            'data': ucpi_data,
            'backgroundColor': '#FF9F40',
            'borderColor': '#FF7F00',
            'borderWidth': 2
        }]
    }
    
    ai_chart = {
        'labels': profit_labels,
        'datasets': [{
            'label': 'AI Profit Score',
            'data': ai_data,
            'backgroundColor': '#8AC926',
            'borderColor': '#6BA01E',
            'borderWidth': 2
        }]
    }
    
    return {
        'profit_chart': profit_chart,
        'ucpi_chart': ucpi_chart,
        'ai_chart': ai_chart
    }


@app.route('/get-crop-suggestions', methods=['POST'])
def get_crop_suggestions():
    """Get crop suggestions for autocomplete"""
    # Check if user is logged in for API access
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "suggestions": []
        })
    
    try:
        data = request.json
        search_term = data.get('search', '').strip().lower()
        
        if not data_store:
            return jsonify({
                "success": True,
                "suggestions": []
            })
        
        # Get unique crops from data store
        all_crops = sorted(list(set([item['crop'] for item in data_store])))
        
        # Filter based on search term
        if search_term:
            suggestions = [crop for crop in all_crops 
                          if search_term in crop.lower()]
        else:
            suggestions = all_crops[:10]
        
        return jsonify({
            "success": True,
            "suggestions": suggestions[:10]
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "suggestions": []
        })


@app.route('/reload-data', methods=['POST'])
def reload_data():
    """Reload data from CSV"""
    # Check if user is logged in for API access
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first"
        })
    
    global data_store
    data_store = load_csv_from_data_folder()
    
    stats = calculate_statistics(data_store)
    
    return jsonify({
        "success": True,
        "message": f"Reloaded {len(data_store)} records from CSV",
        "stats": stats
    })


@app.route('/update-n8n-config', methods=['POST'])
def update_n8n_config():
    """Update n8n configuration"""
    # Check if user is logged in for API access
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first"
        })
    
    global N8N_WEBHOOK_URL, USE_N8N
    
    try:
        data = request.json
        N8N_WEBHOOK_URL = data.get('webhook_url', N8N_WEBHOOK_URL)
        USE_N8N = data.get('use_n8n', USE_N8N)
        
        return jsonify({
            "success": True,
            "message": "n8n configuration updated",
            "config": {
                "webhook_url": N8N_WEBHOOK_URL,
                "use_n8n": USE_N8N
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })


# ---------------- ADDITIONAL PAGE ROUTES ----------------
@app.route('/cam.html')
def cam_page():
    """Live monitoring page"""
    # Check if user is logged in
    if "user_id" not in session:
        return redirect("/")
    return render_template('cam.html')

@app.route('/farmers_dataset_1000.xlsx')
def serve_farmers_data():
    """Serve the farmers dataset Excel file"""
    try:
        # Check if file exists in templates folder
        file_path = os.path.join('templates', 'farmers_dataset_1000.xlsx')
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=False)
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add this import at the top
from flask import send_file
@app.route('/1.html')
def tamper_detection_page():
    """Tamper detection page - 1.html"""
    # Check if user is logged in
    if "user_id" not in session:
        return redirect("/")
    return render_template('1.html')


@app.route('/get-system-status', methods=['GET'])
def get_system_status():
    """Get system status and configuration"""
    # Check if user is logged in for API access
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first"
        })
    
    # Calculate crop distribution
    crop_distribution = {}
    for item in data_store:
        crop = item['crop']
        crop_distribution[crop] = crop_distribution.get(crop, 0) + 1
    
    return jsonify({
        "success": True,
        "status": {
            "data_records": len(data_store),
            "n8n_enabled": USE_N8N,
            "n8n_configured": bool(N8N_WEBHOOK_URL),
            "unique_crops": len(set([item['crop'] for item in data_store])),
            "unique_states": len(set([item['state'] for item in data_store])),
            "crop_distribution": crop_distribution,
            "current_crop": current_crop,
            "timestamp": datetime.now().isoformat()
        }
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint (public)"""
    return jsonify({
        "status": "healthy",
        "service": "Agriculture Dashboard",
        "version": "3.0",
        "data_source": "n8n" if USE_N8N else "local_csv",
        "records_loaded": len(data_store),
        "unique_crops": len(set([item['crop'] for item in data_store])),
        "timestamp": datetime.now().isoformat()
    })


# ---------------- MACHINE LEARNING API ROUTES ----------------
@app.route('/api/ml/metrics', methods=['GET'])
def get_ml_metrics():
    """Get ML model evaluation metrics, clusters, and PCA projections"""
    try:
        data = ml_engine.get_dashboard_payload()
        return jsonify(data)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/ml/predict', methods=['POST'])
def predict_ml():
    """Predict crop profit across Linear Regression, Decision Tree, and Random Forest models"""
    try:
        req = request.get_json() or {}
        crop = req.get('crop', 'Rice')
        state = req.get('state', 'Odisha')
        season = req.get('season', 'Kharif')
        yield_val = float(req.get('yield_t_per_ha', 15.0))
        price_val = float(req.get('price_per_qtl', 1500.0))
        ucpi_val = float(req.get('ucpi_score', 65.0))

        result = ml_engine.predict_profit(
            crop=crop,
            state=state,
            season=season,
            yield_val=yield_val,
            price_val=price_val,
            ucpi_val=ucpi_val
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/ml/recommend', methods=['POST'])
def recommend_crop():
    """Recommend best crops based on state, season, yield and price targets"""
    try:
        req = request.get_json() or {}
        state = req.get('state', 'Odisha')
        season = req.get('season', 'Kharif')
        target_yield = float(req.get('yield_t_per_ha', 15.0))
        expected_price = float(req.get('price_per_qtl', 1500.0))

        result = ml_engine.recommend_crop(
            state=state,
            season=season,
            target_yield=target_yield,
            expected_price=expected_price
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/ml/clustering', methods=['GET'])
def get_ml_clustering():
    """Get K-Means cluster profiles and PCA coordinates for scatter plotting"""
    try:
        payload = ml_engine.get_dashboard_payload()
        return jsonify({
            "success": True,
            "clusters": payload["clusters"],
            "pca_variance_ratio": payload["pca_variance_ratio"],
            "pca_points": payload["pca_points"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/download-ml-report', methods=['GET'])
def download_ml_report():
    """Download the comprehensive Machine Learning Word document"""
    doc_path = os.path.join(os.path.dirname(__file__), "VELAAN_AI_Machine_Learning_Report.docx")
    if os.path.exists(doc_path):
        return send_file(doc_path, as_attachment=True, download_name="VELAAN_AI_Machine_Learning_Report.docx")
    return jsonify({"error": "Report not found"}), 404


if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    
    # Initialize database
    init_db()
    
    print("=" * 80)
    print("🌾 AGRICULTURE DASHBOARD - COMPLETE SOLUTION WITH LOGIN")
    print("=" * 80)
    print("📊 Data Status:")
    print(f"   ✅ Total Records Loaded: {len(data_store)}")
    
    # Show crop distribution
    crop_counts = {}
    for item in data_store:
        crop = item['crop']
        crop_counts[crop] = crop_counts.get(crop, 0) + 1
    
    print(f"   🌱 Unique Crops: {len(crop_counts)}")
    print(f"   📍 Unique States: {len(set([item['state'] for item in data_store]))}")
    
    print("=" * 80)
    print("✨ Features:")
    print("   ✅ User Authentication (Login/Signup)")
    print("   ✅ Protected Dashboard - requires login")
    print("   ✅ Search ANY crop from 3000+ records")
    print("   ✅ Shows ALL records for selected crop")
    print("   ✅ Top 5 States calculation from actual data")
    print("   ✅ Real-time n8n integration")
    print("   ✅ Interactive charts based on actual crop data")
    print("   ✅ Live Monitoring page (/cam.html)")
    print("   ✅ Tamper Detection page (/block.html)")
    print("=" * 80)
    print("🚀 Starting server...")
    print(f"🌐 Login Page: http://localhost:5000")
    print(f"📊 Dashboard (protected): http://localhost:5000/dashboard")
    print(f"🎥 Live Monitoring: http://localhost:5000/cam.html")
    print(f"🛡️ Tamper Detection: http://localhost:8000/block.html")
    print(f"📊 Health check: http://localhost:5000/health")
    print("=" * 80)
    
    app.run(debug=True, port=5000, host='0.0.0.0')