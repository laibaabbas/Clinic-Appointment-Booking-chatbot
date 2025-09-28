from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from typing import List, Dict, Any
import json

def create_memory():
    """Create a new conversation memory"""
    return ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="output"
    )

def add_to_memory(memory, human_input, ai_response):
    """Add a conversation turn to memory"""
    memory.save_context({"input": human_input}, {"output": ai_response})

def get_chat_history(memory) -> List[Dict[str, str]]:
    """Get chat history as a list of message dictionaries"""
    if not memory or not memory.chat_memory:
        return []
    
    messages = []
    for message in memory.chat_memory.messages:
        if isinstance(message, HumanMessage):
            messages.append({"role": "user", "content": message.content})
        elif isinstance(message, AIMessage):
            messages.append({"role": "assistant", "content": message.content})
    
    return messages

def get_memory_as_string(memory) -> str:
    """Get the conversation history as a string"""
    if not memory or not memory.chat_memory:
        return ""
    
    history_str = ""
    for message in memory.chat_memory.messages:
        if isinstance(message, HumanMessage):
            history_str += f"Human: {message.content}\n"
        elif isinstance(message, AIMessage):
            history_str += f"Assistant: {message.content}\n"
    
    return history_str