"""
Real-time learning engine that adapts to user feedback
"""

def update_profile_from_feedback(profile, user_code, suggestion, action):
    """
    Update user profile based on their acceptance/rejection of suggestions
    This learns from user behavior and adapts the AI to match their preferences
    
    action: 'accept', 'reject', or 'ask_more'
    """
    profile.total_interactions += 1
    
    if action == 'accept':
        profile.suggestions_accepted += 1
        # Reinforce patterns in the accepted suggestion
        # This tells the AI: "User likes this style, use it more"
        weight = 1.5
        
        # Update patterns based on accepted suggestion
        # If user accepts a suggestion with docstrings, they likely prefer docstrings
        if suggestion and '"""' in suggestion:
            profile.patterns['uses_docstrings'] = True
        
        if suggestion and '->' in suggestion or ': ' in suggestion.split('\n')[0]:
            profile.patterns['uses_type_hints'] = True
            
    elif action == 'reject':
        profile.suggestions_rejected += 1
        # Reduce weight of these patterns
        # This tells the AI: "User doesn't like this style, avoid it"
        weight = 0.5
    else:  # ask_more
        weight = 1.0
    
    # Update style confidence (0 to 1)
    # More interactions = more confident about user's style
    profile.style_confidence = min(profile.total_interactions / 100, 1.0)
    
    # Update skill level based on interactions and acceptance rate
    if profile.total_interactions >= 100:
        accept_rate = profile.suggestions_accepted / profile.total_interactions
        if accept_rate > 0.7:
            profile.skill_level = 'advanced'
        elif accept_rate > 0.4:
            profile.skill_level = 'intermediate'
    elif profile.total_interactions >= 50:
        profile.skill_level = 'intermediate'
    
    # If Style DNA exists, use it to update patterns
    if profile.style_dna:
        # Keep Style DNA patterns in sync with user feedback
        if action == 'accept' and profile.style_dna:
            # Reinforce DNA patterns when user accepts
            dna = profile.style_dna
            # Update naming convention if consistent
            if dna.get('naming_confidence', 0) > 80:
                profile.naming_convention = dna.get('naming_style', 'snake_case')
    
    return profile

def should_show_teaching_moment(profile):
    """Determine if user is ready for a teaching moment"""
    # Only show teaching after user has some confidence
    if profile.style_confidence < 0.5:
        return False
    
    # Don't overwhelm beginners
    if profile.skill_level == 'beginner' and profile.total_interactions < 20:
        return False
    
    # Show teaching moment every 10 interactions
    return profile.total_interactions % 10 == 0

def get_next_teaching_topic(profile):
    """Suggest next teaching topic based on profile"""
    patterns = profile.patterns
    
    # Priority order of topics
    if not patterns.get('uses_docstrings'):
        return {
            'topic': 'Documentation with Docstrings',
            'difficulty': 'easy',
            'why': 'You rarely use docstrings. They help others understand your code!'
        }
    
    if not patterns.get('uses_type_hints'):
        return {
            'topic': 'Type Hints',
            'difficulty': 'medium',
            'why': 'Type hints make code more maintainable and catch bugs early.'
        }
    
    if patterns.get('error_handling') == 'basic':
        return {
            'topic': 'Advanced Error Handling',
            'difficulty': 'medium',
            'why': 'Learn to handle errors more gracefully and provide better feedback.'
        }
    
    return {
        'topic': 'Code Optimization',
        'difficulty': 'advanced',
        'why': 'Ready to learn performance optimization techniques!'
    }

