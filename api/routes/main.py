"""Main views and health check endpoints."""
from datetime import datetime
from flask import Blueprint, render_template, jsonify
from api.services.manager_service import get_channel_manager

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@main_bp.route('/login')
@main_bp.route('/signup')
def index():
    """Render the dashboard UI and authentication portal."""
    return render_template('index.html')


@main_bp.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint providing status and channel dashboard statistics."""
    cm = get_channel_manager()
    stats = cm.get_dashboard_stats()
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        **stats
    })
