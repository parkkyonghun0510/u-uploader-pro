import urllib.parse
from datetime import datetime
from flask import Blueprint, request, jsonify
from api.auth import require_auth
from api.services.manager_service import get_channel_manager, get_oauth_manager, get_supabase
from api.services.bulk_service import create_bulk_batch, get_bulk_status, get_all_bulk_batches

channels_bp = Blueprint('channels', __name__)


def _build_studio_links(channel_id: str, email: str = "") -> dict:
    """Build YouTube Studio URLs with multi-account authuser support."""
    is_valid_cid = bool(channel_id and channel_id.startswith("UC"))
    auth_param = f"?authuser={urllib.parse.quote(email)}" if email else ""
    base_url = f"https://studio.youtube.com/channel/{channel_id}" if is_valid_cid else "https://studio.youtube.com"
    return {
        "dashboard": f"{base_url}{auth_param}",
        "videos": f"{base_url}/videos/upload{auth_param}" if is_valid_cid else f"https://studio.youtube.com/videos/upload{auth_param}",
        "analytics": f"{base_url}/analytics/tab-overview{auth_param}" if is_valid_cid else f"https://studio.youtube.com/analytics{auth_param}",
        "customization": f"{base_url}/editing/sections{auth_param}" if is_valid_cid else f"https://studio.youtube.com/editing{auth_param}",
        "channel_switcher": "https://www.youtube.com/channel_switcher",
        "account_chooser": f"https://accounts.google.com/AccountChooser?service=youtube&continue={urllib.parse.quote(base_url)}"
    }


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

    # Retrieve stored accounts from database for current user
    sm = get_supabase()
    if sm.is_connected():
        auth_uid = getattr(request, 'auth_user', {}).get('id') if hasattr(request, 'auth_user') and request.auth_user else None
        supa_accs = sm.get_accounts(auth_uid)
        for sa in supa_accs:
            s_id = sa.get('id')
            s_email = sa.get('email')
            if s_id not in existing_ids and (not s_email or s_email not in existing_emails):
                tok = sa.get('google_access_token') or sa.get('access_token')
                ref = sa.get('google_refresh_token') or sa.get('refresh_token')
                img = sa.get('google_profile_image') or sa.get('avatar_url')
                acc_obj = {
                    "account_id": s_id,
                    "email": s_email or "",
                    "display_name": sa.get('display_name', s_email or 'YouTube Account'),
                    "account_type": sa.get('account_type', 'personal'),
                    "is_active": sa.get('is_active', True),
                    "is_verified": sa.get('is_verified', True),
                    "google_profile_image": img,
                    "channels": sa.get('channels', []),
                    "created_at": sa.get('created_at', ''),
                    "access_token": tok,
                    "refresh_token": ref
                }
                accounts.append(acc_obj)
                if s_email:
                    existing_emails.add(s_email)
                if s_id:
                    existing_ids.add(s_id)
                if tok:
                    oauth_mgr.save_account_token(s_id, {
                        "access_token": tok,
                        "refresh_token": ref,
                        "user_info": {
                            "email": s_email,
                            "name": sa.get('display_name', s_email),
                            "picture": img
                        }
                    })

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
                "access_token": tdata.get('access_token'),
                "refresh_token": tdata.get('refresh_token')
            })
            if email:
                existing_emails.add(email)
            existing_ids.add(aid)

    return jsonify(accounts)


@channels_bp.route('/api/channels/accounts/<account_id>', methods=['GET'])
@require_auth
def get_account_detail(account_id: str):
    """Retrieve details for a single YouTube account."""
    cm = get_channel_manager()
    acc = cm.get_account(account_id)
    if acc:
        return jsonify(acc.to_dict()), 200

    oauth_mgr = get_oauth_manager()
    tdata = oauth_mgr.get_account_token(account_id)
    if tdata:
        uinfo = tdata.get('user_info', {})
        yt_ch = tdata.get('youtube_channel') or {}
        return jsonify({
            "account_id": account_id,
            "email": uinfo.get('email', ''),
            "display_name": uinfo.get('name', ''),
            "account_type": "personal",
            "is_active": True,
            "is_verified": True,
            "google_profile_image": uinfo.get('picture', None),
            "channels": [yt_ch.get('id')] if yt_ch.get('id') else [],
            "created_at": tdata.get('connected_at', ''),
            "access_token": tdata.get('access_token'),
            "refresh_token": tdata.get('refresh_token')
        }), 200

    sm = get_supabase()
    if sm.is_connected():
        supa_acc = sm.get_account(account_id)
        if supa_acc:
            return jsonify({
                "account_id": supa_acc.get('id', account_id),
                "email": supa_acc.get('email', ''),
                "display_name": supa_acc.get('display_name', ''),
                "account_type": supa_acc.get('account_type', 'personal'),
                "is_active": supa_acc.get('is_active', True),
                "is_verified": supa_acc.get('is_verified', True),
                "google_profile_image": supa_acc.get('google_profile_image'),
                "channels": supa_acc.get('channels', []),
                "created_at": supa_acc.get('created_at', ''),
                "access_token": supa_acc.get('google_access_token'),
                "refresh_token": supa_acc.get('google_refresh_token')
            }), 200

    return jsonify({"error": "Account not found"}), 404


@channels_bp.route('/api/channels/accounts/<account_id>/sync', methods=['POST'])
@require_auth
def sync_account_studio(account_id: str):
    """Sync YouTube Studio channels and data for a given account."""
    from api.routes.youtube import _get_active_youtube_api, _sync_channel_from_youtube_data
    cm = get_channel_manager()
    api = _get_active_youtube_api(account_id=account_id)
    channels = api.get_my_channels()
    synced = []
    for ch in channels:
        obj = _sync_channel_from_youtube_data(ch, account_id, cm)
        if obj:
            synced.append(obj.to_dict())

    # Fallback to existing channels in ChannelManager or Supabase if none returned by API
    if not synced:
        acc_channels = cm.get_channels_by_account(account_id)
        for c in acc_channels:
            synced.append(c.to_dict())

    sm = get_supabase()
    if not synced and sm.is_connected():
        supa_chs = sm.get_channels(account_id=account_id)
        for sc in supa_chs:
            synced.append(sc)

    return jsonify({
        "status": "success",
        "success": True,
        "message": f"Synchronized {len(synced)} channel(s) from YouTube Studio",
        "channels": synced
    }), 200


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

    # Also load from Supabase channels for current user
    sm = get_supabase()
    if sm.is_connected():
        auth_uid = getattr(request, 'auth_user', {}).get('id') if hasattr(request, 'auth_user') and request.auth_user else None
        supa_channels = sm.get_channels(account_id=account_filter, auth_user_id=auth_uid)
        for sc in supa_channels:
            cid = sc.get('channel_id')
            if cid and cid not in existing_cids:
                branding = sc.get('branding_settings') or {}
                avatar = branding.get('avatar', '') if isinstance(branding, dict) else ''
                ch_list.append({
                    "channel_id": cid,
                    "account_id": sc.get('account_id', ''),
                    "name": sc.get('name', 'YouTube Channel'),
                    "handle": sc.get('handle', ''),
                    "description": sc.get('description', ''),
                    "status": sc.get('status', 'active'),
                    "account_type": "personal",
                    "is_managed": sc.get('is_managed', True),
                    "subscriber_count": sc.get('subscriber_count', 0),
                    "video_count": sc.get('video_count', 0),
                    "view_count": sc.get('view_count', 0),
                    "thumbnail_url": sc.get('custom_url') or avatar or '',
                    "created_at": sc.get('created_at', '')
                })
                existing_cids.add(cid)

    for aid, tdata in oauth_mgr._tokens.items():
        # Check both single youtube_channel and youtube_channels array
        channels_candidates = tdata.get('youtube_channels') or []
        single_ch = tdata.get('youtube_channel')
        if not channels_candidates and single_ch and isinstance(single_ch, dict):
            channels_candidates = [single_ch]

        for yt_ch in channels_candidates:
            if yt_ch and isinstance(yt_ch, dict):
                cid = yt_ch.get('id')
                if cid and cid not in existing_cids:
                    if account_filter and account_filter != aid:
                        continue
                    snippet = yt_ch.get('snippet', {})
                    stats = yt_ch.get('statistics', {})
                    thumbs = snippet.get('thumbnails', {})
                    avatar = (
                        thumbs.get('high', {}).get('url') or
                        thumbs.get('medium', {}).get('url') or
                        thumbs.get('default', {}).get('url')
                    )
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
                        "thumbnail_url": avatar,
                        "created_at": tdata.get('connected_at', '')
                    })
                    existing_cids.add(cid)

    return jsonify(ch_list)


@channels_bp.route('/api/channels/<channel_id>', methods=['GET'])
@require_auth
def get_channel_detail(channel_id: str):
    """Retrieve details for a single managed channel."""
    cm = get_channel_manager()
    ch = cm.get_channel(channel_id)
    if ch:
        return jsonify(ch.to_dict()), 200

    oauth_mgr = get_oauth_manager()
    for aid, tdata in oauth_mgr._tokens.items():
        candidates = tdata.get('youtube_channels') or []
        single = tdata.get('youtube_channel')
        if not candidates and single and isinstance(single, dict):
            candidates = [single]

        for yt_ch in candidates:
            if yt_ch and isinstance(yt_ch, dict) and yt_ch.get('id') == channel_id:
                snippet = yt_ch.get('snippet', {})
                stats = yt_ch.get('statistics', {})
                thumbs = snippet.get('thumbnails', {})
                avatar = (
                    thumbs.get('high', {}).get('url') or
                    thumbs.get('medium', {}).get('url') or
                    thumbs.get('default', {}).get('url')
                )
                return jsonify({
                    "channel_id": channel_id,
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
                    "thumbnail_url": avatar,
                    "created_at": tdata.get('connected_at', '')
                }), 200

    return jsonify({"error": "Channel not found"}), 404


@channels_bp.route('/api/channels/<channel_id>/sync', methods=['POST'])
@require_auth
def sync_single_channel(channel_id: str):
    """Sync YouTube Studio data for a single channel or account."""
    from api.routes.youtube import _get_active_youtube_api, _sync_channel_from_youtube_data
    cm = get_channel_manager()
    oauth_mgr = get_oauth_manager()
    sm = get_supabase()

    # Delegate to account sync if channel_id is formatted as an account ID or email
    is_account = (
        channel_id.startswith("oauth-")
        or "@" in channel_id
        or cm.get_account(channel_id) is not None
        or oauth_mgr.get_account_token(channel_id) is not None
        or (sm.is_connected() and sm.get_account(channel_id) is not None)
    )
    if is_account:
        return sync_account_studio(channel_id)

    ch = cm.get_channel(channel_id)
    aid = ch.account_id if ch else None
    api = _get_active_youtube_api(account_id=aid, channel_id=channel_id)
    details = api.get_channel_details(channel_id)
    if not details:
        channels = api.get_my_channels()
        for c in channels:
            if c.get("id") == channel_id:
                details = c
                break
    if details:
        updated_ch = _sync_channel_from_youtube_data(details, aid or f"oauth-{channel_id}", cm)
        if updated_ch:
            return jsonify({"status": "success", "success": True, "channel": updated_ch.to_dict()}), 200
    if ch:
        return jsonify({"status": "success", "success": True, "channel": ch.to_dict(), "cached": True}), 200

    if sm.is_connected():
        supa_ch = sm.get_channel(channel_id)
        if supa_ch:
            return jsonify({"status": "success", "success": True, "channel": supa_ch, "cached": True}), 200

    return jsonify({"error": "Failed to sync channel from YouTube Studio"}), 400


@channels_bp.route('/api/channels/<channel_id>/studio', methods=['GET'])
@require_auth
def get_channel_studio_hub(channel_id: str):
    """Retrieve full YouTube Studio dashboard intelligence for a channel."""
    from api.routes.youtube import _get_active_youtube_api
    cm = get_channel_manager()
    ch = cm.get_channel(channel_id)
    aid = ch.account_id if ch else None
    if not ch:
        if channel_id.startswith("oauth-") or "@" in channel_id or cm.get_account(channel_id):
            acc_channels = cm.get_channels_by_account(channel_id)
            if acc_channels:
                ch = acc_channels[0]
                channel_id = ch.channel_id
                aid = ch.account_id

    api = _get_active_youtube_api(account_id=aid, channel_id=channel_id)
    studio_data = api.get_studio_dashboard(channel_id)
    if "error" in studio_data and ch:
        studio_data = {
            "channel": {
                "id": ch.channel_id,
                "title": ch.name,
                "handle": ch.handle,
                "custom_url": ch.custom_url or ch.handle,
                "description": ch.description,
                "subscriber_count": ch.subscriber_count,
                "video_count": ch.video_count,
                "view_count": ch.view_count,
                "avatar_url": ch.thumbnail_url or "",
                "banner_url": ch.banner_url or "",
                "studio_url": f"https://studio.youtube.com/channel/{ch.channel_id}",
                "studio_analytics_url": f"https://studio.youtube.com/channel/{ch.channel_id}/analytics/tab-overview",
                "studio_content_url": f"https://studio.youtube.com/channel/{ch.channel_id}/videos/upload"
            },
            "recent_videos": [],
            "cached": True,
            "synced_at": ch.last_sync or ch.created_at
        }

    acc = cm.get_account(aid) if aid else None
    acc_email = acc.email if acc else ""
    if not acc_email and ch and getattr(ch, 'account_id', None):
        acc = cm.get_account(ch.account_id)
        if acc:
            acc_email = acc.email

    studio_data["studio_links"] = _build_studio_links(channel_id, acc_email)
    studio_data["account_email"] = acc_email
    return jsonify(studio_data)


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

    allowed_fields = {
        'name', 'handle', 'description', 'is_managed', 'status',
        'default_language', 'country', 'custom_url',
        'thumbnail_url', 'banner_url', 'subscriber_count', 'video_count', 'view_count'
    }
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


@channels_bp.route('/api/templates/<template_id>', methods=['GET'])
@require_auth
def get_template(template_id: str):
    """Retrieve a single metadata template by ID."""
    cm = get_channel_manager()
    template = cm.get_template(template_id)
    if template:
        return jsonify(template.to_dict()), 200
    return jsonify({"error": "Template not found"}), 404


@channels_bp.route('/api/templates/<template_id>', methods=['PATCH'])
@require_auth
def patch_template(template_id: str):
    """Partially update an existing metadata template."""
    cm = get_channel_manager()
    template = cm.get_template(template_id)
    if not template:
        return jsonify({"error": "Template not found"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid request body"}), 400

    allowed_fields = {
        'name', 'title_template', 'description_template', 'tags',
        'category', 'language', 'privacy_status', 'made_for_kids',
        'upload_schedule', 'is_default'
    }
    disallowed = set(data.keys()) - allowed_fields
    if disallowed:
        return jsonify({"error": f"Disallowed fields in patch: {', '.join(sorted(disallowed))}"}), 400

    updated = cm.update_template(template_id, **data)
    return jsonify(updated.to_dict()), 200


@channels_bp.route('/api/templates/<template_id>', methods=['DELETE'])
@require_auth
def delete_template(template_id: str):
    """Delete a metadata template."""
    cm = get_channel_manager()
    if template_id in cm._templates:
        cm._templates.pop(template_id, None)
        cm._save_templates()
        return jsonify({"message": "Template deleted"}), 200
    return jsonify({"error": "Template not found"}), 404


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


@channels_bp.route('/api/batches/<batch_id>', methods=['PATCH'])
@require_auth
def patch_batch(batch_id: str):
    """Partially update a bulk upload batch."""
    cm = get_channel_manager()
    batch = cm.get_batch(batch_id)
    if not batch:
        return jsonify({"error": "Batch not found"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid request body"}), 400

    allowed_fields = {'name', 'priority', 'status'}
    disallowed = set(data.keys()) - allowed_fields
    if disallowed:
        return jsonify({"error": f"Disallowed fields in patch: {', '.join(sorted(disallowed))}"}), 400

    updated = cm.update_batch(batch_id, **data)
    return jsonify(updated.to_dict()), 200


@channels_bp.route('/api/batches/<batch_id>', methods=['DELETE'])
@require_auth
def delete_batch(batch_id: str):
    """Delete a bulk upload batch from history."""
    cm = get_channel_manager()
    if cm.delete_batch(batch_id):
        return jsonify({"message": "Batch deleted successfully"})
    return jsonify({"error": "Batch not found"}), 404
