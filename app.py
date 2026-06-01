"""Simple chatbot without RAG or external dependencies"""

import streamlit as st
import json
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Simple CafeBot",
    page_icon="☕",
    layout="wide"
)

# Load menu
def load_menu():
    menu_file = Path("data/menu.json")
    if menu_file.exists():
        with open(menu_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Return default menu if file doesn't exist
        return {
            "beverages": {
                "tea": [{"name": "Masala Chai", "price": 3.50}],
                "coffee": [{"name": "Espresso", "price": 3.00}]
            },
            "snacks": [{"name": "Samosa", "price": 2.00}]
        }

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "order" not in st.session_state:
    st.session_state.order = []
if "menu" not in st.session_state:
    st.session_state.menu = load_menu()

# Sidebar
with st.sidebar:
    st.title("☕ CafeBot")
    st.markdown("---")
    
    # Display current order
    st.subheader("🛒 Your Order")
    if st.session_state.order:
        total = 0
        for item in st.session_state.order:
            st.write(f"- {item['quantity']}x {item['name']}: ${item['price'] * item['quantity']:.2f}")
            total += item['price'] * item['quantity']
        st.markdown(f"**Total: ${total:.2f}**")
        
        if st.button("Clear Order"):
            st.session_state.order = []
            st.rerun()
        if st.button("Confirm Order"):
            st.success(f"Order confirmed! Total: ${total:.2f}")
            st.balloons()
            st.session_state.order = []
            st.rerun()
    else:
        st.info("No items in order")
    
    st.markdown("---")
    
    # Display menu
    with st.expander("📋 Menu"):
        st.markdown("**Teas:**")
        for tea in st.session_state.menu["beverages"]["tea"]:
            st.write(f"- {tea['name']}: ${tea['price']:.2f}")
        
        st.markdown("**Coffees:**")
        for coffee in st.session_state.menu["beverages"]["coffee"]:
            st.write(f"- {coffee['name']}: ${coffee['price']:.2f}")
        
        st.markdown("**Snacks:**")
        for snack in st.session_state.menu["snacks"]:
            st.write(f"- {snack['name']}: ${snack['price']:.2f}")

# Main chat interface
st.title("☕ Welcome to Simple CafeBot!")
st.caption("Your ordering assistant - type 'menu' to see items, or tell me what you want!")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Simple response function
def get_response(user_input):
    user_input_lower = user_input.lower()
    
    # Show menu
    if "menu" in user_input_lower or "what do you have" in user_input_lower:
        response = "Here's our menu:\n\n"
        response += "**Teas:**\n"
        for tea in st.session_state.menu["beverages"]["tea"]:
            response += f"- {tea['name']}: ${tea['price']:.2f}\n"
        response += "\n**Coffees:**\n"
        for coffee in st.session_state.menu["beverages"]["coffee"]:
            response += f"- {coffee['name']}: ${coffee['price']:.2f}\n"
        response += "\n**Snacks:**\n"
        for snack in st.session_state.menu["snacks"]:
            response += f"- {snack['name']}: ${snack['price']:.2f}\n"
        response += "\nWhat would you like to order?"
        return response
    
    # Check for order items
    found_items = []
    for category in ["tea", "coffee"]:
        for item in st.session_state.menu["beverages"][category]:
            if item["name"].lower() in user_input_lower:
                found_items.append(item)
    
    for item in st.session_state.menu["snacks"]:
        if item["name"].lower() in user_input_lower:
            found_items.append(item)
    
    # Add items to order
    if found_items:
        for item in found_items:
            # Try to find quantity
            quantity = 1
            words = user_input_lower.split()
            for i, word in enumerate(words):
                if item["name"].lower() in word and i > 0:
                    if words[i-1].isdigit():
                        quantity = int(words[i-1])
            
            st.session_state.order.append({
                "name": item["name"],
                "quantity": quantity,
                "price": item["price"]
            })
        
        total = sum(i["price"] * i["quantity"] for i in st.session_state.order)
        response = f"Added {len(found_items)} item(s) to your order! Current total: ${total:.2f}\n\nAnything else?"
        return response
    
    # Check order status
    if "order" in user_input_lower and ("what" in user_input_lower or "show" in user_input_lower or "my" in user_input_lower):
        if st.session_state.order:
            response = "Your current order:\n"
            for item in st.session_state.order:
                response += f"- {item['quantity']}x {item['name']}: ${item['price'] * item['quantity']:.2f}\n"
            total = sum(i["price"] * i["quantity"] for i in st.session_state.order)
            response += f"\nTotal: ${total:.2f}"
        else:
            response = "Your order is empty. Would you like to order something?"
        return response
    
    # Clear order
    if "clear" in user_input_lower or "cancel" in user_input_lower:
        if "order" in user_input_lower:
            st.session_state.order = []
            response = "Your order has been cleared. Start a new order anytime!"
            return response
    
    # Default response
    return "I can help you order tea, coffee, and snacks. Type 'menu' to see what we have, or tell me what you'd like (e.g., 'I want a masala chai and 2 samosas')"

# Chat input
if prompt := st.chat_input("What would you like to order?"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        response = get_response(prompt)
        st.markdown(response)
        
        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.markdown("---")
st.caption("💡 Try: 'Show menu', 'I want a masala chai', '2 samosas please', or 'Show my order'")