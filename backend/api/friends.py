import os
import pandas as pd
from datetime import datetime
from flask import Blueprint, request, jsonify

# Create blueprint
friends_bp = Blueprint('friends', __name__)

def load_friendships(csv_path):
    """Load friendships from CSV file."""
    if not os.path.exists(csv_path):
        return []
    
    try:
        df = pd.read_csv(csv_path)
        # Convert DataFrame to list of dictionaries
        friendships = df.to_dict('records')
        return friendships
    except Exception as e:
        print(f"Error loading friendships: {e}")
        return []

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

def save_friendship(csv_path, friendship_data):
    """Save a new friendship to the CSV file."""
    try:
        # Load existing friendships
        friendships = load_friendships(csv_path)
        
        # Generate new ID
        new_id = 1
        if friendships:
            new_id = max(f['id'] for f in friendships) + 1
        
        # Create new friendship
        new_friendship = {
            'id': new_id,
            'user_id': friendship_data.get('user_id'),
            'friend_id': friendship_data.get('friend_id'),
            'status': friendship_data.get('status', 'pending'),
            'created_at': friendship_data.get('created_at', datetime.now().isoformat())
        }
        
        # Add to DataFrame and save
        friendships.append(new_friendship)
        df = pd.DataFrame(friendships)
        df.to_csv(csv_path, index=False)
        
        return new_friendship
    except Exception as e:
        print(f"Error saving friendship: {e}")
        return None

def update_friendship(csv_path, friendship_id, status):
    """Update a friendship's status."""
    try:
        # Load existing friendships
        friendships = load_friendships(csv_path)
        
        # Find the friendship to update
        for friendship in friendships:
            if friendship['id'] == friendship_id:
                friendship['status'] = status
                break
        else:
            return None  # Friendship not found
        
        # Save updated friendships
        df = pd.DataFrame(friendships)
        df.to_csv(csv_path, index=False)
        
        return next((f for f in friendships if f['id'] == friendship_id), None)
    except Exception as e:
        print(f"Error updating friendship: {e}")
        return None

@friends_bp.route('/user/<int:user_id>', methods=['GET'])
def get_friends(user_id):
    """Get a user's friends."""
    from app import app
    
    # Load friendships and users
    friendships = load_friendships(app.config['FRIENDSHIPS_CSV'])
    users = load_users(app.config['USERS_CSV'])
    
    # Find accepted friendships for this user
    user_friendships = [
        f for f in friendships 
        if (f['user_id'] == user_id or f['friend_id'] == user_id) and f['status'] == 'accepted'
    ]
    
    # Get friend details
    friends_list = []
    for friendship in user_friendships:
        friend_id = friendship['friend_id'] if friendship['user_id'] == user_id else friendship['user_id']
        friend = next((u for u in users if u['id'] == friend_id), None)
        
        if friend:
            friends_list.append({
                'friendship_id': friendship['id'],
                'user_id': friend['id'],
                'username': friend['username'],
                'elo_rating': friend['elo_rating'],
                'disposals_count': friend['disposals_count'],
                'best_timing': friend['best_timing'],
                'created_at': friendship['created_at']
            })
    
    return jsonify(friends_list)

@friends_bp.route('/requests/<int:user_id>', methods=['GET'])
def get_friend_requests(user_id):
    """Get a user's pending friend requests."""
    from app import app
    
    # Load friendships and users
    friendships = load_friendships(app.config['FRIENDSHIPS_CSV'])
    users = load_users(app.config['USERS_CSV'])
    
    # Find pending requests for this user
    pending_requests = [
        f for f in friendships 
        if f['friend_id'] == user_id and f['status'] == 'pending'
    ]
    
    # Get requester details
    requests_list = []
    for request in pending_requests:
        requester = next((u for u in users if u['id'] == request['user_id']), None)
        
        if requester:
            requests_list.append({
                'request_id': request['id'],
                'user_id': requester['id'],
                'username': requester['username'],
                'created_at': request['created_at']
            })
    
    return jsonify(requests_list)

@friends_bp.route('/add', methods=['POST'])
def add_friend():
    """Send a friend request."""
    from app import app
    
    data = request.get_json()
    if not data or 'user_id' not in data or 'friend_id' not in data:
        return jsonify({'error': 'User ID and friend ID are required'}), 400
    
    user_id = data['user_id']
    friend_id = data['friend_id']
    
    # Check if users exist
    users = load_users(app.config['USERS_CSV'])
    if not any(u['id'] == user_id for u in users) or not any(u['id'] == friend_id for u in users):
        return jsonify({'error': 'User or friend not found'}), 404
    
    # Check if friendship already exists
    friendships = load_friendships(app.config['FRIENDSHIPS_CSV'])
    existing = next(
        (f for f in friendships 
         if (f['user_id'] == user_id and f['friend_id'] == friend_id) or 
            (f['user_id'] == friend_id and f['friend_id'] == user_id)),
        None
    )
    
    if existing:
        return jsonify({'error': 'Friendship already exists', 'status': existing['status']}), 400
    
    # Create new friendship
    new_friendship = save_friendship(app.config['FRIENDSHIPS_CSV'], {
        'user_id': user_id,
        'friend_id': friend_id,
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    })
    
    if not new_friendship:
        return jsonify({'error': 'Failed to create friendship'}), 500
    
    return jsonify(new_friendship), 201

@friends_bp.route('/respond', methods=['POST'])
def respond_to_request():
    """Accept or reject a friend request."""
    from app import app
    
    data = request.get_json()
    if not data or 'request_id' not in data or 'action' not in data:
        return jsonify({'error': 'Request ID and action are required'}), 400
    
    request_id = data['request_id']
    action = data['action']
    
    if action not in ['accept', 'reject']:
        return jsonify({'error': 'Action must be either "accept" or "reject"'}), 400
    
    # Update friendship status
    status = 'accepted' if action == 'accept' else 'rejected'
    updated = update_friendship(app.config['FRIENDSHIPS_CSV'], request_id, status)
    
    if not updated:
        return jsonify({'error': 'Friend request not found'}), 404
    
    return jsonify(updated)
