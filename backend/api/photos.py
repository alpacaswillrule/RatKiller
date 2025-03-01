import os
import base64
import pandas as pd
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
import random

# Create blueprint
photos_bp = Blueprint('photos', __name__)

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

def save_photo(csv_path, photo_data, photo_path, user_id):
    """Save a new photo to the CSV file and the photo to disk."""
    try:
        # Ensure photos directory exists
        photos_dir = os.path.dirname(photo_path)
        os.makedirs(photos_dir, exist_ok=True)
        
        # Save the photo file
        if photo_data.startswith('data:image'):
            # Extract the base64 data
            header, encoded = photo_data.split(",", 1)
            binary_data = base64.b64decode(encoded)
            
            with open(photo_path, 'wb') as f:
                f.write(binary_data)
        else:
            # Handle other formats if needed
            return None
        
        # Load existing photos
        photos = load_photos(csv_path)
        
        # Generate new ID
        new_id = 1
        if photos:
            new_id = max(p['id'] for p in photos) + 1
        
        # Calculate ELO gained (dummy implementation)
        elo_gained = calculate_elo_gain()
        
        # Create new photo record
        timestamp = datetime.now().isoformat()
        new_photo = {
            'id': new_id,
            'user_id': user_id,
            'timestamp': timestamp,
            'photo_path': photo_path,
            'elo_gained': elo_gained
        }
        
        # Add to DataFrame and save
        photos.append(new_photo)
        df = pd.DataFrame(photos)
        df.to_csv(csv_path, index=False)
        
        return new_photo
    except Exception as e:
        print(f"Error saving photo: {e}")
        return None

def calculate_elo_gain():
    """
    Calculate ELO gain based on timing (dummy implementation).
    In a real app, this would consider the time until garbage pickup.
    """
    # For demo purposes, return a random value between 5 and 50
    return random.randint(5, 50)

def update_user_elo(users_csv, user_id, elo_gained):
    """Update a user's ELO rating."""
    try:
        # Load users
        if not os.path.exists(users_csv):
            return False
        
        df = pd.read_csv(users_csv)
        
        # Find user
        user_idx = df.index[df['id'] == user_id].tolist()
        if not user_idx:
            return False
        
        # Update ELO
        df.at[user_idx[0], 'elo_rating'] += elo_gained
        df.at[user_idx[0], 'disposals_count'] += 1
        
        # Save updated users
        df.to_csv(users_csv, index=False)
        return True
    except Exception as e:
        print(f"Error updating user ELO: {e}")
        return False

@photos_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_photos(user_id):
    """Get photos for a specific user."""
    from app import app
    
    # Load photos
    photos = load_photos(app.config['PHOTOS_CSV'])
    
    # Filter by user ID
    user_photos = [p for p in photos if p['user_id'] == user_id]
    
    # Sort by timestamp (newest first)
    user_photos.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify(user_photos)

@photos_bp.route('/upload', methods=['POST'])
def upload_photo():
    """Upload a new photo."""
    from app import app
    
    if 'photo' not in request.json or 'user_id' not in request.json:
        return jsonify({'error': 'Photo data and user ID are required'}), 400
    
    photo_data = request.json['photo']
    user_id = request.json['user_id']
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"user{user_id}_{timestamp}.jpg"
    photo_path = os.path.join(app.config['PHOTOS_FOLDER'], filename)
    
    # Save photo
    new_photo = save_photo(app.config['PHOTOS_CSV'], photo_data, photo_path, user_id)
    if not new_photo:
        return jsonify({'error': 'Failed to save photo'}), 500
    
    # Update user's ELO
    update_user_elo(app.config['USERS_CSV'], user_id, new_photo['elo_gained'])
    
    return jsonify(new_photo), 201

@photos_bp.route('/elo', methods=['POST'])
def calculate_photo_elo():
    """
    Calculate potential ELO gain for a photo.
    This is a dummy endpoint that simulates ELO calculation.
    """
    # Get time until garbage pickup
    hours_until_pickup = request.json.get('hours_until_pickup', 24)
    
    # Calculate ELO based on timing
    elo_gain = 0
    if hours_until_pickup <= 2:
        elo_gain = random.randint(40, 50)  # Very close to pickup time
    elif hours_until_pickup <= 12:
        elo_gain = random.randint(25, 39)  # Same day
    elif hours_until_pickup <= 24:
        elo_gain = random.randint(10, 24)  # Day before
    else:
        elo_gain = random.randint(5, 9)    # Way too early
    
    return jsonify({
        'elo_gain': elo_gain,
        'hours_until_pickup': hours_until_pickup,
        'message': get_elo_message(hours_until_pickup)
    })

def get_elo_message(hours):
    """Get a message based on timing."""
    if hours <= 2:
        return "Perfect timing! Maximum ELO gained."
    elif hours <= 12:
        return "Good timing! Substantial ELO gained."
    elif hours <= 24:
        return "Decent timing. Moderate ELO gained."
    else:
        return "Too early! Minimal ELO gained."
