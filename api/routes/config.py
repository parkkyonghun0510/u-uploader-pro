"""Configuration and profile management routes."""
from flask import Blueprint, request, jsonify
from api.auth import require_auth
from api.services.manager_service import get_config_manager

config_bp = Blueprint('config', __name__)


@config_bp.route('/api/config', methods=['GET'])
@require_auth
def get_config():
    """Retrieve full application configuration."""
    cm = get_config_manager()
    return jsonify(cm.load())


@config_bp.route('/api/config', methods=['POST'])
@require_auth
def save_config():
    """Update application configuration."""
    cm = get_config_manager()
    cm.save(request.json or {})
    return jsonify({"message": "Configuration saved"})


@config_bp.route('/api/profiles', methods=['GET'])
@require_auth
def get_profiles():
    """List all browser profiles."""
    cm = get_config_manager()
    return jsonify(cm.get_profiles())


@config_bp.route('/api/profiles', methods=['POST'])
@require_auth
def create_profile():
    """Create or save a browser profile."""
    cm = get_config_manager()
    profile = request.json or {}
    cm.save_profile(profile)
    return jsonify({"message": "Profile created", "profile": profile}), 201


@config_bp.route('/api/profiles/<profile_name>', methods=['DELETE'])
@require_auth
def delete_profile(profile_name: str):
    """Delete a browser profile."""
    cm = get_config_manager()
    cm.delete_profile(profile_name)
    return jsonify({"message": "Profile deleted"})
