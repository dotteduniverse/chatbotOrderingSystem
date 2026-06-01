"""Advanced menu management with categorization and search"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd

class AdvancedMenuLoader:
    """Enhanced menu loader with search and filtering capabilities"""
    
    def __init__(self, menu_path: str = "data/menu.json"):
        self.menu_path = Path(menu_path)
        self.menu_data = self.load_menu()
        self.menu_df = self.create_dataframe()
        
    def load_menu(self) -> Dict[str, Any]:
        """Load menu from JSON file"""
        try:
            with open(self.menu_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.create_default_menu()
    
    def create_default_menu(self) -> Dict[str, Any]:
        """Create default menu if file doesn't exist"""
        return {
            "beverages": {
                "tea": [
                    {
                        "name": "Masala Chai",
                        "price": 3.50,
                        "variants": ["hot", "iced"],
                        "category": "tea",
                        "description": "Traditional Indian spiced tea with cardamom, ginger, and cinnamon",
                        "tags": ["spicy", "traditional", "popular"],
                        "preparation_time": 5
                    },
                    {
                        "name": "Green Tea",
                        "price": 3.00,
                        "variants": ["hot"],
                        "category": "tea",
                        "description": "Light and refreshing Japanese green tea with antioxidants",
                        "tags": ["healthy", "light", "organic"],
                        "preparation_time": 3
                    },
                    {
                        "name": "Ginger Tea",
                        "price": 3.50,
                        "variants": ["hot"],
                        "category": "tea",
                        "description": "Spicy and warming tea with fresh ginger and honey",
                        "tags": ["spicy", "medicinal", "winter"],
                        "preparation_time": 5
                    }
                ],
                "coffee": [
                    {
                        "name": "Espresso",
                        "price": 3.00,
                        "variants": ["hot", "iced"],
                        "category": "coffee",
                        "description": "Strong and concentrated coffee shot",
                        "tags": ["strong", "quick", "popular"],
                        "preparation_time": 3
                    },
                    {
                        "name": "Latte",
                        "price": 4.50,
                        "variants": ["hot", "iced"],
                        "category": "coffee",
                        "description": "Espresso with steamed milk and light foam",
                        "tags": ["creamy", "smooth", "popular"],
                        "preparation_time": 5
                    },
                    {
                        "name": "Cold Coffee",
                        "price": 4.00,
                        "variants": ["cold"],
                        "category": "coffee",
                        "description": "Chilled coffee with milk, ice, and a touch of vanilla",
                        "tags": ["cold", "refreshing", "summer"],
                        "preparation_time": 4
                    },
                    {
                        "name": "Cappuccino",
                        "price": 4.00,
                        "variants": ["hot"],
                        "category": "coffee",
                        "description": "Espresso with equal parts steamed milk and foam",
                        "tags": ["creamy", "italian", "popular"],
                        "preparation_time": 5
                    }
                ]
            },
            "snacks": [
                {
                    "name": "Samosa",
                    "price": 2.00,
                    "quantity_options": [1, 2, 3, 4, 5, 6],
                    "description": "Crispy pastry filled with spiced potatoes and peas",
                    "tags": ["spicy", "popular", "savory"],
                    "preparation_time": 8,
                    "spice_level": "medium"
                },
                {
                    "name": "Veg Puff",
                    "price": 2.50,
                    "quantity_options": [1, 2, 3, 4],
                    "description": "Flaky puff pastry with mixed vegetable filling",
                    "tags": ["savory", "bakery", "vegetarian"],
                    "preparation_time": 10,
                    "spice_level": "mild"
                },
                {
                    "name": "Cookies",
                    "price": 1.50,
                    "quantity_options": [1, 2, 3, 4, 5, 6, 12],
                    "description": "Butter cookies - plain or chocolate chip",
                    "tags": ["sweet", "snack", "popular"],
                    "preparation_time": 2,
                    "spice_level": "none"
                },
                {
                    "name": "Sandwich",
                    "price": 4.00,
                    "quantity_options": [1, 2],
                    "description": "Grilled vegetable sandwich with mint chutney",
                    "tags": ["savory", "healthy", "filling"],
                    "preparation_time": 12,
                    "spice_level": "mild"
                }
            ]
        }
    
    def create_dataframe(self) -> pd.DataFrame:
        """Create pandas DataFrame for easy querying"""
        items = []
        
        # Add beverages
        for category, beverages in self.menu_data["beverages"].items():
            for item in beverages:
                items.append({
                    'name': item['name'],
                    'category': f'beverage.{category}',
                    'price': item['price'],
                    'type': 'beverage',
                    'description': item.get('description', ''),
                    'tags': ', '.join(item.get('tags', [])),
                    'preparation_time': item.get('preparation_time', 5)
                })
        
        # Add snacks
        for item in self.menu_data["snacks"]:
            items.append({
                'name': item['name'],
                'category': 'snack',
                'price': item['price'],
                'type': 'snack',
                'description': item.get('description', ''),
                'tags': ', '.join(item.get('tags', [])),
                'preparation_time': item.get('preparation_time', 5)
            })
        
        return pd.DataFrame(items)
    
    def search_items(self, query: str) -> List[Dict]:
        """Advanced search with fuzzy matching"""
        query_lower = query.lower()
        
        # Calculate relevance scores
        results = []
        for _, item in self.menu_df.iterrows():
            score = 0
            
            # Name match
            if query_lower in item['name'].lower():
                score += 3
            
            # Category match
            if query_lower in item['category'].lower():
                score += 2
            
            # Tag match
            if query_lower in item['tags'].lower():
                score += 1
            
            # Description match
            if query_lower in item['description'].lower():
                score += 1
            
            if score > 0:
                results.append({
                    **item.to_dict(),
                    'relevance_score': score
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results
    
    def get_similar_items(self, item_name: str, limit: int = 3) -> List[Dict]:
        """Get similar items based on tags and category"""
        item = self.menu_df[self.menu_df['name'].str.lower() == item_name.lower()]
        if item.empty:
            return []
        
        item_tags = set(item.iloc[0]['tags'].split(', '))
        item_category = item.iloc[0]['category']
        
        # Find similar items
        similar = []
        for _, other in self.menu_df.iterrows():
            if other['name'].lower() == item_name.lower():
                continue
            
            other_tags = set(other['tags'].split(', '))
            tag_overlap = len(item_tags.intersection(other_tags))
            
            if tag_overlap > 0 or other['category'] == item_category:
                similar.append({
                    **other.to_dict(),
                    'similarity_score': tag_overlap
                })
        
        similar.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similar[:limit]
    
    def get_recommendations(self, preferences: List[str], limit: int = 3) -> List[Dict]:
        """Get recommendations based on preferences"""
        recommendations = []
        
        for _, item in self.menu_df.iterrows():
            score = 0
            item_tags = set(item['tags'].split(', '))
            
            for pref in preferences:
                if pref.lower() in item_tags:
                    score += 1
                if pref.lower() in item['name'].lower():
                    score += 2
                if pref.lower() in item['description'].lower():
                    score += 1
            
            if score > 0:
                recommendations.append({
                    **item.to_dict(),
                    'recommendation_score': score
                })
        
        recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
        return recommendations[:limit]
    
    def get_item_details(self, item_name: str) -> Optional[Dict]:
        """Get detailed information about a specific item"""
        item = self.menu_df[self.menu_df['name'].str.lower() == item_name.lower()]
        if not item.empty:
            return item.iloc[0].to_dict()
        return None
    
    def format_for_context(self) -> str:
        """Format menu for LLM context"""
        context = "CAFE MENU\n\n"
        
        context += "BEVERAGES:\n"
        for category, items in self.menu_data["beverages"].items():
            context += f"\n{category.upper()}:\n"
            for item in items:
                context += f"- {item['name']} (${item['price']:.2f})\n"
                context += f"  {item.get('description', '')}\n"
                if item.get('variants'):
                    context += f"  Available: {', '.join(item['variants'])}\n"
        
        context += "\nSNACKS:\n"
        for item in self.menu_data["snacks"]:
            context += f"- {item['name']} (${item['price']:.2f})\n"
            context += f"  {item.get('description', '')}\n"
        
        return context