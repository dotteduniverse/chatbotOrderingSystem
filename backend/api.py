"""FastAPI backend for chatbot ordering system"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from .menu_loader import MenuLoader
from .order_processor import OrderProcessor

app = FastAPI(title="Chatbot Ordering System API", version="1.0.0")

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
menu_loader = MenuLoader()
order_processor = OrderProcessor()

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    order_summary: Optional[str] = None

class OrderItem(BaseModel):
    name: str
    quantity: int = 1
    variant: Optional[str] = None

class ConfirmOrderRequest(BaseModel):
    customer_name: Optional[str] = None
    session_id: str

@app.get("/")
async def root():
    return {"message": "Chatbot Ordering System API", "status": "running"}

@app.get("/menu")
async def get_menu():
    """Get complete menu"""
    return {
        "menu": menu_loader.menu_data,
        "formatted": menu_loader.format_menu_for_display()
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process chat message and return response"""
    
    # Simple response logic (will be enhanced with LLM later)
    message_lower = request.message.lower()
    
    # Check for menu request
    if "menu" in message_lower or "what do you have" in message_lower:
        response = f"Here's our menu:\n\n{menu_loader.format_menu_for_display()}\n\nWhat would you like to order?"
    
    # Check for order summary
    elif "summary" in message_lower or "what's in my order" in message_lower:
        summary = order_processor.get_current_order_summary()
        response = summary
    
    # Check for order confirmation
    elif "confirm" in message_lower or "checkout" in message_lower:
        result = order_processor.confirm_order()
        if result["success"]:
            response = f"{result['message']}\n\nThank you for your order! It will be ready in 10 minutes."
        else:
            response = result["message"]
    
    # Check for cancel
    elif "cancel" in message_lower:
        order_processor.current_order = None
        response = "Your order has been cancelled. Start a new order anytime!"
    
    # Try to extract order from message
    else:
        extraction = order_processor.extract_order_from_message(request.message, menu_loader)
        
        if extraction["items"]:
            for item in extraction["items"]:
                order_processor.add_to_order(
                    item["name"], 
                    item["quantity"], 
                    price=item["price"]
                )
            response = f"Added {len(extraction['items'])} item(s) to your order. {order_processor.get_current_order_summary()}\n\nAnything else?"
        else:
            response = f"I heard: '{request.message}'. I can help you order from our menu. Type 'menu' to see what we have, or tell me what you'd like to order!"
    
    return ChatResponse(
        response=response,
        session_id=request.session_id or "default_session",
        order_summary=order_processor.get_current_order_summary() if order_processor.current_order else None
    )

@app.post("/order/add")
async def add_to_order(item: OrderItem, session_id: str = "default"):
    """Add item to current order"""
    price = menu_loader.get_item_price(item.name)
    if price == 0:
        raise HTTPException(status_code=404, detail=f"Item '{item.name}' not found")
    
    order_processor.add_to_order(item.name, item.quantity, item.variant, price)
    
    return {
        "success": True,
        "message": f"Added {item.quantity}x {item.name} to your order",
        "order_summary": order_processor.get_current_order_summary()
    }

@app.post("/order/confirm")
async def confirm_order(request: ConfirmOrderRequest):
    """Confirm current order"""
    result = order_processor.confirm_order(request.customer_name)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@app.get("/order/current")
async def get_current_order():
    """Get current order summary"""
    return {
        "order_summary": order_processor.get_current_order_summary(),
        "has_items": bool(order_processor.current_order and order_processor.current_order.items)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)