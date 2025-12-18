#!/usr/bin/env python3
"""
Simple test application for end-to-end testing.
Listens on port 8080 and responds with a simple JSON message.
"""
import os
from flask import Flask, jsonify

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))

@app.route("/", methods=["GET"])
def hello():
    """Root endpoint"""
    return jsonify({
        "message": "Hello from Cloud Run-style app!",
        "status": "running",
        "port": PORT
    }), 200

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route("/test/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def test_path(path):
    """Test endpoint that echoes the path"""
    return jsonify({
        "path": f"/test/{path}",
        "message": "Path-based routing works!"
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)
