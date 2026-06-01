"""Simplified but powerful chatbot ordering system with RAG"""

import streamlit as st
from langchain_ollama import ChatOllama
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Simple menu loader
class SimpleMenuLoader:
    def __init__(self):
        self.menu_data = self.load_menu()
    
    def load_menu(self):
        menu_file = Path("data/menu.json")
        if menu_file.exists():
            with open(menu_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self.create_default_menu()
    
    def create_default_menu(self):
        return {
            "beverages": {
                "tea": [
                    {"name": "Masala Chai", "price": 3.50, "description": "Spiced Indian tea"},
                    {"name": "Green Tea", "price": 3.00, "description": "Healthy Japanese tea"},
                    {"name": "Ginger Tea", "price": 3.50, "description": "Warming ginger tea"}
                ],
                "coffee": [
                    {"name": "Espresso", "price": 3.00, "description": "Strong coffee"},
                    {"name": "Latte", "price": 4.50, "description": "Creamy milk coffee"},
                    {"name": "Cold Coffee", "price": 4.00, "description": "Chilled coffee drink"}
                ]
            },
            "snacks": [
                {"name": "Samosa", "price": 2.00, "description": "Spiced potato pastry"},
                {"name": "Cookies", "price": 1.50, "description": "Butter cookies"},
                {"name": "Sandwich", "price": 4.00, "description": "Grilled veg sandwich"}
            ]
        }
    
    def search_items(self, query):
        results = []
        query_lower = query.lower()
        
        for category in ["tea", "coffee"]:
            for item in self.menu_data["beverages"][category]:
                if query_lower in item["name"].lower():
                    results.append(item)
        
        for item in self.menu_data["snacks"]:
            if query_lower in item["name"].lower():
                results.append(item)
        
        return results
    
    def get_all_items(self):
        items = []
        for category in ["tea", "coffee"]:
            for item in self.menu_data["beverages"][category]:
                items.append({**item, "type": "beverage"})
        for item in self.menu_data["snacks"]:
            items.append({**item, "type": "snack"})
        return items

# Page config
st.set_page_config(
    page_title="CafeBot Pro",
    page_icon="☕",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_order" not in st.session_state:
    st.session_state.current_order = []
if "llm" not in st.session_state:
    st.session_state.llm = None
if "menu_loader" not in st.session_state:
    st.session_state.menu_loader = SimpleMenuLoader()

# Sidebar
with st.sidebar:
    st.title("☕ CafeBot Pro")
    st.markdown("---")
    
    # Model setup
    st.subheader("🤖 AI Setup")
    
    if st.button("🚀 Start AI Assistant", type="primary"):
        with st.spinner("Starting AI..."):
            try:
                st.session_state.llm = ChatOllama(
                    model="llama3.2:1b",
                    temperature=0.7
                )
                st.success("✅ AI Ready!")
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("Make sure Ollama is running: `ollama serve`")
    
    if st.session_state.llm:
        st.success("AI Assistant Active")
    
    st.markdown("---")
    
    # Order display
    st.subheader("🛒 Your Order")
    if st.session_state.current_order:
        total = sum(i['quantity'] * i['price'] for i in st.session_state.current_order)
        st.metric("Total", f"${total:.2f}")
        
        for item in st.session_state.current_order:
            st.write(f"{item['quantity']}x {item['name']} - ${item['quantity'] * item['price']:.2f}")
        
        if st.button("Clear Order"):
            st.session_state.current_order = []
            st.rerun()
        if st.button("Checkout"):
            st.success(f"Order confirmed! Total: ${total:.2f}")
            st.balloons()
            st.session_state.current_order = []
            st.rerun()
    else:
        st.info("No items yet")
    
    st.markdown("---")
    
    # Menu preview
    with st.expander("📋 View Menu"):
        st.markdown("**Tea**")
        for tea in st.session_state.menu_loader.menu_data["beverages"]["tea"]:
            st.write(f"- {tea['name']}: ${tea['price']:.2f}")
        
        st.markdown("**Coffee**")
        for coffee in st.session_state.menu_loader.menu_data["beverages"]["coffee"]:
            st.write(f"- {coffee['name']}: ${coffee['price']:.2f}")
        
        st.markdown("**Snacks**")
        for snack in st.session_state.menu_loader.menu_data["snacks"]:
            st.write(f"- {snack['name']}: ${snack['price']:.2f}")

# Main chat
st.title("☕ CafeBot Pro")
st.caption("Intelligent ordering assistant with AI")

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Generate AI response function
def get_ai_response(user_input: str) -> str:
    """Get response using LLM with context"""
    
    # Prepare context
    menu_context = "\n".join([
        f"- {item['name']}: ${item['price']:.2f} - {item.get('description', '')}"
        for item in st.session_state.menu_loader.get_all_items()
    ])
    
    order_context = ""
    if st.session_state.current_order:
        order_context = "Current order:\n"
        for item in st.session_state.current_order:
            order_context += f"- {item['quantity']}x {item['name']}\n"
        total = sum(i['quantity'] * i['price'] for i in st.session_state.current_order)
        order_context += f"Total: ${total:.2f}\n"
    
    prompt = f"""You are CafeBot, a helpful ordering assistant.

MENU:
{menu_context}

{order_context}

Customer: {user_input}

Provide a helpful response. If customer wants to order, acknowledge items. If asking about menu, provide details. Be friendly!"""

    try:
        response = st.session_state.llm.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    except:
        return "I'm having trouble connecting. Please check if Ollama is running."

# Process order from text (simple extraction)
def extract_order_from_text(text: str) -> List[Dict]:
    """Simple order extraction from text"""
    items_found = []
    text_lower = text.lower()
    
    for item in st.session_state.menu_loader.get_all_items():
        if item['name'].lower() in text_lower:
            quantity = 1
            # Look for numbers before item
            words = text_lower.split()
            for i, word in enumerate(words):
                if item['name'].lower() in word and i > 0 and words[i-1].isdigit():
                    quantity = int(words[i-1])
                    break
            items_found.append({
                'name': item['name'],
                'quantity': quantity,
                'price': item['price']
            })
    
    return items_found

# Chat input
if prompt := st.chat_input("What would you like to order?"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            if st.session_state.llm:
                # Extract order items
                order_items = extract_order_from_text(prompt)
                if order_items:
                    for item in order_items:
                        st.session_state.current_order.append(item)
                    
                    # Get AI response
                    response = get_ai_response(prompt)
                    
                    # Add order summary
                    total = sum(i['quantity'] * i['price'] for i in st.session_state.current_order)
                    response += f"\n\n**Current total: ${total:.2f}**"
                else:
                    response = get_ai_response(prompt)
            else:
                response = "Please click 'Start AI Assistant' in the sidebar to begin!"
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.markdown("---")
st.caption("💡 Try: 'Show menu', 'I want a masala chai', or '2 samosas please'")