from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from models import db, User, Preference, Group, GroupMember, Attraction, Itinerary
from nlp.language_processor import LanguageProcessor
from nlp.preference_extractor import PreferenceExtractor
from aggregator import ItineraryAggregator
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/travel_planner_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

db.init_app(app)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize NLP components
lang_processor = LanguageProcessor()
pref_extractor = PreferenceExtractor()
aggregator = ItineraryAggregator()

# Routes
@app.route('/api/users', methods=['POST'])
def create_user():
    """Create new user"""
    data = request.json
    user = User(
        username=data['username'],
        email=data['email']
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'id': user.id, 'username': user.username}), 201

@app.route('/api/preferences', methods=['POST'])
def submit_preference():
    """Submit user preference in regional language"""
    data = request.json
    
    # Detect language
    language = lang_processor.detect_language(data['preference_text'])
    
    # Translate to English
    english_text = lang_processor.translate_to_english(data['preference_text'], language)
    
    # Extract preferences
    categories = pref_extractor.extract_categories(english_text)
    budget = pref_extractor.extract_budget(english_text)
    duration = pref_extractor.extract_duration(english_text)
    
    # Save preference
    preference = Preference(
        user_id=data['user_id'],
        group_id=data.get('group_id'),
        preference_text=data['preference_text'],
        language=language,
        extracted_categories=categories,
        budget=budget,
        duration_days=duration
    )
    db.session.add(preference)
    db.session.commit()
    
    # Emit to group if applicable
    if data.get('group_id'):
        socketio.emit('preference_added', {
            'user_id': data['user_id'],
            'categories': categories
        }, room=f"group_{data['group_id']}")
    
    return jsonify({
        'id': preference.id,
        'language': language,
        'categories': categories,
        'budget': budget,
        'duration': duration
    }), 201

@app.route('/api/groups', methods=['POST'])
def create_group():
    """Create a new travel group"""
    data = request.json
    group = Group(
        name=data['name'],
        created_by=data['user_id']
    )
    db.session.add(group)
    db.session.commit()
    
    # Add creator as member
    member = GroupMember(group_id=group.id, user_id=data['user_id'])
    db.session.add(member)
    db.session.commit()
    
    return jsonify({'id': group.id, 'name': group.name}), 201

@app.route('/api/groups/<int:group_id>/members', methods=['POST'])
def add_group_member(group_id):
    """Add member to group"""
    data = request.json
    member = GroupMember(group_id=group_id, user_id=data['user_id'])
    db.session.add(member)
    db.session.commit()
    return jsonify({'success': True}), 201

@app.route('/api/groups/<int:group_id>/itinerary', methods=['POST'])
def generate_itinerary(group_id):
    """Generate itinerary for group"""
    # Get all preferences for the group
    preferences = Preference.query.filter_by(group_id=group_id).all()
    
    # Aggregate preferences
    aggregated = aggregator.aggregate_preferences(preferences)
    
    # Get attractions from database
    attractions = Attraction.query.all()
    
    # Generate itinerary
    itinerary_plan = aggregator.generate_itinerary(aggregated, attractions)
    
    # Save itinerary
    itinerary = Itinerary(
        group_id=group_id,
        name=f"Group Trip - {aggregated['duration']} days",
        total_days=aggregated['duration'],
        generated_plan=itinerary_plan
    )
    db.session.add(itinerary)
    db.session.commit()
    
    # Emit to group
    socketio.emit('itinerary_generated', {
        'itinerary_id': itinerary.id,
        'plan': itinerary_plan
    }, room=f"group_{group_id}")
    
    return jsonify({
        'id': itinerary.id,
        'plan': itinerary_plan
    }), 201

@app.route('/api/attractions', methods=['GET'])
def get_attractions():
    """Get all attractions"""
    attractions = Attraction.query.all()
    return jsonify([{
        'id': a.id,
        'name': a.name,
        'location': a.location,
        'category': a.category,
        'rating': a.rating
    } for a in attractions])

# WebSocket events
@socketio.on('join_group')
def handle_join_group(data):
    """Join group room for real-time updates"""
    group_id = data['group_id']
    join_room(f"group_{group_id}")
    emit('joined_group', {'group_id': group_id})

@socketio.on('update_itinerary')
def handle_update_itinerary(data):
    """Handle real-time itinerary updates"""
    group_id = data['group_id']
    emit('itinerary_updated', data, room=f"group_{group_id}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, port=5000)