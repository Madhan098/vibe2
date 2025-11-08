"""
Simple in-memory data storage for demo
In production, use SQLAlchemy with SQLite
"""
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
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
        # GitHub health report
        self.github_health_report = None  # Store GitHub health analysis
        # GitHub integration
        self.github_token = None  # Store GitHub OAuth token
        self.github_username = None  # Store GitHub username
        self.github_connected = False  # Track if GitHub is connected
    
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
            'current_quality_score': self.current_quality_score,
            'github_health_report': self.github_health_report,  # Include health report
            'github_connected': self.github_connected,  # Include GitHub connection status
            'github_username': self.github_username  # Include GitHub username
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

def create_session(user_id, expires_in_days=30):
    """Create session token with expiration (default: 30 days)"""
    token = str(uuid.uuid4())
    now = datetime.utcnow()
    sessions_db[token] = {
        'user_id': user_id,
        'created_at': now,
        'last_accessed': now,
        'expires_at': now + timedelta(days=expires_in_days)
    }
    return token

def get_session(token):
    """Get session and update last accessed time - returns None if expired"""
    session = sessions_db.get(token)
    if not session:
        return None
    
    # Check if session has expired
    now = datetime.utcnow()
    if session.get('expires_at') and now > session['expires_at']:
        # Session expired, delete it
        delete_session(token)
        return None
    
    # Update last accessed time and extend expiration (refresh on activity)
    session['last_accessed'] = now
    # Extend expiration by 30 days from last access (keep session alive if user is active)
    session['expires_at'] = now + timedelta(days=30)
    
    return session

def cleanup_expired_sessions():
    """Remove expired sessions (call periodically)"""
    now = datetime.utcnow()
    expired_tokens = []
    for token, session in sessions_db.items():
        if session.get('expires_at') and now > session['expires_at']:
            expired_tokens.append(token)
    
    for token in expired_tokens:
        delete_session(token)
    
    return len(expired_tokens)

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

def save_style_profile(user_id, style_profile_data):
    """Save or update user's style profile (DNA)"""
    profile = profiles_db.get(user_id)
    if not profile:
        # Create profile if it doesn't exist
        profile = UserProfile(user_id)
        profiles_db[user_id] = profile
    
    # Store the complete style profile
    profile.style_dna = style_profile_data
    profile.dna_extracted = True
    
    # Extract key patterns for quick access
    profile.naming_convention = style_profile_data.get('naming_style', 'snake_case')
    profile.style_confidence = style_profile_data.get('naming_confidence', 0.0) / 100.0
    
    # Update patterns
    profile.patterns = {
        'naming_style': style_profile_data.get('naming_style', 'snake_case'),
        'uses_docstrings': style_profile_data.get('documentation_percentage', 0) > 50,
        'uses_type_hints': style_profile_data.get('type_hints_percentage', 0) > 50,
        'error_handling': style_profile_data.get('error_handling_style', 'basic')
    }
    
    # Store quality scores
    if profile.initial_quality_score is None:
        profile.initial_quality_score = style_profile_data.get('code_quality_score', 50)
    profile.current_quality_score = style_profile_data.get('code_quality_score', 50)
    
    # Update skill level based on quality score
    quality = style_profile_data.get('code_quality_score', 50)
    if quality >= 80:
        profile.skill_level = 'advanced'
    elif quality >= 60:
        profile.skill_level = 'intermediate'
    else:
        profile.skill_level = 'beginner'
    
    return profile

def get_style_profile(user_id):
    """Get user's stored style profile (DNA)"""
    profile = profiles_db.get(user_id)
    if profile and profile.style_dna:
        return profile.style_dna
    return None

def update_style_profile_from_feedback(user_id, feedback_data):
    """Update style profile based on user feedback (accept/reject)"""
    profile = profiles_db.get(user_id)
    if not profile or not profile.style_dna:
        return None
    
    # Update interaction counts
    profile.total_interactions += 1
    if feedback_data.get('action') == 'accept':
        profile.suggestions_accepted += 1
    else:
        profile.suggestions_rejected += 1
    
    # Update style DNA based on feedback (learning)
    # This allows the profile to evolve based on user preferences
    if feedback_data.get('action') == 'accept' and feedback_data.get('suggestion'):
        # User accepted - strengthen patterns in the suggestion
        # This is a simplified learning mechanism
        pass  # Could add more sophisticated learning here
    
    return profile

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

