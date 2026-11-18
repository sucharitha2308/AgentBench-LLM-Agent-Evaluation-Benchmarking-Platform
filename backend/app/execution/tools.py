from typing import Any, Dict, List, Optional


# Controlled mock database for customer support operations
ORDERS_DB = {
    "ORD-1001": {
        "order_id": "ORD-1001",
        "customer": "Alex Mercer",
        "status": "Shipped",
        "items": [
            {"name": "Wireless Noise Cancelling Headphones", "qty": 1, "price": 149.99},
            {"name": "USB-C Braided Cable 2m", "qty": 1, "price": 19.99}
        ],
        "total_amount": 169.98,
        "items_count": 2,
        "carrier": "FedEx",
        "tracking_number": "TRK-982341",
        "estimated_delivery": "Tomorrow by 5:00 PM"
    },
    "ORD-1002": {
        "order_id": "ORD-1002",
        "customer": "Samantha Lee",
        "status": "Delivered",
        "delivered_at": "3 days ago",
        "items": [
            {"name": "Mechanical Gaming Keyboard", "qty": 1, "price": 119.50}
        ],
        "total_amount": 119.50,
        "items_count": 1,
        "eligible_for_refund": True,
        "refund_window_days_remaining": 27
    },
    "ORD-1003": {
        "order_id": "ORD-1003",
        "customer": "Jordan Taylor",
        "status": "Delivered",
        "delivered_at": "45 days ago",
        "items": [
            {"name": "Ultra HD Webcam 4K", "qty": 1, "price": 89.00}
        ],
        "total_amount": 89.00,
        "items_count": 1,
        "eligible_for_refund": False,
        "refund_window_days_remaining": 0,
        "ineligible_reason": "Return window exceeded 30-day limit"
    },
    "ORD-1004": {
        "order_id": "ORD-1004",
        "customer": "Morgan Rivera",
        "status": "Cancelled",
        "cancelled_at": "Yesterday",
        "refund_status": "Processed",
        "total_amount": 45.00
    },
    "ORD-1005": {
        "order_id": "ORD-1005",
        "customer": "Taylor Swift",
        "status": "Shipped",
        "carrier": "UPS",
        "tracking_number": "UPS-772199",
        "total_amount": 250.00
    },
    "ORD-1006": {
        "order_id": "ORD-1006",
        "customer": "Chris Pine",
        "status": "Processing",
        "notes": "Items currently being packed at central warehouse",
        "total_amount": 79.99
    },
    "ORD-1007": {
        "order_id": "ORD-1007",
        "customer": "Dana Scully",
        "status": "Confirmed",
        "notes": "Order placed recently, payment verified",
        "total_amount": 34.50
    }
}

PRODUCTS_DB = [
    {
        "id": "PROD-01",
        "name": "Sony WH-1000XM5 Wireless Noise Cancelling Headphones",
        "category": "Audio",
        "price": 349.99,
        "in_stock": True,
        "rating": 4.8
    },
    {
        "id": "PROD-02",
        "name": "Anker Space Q45 Wireless Noise Cancelling Headphones",
        "category": "Audio",
        "price": 129.99,
        "in_stock": True,
        "rating": 4.6
    },
    {
        "id": "PROD-03",
        "name": "Keychron K2 Pro Mechanical Wireless Keyboard",
        "category": "Peripherals",
        "price": 109.00,
        "in_stock": True,
        "rating": 4.7
    },
    {
        "id": "PROD-04",
        "name": "Logitech MX Master 3S Wireless Mouse",
        "category": "Peripherals",
        "price": 99.99,
        "in_stock": True,
        "rating": 4.9
    },
    {
        "id": "PROD-05",
        "name": "Anker USB-C to USB-C Braided Cable 2-Pack 6ft",
        "category": "Cables & Power",
        "price": 16.99,
        "in_stock": True,
        "rating": 4.8
    }
]

WEATHER_DB = {
    "seattle": {"location": "Seattle, WA", "condition": "Overcast with light rain", "temperature_f": 52, "shipping_delays": "None"},
    "munich": {"location": "München, Germany", "condition": "Partly cloudy", "temperature_c": 14, "shipping_delays": "None"},
    "münchen": {"location": "München, Germany", "condition": "Partly cloudy", "temperature_c": 14, "shipping_delays": "None"},
    "chicago": {"location": "Chicago, IL", "condition": "Heavy snow blizzard alert", "temperature_f": 18, "shipping_delays": "Possible 24hr carrier delay due to storm"},
    "new york": {"location": "New York, NY", "condition": "Clear and sunny", "temperature_f": 65, "shipping_delays": "None"},
}


class ToolRegistry:
    """Safe, sandboxed deterministic tool registry."""

    @staticmethod
    def get_order(order_id: str) -> Dict[str, Any]:
        """Lookup order by order_id."""
        if not order_id or not isinstance(order_id, str):
            return {"success": False, "error": "Invalid order_id parameter"}
        
        # Clean order ID of surrounding punctuation or whitespace
        cleaned = order_id.strip().strip("?.!,'\"").upper()
        if cleaned in ORDERS_DB:
            return {"success": True, "data": ORDERS_DB[cleaned]}
        return {"success": False, "error": f"Order '{cleaned}' not found in records."}

    @staticmethod
    def check_refund_eligibility(order_id: str) -> Dict[str, Any]:
        """Check if an order is eligible for refund."""
        if not order_id or not isinstance(order_id, str):
            return {"success": False, "error": "Invalid order_id parameter"}
        
        cleaned = order_id.strip().strip("?.!,'\"").upper()
        if cleaned not in ORDERS_DB:
            return {"success": False, "error": f"Order '{cleaned}' not found."}
        
        order = ORDERS_DB[cleaned]
        if order.get("status") == "Cancelled":
            return {
                "success": True,
                "order_id": cleaned,
                "eligible": True,
                "status": "Cancelled",
                "message": "Order was cancelled and refund has already been processed to original payment method."
            }
        
        if order.get("eligible_for_refund", False):
            return {
                "success": True,
                "order_id": cleaned,
                "eligible": True,
                "max_refund_amount": order.get("total_amount", 0.0),
                "reason": f"Within return window ({order.get('refund_window_days_remaining')} days remaining)"
            }
        else:
            return {
                "success": True,
                "order_id": cleaned,
                "eligible": False,
                "reason": order.get("ineligible_reason", "Item delivered more than 30 days ago or ineligible product.")
            }

    @staticmethod
    def search_products(query: str) -> Dict[str, Any]:
        """Search products catalog matching keywords in query."""
        if not query or not isinstance(query, str):
            return {"success": False, "error": "Empty search query"}
        
        terms = [t.lower() for t in query.split() if len(t) > 2]
        matches = []
        for prod in PRODUCTS_DB:
            name_lower = prod["name"].lower()
            cat_lower = prod["category"].lower()
            if any(term in name_lower or term in cat_lower for term in terms):
                matches.append(prod)
        
        return {
            "success": True,
            "query": query,
            "results_count": len(matches),
            "products": matches
        }

    @staticmethod
    def get_weather(location: str) -> Dict[str, Any]:
        """Get weather conditions for a location to estimate delivery conditions."""
        if not location or not isinstance(location, str):
            return {"success": False, "error": "Invalid location"}
        
        loc_lower = location.lower().strip()
        for key, data in WEATHER_DB.items():
            if key in loc_lower:
                return {"success": True, "weather": data}
        
        return {
            "success": True,
            "weather": {
                "location": location,
                "condition": "Clear and normal shipping conditions",
                "shipping_delays": "None"
            }
        }

    @classmethod
    def execute_tool(cls, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Safe execution dispatch with strict validation."""
        tool_dispatch = {
            "get_order": cls.get_order,
            "check_refund_eligibility": cls.check_refund_eligibility,
            "search_products": cls.search_products,
            "get_weather": cls.get_weather,
        }
        
        if tool_name not in tool_dispatch:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' is not an authorized or recognized tool."
            }
            
        try:
            fn = tool_dispatch[tool_name]
            return fn(**arguments)
        except TypeError as e:
            return {
                "success": False,
                "error": f"Invalid arguments passed to '{tool_name}': {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}"
            }
