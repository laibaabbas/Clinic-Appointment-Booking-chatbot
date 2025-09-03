import streamlit as st
import requests
import uuid
import json
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Care Health Clinic - Appointment Booking",
    page_icon="🏥",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
    <style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .message {
        padding: 12px 16px;
        margin-bottom: 12px;
        border-radius: 8px;
        line-height: 1.4;
        max-width: 80%;
    }
    
    .user-message {
        background-color: rgba(0, 123, 255, 0.1);
        margin-left: auto;
        border: 1px solid rgba(0, 123, 255, 0.2);
    }
    
    .assistant-message {
        background-color: rgba(108, 117, 125, 0.1);
        margin-right: auto;
        border: 1px solid rgba(108, 117, 125, 0.2);
    }
    .stButton button {
        width: 100%;
    }
     /* Dark theme adjustments */
    @media (prefers-color-scheme: dark) {
        .user-message {
            background-color: rgba(0, 123, 255, 0.15);
            border: 1px solid rgba(0, 123, 255, 0.3);
        }
        
        .assistant-message {
            background-color: rgba(108, 117, 125, 0.15);
            border: 1px solid rgba(108, 117, 125, 0.3);
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "waiting_for_confirmation" not in st.session_state:
    st.session_state.waiting_for_confirmation = False
if "appointment_details" not in st.session_state:
    st.session_state.appointment_details = None

# Backend API URL
API_URL = "http://localhost:8000"

def send_message(message):
    """Send message to backend API"""
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={
                "message": message,
                "session_id": st.session_state.session_id
            },
            timeout=30
        )
        
        # Check if response is valid JSON
        try:
            return response.json()
        except json.JSONDecodeError:
            st.error(f"Invalid response from server: {response.text}")
            return {"response": "Sorry, I'm having trouble connecting to the server. Please try again.", "status": "error"}
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        return {"response": "Sorry, I'm having trouble connecting to the server. Please try again.", "status": "error"}

def confirm_appointment():
    """Confirm the appointment"""
    try:
        response = requests.post(
            f"{API_URL}/confirm/{st.session_state.session_id}"
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            # Handle duplicate appointment error
            error_detail = response.json().get("detail", "Unknown error")
            return {"error": error_detail}
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error confirming appointment: {e}")
        return {"error": "Connection error"}

def get_doctors():
    """Get list of doctors"""
    try:
        response = requests.get(f"{API_URL}/doctors")
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error getting doctors list: {e}")
        return None
def handle_response(response):
    """Handle the response from the backend"""
    if response:
        # Add assistant response to conversation
        message_data = {
            "role": "assistant", 
            "content": response.get("response", "Sorry, I didn't understand that.")
        }
        
        # Check the response status
        if response.get("status") == "confirmation" and response.get("appointment"):
            message_data["type"] = "confirmation"
            st.session_state.waiting_for_confirmation = True
            st.session_state.appointment_details = response.get("appointment")
        elif response.get("status") == "confirmed":
            message_data["type"] = "confirmed"
            st.session_state.waiting_for_confirmation = False
            st.session_state.appointment_details = None
        
        st.session_state.conversation.append(message_data)
        
        # Rerun to update the UI
        st.rerun()

# Header section
st.title("🏥 Care Health Clinic")
st.subheader("Book Your Appointment with Ease")

# Create two columns for layout
col1, col2 = st.columns([1, 2])

# Left column - Clinic information
with col1:
    st.header("Clinic Information")
    
    # Get doctors info (cache this to avoid multiple calls)
    @st.cache_data
    def load_doctors_info():
        return get_doctors()
    
    doctors_info = load_doctors_info()
    
    if doctors_info:
        clinic = doctors_info.get("clinic", {})
        doctors = doctors_info.get("doctors", [])
        
        st.write(f"**Name:** {clinic.get('name', 'N/A')}")
        st.write(f"**Address:** {clinic.get('address', 'N/A')}")
        st.write(f"**Hours:** {clinic.get('hours', 'N/A')}")
        st.write(f"**Contact:** {clinic.get('contact', 'N/A')}")
        
        st.header("Available Doctors")
        for doctor in doctors:
            with st.expander(f"👨‍⚕️ {doctor.get('name', 'N/A')}"):
                st.write(f"**Specialization:** {doctor.get('specialization', 'N/A')}")
                st.write("**Available Slots:**")
                for slot in doctor.get('slots', []):
                    st.write(f"- {slot}")

# Right column - Chat interface
with col2:
    st.header("Chat with Our Assistant")

    # Display conversation history
    for message in st.session_state.conversation:
        if message["role"] == "user":
            st.markdown(f'<div class="stChatMessage message user-message">👤 **You:** {message["content"]}</div>', 
                        unsafe_allow_html=True)
        else:
            if message.get("type") == "confirmation":
                st.markdown(f'<div class="stChatMessage message confirmation-message">🤖 **Assistant:** {message["content"]}</div>', 
                            unsafe_allow_html=True)
            elif message.get("type") == "confirmed":
                st.markdown(f'<div class="stChatMessage message confirmed-message">✅ **Assistant:** {message["content"]}</div>', 
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="stChatMessage message assistant-message">🤖 **Assistant:** {message["content"]}</div>', 
                            unsafe_allow_html=True)
    # If waiting for confirmation, show the confirmation button
    if st.session_state.waiting_for_confirmation and st.session_state.appointment_details:
        st.info("Please confirm your appointment:")
        
        appointment = st.session_state.appointment_details
        st.write(f"**Patient Name:** {appointment.get('patient_name', 'N/A')}")
        st.write(f"**Age:** {appointment.get('patient_age', 'N/A')}")
        st.write(f"**Doctor:** {appointment.get('doctor_name', 'N/A')}")
        st.write(f"**Date:** {appointment.get('date', 'N/A')}")
        st.write(f"**Time:** {appointment.get('time', 'N/A')}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Appointment"):
                # User confirms by typing "yes" or similar
                st.session_state.conversation.append({"role": "user", "content": "yes"})
                response = send_message("yes")
                handle_response(response)
        
        with col2:
            if st.button("❌ Cancel"):
                st.session_state.waiting_for_confirmation = False
                st.session_state.conversation.append({
                    "role": "assistant", 
                    "content": "Appointment booking cancelled. How else can I help you?"
                })
                st.rerun()
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message to conversation
        st.session_state.conversation.append({"role": "user", "content": user_input})
        
        # Send to backend
        response = send_message(user_input)
        handle_response(response)


# Footer
st.markdown("---")
st.markdown("© 2023 Care Health Clinic. All rights reserved.")