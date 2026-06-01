"""Order processing and management"""

from typing import Dict, List, Any
from datetime import datetime
import json

class OrderItem:
    """Represents a single item in an order"""
    
    def __init__(self, name: str, quantity: int = 1, variant: str = None, price: float = 0.0):
        self.name = name
        self.quantity = quantity
        self.variant = variant
        self.price = price
    
    def subtotal(self) -> float:
        return self.quantity * self.price
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "quantity": self.quantity,
            "variant": self.variant,
            "price": self.price,
            "subtotal": self.subtotal()
        }
    
    def __str__(self) -> str:
        variant_str = f" ({self.variant})" if self.variant else ""
        return f"{self.quantity}x {self.name}{variant_str} @ ${self.price:.2f} = ${self.subtotal():.2f}"

class Order:
    """Represents a complete customer order"""
    
    def __init__(self, order_id: str = None):
        self.order_id = order_id or datetime.now().strftime("%Y%m%d%H%M%S")
        self.items: List[OrderItem] = []
        self.status = "pending"
        self.created_at = datetime.now()
        self.customer_name = None
    
    def add_item(self, item: OrderItem):
        """Add an item to the order"""
        # Check if same item and variant exists
        for existing in self.items:
            if (existing.name.lower() == item.name.lower() and 
                existing.variant == item.variant):
                existing.quantity += item.quantity
                return
        self.items.append(item)
    
    def remove_item(self, item_name: str, quantity: int = None):
        """Remove an item or reduce quantity"""
        for i, item in enumerate(self.items):
            if item.name.lower() == item_name.lower():
                if quantity is None or quantity >= item.quantity:
                    del self.items[i]
                else:
                    item.quantity -= quantity
                return True
        return False
    
    def total(self) -> float:
        """Calculate order total"""
        return sum(item.subtotal() for item in self.items)
    
    def summary(self) -> str:
        """Generate order summary as string"""
        if not self.items:
            return "Your cart is empty."
        
        summary = f"📋 Order #{self.order_id}\n"
        summary += "=" * 40 + "\n"
        for item in self.items:
            summary += f"  {item}\n"
        summary += "=" * 40 + "\n"
        summary += f"  TOTAL: ${self.total():.2f}\n"
        summary += f"  Status: {self.status}\n"
        
        if self.customer_name:
            summary += f"  Customer: {self.customer_name}\n"
        
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary for storage"""
        return {
            "order_id": self.order_id,
            "items": [item.to_dict() for item in self.items],
            "total": self.total(),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "customer_name": self.customer_name
        }

class OrderProcessor:
    """Process and manage orders"""
    
    def __init__(self):
        self.current_order = None
        self.order_history: List[Order] = []
    
    def start_new_order(self) -> Order:
        """Start a new order"""
        self.current_order = Order()
        return self.current_order
    
    def add_to_order(self, item_name: str, quantity: int = 1, variant: str = None, price: float = 0.0):
        """Add item to current order"""
        if not self.current_order:
            self.start_new_order()
        
        item = OrderItem(item_name, quantity, variant, price)
        self.current_order.add_item(item)
    
    def get_current_order_summary(self) -> str:
        """Get summary of current order"""
        if not self.current_order:
            return "No active order. Start by telling me what you'd like to order!"
        return self.current_order.summary()
    
    def confirm_order(self, customer_name: str = None) -> Dict[str, Any]:
        """Confirm and save the current order"""
        if not self.current_order or not self.current_order.items:
            return {"success": False, "message": "No items in order"}
        
        if customer_name:
            self.current_order.customer_name = customer_name
        
        self.current_order.status = "confirmed"
        self.order_history.append(self.current_order)
        
        order_data = self.current_order.to_dict()
        
        # Save to file for persistence
        self.save_order_to_file(order_data)
        
        # Clear current order for next customer
        old_order = self.current_order
        self.current_order = None
        
        return {
            "success": True,
            "message": f"Order #{old_order.order_id} confirmed! Total: ${old_order.total():.2f}",
            "order": order_data
        }
    
    def save_order_to_file(self, order_data: Dict[str, Any]):
        """Save order to JSON file for persistence"""
        import os
        orders_file = "data/orders.json"
        
        # Load existing orders
        existing_orders = []
        if os.path.exists(orders_file):
            try:
                with open(orders_file, 'r') as f:
                    existing_orders = json.load(f)
            except:
                pass
        
        # Add new order
        existing_orders.append(order_data)
        
        # Save back
        with open(orders_file, 'w') as f:
            json.dump(existing_orders, f, indent=2)
    
    def extract_order_from_message(self, message: str, menu_loader) -> Dict[str, Any]:
        """Simple rule-based extraction of order from natural language"""
        message_lower = message.lower()
        items_found = []
        
        # Simple keyword matching (in real app, use LLM for this)
        for item in menu_loader.get_all_items():
            if item["name"].lower() in message_lower:
                # Try to extract quantity
                quantity = 1
                words = message_lower.split()
                for i, word in enumerate(words):
                    if item["name"].lower() in word and i > 0:
                        if words[i-1].isdigit():
                            quantity = int(words[i-1])
                        elif "a" in words[i-1] or "an" in words[i-1]:
                            quantity = 1
                
                items_found.append({
                    "name": item["name"],
                    "quantity": quantity,
                    "price": item["price"]
                })
        
        return {
            "items": items_found,
            "message": f"Found {len(items_found)} items in your message"
        }