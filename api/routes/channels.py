"""Channels, channel accounts, metadata templates, and batch upload routes."""
from flask import Blueprint, request, jsonify
from api.auth import require_auth
from api.services.manager_service import get_channel_manager, get_oauth_manager
from api.services.bulk_service import create_bulk_batch, get_bulk_status, get_all_bulk_batches

channels_bp = Blueprint('channels', __name__)


# ============ CHANNEL ACCOUNTS ============

@channels_bp.route('/api/channels/accounts', methods=['GET'])
@require_auth
def get_accounts():
    """List all configured YouTube accounts."""
    cm = get_channel_manager()
    accounts = [acc.to_dict() for acc in cm.get_all_accounts()]

    oauth_mgr = get_oauth_manager()
    existing_emails = {a.get('email') for a in accounts if a.get('email')}
    existing_ids = {a.get('account_id') for a in accounts if a.get('account_id')}

    for aid, tdata in oauth_mgr._tokens.items():
        uinfo = tdata.get('user_info', {})
        email = uinfo.get('email', '')
        if (email and email not in existing_emails) and (aid not in existing_ids):
            yt_ch = tdata.get('youtube_channel') or {}
            accounts.append({
                "account_id": aid,
                "email": email,
                "display_name": uinfo.get('name', email),
                "account_type": "personal",
                "is_active": True,
                "is_verified": True,
                "google_profile_image": uinfo.get('picture', None),
                "channels": [yt_ch.get('id')] if yt_ch.get('id') else [],
                "created_at": tdata.get('connected_at', ''),
                "access_token": tdata.get('access_token')
            })
            if email:
                existing_emails.add(email)
            existing_ids.add(aid)

    return jsonify(accounts)


@channels_bp.route('/api/channels/accounts', methods=['POST'])
@require_auth
def create_account():
    """Add a new YouTube account."""
    cm = get_channel_manager()
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid request body"}), 400

    email = str(data.get('email', '')).strip()
    display_name = str(data.get('display_name', '')).strip()
    if not email or not display_name:
        return jsonify({"error": "email and display_name are required"}), 400

    valid_types = ('personal', 'brand', 'business')
    if 'account_type' in data:
        account_type = data['account_type']
        if account_type not in valid_types:
            return jsonify({"error": f"Invalid account_type. Must be one of: {', '.join(valid_types)}"}), 400
    else:
        account_type = 'personal'

    try:
        account = cm.add_account(
            email=email,
            display_name=display_name,
            account_type=account_type,
            access_token=data.get('access_token'),
            refresh_token=data.get('refresh_token')
        )
        return jsonify(account.to_dict()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@channels_bp.route('/api/channels/accounts/<account_id>', methods=['PATCH'])
@require_auth
def patch_account(account_id: str):
    """Partially update an account."""
    cm = get_channel_manager()
    account = cm.get_account(account_id)
    if not account:
        return jsonify({"error": "Account not found"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid request body"}), 400

    allowed_fields = {'display_name', 'email', 'account_type', 'google_profile_image', 'is_active'}
    disallowed = set(data.keys()) - allowed_fields
    if disallowed:
        return jsonify({"error": f"Disallowed fields in patch: {', '.join(sorted(disallowed))}"}), 400

    if 'account_type' in data:
        valid_types = ('personal', 'brand', 'business')
        if data['account_type'] not in valid_types:
            return jsonify({"error": f"Invalid account_type. Must be one of: {', '.join(valid_types)}"}), 400

    updated = cm.update_account(account_id, **data)
    return jsonify(updated.to_dict()), 200


@channels_bp.route('/api/channels/accounts/<account_id>', methods=['DELETE'])
@require_auth
def delete_account(account_id: str):
    """Delete a YouTube account."""
    cm = get_channel_manager()
    oauth_mgr = get_oauth_manager()

    account = cm.get_account(account_id)
    token = oauth_mgr.get_account_token(account_id)
    if not account and not token:
        return jsonify({"error": "Account not found"}), 404

    if account:
        channels = cm.get_channels_by_account(account_id)
        force = request.args.get('force', '').lower() in ('true', '1')
        if channels and not force:
            return jsonify({
                "error": "Account has associated channels. Pass ?force=true to cascade delete.",
                "channel_count": len(channels)
            }), 409
        cm.remove_account(account_id)

    if token:
        oauth_mgr.remove_account_token(account_id)

    return jsonify({"message": "Account deleted"}), 200


@channels_bp.route('/api/channels/browser-profiles', methods=['GET'])
def get_browser_profiles():
    """List detected Firefox browser profiles and their cookie status."""
    from pathlib import Path
    profiles = []
    base_dir = Path.cwd()

    # Check default ./profile
    default_p = base_dir / "profile"
    if default_p.exists():
        has_cookies = any(default_p.glob("*cookie*")) or any(default_p.glob("*.pkl")) or any(default_p.glob("*.sqlite"))
        profiles.append({
            "name": "default",
            "path": str(default_p),
            "has_cookies": has_cookies
        })

    # Check ./profiles/ directory
    profiles_dir = base_dir / "profiles"
    if profiles_dir.exists() and profiles_dir.is_dir():
        for child in sorted(profiles_dir.iterdir()):
            if child.is_dir():
                has_cookies = any(child.glob("*cookie*")) or any(child.glob("*.pkl")) or any(child.glob("*.sqlite"))
                profiles.append({
                    "name": child.name,
                    "path": str(child),
                    "has_cookies": has_cookies
                })

    return jsonify(profiles)


# ============ CHANNELS ============

@channels_bp.route('/api/channels', methods=['GET'])
@require_auth
def get_channels():
    """List all managed YouTube channels, optionally filtered by account_id."""
    cm = get_channel_manager()
    account_filter = request.args.get('account_id', None)
    if account_filter:
        channels = cm.get_channels_by_account(account_filter)
    else:
        channels = cm.get_all_channels()
    ch_list = [ch.to_dict() for ch in channels]

    oauth_mgr = get_oauth_manager()
    existing_cids = {c.get('channel_id') for c in ch_list if c.get('channel_id')}
    for aid, tdata in oauth_mgr._tokens.items():
        yt_ch = tdata.get('youtube_channel')
        if yt_ch and isinstance(yt_ch, dict):
            cid = yt_ch.get('id')
            if cid and cid not in existing_cids:
                if account_filter and account_filter != aid:
                    continue
                snippet = yt_ch.get('snippet', {})
                stats = yt_ch.get('statistics', {})
                ch_list.append({
                    "channel_id": cid,
                    "account_id": aid,
                    "name": snippet.get('title', 'YouTube Channel'),
                    "handle": snippet.get('customUrl', ''),
                    "description": snippet.get('description', ''),
                    "status": "active",
                    "account_type": "personal",
                    "is_managed": True,
                    "subscriber_count": int(stats.get('subscriberCount', 0)),
                    "video_count": int(stats.get('videoCount', 0)),
                    "view_count": int(stats.get('viewCount', 0)),
                    "created_at": tdata.get('connected_at', '')
                })
                existing_cids.add(cid)

    return jsonify(ch_list)


@channels_bp.route('/api/channels', methods=['POST'])
@require_auth
def create_channel():
    """Add a new managed channel."""
    cm = get_channel_manager()
    oauth_mgr = get_oauth_manager()
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid request body"}), 400

    account_id = str(data.get('account_id', '')).strip()
    channel_id = str(data.get('channel_id', '')).strip()
    name = str(data.get('name', '')).strip()

    if not account_id or not channel_id or not name:
        return jsonify({"error": "account_id, channel_id, and name are required"}), 400

    account = cm.get_account(account_id)
    oauth_token = oauth_mgr.get_account_token(account_id)
    if not account and not oauth_token:
        return jsonify({"error": "Unknown account_id"}), 400

    if not account and oauth_token:
        uinfo = oauth_token.get('user_info', {})
        account = cm.add_account(
            email=uinfo.get('email', 'oauth@google.com'),
            display_name=uinfo.get('name', 'Google Account'),
            account_type='personal',
            access_token=oauth_token.get('access_token'),
            refresh_token=oauth_token.get('refresh_token'),
            account_id=account_id
        )

    try:
        channel = cm.add_channel(
            account_id=account_id,
            channel_id=channel_id,
            name=name,
            handle=data.get('handle', ''),
            description=data.get('description', ''),
            is_managed=data.get('is_managed', False)
        )
        return jsonify(channel.to_dict()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@channels_bp.route('/api/channels/<channel_id>', methods=['PATCH'])
@require_auth
def patch_channel(channel_id: str):
    """Partially update a managed channel."""
    cm = get_channel_manager()
    channel = cm.get_channel(channel_id)
    if not channel:
        return jsonify({"error": "Channel not found"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid request body"}), 400

    allowed_fields = {'name', 'handle', 'description', 'is_managed', 'status', 'default_language', 'country', 'custom_url'}
    disallowed = set(data.keys()) - allowed_fields
    if disallowed:
        return jsonify({"error": f"Disallowed fields in patch: {', '.join(sorted(disallowed))}"}), 400

    updated = cm.update_channel(channel_id, **data)
    return jsonify(updated.to_dict()), 200


@channels_bp.route('/api/channels/<channel_id>', methods=['DELETE'])
@require_auth
def delete_channel(channel_id: str):
    """Delete a managed channel."""
    cm = get_channel_manager()
    oauth_mgr = get_oauth_manager()

    channel = cm.get_channel(channel_id)
    found_in_oauth = False
    for aid, tdata in list(oauth_mgr._tokens.items()):
        yt_ch = tdata.get('youtube_channel')
        if yt_ch and isinstance(yt_ch, dict) and yt_ch.get('id') == channel_id:
            tdata['youtube_channel'] = None
            oauth_mgr._save_tokens()
            found_in_oauth = True

    if not channel and not found_in_oauth:
        return jsonify({"error": "Channel not found"}), 404
    if channel:
        cm.remove_channel(channel_id)
    return jsonify({"message": "Channel deleted"}), 200


@channels_bp.route('/api/channels/<channel_id>/analytics', methods=['GET'])
@require_auth
def get_channel_analytics(channel_id: str):
    """Retrieve channel analytics."""
    cm = get_channel_manager()
    channel = cm.get_channel(channel_id)
    if not channel:
        return jsonify({"error": "Channel not found"}), 404
    analytics = cm.get_channel_analytics(channel_id)
    return jsonify(analytics)



# ============ METADATA TEMPLATES ============

@channels_bp.route('/api/templates', methods=['GET'])
@require_auth
def get_templates():
    """List metadata templates, optionally filtered by channel_id."""
    cm = get_channel_manager()
    channel_id = request.args.get('channel_id', None)
    if channel_id:
        templates = cm.get_templates_by_channel(channel_id)
    else:
        templates = cm.get_all_templates() if hasattr(cm, 'get_all_templates') else []
    return jsonify([t.to_dict() for t in templates])


@channels_bp.route('/api/templates', methods=['POST'])
@require_auth
def create_template():
    """Create a new metadata template."""
    cm = get_channel_manager()
    data = request.json or {}
    template = cm.add_template(
        channel_id=data.get('channel_id', ''),
        name=data.get('name', ''),
        title_template=data.get('title_template', ''),
        description_template=data.get('description_template', ''),
        tags=data.get('tags', []),
        category=data.get('category', '22'),
        language=data.get('language', 'en'),
        privacy_status=data.get('privacy_status', 'private'),
        upload_schedule=data.get('upload_schedule')
    )
    return jsonify(template.to_dict()), 201


@channels_bp.route('/api/templates/<template_id>', methods=['DELETE'])
@require_auth
def delete_template(template_id: str):
    """Delete a metadata template."""
    cm = get_channel_manager()
    cm._templates.pop(template_id, None)
    cm._save_templates()
    return jsonify({"message": "Template deleted"})


# ============ BULK UPLOAD BATCHES ============

@channels_bp.route('/api/batches', methods=['GET'])
@require_auth
def get_batches():
    """List all bulk upload batches."""
    cm = get_channel_manager()
    return jsonify([b.to_dict() for b in cm.get_all_batches()])


@channels_bp.route('/api/batches', methods=['POST'])
@require_auth
def create_batch():
    """Create and execute a bulk multi-channel upload batch."""
    data = request.json or {}
    cm = get_channel_manager()

    video_paths = data.get('video_paths', [])
    channel_ids = data.get('channel_ids', [])
    channel_id = data.get('channel_id') or (channel_ids[0] if channel_ids else '')

    if video_paths and channel_ids:
        try:
            create_bulk_batch(
                video_paths=video_paths,
                channel_ids=channel_ids,
                metadata={'template_id': data.get('template_id')} if data.get('template_id') else None,
                priority=data.get('priority', 'normal')
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    name = data.get('name', f"Batch {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    total_videos = data.get('total_videos', len(video_paths))
    batch = cm.create_batch(
        channel_id=channel_id,
        account_id=data.get('account_id', ''),
        name=name,
        video_paths=video_paths,
        template_id=data.get('template_id'),
        priority=data.get('priority', 'normal')
    )
    if total_videos > 0:
        batch.total_videos = total_videos
        cm._save_batches()

    return jsonify(batch.to_dict()), 201


@channels_bp.route('/api/batches/<batch_id>', methods=['GET'])
@require_auth
def get_batch(batch_id: str):
    """Retrieve batch details by batch_id."""
    cm = get_channel_manager()
    batch = cm.get_batch(batch_id)
    if batch:
        return jsonify(batch.to_dict())
    return jsonify({"error": "Batch not found"}), 404


@channels_bp.route('/api/batches/<batch_id>', methods=['DELETE'])
@require_auth
def delete_batch(batch_id: str):
    """Delete a bulk upload batch from history."""
    cm = get_channel_manager()
    if cm.delete_batch(batch_id):
        return jsonify({"message": "Batch deleted successfully"})
    return jsonify({"error": "Batch not found"}), 404
