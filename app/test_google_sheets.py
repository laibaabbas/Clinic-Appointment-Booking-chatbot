import os
from dotenv import load_dotenv
from app.sheets import get_google_sheets_client, save_appointment_to_sheet
from app.models import Appointment, AppointmentStatus

load_dotenv()

def test_google_sheets():
    try:
        # Test getting the client
        client = get_google_sheets_client()
        print("Google Sheets client created successfully!")
        
        # Test accessing the sheet
        sheet_title = os.getenv("SHEET_TITLE")
        sheet = client.open(sheet_title).sheet1
        print(f"Accessed sheet: {sheet_title}")
        
        # Test saving an appointment
        test_appointment = Appointment(
            patient_name="Test Patient",
            patient_age=30,
            doctor_id="TEST",
            doctor_name="Dr. Test",
            date="2025-12-31",
            time="10:00",
            status=AppointmentStatus.PENDING
        )
        
        success = save_appointment_to_sheet(test_appointment, "TEST")
        if success:
            print("Appointment saved successfully!")
        else:
            print("Failed to save appointment")
            
    except Exception as e:
        print(f"Error testing Google Sheets: {e}")

if __name__ == "__main__":
    test_google_sheets()