import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from pathlib import Path
from typing import List, Dict
from .models import Appointment
from datetime import datetime
from .utils import normalize_time

def get_google_sheets_client():
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    # Get the absolute path to the credentials file
    # Get the project root directory
    project_root = Path(__file__).resolve().parent.parent
    creds_file_name = os.getenv("GOOGLE_SHEETS_SERVICE_ACCOUNT_FILE")
    
    # Construct the full path to the credentials file
    if "/" in creds_file_name:
        # If the path includes directories, use it as is
        creds_path = project_root / creds_file_name
    else:
        # If it's just a filename, assume it's in the credentials directory
        creds_path = project_root / "app" / "credentials" / creds_file_name
    
    print(f"Looking for credentials at: {creds_path}")  # Debug print
    
    if not creds_path.exists():
        raise FileNotFoundError(f"Credentials file not found at: {creds_path}")
    
    creds = ServiceAccountCredentials.from_json_keyfile_name(str(creds_path), scope)
    client = gspread.authorize(creds)
    return client

def check_existing_appointment(doctor_id: str, date: str, time: str) -> bool:
    """
    Check if an appointment already exists for the same doctor, date, and time
    """
    try:
        client = get_google_sheets_client()
        sheet_title = os.getenv("SHEET_TITLE")
        sheet = client.open(sheet_title).sheet1
        
        # Get all records
        records = sheet.get_all_records()
        
        # Normalize the time for comparison
        normalized_time = normalize_time(time)
        
        for record in records:
            record_time = normalize_time(record.get('time', ''))
            
            if (record.get('doctor_id') == doctor_id and 
                record.get('date') == date and 
                record_time == normalized_time and
                record.get('status', 'pending') != 'cancelled'):
                return True
                
        return False
    except Exception as e:
        print(f"Error checking existing appointments: {e}")
        return False

def get_available_slots(doctor_id: str, date: str, clinic_data) -> List[str]:
    """
    Get available time slots for a doctor on a specific date
    """
    try:
        # Get the doctor's available slots from clinic data
        doctor = next((doc for doc in clinic_data.doctors if doc.id == doctor_id), None)
        if not doctor:
            return []
        
        # Check which slots are already booked
        client = get_google_sheets_client()
        sheet_title = os.getenv("SHEET_TITLE")
        sheet = client.open(sheet_title).sheet1
        
        # Get all records for this doctor and date
        records = sheet.get_all_records()
        booked_slots = []
        
        for record in records:
            if (record.get('doctor_id') == doctor_id and 
                record.get('date') == date and
                record.get('status', 'pending') != 'cancelled'):
                booked_slots.append(normalize_time(record.get('time', '')))
        
        # Return available slots (doctor's slots minus booked slots)
        available_slots = [slot for slot in doctor.slots if normalize_time(slot) not in booked_slots]
        return available_slots
        
    except Exception as e:
        print(f"Error getting available slots: {e}")
        return []

def save_appointment_to_sheet(appointment: Appointment, clinic_code: str, clinic_data) -> Dict:
    """
    Save appointment to Google Sheets and return result with status message
    """
    try:
        client = get_google_sheets_client()
        sheet_title = os.getenv("SHEET_TITLE")
        sheet = client.open(sheet_title).sheet1
        
        # Check if appointment already exists
        if check_existing_appointment(appointment.doctor_id, appointment.date, appointment.time):
            available_slots = get_available_slots(appointment.doctor_id, appointment.date, clinic_data)
            
            if available_slots:
                return {
                    "success": False,
                    "message": f"This time slot is already booked. Available slots for Dr. {appointment.doctor_name} on {appointment.date}: {', '.join(available_slots)}"
                }
            else:
                return {
                    "success": False,
                    "message": f"This time slot is already booked. Dr. {appointment.doctor_name} has no available slots on {appointment.date}."
                }
        
        
        # Get next sequence number
        seq_num = get_next_sequence_number(sheet, clinic_code, appointment.doctor_id)
        
        # Generate appointment ID
        appointment.appointment_id = f"{clinic_code}{appointment.doctor_id}{seq_num}"
        appointment.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare row data
        row = [
            appointment.appointment_id,
            appointment.patient_name,
            str(appointment.patient_age),
            appointment.doctor_id,
            appointment.doctor_name,
            appointment.date,
            appointment.time,
            appointment.status,
            appointment.created_at
        ]
        
        # Append to sheet
        sheet.append_row(row)
        
        return {
            "success": True,
            "message": f"Appointment confirmed! Your appointment ID is: {appointment.appointment_id}",
            "appointment_id": appointment.appointment_id
        }
    except Exception as e:
        print(f"Error saving to Google Sheets: {e}")
        return {
            "success": False,
            "message": "Failed to save appointment. Please try again."
        }

def get_next_sequence_number(sheet, clinic_code: str, doctor_id: str) -> int:
    # Get all existing appointment IDs
    existing_ids = sheet.col_values(1)  # Assuming appointment_id is in column 1
    
    # Filter IDs for this clinic and doctor
    prefix = f"{clinic_code}{doctor_id}"
    sequence_numbers = []
    
    for app_id in existing_ids[1:]:  # Skip header
        if app_id and app_id.startswith(prefix):
            try:
                num = int(app_id[len(prefix):])
                sequence_numbers.append(num)
            except ValueError:
                continue
    
    return max(sequence_numbers) + 1 if sequence_numbers else 1


# def get_next_sequence_number(sheet, clinic_code: str, doctor_id: str) -> int:
#     # Get all existing appointment IDs
#     existing_ids = sheet.col_values(1)  # Assuming appointment_id is in column 1
    
#     # Filter IDs for this clinic and doctor
#     prefix = f"{clinic_code}{doctor_id}"
#     sequence_numbers = []
    
#     for app_id in existing_ids[1:]:  # Skip header
#         if app_id.startswith(prefix):
#             try:
#                 num = int(app_id[len(prefix):])
#                 sequence_numbers.append(num)
#             except ValueError:
#                 continue
    
#     return max(sequence_numbers) + 1 if sequence_numbers else 1

# def save_appointment_to_sheet(appointment: Appointment, clinic_code: str) -> bool:
#     try:
#         client = get_google_sheets_client()
#         sheet_title = os.getenv("SHEET_TITLE")
#         sheet = client.open(sheet_title).sheet1
        
#         # Get next sequence number
#         seq_num = get_next_sequence_number(sheet, clinic_code, appointment.doctor_id)
        
#         # Generate appointment ID
#         appointment.appointment_id = f"{clinic_code}{appointment.doctor_id}{seq_num}"
#         appointment.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
#         # Prepare row data
#         row = [
#             appointment.appointment_id,
#             appointment.patient_name,
#             appointment.patient_age,
#             appointment.doctor_id,
#             appointment.doctor_name,
#             appointment.date,
#             appointment.time,
#             appointment.status,
#             appointment.created_at
#         ]
        
#         # Append to sheet
#         sheet.append_row(row)
#         return True
#     except Exception as e:
#         print(f"Error saving to Google Sheets: {e}")
#         return False