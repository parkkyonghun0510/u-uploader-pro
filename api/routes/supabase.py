"""Supabase integration, database sync, profile and connection routes."""
import os
from flask import Blueprint, request, jsonify
from api.auth import require_auth
from api.services.manager_service import (
    get_supabase,
    get_channel_manager,
    get_upload_queue,
)

supabase_bp = Blueprint('supabase', __name__, url_prefix='/api/supabase')


@supabase_bp.route('/sync', methods=['POST'])
@require_auth
def sync_to_supabase():
    """Trigger a full sync of local data to Supabase."""
    supabase = get_supabase()
    if not supabase.is_connected():
        return jsonify({"error": "Supabase not connected"}), 503
    try:
        cm = get_channel_manager()
        queue = get_upload_queue()
        accounts = cm.get_all_accounts()
        channels = cm.get_all_channels()
        templates = cm.get_all_templates() if hasattr(cm, 'get_all_templates') else []
        batches = cm.get_all_batches()
        jobs = queue.get_all_jobs()

        result = {
            "synced": True,
            "accounts": len(accounts),
            "channels": len(channels),
            "templates": len(templates),
            "batches": len(batches),
            "jobs": len(jobs)
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@supabase_bp.route('/stats', methods=['GET'])
@require_auth
def supabase_stats():
    """Get Supabase dashboard stats."""
    supabase = get_supabase()
    if not supabase.is_connected():
        return jsonify({"connected": False}), 503
    try:
        stats = supabase.get_dashboard_stats()
        return jsonify({"connected": True, **stats})
    except Exception as e:
        return jsonify({"connected": True, "error": str(e)})


@supabase_bp.route('/health', methods=['GET'])
def supabase_health():
    """Check Supabase connection health."""
    supabase = get_supabase()
    connected = supabase.is_connected()
    return jsonify({
        "supabase_connected": connected,
        "status": "healthy" if connected else "degraded"
    })


@supabase_bp.route('/storage/upload', methods=['POST'])
@require_auth
def supabase_upload():
    """Upload a file to Supabase Storage."""
    supabase = get_supabase()
    if not supabase.is_connected():
        return jsonify({"error": "Supabase not connected"}), 503
    try:
        data = request.json or {}
        file_path = data.get('file_path')
        bucket = data.get('bucket', 'videos')
        channel_id = data.get('channel_id')
        if not file_path or not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 400
        url = supabase.upload_video(file_path, bucket, channel_id)
        if url:
            return jsonify({"success": True, "url": url})
        return jsonify({"error": "Upload failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@supabase_bp.route('/profile', methods=['GET'])
@require_auth
def get_supabase_profile():
    """Get current user's Supabase profile."""
    sm = get_supabase()
    if not sm.is_connected():
        return jsonify({"error": "Not connected"}), 503
    profile = sm.get_profile(request.auth_user['id'])
    if profile:
        return jsonify(profile)
    return jsonify({"error": "Profile not found"}), 404


@supabase_bp.route('/accounts', methods=['GET'])
@require_auth
def get_supabase_accounts():
    """Get all accounts for current user's profile."""
    sm = get_supabase()
    if not sm.is_connected():
        return jsonify({"error": "Not connected"}), 503
    accounts = sm.get_accounts(request.auth_user['id'])
    return jsonify(accounts)


@supabase_bp.route('/accounts', methods=['POST'])
@require_auth
def create_supabase_account():
    """Add a new account to current user's profile."""
    sm = get_supabase()
    if not sm.is_connected():
        return jsonify({"error": "Not connected"}), 503
    data = request.json or {}
    raw_type = data.get('account_type', 'personal')
    valid_types = ('personal', 'brand', 'business')
    account_type = raw_type if raw_type in valid_types else 'personal'
    try:
        account = sm.add_account(
            email=data.get('email', ''),
            display_name=data.get('display_name', ''),
            account_type=account_type,
            google_access_token=data.get('google_access_token'),
            google_refresh_token=data.get('google_refresh_token'),
            auth_user_id=request.auth_user['id']
        )
        if account:
            return jsonify(account), 201
        return jsonify({"error": "Failed to create account"}), 500
    except Exception as e:
        return jsonify({"error": "Failed to create account", "debug": str(e)}), 500


@supabase_bp.route('/accounts/<account_id>', methods=['DELETE'])
@require_auth
def delete_supabase_account(account_id: str):
    """Delete an account from current profile."""
    sm = get_supabase()
    if not sm.is_connected():
        return jsonify({"error": "Not connected"}), 503
    success = sm.delete_account(account_id)
    if success:
        return jsonify({"message": "Account deleted"})
    return jsonify({"error": "Account not found or access denied"}), 404


@supabase_bp.route('/connections', methods=['GET'])
@require_auth
def get_profile_connections():
    """Get profile connections for current user."""
    sm = get_supabase()
    if not sm.is_connected():
        return jsonify({"error": "Not connected"}), 503
    connections = sm.get_profile_connections()
    return jsonify(connections)


@supabase_bp.route('/connections', methods=['POST'])
@require_auth
def add_profile_connection():
    """Add a profile connection."""
    sm = get_supabase()
    if not sm.is_connected():
        return jsonify({"error": "Not connected"}), 503
    data = request.json or {}
    connection = sm.add_profile_connection(
        account_id=data.get('account_id', ''),
        connection_type=data.get('connection_type', 'google'),
        is_primary=data.get('is_primary', False)
    )
    if connection:
        return jsonify(connection), 201
    return jsonify({"error": "Failed to create connection"}), 500


@supabase_bp.route('/dashboard', methods=['GET'])
@require_auth
def supabase_dashboard():
    """Get Supabase dashboard stats and account summary."""
    sm = get_supabase()
    if not sm.is_connected():
        return jsonify({"error": "Not connected"}), 503
    stats = sm.get_dashboard_stats()
    accounts = sm.get_accounts()
    return jsonify({"stats": stats, "accounts": accounts, "account_count": len(accounts)})
