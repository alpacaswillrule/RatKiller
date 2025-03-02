import os
import csv
import json
from datetime import datetime
import pandas as pd
from flask import Blueprint, request, jsonify

# Use the correct import for Gemini as you specified
from google import genai

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
        
        # Append new message and save DataFrame to CSV
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
    """Add a new chat message and generate a Gemini response."""
    from app import app
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Message content is required'}), 400
    
    # Save the user's message
    user_message = {
        'user_id': data.get('user_id', 1),  # Default to user 1 if not specified
        'message': data['message'],
        'timestamp': datetime.now().isoformat(),
        'is_system_message': 0
    }
    
    saved_message = save_message(app.config['CHAT_HISTORY_CSV'], user_message)
    if not saved_message:
        return jsonify({'error': 'Failed to save message'}), 500
    
    # Prepare the prompt by combining system instructions with the user input.


    input_instructions = """ You are a chatbot representing Boston's 311 Rat Reporting Service—a free, 24/7 service connecting Boston residents with city services and information. Your primary role is to help users report rat sightings efficiently while gathering all necessary details. Follow these guidelines:

1. Reporting Process  
   - Location Input (Mandatory):  
     Always ask:  
     "Where did you see the rat? You can type the address or send your live location."  
   - Issue Description (Optional but Recommended):  
     Prompt with:  
     "Tell us what you saw: a rat running, a nest, or perhaps a trash issue?"  
   - Confirmation & Data Submission:  
     After collecting the information, confirm with the user:  
     "Thanks! Your report is being sent to 311. Here’s your confirmation number: #RAT12345."

2. Additional Features for Engagement  
   - Incentives & Gamification:  
     "Earn points for reporting! Your neighborhood is ranked #3 in cleanups—keep up the great work!"  
   - Proactive Education & Prevention:  
     "Want to prevent more rats in your area? Here are 3 quick tips:  
       1. Secure trash in closed bins.  
       2. Don’t leave food waste outside overnight.  
       3. Seal small holes where rats might enter buildings."  
   - AI Auto-Response for Common Issues:  
     If a user mentions trash overflow, suggest:  
     "We recommend reporting waste issues to 311 here: [Link]."  
     If a user mentions a rat infestation in a building, provide landlord/tenant guidelines.

3. Fallback Instructions  
   - If you are unable to handle a specific query or need more information, advise the user to call the 311 hotline at 617-635-4500 or download the official app.
    - IF the user responds in a different langage, please respond in that language aswell.
   And remember, always be polite, professional, and helpful and most importantly, BREIF AND TO THE POINT!
"""

    system_instructions = app.config.get('SYSTEM_INSTRUCTIONS', input_instructions)




    
    prompt = f"{system_instructions}\nUser: {data['message']}\nAssistant:"

    print('The prompt from the user is:', prompt)
    
    # Initialize the Gemini client using the API key from environment variables.
    client = genai.Client(api_key=os.environ.get("API_KEY"))
    
    # Generate the response using Gemini.
    response = client.models.generate_content(
        model="gemini-2.0-pro-exp-02-05",
        contents=prompt
    )
    
    # Extract the generated text.
    generated_text = response.text
    
    # Save the generated system response.
    system_message = {
        'user_id': 0,  # System user ID
        'message': generated_text,
        'timestamp': datetime.now().isoformat(),
        'is_system_message': 1
    }
    
    saved_response = save_message(app.config['CHAT_HISTORY_CSV'], system_message)
    
    return jsonify({
        'user_message': saved_message,
        'system_response': saved_response
    })
