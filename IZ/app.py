from flask import Flask, render_template, request, redirect, session, url_for, flash
import json
import os
from datetime import datetime

# Initialize the Flask app
app = Flask(__name__)
# SECRET KEY is required for 'session' (logging in) to work. 
# It keeps the data safe. In a real app, make this a long random string.
app.secret_key = "my_super_secret_gym_key"

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
DATA_FILE = 'data.json'
USERS_FILE = 'users.json'


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------
def load_data(filename, default):
    """Generic function to read JSON data from a file"""
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except:
        return default

def save_data(filename, data):
    """Generic function to save JSON data to a file"""
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def get_user_meals(username):
    """Get meals ONLY for the specific user"""
    all_meals = load_data(DATA_FILE, [])
    # Filter list: Keep meal only if meal['username'] matches
    user_meals = [m for m in all_meals if m.get('username') == username]
    return user_meals

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

# 1. Homepage (The Dashboard)
@app.route('/')
def index():
    # Check if user is logged in
    if 'username' not in session:
        return redirect(url_for('login')) # Send to login page if not logged in
    
    current_user = session['username']
    
    # Get ONLY this user's meals
    today_meals = get_user_meals(current_user)
    
    total_calories = 0
    total_protein = 0
    
    for meal in today_meals:
        total_calories += int(meal.get('calories', 0))
        total_protein += int(meal.get('protein', 0))
        
    current_date = datetime.now().strftime("%B %d, %Y")

    return render_template('index.html', 
                         meals=today_meals, 
                         total_calories=total_calories, 
                         total_protein=total_protein,
                         date=current_date,
                         username=current_user)

# 2. Add Meal Route
@app.route('/add', methods=['POST'])
def add_meal():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Get form data
    meal_name = request.form.get('meal_name')
    calories = request.form.get('calories')
    protein = request.form.get('protein')
    
    # Create the new meal entry
    new_meal = {
        'username': session['username'], # Attach the username!
        'name': meal_name,
        'calories': calories,
        'protein': protein,
        'time': datetime.now().strftime("%I:%M %p")
    }
    
    # Load ALL meals, add new one, and save back
    all_meals = load_data(DATA_FILE, [])
    all_meals.append(new_meal)
    save_data(DATA_FILE, all_meals)
    
    return redirect('/')

# 3. Reset (Clear only MY data)
@app.route('/reset')
def reset():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    current_user = session['username']
    all_meals = load_data(DATA_FILE, [])
    
    # Keep meals that do NOT belong to this user
    # (i.e., Delete only this user's meals)
    remaining_meals = [m for m in all_meals if m.get('username') != current_user]
    
    save_data(DATA_FILE, remaining_meals)
    return redirect('/')

# ---------------------------------------------------------
# LOGIN SYSTEM ROUTES
# ---------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        users = load_data(USERS_FILE, {})
        
        # Check if user exists and password matches
        if username in users and users[username] == password:
            session['username'] = username # Log them in!
            return redirect('/')
        else:
            return render_template('login.html', error="Invalid username or password")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        users = load_data(USERS_FILE, {})
        
        if username in users:
            return render_template('register.html', error="Username already taken!")
        
        # Add new user
        users[username] = password
        save_data(USERS_FILE, users)
        
        # Log them in automatically
        session['username'] = username
        return redirect('/')
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None) # Remove user from session
    return redirect(url_for('login'))

# Start the server
if __name__ == '__main__':
    # host='0.0.0.0' allows other devices on the same WiFi to connect!
    app.run(debug=True, host='0.0.0.0', port=5002)
