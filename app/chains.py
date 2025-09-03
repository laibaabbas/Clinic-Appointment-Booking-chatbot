from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import BaseOutputParser

from langchain_groq.chat_models import ChatGroq
import os
from typing import Dict, Any
from .models import ClinicData

# Since you're using Groq, we'll need to set up the appropriate model
# For now, I'll use OpenAI as an example. You'll need to adjust for Groq.

def create_chat_chain(clinic_data):
    doctors_list = "\n".join([f"- {doc.name} ({doc.specialization}): Available at {', '.join(doc.slots)}" for doc in clinic_data.doctors])
    
    prompt_template = PromptTemplate(
        input_variables=["user_input", "conversation_history"],
        template="""
        You are a friendly and helpful assistant at {clinic_name}. Your primary role is to help patients with:
        1. Providing information about the clinic, doctors, services, hours, etc.
        2. Helping patients book appointments when they're ready.
        
        Clinic Information:
        - Name: {clinic_name}
        - Address: {clinic_address}
        - Hours: {clinic_hours}
        - Contact: {clinic_contact}
        
        Available Doctors:
        {doctors_list}
        
        Be natural, friendly, and conversational. When patients ask about doctors or services, 
        provide helpful information. When they want to book an appointment, guide them through 
        the process conversationally.
        
        If the user provides appointment information (name, age, doctor, date, time), 
        note it and ask for any missing pieces naturally.
        
        For dates, if the user provides a partial date (like "22 sep"), assume the current year.
        and if the user say something like book appoinment for tomorrow or day after tomorrow then
        then you should get that date your own, and ask if what data yoy have assume is correct ,if not 
        then ask you exact date.

        For times, convert to 24-hour format (e.g., "9am" becomes "09:00", "3pm" becomes "15:00") , and 
        if it something like 12 O clock or something similar then as assume it as the day times 
        (like "9 o clock" becomes "09:00","12 o clock" becomes "12:00" "3 o clock" becomes "15:00").

        Also do'nt book appointment for date which are already have been passed or non realistic dates(i.e, 30 feb)
        and oct of clinic Hours {clinic_hours}


        Conversation History:
        {conversation_history}
        
        User Input: {user_input}
        
        Please respond in the following format:
        Extracted:
        name: [extracted name or empty]
        age: [extracted age or empty]
        doctor: [extracted doctor name or empty]
        date: [extracted date or empty]
        time: [extracted time or empty]
        missing: [comma-separated list of missing fields or none]
        
        
        Please respond in a friendly, helpful manner.
        """
    )
    
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0.3,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    
    return LLMChain(llm=llm, prompt=prompt_template)

class InfoExtractor(BaseOutputParser):
    def parse(self, text: str) -> Dict[str, Any]:
        # Parse the LLM response to extract structured information
        # This is a simplified version - you might want to use a more robust approach
        extracted = {}
        lines = text.split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                extracted[key.strip().lower()] = value.strip()
        return extracted

def create_extraction_chain(clinic_data: ClinicData):
    doctors_list = "\n".join([f"- {doc.name} ({doc.specialization}): Available slots: {', '.join(doc.slots)}" for doc in clinic_data.doctors])
    doctor_names = [doc.name for doc in clinic_data.doctors]
    
    prompt_template = PromptTemplate(
        input_variables=["user_input", "conversation_history"],
        template="""
        You are a helpful assistant at {clinic_name}. Your role is to help patients book appointments.
        
        Your primary role is to help patients with:
        1. Providing information about the clinic, doctors, services, hours, etc.
        2. Helping patients book appointments when they're ready.

        Clinic Information:
        - Name: {clinic_name}
        - Address: {clinic_address}
        - Hours: {clinic_hours}
        - Contact: {clinic_contact}
        
        Available Doctors:
        {doctors_list}
        
        Be natural, friendly, and conversational. When patients ask about doctors or services, 
        provide helpful information. When they want to book an appointment, guide them through 
        the process conversationally.
        
        If the user provides appointment information (name, age, doctor, date, time), 
        note it and ask for any missing pieces naturally.

        Always be polite, patient, and helpful. Answer any questions the patient might have about the clinic, doctors, or procedures.
        Your task is to extract the following information from the user's message:
        - patient name
        - patient age
        - doctor name
        - appointment date
        - appointment time
        
        If any information is missing, note what's missing.
        
        For dates, if the user provides a partial date (like "22 sep"), assume the current year.
        and if the user say something like book appoinment for tomorrow or day after tomorrow then
        then you should get that date your own, and ask if what data yoy have assume is correct ,if not 
        then ask you exact date.

        For times, convert to 24-hour format (e.g., "9am" becomes "09:00", "3pm" becomes "15:00") , and 
        if it something like 12 O clock or something similar then as assume it as the day times 
        (like "9 o clock" becomes "09:00",, "12 o clock" becomes "12:00" "3 o clock" becomes "15:00").


        
        Conversation History:
        {conversation_history}
        
        User Input: {user_input}
        
        Please respond in the following format:
        Extracted:
        name: [extracted name or empty]
        age: [extracted age or empty]
        doctor: [extracted doctor name or empty]
        date: [extracted date or empty]
        time: [extracted time or empty]
        missing: [comma-separated list of missing fields or none]
        
        
        Please respond in a friendly, helpful manner.
        """
    )
    
    # Use Groq instead of OpenAI
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",  # Or another Groq model
        temperature=0.7,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    
    return LLMChain(llm=llm, prompt=prompt_template, output_parser=InfoExtractor())

def create_confirmation_chain():
    prompt_template = PromptTemplate(
        input_variables=["appointment_details"],
        template="""
        Please confirm the following appointment details with the patient in a friendly manner:
        
        {appointment_details}
        
        Ask if the information is correct and if they would like to confirm the booking.
        """
    )
    
    # llm = ChatOpenAI(
    #     model_name="llama-3.3-70b-versatile",
    #     temperature=0.7,
    #     openai_api_key=os.getenv("GROQ_API_KEY"),
    #     # openai_api_base="https://api.groq.com/openai/v1"
    # )

    # Use Groq instead of OpenAI
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",  # Or another Groq model
        temperature=0.3,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )

    
    return LLMChain(llm=llm, prompt=prompt_template)