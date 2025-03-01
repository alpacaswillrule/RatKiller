from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os

# Import configuration
import config

# Import API modules
from api.chat import chat_bp
from api.leaderboard import leaderboard_bp
from api.friends import friends_bp
from api.photos import photos_bp

# Create Flask app
app = Flask(__name__)

# Load configuration
app.config.from_object(config)

# Enable CORS
CORS(app)

# Register blueprints
app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(leaderboard_bp, url_prefix='/api/leaderboard')
app.register_blueprint(friends_bp, url_prefix='/api/friends')
app.register_blueprint(photos_bp, url_prefix='/api/photos')

# Ensure directories exist
os.makedirs(app.config['DATA_DIR'], exist_ok=True)
os.makedirs(app.config['PHOTOS_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    """API root endpoint."""
    return jsonify({
        'name': 'Rat Reporter API',
        'version': '1.0.0',
        'endpoints': [
            '/api/chat/messages',
            '/api/leaderboard',
            '/api/friends/user/<user_id>',
            '/api/photos/user/<user_id>'
        ]
    })

@app.route('/api/user/<int:user_id>')
def get_user(user_id):
    """Get user information."""
    import pandas as pd
    
    # Load users
    if not os.path.exists(app.config['USERS_CSV']):
        return jsonify({'error': 'User not found'}), 404
    
    df = pd.read_csv(app.config['USERS_CSV'])
    user = df[df['id'] == user_id]
    
    if user.empty:
        return jsonify({'error': 'User not found'}), 404
    
    # Convert to dictionary
    user_data = user.iloc[0].to_dict()
    
    return jsonify(user_data)

@app.route('/api/user/<int:user_id>/elo', methods=['PUT'])
def update_user_elo(user_id):
    """Update a user's ELO rating."""
    import pandas as pd
    
    data = request.get_json()
    if not data or 'elo_change' not in data:
        return jsonify({'error': 'ELO change value is required'}), 400
    
    elo_change = data['elo_change']
    
    # Load users
    if not os.path.exists(app.config['USERS_CSV']):
        return jsonify({'error': 'User not found'}), 404
    
    df = pd.read_csv(app.config['USERS_CSV'])
    user_idx = df.index[df['id'] == user_id].tolist()
    
    if not user_idx:
        return jsonify({'error': 'User not found'}), 404
    
    # Update ELO
    df.at[user_idx[0], 'elo_rating'] += elo_change
    
    # Save updated users
    df.to_csv(app.config['USERS_CSV'], index=False)
    
    # Return updated user data
    user_data = df.iloc[user_idx[0]].to_dict()
    
    return jsonify(user_data)

@app.route('/api/photos/<path:filename>')
def get_photo(filename):
    """Serve photo files."""
    return send_from_directory(app.config['PHOTOS_FOLDER'], filename)

@app.route('/api/garbage-time')
def get_garbage_time():
    """Get time until next garbage pickup."""
    import datetime
    
    now = datetime.datetime.now()
    
    # Find next Tuesday
    days_until_tuesday = (1 - now.weekday()) % 7
    if days_until_tuesday == 0 and now.hour >= 13:  # If it's Tuesday after 1 PM
        days_until_tuesday = 7
    
    next_tuesday = now + datetime.timedelta(days=days_until_tuesday)
    next_pickup = datetime.datetime(
        next_tuesday.year,
        next_tuesday.month,
        next_tuesday.day,
        13, 0, 0  # 1 PM
    )
    
    # Calculate hours until pickup
    time_diff = next_pickup - now
    hours_until_pickup = time_diff.total_seconds() / 3600
    
    return jsonify({
        'next_pickup': next_pickup.isoformat(),
        'hours_until_pickup': round(hours_until_pickup, 1)
    })

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
