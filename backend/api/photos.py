import os
import base64
import pandas as pd
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
import random
import numpy as np
from ultralytics import YOLO
import cv2
import io
from PIL import Image

# Create blueprint
photos_bp = Blueprint('photos', __name__)

# Load YOLOv8 model
model = None

def get_model():
    """Get or initialize the YOLOv8 model."""
    global model
    if model is None:
        try:
            # Use models directory to store the model
            models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
            os.makedirs(models_dir, exist_ok=True)
            model_path = os.path.join(models_dir, 'yolov8x.pt')
            
            # Initialize the model (it will download if not present)
            model = YOLO(model_path)
        except Exception as e:
            print(f"Error loading YOLOv8 model: {e}")
    return model

# Trash-related classes in COCO dataset that YOLOv8 can detect
TRASH_CLASSES = ['bottle', 'cup', 'wine glass', 'fork', 'knife', 'spoon', 
                 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 
                 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 
                 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 
                 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 
                 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 
                 'book', 'clock', 'vase', 'scissors', 'teddy bear', 
                 'hair drier', 'toothbrush', 'backpack', 'umbrella', 
                 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 
                 'sports ball', 'kite', 'baseball bat', 'baseball glove', 
                 'skateboard', 'surfboard', 'tennis racket', 'bag', 'trash', 'trash can', 'garbage bin', 'garbage can','garbage']

def detect_trash(image_path):
    """
    Detect trash in an image using YOLOv8.
    Returns a tuple of (has_trash, detections, annotated_image)
    """
    try:
        model = get_model()
        if model is None:
            return False, [], None
        
        # Run inference
        results = model(image_path)
        
        # Get detections
        detections = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0].item())
                class_name = result.names[class_id]
                
                # Check if the detected object is trash-related
                if class_name in TRASH_CLASSES:
                    confidence = box.conf[0].item()
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    detections.append({
                        'class': class_name,
                        'confidence': confidence,
                        'bbox': [x1, y1, x2, y2]
                    })
        
        # Get annotated image
        annotated_image = results[0].plot() if results else None
        
        # Return results
        has_trash = len(detections) > 0
        return has_trash, detections, annotated_image
    
    except Exception as e:
        print(f"Error detecting trash: {e}")
        return False, [], None

def get_next_tuesday_2pm():
    """Get the datetime of the next Tuesday at 2:00 PM."""
    now = datetime.now()
    days_until_tuesday = (1 - now.weekday()) % 7  # 1 = Tuesday
    if days_until_tuesday == 0 and now.hour >= 14:  # If it's Tuesday after 2 PM
        days_until_tuesday = 7
    
    next_tuesday = now + timedelta(days=days_until_tuesday)
    next_tuesday = next_tuesday.replace(hour=14, minute=0, second=0, microsecond=0)
    
    return next_tuesday

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

def save_photo(csv_path, photo_data, photo_path, user_id, is_violation_report=False, violation_type=None, comment=None, location=None):
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
        
        # Calculate ELO gained with trash detection
        elo_gained = calculate_elo_gain(is_violation_report, violation_type, photo_path)
        
        # Create new photo record
        timestamp = datetime.now().isoformat()
        new_photo = {
            'id': new_id,
            'user_id': user_id,
            'timestamp': timestamp,
            'photo_path': photo_path,
            'elo_gained': elo_gained,
            'is_violation_report': is_violation_report
        }
        
        # Add violation report details if applicable
        if is_violation_report:
            new_photo['violation_type'] = violation_type
            new_photo['comment'] = comment
            new_photo['location'] = location
        
        # Add to DataFrame and save
        photos.append(new_photo)
        df = pd.DataFrame(photos)
        df.to_csv(csv_path, index=False)
        
        return new_photo
    except Exception as e:
        print(f"Error saving photo: {e}")
        return None

def calculate_elo_gain(is_violation_report=False, violation_type=None, photo_path=None):
    """
    Calculate ELO gain based on trash detection and timing until next Tuesday at 2 PM.
    For violation reports, verify trash presence first, then apply violation bonuses.
    """
    # First, detect if there's trash in the image
    has_trash, detections, _ = detect_trash(photo_path) if photo_path else (False, [], None)
    
    if not has_trash:
        # No trash detected, return zero ELO
        return 0
    
    # Calculate base ELO based on time until next Tuesday at 2 PM
    now = datetime.now()
    next_tuesday = get_next_tuesday_2pm()
    time_until_tuesday = (next_tuesday - now).total_seconds() / 3600  # hours
    
    # Calculate base ELO (more ELO for shorter time until Tuesday)
    max_hours = 7 * 24  # Maximum: one week
    time_factor = 1 - min(time_until_tuesday / max_hours, 1)  # 0 to 1
    base_elo = int(40 * time_factor) + 10  # 10 to 50
    
    if is_violation_report:
        # Add bonus for violation reports
        violation_bonus = 0
        if violation_type == 'improper_disposal':
            violation_bonus = random.randint(15, 25)
        elif violation_type == 'unsecured_trash':
            violation_bonus = random.randint(10, 20)
        elif violation_type == 'wrong_day':
            violation_bonus = random.randint(20, 30)
        elif violation_type == 'no_recycling':
            violation_bonus = random.randint(25, 35)
        elif violation_type == 'overflowing':
            violation_bonus = random.randint(5, 15)
        else:  # other or unspecified
            violation_bonus = random.randint(5, 10)
        
        return base_elo + violation_bonus
    else:
        return base_elo

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
    
    # Check if this is a violation report
    is_violation_report = request.json.get('is_violation_report', False)
    violation_type = request.json.get('violation_type')
    comment = request.json.get('comment')
    location = request.json.get('location')
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    prefix = "violation" if is_violation_report else "user"
    filename = f"{prefix}{user_id}_{timestamp}.jpg"
    photo_path = os.path.join(app.config['PHOTOS_FOLDER'], filename)
    
    # Save photo
    new_photo = save_photo(
        app.config['PHOTOS_CSV'], 
        photo_data, 
        photo_path, 
        user_id,
        is_violation_report,
        violation_type,
        comment,
        location
    )
    
    if not new_photo:
        return jsonify({'error': 'Failed to save photo'}), 500
    
    # Update user's ELO
    update_user_elo(app.config['USERS_CSV'], user_id, new_photo['elo_gained'])
    
    return jsonify(new_photo), 201

@photos_bp.route('/elo', methods=['POST'])
def calculate_photo_elo():
    """
    Calculate potential ELO gain for a photo or violation report.
    This is a dummy endpoint that simulates ELO calculation.
    """
    # Check if this is a violation report
    is_violation_report = request.json.get('is_violation_report', False)
    
    # Get photo data if provided
    photo_data = request.json.get('photo')
    photo_path = None
    
    # If photo data is provided, save it temporarily for trash detection
    if photo_data:
        try:
            # Extract the base64 data
            if photo_data.startswith('data:image'):
                header, encoded = photo_data.split(",", 1)
                binary_data = base64.b64decode(encoded)
                
                # Save to a temporary file
                temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
                os.makedirs(temp_dir, exist_ok=True)
                photo_path = os.path.join(temp_dir, f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                
                with open(photo_path, 'wb') as f:
                    f.write(binary_data)
        except Exception as e:
            print(f"Error processing photo data: {e}")
    
    # Detect trash in the image
    has_trash, detections, _ = detect_trash(photo_path) if photo_path else (False, [], None)
    
    # Clean up temporary file
    if photo_path and os.path.exists(photo_path):
        try:
            os.remove(photo_path)
        except:
            pass
    
    if not has_trash:
        return jsonify({
            'elo_gain': 0,
            'has_trash': False,
            'message': "No trash detected in the image. No ELO gained."
        })
    
    if is_violation_report:
        # Get violation type
        violation_type = request.json.get('violation_type', 'other')
        
        # Calculate ELO based on violation type and time until Tuesday
        now = datetime.now()
        next_tuesday = get_next_tuesday_2pm()
        time_until_tuesday = (next_tuesday - now).total_seconds() / 3600  # hours
        
        # Calculate base ELO (more ELO for shorter time until Tuesday)
        max_hours = 7 * 24  # Maximum: one week
        time_factor = 1 - min(time_until_tuesday / max_hours, 1)  # 0 to 1
        base_elo = int(40 * time_factor) + 10  # 10 to 50
        
        # Add violation bonus
        violation_bonus = 0
        if violation_type == 'improper_disposal':
            violation_bonus = random.randint(15, 25)
        elif violation_type == 'unsecured_trash':
            violation_bonus = random.randint(10, 20)
        elif violation_type == 'wrong_day':
            violation_bonus = random.randint(20, 30)
        elif violation_type == 'no_recycling':
            violation_bonus = random.randint(25, 35)
        elif violation_type == 'overflowing':
            violation_bonus = random.randint(5, 15)
        else:  # other or unspecified
            violation_bonus = random.randint(5, 10)
        
        elo_gain = base_elo + violation_bonus
        
        return jsonify({
            'elo_gain': elo_gain,
            'has_trash': True,
            'violation_type': violation_type,
            'time_until_tuesday': round(time_until_tuesday, 1),
            'message': get_violation_message(violation_type)
        })
    else:
        # Calculate ELO based on timing until next Tuesday at 2 PM
        now = datetime.now()
        next_tuesday = get_next_tuesday_2pm()
        time_until_tuesday = (next_tuesday - now).total_seconds() / 3600  # hours
        
        # Calculate ELO (more ELO for shorter time until Tuesday)
        max_hours = 7 * 24  # Maximum: one week
        time_factor = 1 - min(time_until_tuesday / max_hours, 1)  # 0 to 1
        elo_gain = int(40 * time_factor) + 10  # 10 to 50
        
        return jsonify({
            'elo_gain': elo_gain,
            'has_trash': True,
            'time_until_tuesday': round(time_until_tuesday, 1),
            'message': get_elo_message(time_until_tuesday)
        })

@photos_bp.route('/detect-trash', methods=['POST'])
def detect_trash_endpoint():
    """
    Detect trash in an uploaded image and return the results.
    """
    if 'photo' not in request.json:
        return jsonify({'error': 'Photo data is required'}), 400
    
    photo_data = request.json['photo']
    
    try:
        # Extract the base64 data
        if photo_data.startswith('data:image'):
            header, encoded = photo_data.split(",", 1)
            binary_data = base64.b64decode(encoded)
            
            # Save to a temporary file
            temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            photo_path = os.path.join(temp_dir, f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
            
            with open(photo_path, 'wb') as f:
                f.write(binary_data)
            
            # Detect trash
            has_trash, detections, annotated_image = detect_trash(photo_path)
            
            # Convert annotated image to base64 if available
            annotated_image_base64 = None
            if annotated_image is not None:
                # Convert numpy array to PIL Image
                pil_image = Image.fromarray(annotated_image)
                
                # Save to bytes buffer
                buffer = io.BytesIO()
                pil_image.save(buffer, format="JPEG")
                
                # Convert to base64
                annotated_image_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"
            
            # Clean up temporary file
            if os.path.exists(photo_path):
                os.remove(photo_path)
            
            return jsonify({
                'has_trash': has_trash,
                'detections': detections,
                'annotated_image': annotated_image_base64
            })
        else:
            return jsonify({'error': 'Invalid image format'}), 400
    
    except Exception as e:
        return jsonify({'error': f'Error detecting trash: {str(e)}'}), 500

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

def get_violation_message(violation_type):
    """Get a message based on violation type."""
    if violation_type == 'improper_disposal':
        return "Thank you for reporting improper garbage disposal!"
    elif violation_type == 'unsecured_trash':
        return "Unsecured trash can attract rats. Good catch!"
    elif violation_type == 'wrong_day':
        return "Wrong day placement is a common violation. Thanks for reporting!"
    elif violation_type == 'no_recycling':
        return "Recycling is important! Thanks for promoting proper waste separation."
    elif violation_type == 'overflowing':
        return "Overflowing containers are a health hazard. Good job reporting!"
    else:
        return "Thank you for helping keep our city clean!"
