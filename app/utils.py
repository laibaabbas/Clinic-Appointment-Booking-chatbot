import re
import json
from datetime import datetime
from typing import Dict, Any, List
from dateutil import parser
import calendar
from .models import ClinicData, Doctor, Appointment

def load_clinic_data(file_path: str) -> ClinicData:
    with open(file_path, 'r') as f:
        data = json.load(f)
    return ClinicData(**data)


def find_doctor_by_name(doctors: List[Doctor], name: str) -> Doctor:
    """
    Find a doctor by name (case-insensitive partial match)
    Improved to handle first names and last names better
    """
    if not name:
        return None
        
    name_lower = name.lower().strip()
    
    # Remove titles like "dr.", "doctor", etc.
    name_lower = re.sub(r'(dr\.|doctor|dr)\s*', '', name_lower)
    
    # Try exact match first
    for doctor in doctors:
        if name_lower == doctor.name.lower():
            return doctor
    
    # Try partial match with first name
    for doctor in doctors:
        doctor_name_lower = doctor.name.lower()
        # Check if the provided name matches the first part of the doctor's name
        if doctor_name_lower.startswith(name_lower):
            return doctor
        
        # Check if any part of the doctor's name contains the provided name
        if name_lower in doctor_name_lower:
            return doctor
    
    return None

def find_doctor_by_id(doctors: List[Doctor], id: str) -> Doctor:
    for doctor in doctors:
        if doctor.id == id:
            return doctor
    return None

def normalize_date(date_str: str) -> str:
    """
    Convert various date formats to YYYY-MM-DD
    Handles dates like "22 sep", "22 september", "22/09", etc.
    """
    try:
        # If only day and month are provided, assume current year
        if len(date_str.split()) == 2 and date_str.split()[1].isalpha():
            day, month_str = date_str.split()
            current_year = datetime.now().year
            date_str = f"{day} {month_str} {current_year}"
        
        # Try parsing with different formats
        for fmt in ("%d %b %Y", "%d %B %Y", "%d-%b-%Y", "%d-%B-%Y", "%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d", "%d %b", "%d %B"):
            try:
                dt = datetime.strptime(date_str, fmt)
                # If year wasn't provided, use current year
                if dt.year == 2025:  # Default year when not provided
                    dt = dt.replace(year=datetime.now().year)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        # Try with dateutil parser as a fallback
        try:
            dt = parser.parse(date_str)
            return dt.strftime("%Y-%m-%d")
        except:
            return date_str  # Return as is if cannot parse
    except:
        return date_str

def normalize_time(time_str: str) -> str:
    """
    Convert various time formats to HH:MM in 24-hour format
    """
    try:
        # Handle common time formats
        time_str = time_str.lower().replace(".", "").replace(" ", "")
        
        # Handle formats like "9am", "9:30pm"
        if "am" in time_str or "pm" in time_str:
            time_str = time_str.replace("am", " AM").replace("pm", " PM")
        
        # Try parsing with different formats
        for fmt in ("%I:%M%p", "%I%p", "%H:%M", "%I:%M %p", "%I %p"):
            try:
                dt = datetime.strptime(time_str, fmt)
                return dt.strftime("%H:%M")
            except ValueError:
                continue
        
        return time_str  # Return as is if cannot parse
    except:
        return time_str


def normalize_doctor_name(doctors: List[Doctor], name: str) -> str:
    doctor = find_doctor_by_name(doctors, name)
    return doctor.name if doctor else name

def generate_appointment_id(clinic_code: str, doctor_id: str, sequence_num: int) -> str:
    return f"{clinic_code}{doctor_id}{sequence_num}"

def extract_info_from_text(text: str, patterns: Dict[str, str]) -> Dict[str, str]:
    extracted = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted[key] = match.group(1).strip()
    return extracted