"""
Simple in-memory data storage for demo
In production, use SQLAlchemy with SQLite
"""
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

# In-memory storage (resets on server restart - good for demo)
users_db = {}
sessions_db = {}
profiles_db = {}
interactions_db = []

class User:
    def __init__(self, email, name, password):
        self.id = str(uuid.uuid4())
        self.email = email.lower().strip()
        self.name = name.strip()
        self.password_hash = generate_password_hash(password)
        self.created_at = datetime.utcnow()
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'created_at': self.created_at.isoformat()
        }

class UserProfile:
    def __init__(self, user_id):
        self.user_id = user_id
        self.skill_level = 'beginner'
        self.naming_convention = 'snake_case'
        self.total_interactions = 0
        self.suggestions_accepted = 0
        self.suggestions_rejected = 0
        self.style_confidence = 0.0
        self.patterns = {
            'naming_style': {},
            'uses_docstrings': False,
            'uses_type_hints': False,
            'error_handling': 'basic'
        }
        # Style DNA - new fields
        self.style_dna = None  # Full Style DNA profile
        self.dna_extracted = False
        self.evolution_history = []  # Track growth over time
        self.initial_quality_score = None
        self.current_quality_score = None
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'skill_level': self.skill_level,
            'naming_convention': self.naming_convention,
            'total_interactions': self.total_interactions,
            'suggestions_accepted': self.suggestions_accepted,
            'suggestions_rejected': self.suggestions_rejected,
            'style_confidence': self.style_confidence,
            'patterns': self.patterns,
            'style_dna': self.style_dna,
            'dna_extracted': self.dna_extracted,
            'evolution_history': self.evolution_history,
            'initial_quality_score': self.initial_quality_score,
            'current_quality_score': self.current_quality_score
        }

def create_user(email, name, password):
    """Create new user"""
    if email.lower() in users_db:
        return None, "Email already exists"
    
    user = User(email, name, password)
    users_db[email.lower()] = user
    
    # Create profile
    profile = UserProfile(user.id)
    profiles_db[user.id] = profile
    
    return user, None

def get_user_by_email(email):
    """Get user by email"""
    return users_db.get(email.lower())

def get_user_by_id(user_id):
    """Get user by ID"""
    for user in users_db.values():
        if user.id == user_id:
            return user
    return None

def create_session(user_id):
    """Create session token (persistent - doesn't expire)"""
    token = str(uuid.uuid4())
    sessions_db[token] = {
        'user_id': user_id,
        'created_at': datetime.utcnow(),
        'last_accessed': datetime.utcnow()
    }
    return token

def get_session(token):
    """Get session and update last accessed time"""
    session = sessions_db.get(token)
    if session:
        session['last_accessed'] = datetime.utcnow()
    return session

def delete_session(token):
    """Delete session"""
    if token in sessions_db:
        del sessions_db[token]

def get_user_profile(user_id):
    """Get user profile"""
    return profiles_db.get(user_id)

def update_profile(user_id, updates):
    """Update user profile"""
    profile = profiles_db.get(user_id)
    if profile:
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        return profile
    return None

def log_interaction(user_id, interaction_data):
    """Log code interaction"""
    interaction = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'timestamp': datetime.utcnow(),
        **interaction_data
    }
    interactions_db.append(interaction)
    return interaction

