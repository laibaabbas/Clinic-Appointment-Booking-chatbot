
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import os

from dotenv import load_dotenv

from .models import ClinicData, Appointment, ConversationState
from .utils import load_clinic_data, normalize_date, normalize_time, normalize_doctor_name, find_doctor_by_name
from .chains import create_extraction_chain, create_confirmation_chain
from .sheets import save_appointment_to_sheet , get_available_slots
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

# In-memory storage for conversation states (in production, use a database)
conversation_states: Dict[str, ConversationState] = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    session_id: str
    status: str
    missing_info: List[str] = []
    appointment: Dict[str, Any] = None

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id
    
    # Initialize or get conversation state
    if session_id not in conversation_states:
        conversation_states[session_id] = ConversationState()
    
    state = conversation_states[session_id]
    
    # Create extraction chain
    extraction_chain = create_extraction_chain(clinic_data)
    
    # Extract information from user input
    extracted_info = extraction_chain.run({
        "user_input": request.message,
        "conversation_history": str(state.collected_data),
        "clinic_name": clinic_data.clinic.name,
        "clinic_address": clinic_data.clinic.address,
        "clinic_hours": clinic_data.clinic.hours,
        "clinic_contact": clinic_data.clinic.contact,
        "doctors_list": "\n".join([f"- {doc.name} ({doc.specialization})" for doc in clinic_data.doctors])
    })
    
    # Update collected data
    for key, value in extracted_info.items():
        if value and value != "empty":
            state.collected_data[key] = value
    
    from .utils import load_clinic_data, normalize_date, normalize_time, normalize_doctor_name, find_doctor_by_name
    # Validate doctor name if provided
    if "doctor" in state.collected_data and state.collected_data["doctor"]:
        doctor_name = state.collected_data["doctor"]
        doctor = find_doctor_by_name(clinic_data.doctors, doctor_name)
        
        if not doctor:
            # Invalid doctor name
            doctor_names = [doc.name for doc in clinic_data.doctors]
            response_text = f"I couldn't find a doctor named '{doctor_name}'. Please choose from our available doctors: {', '.join(doctor_names)}"
            
            # Remove the invalid doctor from collected data
            state.collected_data.pop("doctor", None)
            
            return ChatResponse(
                response=response_text,
                session_id=session_id,
                status="error",
                missing_info=["doctor"]
            )
    
    # Check if we have all required information
    required_fields = ["name", "age", "doctor", "date", "time"]
    missing_fields = []
    
    for field in required_fields:
        if field not in state.collected_data or not state.collected_data[field]:
            missing_fields.append(field)
    
    if missing_fields:
        # Ask for missing information
        response_text = f"I need some more information to book your appointment. Please provide your: {', '.join(missing_fields)}"
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            status="missing_info",
            missing_info=missing_fields
        )
    else:
        # All information is collected, create appointment
        from .utils import find_doctor_by_name, normalize_date, normalize_time
        
        # Normalize data
        normalized_date = normalize_date(state.collected_data["date"])
        normalized_time = normalize_time(state.collected_data["time"])
        doctor = find_doctor_by_name(clinic_data.doctors, state.collected_data["doctor"])
        
        if not doctor:
            # This shouldn't happen if we validated above, but just in case
            return ChatResponse(
                response="I couldn't find that doctor. Please choose from our available doctors.",
                session_id=session_id,
                status="error",
                missing_info=["doctor"]
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
        
        return ChatResponse(
            response=confirmation_text,
            session_id=session_id,
            status="confirmation",
            appointment=appointment.dict()
        )

@app.post("/confirm/{session_id}")
async def confirm_appointment(session_id: str):
    if session_id not in conversation_states:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = conversation_states[session_id]
    
    if not state.appointment:
        raise HTTPException(status_code=400, detail="No appointment to confirm")
    
    try:
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
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
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