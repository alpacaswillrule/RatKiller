import os
import pandas as pd
from flask import Blueprint, request, jsonify

# Create blueprint
leaderboard_bp = Blueprint('leaderboard', __name__)

def load_users(csv_path):
    """Load users from CSV file."""
    if not os.path.exists(csv_path):
        return []
    
    try:
        df = pd.read_csv(csv_path)
        # Convert DataFrame to list of dictionaries
        users = df.to_dict('records')
        return users
    except Exception as e:
        print(f"Error loading users: {e}")
        return []

def load_photos(csv_path):
    """Load photos from CSV file."""
    if not os.path.exists(csv_path):
        return []
    
    try:
        df = pd.read_csv(csv_path)
        # Convert DataFrame to list of dictionaries
        photos = df.to_dict('records')
        return photos
    except Exception as e:
        print(f"Error loading photos: {e}")
        return []

@leaderboard_bp.route('/', methods=['GET'])
def get_leaderboard():
    """Get leaderboard data."""
    from app import app
    
    # Get time period filter
    period = request.args.get('period', 'alltime')
    
    # Load users and photos
    users = load_users(app.config['USERS_CSV'])
    photos = load_photos(app.config['PHOTOS_CSV'])
    
    # Filter photos by time period if needed
    if period != 'alltime':
        import datetime
        now = datetime.datetime.now()
        
        if period == 'weekly':
            cutoff = now - datetime.timedelta(days=7)
        elif period == 'monthly':
            cutoff = now - datetime.timedelta(days=30)
        else:
            cutoff = now - datetime.timedelta(days=365)
        
        cutoff_str = cutoff.isoformat()
        photos = [p for p in photos if p['timestamp'] >= cutoff_str]
    
    # Calculate leaderboard data
    leaderboard = []
    for user in users:
        user_photos = [p for p in photos if p['user_id'] == user['id']]
        
        # Calculate total ELO gained from photos
        total_elo_gained = sum(p['elo_gained'] for p in user_photos)
        
        # Find best timing (lowest value is best)
        best_timing = user['best_timing'] if user_photos else 0
        
        leaderboard.append({
            'user_id': user['id'],
            'username': user['username'],
            'elo_rating': user['elo_rating'],
            'disposals_count': len(user_photos),
            'best_timing': best_timing,
            'total_elo_gained': total_elo_gained
        })
    
    # Sort by ELO rating (descending)
    leaderboard.sort(key=lambda x: x['elo_rating'], reverse=True)
    
    # Add rank
    for i, entry in enumerate(leaderboard):
        entry['rank'] = i + 1
    
    return jsonify(leaderboard)

@leaderboard_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_rank(user_id):
    """Get a specific user's rank and stats."""
    from app import app
    
    # Get leaderboard
    leaderboard = get_leaderboard().json
    
    # Find user
    user_entry = next((entry for entry in leaderboard if entry['user_id'] == user_id), None)
    
    if not user_entry:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user_entry)
