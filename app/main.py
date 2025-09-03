from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

from .models import ClinicData, Appointment, ConversationState
from .utils import load_clinic_data, normalize_date, normalize_time, find_doctor_by_name
from .chains import create_chat_chain, create_confirmation_chain

from .sheets import save_appointment_to_sheet , get_available_slots
from .extractor import extract_appointment_info, has_booking_intent, has_info_intent

# Load environment variables
load_dotenv()

app = FastAPI(title="Clinic Appointment Chatbot API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load clinic data
clinic_data = load_clinic_data("app/data/clinic_data.json")

# In-memory storage for conversation states
conversation_states: Dict[str, ConversationState] = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    session_id: str
    status: str
    appointment: Dict[str, Any] = None

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id
    
    # Initialize or get conversation state
    if session_id not in conversation_states:
        conversation_states[session_id] = ConversationState()
    
    state = conversation_states[session_id]
    
    # Check if this is a confirmation response
    if state.current_step == "confirmation" and has_booking_intent(request.message):
        # User confirmed the appointment
        if state.appointment:
            # Save to Google Sheets
            result = save_appointment_to_sheet(state.appointment, clinic_data.clinic.code, clinic_data)
            
            if result["success"]:
                # Clear conversation state
                appointment_id = state.appointment.appointment_id if hasattr(state.appointment, 'appointment_id') else "N/A"
                response_text = f"Appointment confirmed! Your appointment ID is: {appointment_id}"
                conversation_states[session_id] = ConversationState()
                
                return ChatResponse(
                    response=response_text,
                    session_id=session_id,
                    status="confirmed"
                )
            else:
                return ChatResponse(
                    response="Sorry, there was an error saving your appointment. Please try again.",
                    session_id=session_id,
                    status="error"
                )
    
    # Create chat chain
    chat_chain = create_chat_chain(clinic_data)
    
    # Get response from the chatbot
    response_text = chat_chain.run({
        "user_input": request.message,
        "conversation_history": str(state.collected_data),
        "clinic_name": clinic_data.clinic.name,
        "clinic_address": clinic_data.clinic.address,
        "clinic_hours": clinic_data.clinic.hours,
        "clinic_contact": clinic_data.clinic.contact,
        "doctors_list": "\n".join([f"- {doc.name} ({doc.specialization}): Available at {', '.join(doc.slots)}" for doc in clinic_data.doctors])
    })
    
    # Ensure response is a string
    if isinstance(response_text, dict):
        response_text = str(response_text)
    
    # Extract appointment information if provided
    extracted_info = extract_appointment_info(request.message, state.collected_data)
    
    # Validate and clean extracted information
    if 'name' in extracted_info:
        # Clean the name - remove any extra text after the actual name
        name = extracted_info['name']
        if ' and ' in name:
            name = name.split(' and ')[0].strip()
        if ' i am ' in name:
            name = name.split(' i am ')[0].strip()
        if ' i\'m ' in name:
            name = name.split(' i\'m ')[0].strip()
        extracted_info['name'] = name
    
    # Update collected data with any extracted information
    for key, value in extracted_info.items():
        if value and value != "empty":
            state.collected_data[key] = value
    
    # Check if we have all required information for booking
    required_fields = ["name", "age", "doctor", "date", "time"]
    has_all_info = all(field in state.collected_data and state.collected_data[field] for field in required_fields)
    
    # Check if user wants to book an appointment
    wants_to_book = has_booking_intent(request.message)
    
    if has_all_info and wants_to_book:
        # All information is collected, create appointment
        normalized_date = normalize_date(state.collected_data["date"])
        normalized_time = normalize_time(state.collected_data["time"])
        doctor = find_doctor_by_name(clinic_data.doctors, state.collected_data["doctor"])
        
        if not doctor:
            # Invalid doctor name
            doctor_names = [doc.name for doc in clinic_data.doctors]
            response_text = f"I couldn't find a doctor named '{state.collected_data['doctor']}'. Please choose from our available doctors: {', '.join(doctor_names)}"
            
            # Remove the invalid doctor from collected data
            state.collected_data.pop("doctor", None)
            
            return ChatResponse(
                response=response_text,
                session_id=session_id,
                status="error"
            )
        
        # Create appointment object
        appointment = Appointment(
            patient_name=state.collected_data["name"],
            patient_age=int(state.collected_data["age"]),
            doctor_id=doctor.id,
            doctor_name=doctor.name,
            date=normalized_date,
            time=normalized_time
        )
        
        state.appointment = appointment
        state.current_step = "confirmation"
        
        # Ask for confirmation
        confirmation_chain = create_confirmation_chain()
        confirmation_text = confirmation_chain.run({
            "appointment_details": f"""
            Patient: {appointment.patient_name}
            Age: {appointment.patient_age}
            Doctor: {appointment.doctor_name}
            Date: {appointment.date}
            Time: {appointment.time}
            """
        })
        
        # Ensure confirmation text is a string
        if isinstance(confirmation_text, dict):
            confirmation_text = str(confirmation_text)
        
        return ChatResponse(
            response=confirmation_text,
            session_id=session_id,
            status="confirmation",
            appointment=appointment.dict()
        )
    else:
        # Just return the chatbot's response
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            status="chat"
        )

@app.post("/confirm/{session_id}")
async def confirm_appointment(session_id: str):
    if session_id not in conversation_states:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = conversation_states[session_id]
    
    if not state.appointment:
        raise HTTPException(status_code=400, detail="No appointment to confirm")
    
    # Save to Google Sheets
    result = save_appointment_to_sheet(state.appointment, clinic_data.clinic.code, clinic_data)

    if result["success"]:
        # Clear conversation state
        conversation_states[session_id] = ConversationState()
        
        return {
            "message": result["message"],
            "appointment_id": result.get("appointment_id")
        }
    else:
        # Return the error message from the save function
        raise HTTPException(status_code=400, detail=result["message"])

# Add a new endpoint to check availability
@app.get("/availability/{doctor_id}/{date}")
async def check_availability(doctor_id: str, date: str):
    # Normalize the date
    from .utils import normalize_date
    normalized_date = normalize_date(date)
    
    available_slots = get_available_slots(doctor_id, normalized_date, clinic_data)
    
    return {
        "doctor_id": doctor_id,
        "date": normalized_date,
        "available_slots": available_slots
    }

@app.get("/doctors")
async def get_doctors():
    return {
        "clinic": clinic_data.clinic.dict(),
        "doctors": [doctor.dict() for doctor in clinic_data.doctors]
    }

@app.get("/")
async def root():
    return {"message": "Clinic Appointment Chatbot API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)