import re
from typing import Dict, Any
from datetime import datetime, timedelta

def extract_appointment_info(text: str, current_state: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Enhanced regex-based extraction of appointment information with context awareness
    """
    if current_state is None:
        current_state = {}
    
    extracted = current_state.copy()
    
    # Simple patterns to extract information
    patterns = {
        'name': r'(?:name is|I am|call me|my name is|I\'m) ([A-Za-z\s]+)',
        'age': r'(?:age|I am|I\'m) (\d+)',
        'doctor': r'(?:doctor|dr\.|dctor|with) ([A-Za-z\s]+)',
        'date': r'(?:on|for|date) ([A-Za-z0-9\s,]+)',
        'time': r'(?:at|around|time) ([0-9:]+[ap]m|[0-9]+\s*[ap]m|[0-9]+\s*o\'clock)'
    }
    
    # Handle relative dates
    text_lower = text.lower()
    today = datetime.now()
    
    if 'tomorrow' in text_lower:
        extracted['date'] = (today + timedelta(days=1)).strftime('%Y-%m-%d')
    elif 'day after tomorrow' in text_lower:
        extracted['date'] = (today + timedelta(days=2)).strftime('%Y-%m-%d')
    elif 'next week' in text_lower:
        extracted['date'] = (today + timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Extract information using patterns
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted[key] = match.group(1).strip()
    
    # Handle "o'clock" times
    if 'time' in extracted and 'o\'clock' in extracted['time'].lower():
        time_str = extracted['time'].lower().replace('o\'clock', '').strip()
        try:
            hour = int(time_str)
            if hour < 12 and 'pm' not in text_lower:
                extracted['time'] = f"{hour:02d}:00"
            else:
                extracted['time'] = f"{hour:02d}:00"
        except ValueError:
            pass
    
    return extracted

def has_booking_intent(text: str) -> bool:
    """
    Check if the user wants to book an appointment
    """
    booking_keywords = [
        'book', 'appointment', 'schedule', 'reserve', 
        'see a doctor', 'meet with', 'visit doctor', 'confirm',
        'yes', 'yeah', 'sure', 'ok', 'okay'
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in booking_keywords)

def has_info_intent(text: str) -> bool:
    """
    Check if the user wants information
    """
    info_keywords = [
        'info', 'information', 'tell me', 'what is', 'who is',
        'details', 'about', 'explain', 'describe', 'know'
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in info_keywords)