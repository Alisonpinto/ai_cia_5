import os
import random
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database.db import Database
from agents.client_agent import ClientAgent
from agents.negotiator_agent import NegotiatorAgent

app = Flask(__name__)
app.secret_key = "cloud-agent-secret-key-change-me"
db = Database()

# -----------------------------------------------------
# PAGE ROUTES (return HTML)
# -----------------------------------------------------

@app.route("/")
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    return redirect(url_for('login_page'))

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template("dashboard.html", username=session.get('username'))

@app.route("/results")
def results_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template("results.html", username=session.get('username'))

# -----------------------------------------------------
# API ROUTES (return JSON)
# -----------------------------------------------------

@app.route("/api/register", methods=["POST"])
def api_register():
    """
    Body: {username, password, email}
    Creates user with a generated key like 'KEY-XXXX-123'
    Returns: {status: 'ok', user_key: '...'} or {status: 'error', message: '...'}
    """
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    email = data.get('email', '').strip()

    if not username or not password or not email:
        return jsonify({"status": "error", "message": "All fields are required"}), 400

    existing_user = db.get_user_by_username(username)
    if existing_user:
        return jsonify({"status": "error", "message": "Username already exists"}), 400

    prefix = username.upper()[:4]
    random_digits = random.randint(100, 999)
    user_key = f"KEY-{prefix}-{random_digits}"

    try:
        db.create_user(username, password, email, user_key)
        return jsonify({"status": "ok", "user_key": user_key})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/login", methods=["POST"])
def api_login():
    """
    Body: {username, user_key}
    Validates credentials against DB.
    Sets session['user_id'], session['username'].
    Returns: {status: 'ok'} or {status: 'error', message: '...'}
    """
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    user_key = data.get('user_key', '').strip()

    user = db.get_user_by_username(username)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 401
    if user['user_key'] != user_key:
        return jsonify({"status": "error", "message": "Invalid key"}), 401

    session['user_id'] = user['id']
    session['username'] = user['username']
    return jsonify({"status": "ok"})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"status": "ok"})

@app.route("/api/search", methods=["POST"])
def api_search():
    """
    Body: {service_type, max_price, min_trust, duration}
    Runs the full agent negotiation flow.
    Returns the result dict from negotiator.handle_request() as JSON,
    plus the agent log so the UI can display it.
    """
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    try:
        data = request.get_json() or {}

        # Reset logs so each search shows a fresh conversation
        db.reset_logs()

        # Build client agent
        client = ClientAgent(
            user_id=session['user_id'],
            username=session['username'],
            db=db
        )
        request_obj = client.build_request(
            service_type=data.get('service_type', 'SaaS'),
            max_price=float(data.get('max_price', 5.0)),
            min_trust=float(data.get('min_trust', 0.7)),
            min_score=float(data.get('min_score', 0.0)),
            duration=int(data.get('duration', 2))
        )

        negotiator = NegotiatorAgent(db=db)
        result = negotiator.handle_request(request_obj)

        # If success, notify client
        if result.get('success') and result.get('chosen'):
            client.receive_contract(result['contract_id'], result['chosen']['name'])

        # Attach the log so UI can show the conversation
        result['logs'] = [dict(row) for row in db.get_logs(limit=100)]
        result['status'] = 'ok'
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "success": False,
            "reason": f"Search error: {str(e)}",
            "logs": [dict(row) for row in db.get_logs(limit=100)]
        }), 500

@app.route("/api/services", methods=["GET"])
def api_services():
    """Returns all services (for debug / dashboard stats)."""
    services = db.get_all_services()
    return jsonify([dict(s) for s in services])

@app.route("/api/logs", methods=["GET"])
def api_logs():
    """Returns recent agent logs."""
    return jsonify([dict(row) for row in db.get_logs(limit=100)])

@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Returns high-level stats for the dashboard."""
    services = db.get_all_services()
    by_type = {'SaaS': 0, 'IaaS': 0, 'PaaS': 0}
    for s in services:
        by_type[s['service_type']] = by_type.get(s['service_type'], 0) + 1
    return jsonify({
        'total_services': len(services),
        'by_type': by_type,
        'total_providers': len(set(s['provider_id'] for s in services))
    })

@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "Endpoint not found"}), 404
    return redirect(url_for('login_page'))

@app.errorhandler(500)
def internal_server_error(e):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>500 - Server Error</title><link rel="stylesheet" href="/static/style.css"></head>
    <body class="dashboard-body"><div class="container text-center mt-4"><div class="card"><h1 class="heading">500 - Server Error</h1><p class="subheading mt-2">An unexpected server error occurred.</p><a href="/login" class="btn btn-primary mt-3">Return to Login</a></div></div></body>
    </html>
    """, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

