"""Menu loading and management utilities"""

import json
from typing import Dict, List, Any
from pathlib import Path

class MenuLoader:
    """Load and manage menu items from JSON file"""
    
    def __init__(self, menu_path: str = "data/menu.json"):
        self.menu_path = Path(menu_path)
        self.menu_data = self.load_menu()
    
    def load_menu(self) -> Dict[str, Any]:
        """Load menu data from JSON file"""
        try:
            with open(self.menu_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Menu file not found at {self.menu_path}")
            return self.get_default_menu()
        except json.JSONDecodeError:
            print(f"Invalid JSON in {self.menu_path}")
            return self.get_default_menu()
    
    def get_default_menu(self) -> Dict[str, Any]:
        """Return default menu if file is missing"""
        return {
            "beverages": {
                "tea": [
                    {"name": "Masala Chai", "price": 3.50, "variants": ["hot", "iced"]},
                    {"name": "Green Tea", "price": 3.00, "variants": ["hot"]}
                ],
                "coffee": [
                    {"name": "Espresso", "price": 3.00, "variants": ["hot", "iced"]},
                    {"name": "Latte", "price": 4.50, "variants": ["hot", "iced"]}
                ]
            },
            "snacks": [
                {"name": "Samosa", "price": 2.00},
                {"name": "Cookies", "price": 1.50}
            ]
        }
    
    def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all menu items as a flat list"""
        items = []
        
        # Add beverages
        for category in self.menu_data["beverages"].values():
            for item in category:
                items.append({**item, "type": "beverage"})
        
        # Add snacks
        for item in self.menu_data["snacks"]:
            items.append({**item, "type": "snack"})
        
        return items
    
    def search_item(self, query: str) -> List[Dict[str, Any]]:
        """Simple text search for menu items"""
        query_lower = query.lower()
        results = []
        
        for item in self.get_all_items():
            if (query_lower in item["name"].lower() or 
                query_lower in item.get("description", "").lower()):
                results.append(item)
        
        return results
    
    def get_item_price(self, item_name: str) -> float:
        """Get price of an item by name"""
        for item in self.get_all_items():
            if item["name"].lower() == item_name.lower():
                return item["price"]
        return 0.0
    
    def format_menu_for_display(self) -> str:
        """Format menu as readable string for LLM context"""
        menu_text = "=== MENU ===\n\n"
        
        menu_text += "BEVERAGES:\n"
        for category, items in self.menu_data["beverages"].items():
            menu_text += f"\n{category.upper()}:\n"
            for item in items:
                variants = f" ({', '.join(item['variants'])})" if 'variants' in item else ""
                desc = f" - {item['description']}" if 'description' in item else ""
                menu_text += f"  • {item['name']}{variants}: ${item['price']:.2f}{desc}\n"
        
        menu_text += "\nSNACKS:\n"
        for item in self.menu_data["snacks"]:
            desc = f" - {item['description']}" if 'description' in item else ""
            menu_text += f"  • {item['name']}: ${item['price']:.2f}{desc}\n"
        
        return menu_text