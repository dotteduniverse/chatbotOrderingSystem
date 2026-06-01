"""Advanced response formatting"""

from typing import Dict, Any, List
import streamlit as st

class ResponseFormatter:
    """Format responses for better UI presentation"""
    
    @staticmethod
    def format_menu_display(menu_data: Dict[str, Any]) -> str:
        """Format menu for beautiful display"""
        formatted = "## 📋 Our Menu\n\n"
        
        # Beverages section
        formatted += "### 🍵 Beverages\n\n"
        
        # Teas
        if "tea" in menu_data["beverages"]:
            formatted += "**Teas:**\n"
            for tea in menu_data["beverages"]["tea"]:
                price_str = f"${tea['price']:.2f}"
                variants = f" ({', '.join(tea.get('variants', ['hot']))})" if tea.get('variants') else ""
                formatted += f"- **{tea['name']}**{variants}: {price_str}\n"
                if tea.get('description'):
                    formatted += f"  *{tea['description']}*\n"
            formatted += "\n"
        
        # Coffees
        if "coffee" in menu_data["beverages"]:
            formatted += "**Coffees:**\n"
            for coffee in menu_data["beverages"]["coffee"]:
                price_str = f"${coffee['price']:.2f}"
                variants = f" ({', '.join(coffee.get('variants', ['hot']))})" if coffee.get('variants') else ""
                formatted += f"- **{coffee['name']}**{variants}: {price_str}\n"
                if coffee.get('description'):
                    formatted += f"  *{coffee['description']}*\n"
            formatted += "\n"
        
        # Snacks section
        formatted += "### 🍪 Snacks\n\n"
        for snack in menu_data["snacks"]:
            price_str = f"${snack['price']:.2f}"
            formatted += f"- **{snack['name']}**: {price_str}\n"
            if snack.get('description'):
                formatted += f"  *{snack['description']}*\n"
        
        return formatted
    
    @staticmethod
    def format_order_summary(order_items: List[Dict]) -> str:
        """Format order summary with emojis and clear formatting"""
        if not order_items:
            return "🛒 Your cart is empty"
        
        summary = "## 🛒 Your Order\n\n"
        summary += "| Item | Quantity | Price | Subtotal |\n"
        summary += "|------|----------|-------|----------|\n"
        
        total = 0
        for item in order_items:
            subtotal = item['quantity'] * item['price']
            total += subtotal
            summary += f"| {item['name']} | {item['quantity']} | ${item['price']:.2f} | ${subtotal:.2f} |\n"
        
        summary += f"\n**Total: ${total:.2f}**\n"
        
        return summary
    
    @staticmethod
    def format_recommendation(item_name: str, price: float, reason: str) -> str:
        """Format a recommendation"""
        return f"💡 **Recommendation**: Try our {item_name} (${price:.2f}) - {reason}"
    
    @staticmethod
    def create_order_card(order: Dict) -> str:
        """Create a beautiful order card"""
        card = "```\n"
        card += "╔════════════════════════════════╗\n"
        card += f"║ Order #{order['order_id'][-8:]}    \n"
        card += "╠════════════════════════════════╣\n"
        
        for item in order['items']:
            card += f"║ {item['quantity']}x {item['name'][:20]:<20} ║\n"
        
        card += "╠════════════════════════════════╣\n"
        card += f"║ Total: ${order['total']:.2f}{' ' * 13}║\n"
        card += f"║ Status: {order['status']}{' ' * 11}║\n"
        card += "╚════════════════════════════════╝\n"
        card += "```"
        return card