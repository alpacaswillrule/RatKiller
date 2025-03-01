import os
import csv
import json
from datetime import datetime
import pandas as pd
from flask import Blueprint, request, jsonify

# Create blueprint
chat_bp = Blueprint('chat', __name__)

def load_chat_history(csv_path):
    """Load chat history from CSV file."""
    if not os.path.exists(csv_path):
        return []
    
    try:
        df = pd.read_csv(csv_path)
        # Convert DataFrame to list of dictionaries
        chat_history = df.to_dict('records')
        return chat_history
    except Exception as e:
        print(f"Error loading chat history: {e}")
        return []

def save_message(csv_path, message_data):
    """Save a new message to the CSV file."""
    try:
        # Load existing messages
        messages = load_chat_history(csv_path)
        
        # Generate new ID
        new_id = 1
        if messages:
            new_id = max(msg['id'] for msg in messages) + 1
        
        # Create new message
        new_message = {
            'id': new_id,
            'user_id': message_data.get('user_id', 0),
            'message': message_data.get('message', ''),
            'timestamp': message_data.get('timestamp', datetime.now().isoformat()),
            'is_system_message': message_data.get('is_system_message', 0)
        }
        
        # Add to DataFrame and save
        messages.append(new_message)
        df = pd.DataFrame(messages)
        df.to_csv(csv_path, index=False)
        
        return new_message
    except Exception as e:
        print(f"Error saving message: {e}")
        return None

@chat_bp.route('/messages', methods=['GET'])
def get_messages():
    """Get all chat messages."""
    from app import app
    chat_history = load_chat_history(app.config['CHAT_HISTORY_CSV'])
    return jsonify(chat_history)

@chat_bp.route('/messages', methods=['POST'])
def add_message():
    """Add a new chat message."""
    from app import app
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Message content is required'}), 400
    
    # Save user message
    user_message = {
        'user_id': data.get('user_id', 1),  # Default to user 1 if not specified
        'message': data['message'],
        'timestamp': datetime.now().isoformat(),
        'is_system_message': 0
    }
    
    saved_message = save_message(app.config['CHAT_HISTORY_CSV'], user_message)
    if not saved_message:
        return jsonify({'error': 'Failed to save message'}), 500
    
    # Generate system response (in a real app, this would be more sophisticated)
    system_responses = [
        "Thank you for your message. A city representative will respond shortly.",
        "Your report has been logged. We'll investigate this issue.",
        "Thanks for helping keep our community clean!",
        "We've received your message and will follow up soon."
    ]
    
    import random
    system_message = {
        'user_id': 0,  # System user ID is 0
        'message': random.choice(system_responses),
        'timestamp': datetime.now().isoformat(),
        'is_system_message': 1
    }
    
    saved_response = save_message(app.config['CHAT_HISTORY_CSV'], system_message)
    
    return jsonify({
        'user_message': saved_message,
        'system_response': saved_response
    })
