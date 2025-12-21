#!/usr/bin/env python3
"""
Example Cloud Run-style Service
A simple REST API service that demonstrates the Cloud Run deployment model.
Listens on port 8080 and provides various endpoints.
"""
import os
from datetime import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))
SERVICE_NAME = os.getenv("SERVICE_NAME", "example-service")
VERSION = "1.0.0"

# In-memory storage for demo purposes
items = []
item_counter = 0

@app.route("/", methods=["GET"])
def root():
    """Root endpoint - service information"""
    return jsonify({
        "service": SERVICE_NAME,
        "version": VERSION,
        "status": "running",
        "port": PORT,
        "message": "Welcome to the Example Cloud Run Service!",
        "endpoints": {
            "health": "/health",
            "items": "/items",
            "info": "/info"
        }
    }), 200

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": SERVICE_NAME
    }), 200

@app.route("/info", methods=["GET"])
def info():
    """Service information endpoint"""
    return jsonify({
        "service": SERVICE_NAME,
        "version": VERSION,
        "port": PORT,
        "environment": os.getenv("ENV", "development"),
        "items_count": len(items),
        "uptime_info": "Service is running"
    }), 200

@app.route("/items", methods=["GET"])
def get_items():
    """Get all items"""
    return jsonify({
        "items": items,
        "count": len(items)
    }), 200

@app.route("/items", methods=["POST"])
def create_item():
    """Create a new item"""
    global item_counter
    
    data = request.get_json() or {}
    item_counter += 1
    
    item = {
        "id": item_counter,
        "name": data.get("name", f"Item {item_counter}"),
        "description": data.get("description", ""),
        "created_at": datetime.utcnow().isoformat()
    }
    
    items.append(item)
    
    return jsonify({
        "message": "Item created successfully",
        "item": item
    }), 201

@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    """Get a specific item by ID"""
    item = next((i for i in items if i["id"] == item_id), None)
    
    if not item:
        return jsonify({
            "error": "Item not found",
            "item_id": item_id
        }), 404
    
    return jsonify(item), 200

@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Delete an item by ID"""
    global items
    
    item = next((i for i in items if i["id"] == item_id), None)
    
    if not item:
        return jsonify({
            "error": "Item not found",
            "item_id": item_id
        }), 404
    
    items = [i for i in items if i["id"] != item_id]
    
    return jsonify({
        "message": "Item deleted successfully",
        "item_id": item_id
    }), 200

@app.route("/test/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def test_path(path):
    """Test endpoint that demonstrates path-based routing"""
    return jsonify({
        "path": f"/test/{path}",
        "method": request.method,
        "message": "Path-based routing works!",
        "query_params": dict(request.args),
        "headers": dict(request.headers)
    }), 200

if __name__ == "__main__":
    print(f"Starting {SERVICE_NAME} on port {PORT}...")
    app.run(host="0.0.0.0", port=PORT, debug=False)
