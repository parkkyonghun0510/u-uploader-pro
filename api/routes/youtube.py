"""YouTube Data API and Google OAuth2 integration routes."""
from datetime import datetime
from flask import Blueprint, request, jsonify
from api.extensions import logger
from api.auth import require_auth
from api.services.manager_service import (
    get_classes,
    get_google_oauth,
    get_oauth_manager,
    get_channel_manager,
)

youtube_bp = Blueprint('youtube', __name__)


# ============ YOUTUBE API ENDPOINTS ============

@youtube_bp.route('/api/youtube/auth', methods=['GET', 'POST'])
@require_auth
def youtube_auth():
    """Authenticate, configure, and inspect YouTube Data API key/status."""
    _, _, _, _, _, _, _, YouTubeAPI, _, _, _, _, _, _ = get_classes()
    if request.method == 'GET':
        api = YouTubeAPI()
        has_key = bool(api.api_key)
        masked = f"{api.api_key[:4]}...{api.api_key[-4:]}" if (api.api_key and len(api.api_key) > 8) else ("Configured" if has_key else "")
        return jsonify({
            "configured": has_key,
            "api_key_masked": masked
        })

    data = request.json or {}
    api_key = data.get('api_key')
    access_token = data.get('access_token')

    api = YouTubeAPI(access_token=access_token)
    if api_key:
        api.save_api_key(api_key)

    channels = api.get_my_channels()
    return jsonify({"message": "YouTube API connected", "channels": channels})


def _get_active_youtube_api(account_id: str = None, channel_id: str = None):
    """Instantiate YouTubeAPI configured with active OAuth access token, auto-refreshing if expired."""
    _, _, _, _, _, _, _, YouTubeAPI, _, _, _, _, _, _ = get_classes()
    oauth_mgr = get_oauth_manager()
    google_oauth = get_google_oauth()
    access_token = oauth_mgr.get_valid_access_token(
        account_id=account_id,
        channel_id=channel_id,
        google_oauth=google_oauth
    )
    return YouTubeAPI(access_token=access_token)


def _sync_channel_from_youtube_data(ch_dict: dict, account_id: str, channel_manager):
    """Helper to upsert a YouTube channel and its Studio metadata into ChannelManager."""
    if not ch_dict or not isinstance(ch_dict, dict):
        return None
    cid = ch_dict.get("id")
    if not cid:
        return None

    snippet = ch_dict.get("snippet", {})
    stats = ch_dict.get("statistics", {})
    branding = ch_dict.get("brandingSettings", {})

    channel_name = snippet.get("title") or "YouTube Channel"
    handle = snippet.get("customUrl", "")
    description = snippet.get("description", "")
    thumbs = snippet.get("thumbnails", {})
    avatar = (
        thumbs.get("high", {}).get("url") or
        thumbs.get("medium", {}).get("url") or
        thumbs.get("default", {}).get("url") or ""
    )
    banner = branding.get("image", {}).get("bannerExternalUrl", "")

    try:
        subs = int(stats.get("subscriberCount", 0))
    except (ValueError, TypeError):
        subs = 0
    try:
        vids = int(stats.get("videoCount", 0))
    except (ValueError, TypeError):
        vids = 0
    try:
        views = int(stats.get("viewCount", 0))
    except (ValueError, TypeError):
        views = 0

    existing = channel_manager.get_channel(cid)
    now_iso = datetime.now().isoformat()
    if existing:
        existing.account_id = account_id
        existing.name = channel_name
        existing.handle = handle
        existing.description = description
        existing.subscriber_count = subs
        existing.video_count = vids
        existing.view_count = views
        existing.custom_url = handle
        existing.thumbnail_url = avatar
        existing.banner_url = banner
        existing.last_sync = now_iso
        channel_manager._save_channels()
        channel_obj = existing
    else:
        channel_obj = channel_manager.add_channel(
            account_id=account_id,
            channel_id=cid,
            name=channel_name,
            handle=handle,
            description=description,
            is_managed=True,
            subscriber_count=subs,
            video_count=vids,
            view_count=views,
            custom_url=handle,
            thumbnail_url=avatar,
            banner_url=banner,
            last_sync=now_iso
        )

    # Link to account if present
    acc = channel_manager.get_account(account_id)
    if acc:
        if cid not in acc.channels:
            acc.channels.append(cid)
        if not acc.google_profile_image and avatar:
            acc.google_profile_image = avatar
        channel_manager._save_accounts()

    # Also persist to Supabase if connected
    try:
        from youtube_uploader_selenium.supabase_manager import SupabaseManager
        sm = SupabaseManager()
        if sm.is_connected():
            sm.upsert_channel(account_id, ch_dict)
    except Exception as e:
        logger.warning(f"Failed to upsert synced channel to Supabase: {e}")

    return channel_obj


@youtube_bp.route('/api/youtube/channels', methods=['GET'])
@require_auth
def youtube_get_channels():
    """Fetch current user channels from YouTube API."""
    api = _get_active_youtube_api(request.args.get('account_id'), channel_id=request.args.get('channel_id'))
    channels = api.get_my_channels()
    return jsonify(channels)


@youtube_bp.route('/api/youtube/channels/<channel_id>', methods=['GET'])
@require_auth
def youtube_get_channel_details(channel_id: str):
    """Fetch specific channel details from YouTube API."""
    api = _get_active_youtube_api(request.args.get('account_id'), channel_id=channel_id)
    details = api.get_channel_details(channel_id)
    if details:
        return jsonify(details)
    return jsonify({"error": "Channel not found"}), 404


@youtube_bp.route('/api/youtube/channels/<channel_id>/videos', methods=['GET'])
@require_auth
def youtube_get_channel_videos(channel_id: str):
    """Fetch videos for a given channel."""
    api = _get_active_youtube_api(request.args.get('account_id'), channel_id=channel_id)
    max_results = int(request.args.get('max_results', 50))
    videos = api.get_channel_videos(channel_id, max_results)
    return jsonify(videos)


@youtube_bp.route('/api/youtube/studio/<channel_id>', methods=['GET'])
@require_auth
def youtube_get_studio(channel_id: str):
    """Retrieve full YouTube Studio dashboard data for a channel."""
    api = _get_active_youtube_api(request.args.get('account_id'), channel_id=channel_id)
    studio_data = api.get_studio_dashboard(channel_id)

    # Fallback to locally cached data if API call failed
    if "error" in studio_data:
        cm = get_channel_manager()
        ch = cm.get_channel(channel_id)
        if ch:
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
                "analytics_summary": {
                    "subscribers": ch.subscriber_count,
                    "total_views": ch.view_count,
                    "total_videos": ch.video_count
                },
                "cached": True,
                "synced_at": ch.last_sync or datetime.now().isoformat()
            }
        else:
            return jsonify(studio_data), 404

    from api.routes.channels import _build_studio_links
    cm = get_channel_manager()
    ch = cm.get_channel(channel_id)
    aid = request.args.get('account_id') or (ch.account_id if ch else None)
    acc = cm.get_account(aid) if aid else None
    acc_email = acc.email if acc else ""

    studio_data["studio_links"] = _build_studio_links(channel_id, acc_email)
    studio_data["account_email"] = acc_email
    return jsonify(studio_data)


@youtube_bp.route('/api/youtube/sync-studio', methods=['POST'])
@require_auth
def youtube_sync_studio():
    """Sync YouTube Studio channel data and statistics for all or specified connected accounts."""
    data = request.get_json(silent=True) or {}
    target_account = data.get('account_id')
    target_channel = data.get('channel_id')

    oauth_mgr = get_oauth_manager()
    channel_manager = get_channel_manager()

    accounts_to_sync = []
    if target_account:
        token_entry = oauth_mgr.get_account_token(target_account)
        if token_entry:
            accounts_to_sync.append((target_account, token_entry))
    else:
        for aid, tdata in oauth_mgr._tokens.items():
            if aid.startswith("oauth-") or tdata.get("user_info"):
                accounts_to_sync.append((aid, tdata))

    synced_channels = []
    for aid, tdata in accounts_to_sync:
        api = _get_active_youtube_api(account_id=aid, channel_id=target_channel)
        channels = api.get_my_channels()
        for ch in channels:
            cid = ch.get("id")
            if target_channel and cid != target_channel:
                continue
            saved_ch = _sync_channel_from_youtube_data(ch, aid, channel_manager)
            if saved_ch:
                synced_channels.append(saved_ch.to_dict())

    return jsonify({
        "status": "success",
        "success": True,
        "message": f"Successfully synchronized {len(synced_channels)} channel(s) from YouTube Studio",
        "synced_channels": synced_channels,
        "count": len(synced_channels)
    })


@youtube_bp.route('/api/youtube/search', methods=['GET'])
@require_auth
def youtube_search():
    """Search videos or channels via YouTube API."""
    api = _get_active_youtube_api(request.args.get('account_id'), channel_id=request.args.get('channel_id'))
    query = request.args.get('q', '')
    max_results = int(request.args.get('max_results', 10))
    search_type = request.args.get('type', 'video')
    if search_type == 'channel':
        results = api.search_channels(query)
    else:
        results = api.search_videos(query, max_results)
    return jsonify(results)


@youtube_bp.route('/api/youtube/analytics/<channel_id>', methods=['GET'])
@require_auth
def youtube_analytics(channel_id: str):
    """Fetch analytics for a channel via YouTube API."""
    api = _get_active_youtube_api(request.args.get('account_id'), channel_id=channel_id)
    analytics = api.get_channel_analytics(channel_id)
    return jsonify(analytics)


def _build_redirect_uri(req, custom_uri: str = None) -> str:
    """Safely build OAuth redirect URI respecting proxy headers and env overrides."""
    if custom_uri:
        return custom_uri
    import os
    env_redirect = os.environ.get("OAUTH_REDIRECT_URI")
    if env_redirect:
        return env_redirect
    proto = req.headers.get('X-Forwarded-Proto', req.scheme)
    host = req.headers.get('X-Forwarded-Host', req.host)
    return f"{proto}://{host}/api/youtube/oauth/callback"


# ============ OAUTH2 ENDPOINTS ============

@youtube_bp.route('/api/youtube/oauth/config', methods=['GET'])
@require_auth
def youtube_oauth_config():
    """Check OAuth setup status and retrieve dynamic redirect URI."""
    oauth = get_google_oauth()
    redirect_uri = _build_redirect_uri(request)
    client = oauth.get_active_client(redirect_uri) if hasattr(oauth, 'get_active_client') else None
    is_configured = bool(client and client.get("is_valid", False))
    return jsonify({
        "configured": is_configured,
        "client": client,
        "redirect_uri": redirect_uri
    })


@youtube_bp.route('/api/oauth/google', methods=['GET', 'POST'])
@youtube_bp.route('/api/youtube/oauth/connect', methods=['GET', 'POST'])
@require_auth
def youtube_oauth_connect():
    """Generate Google OAuth2 authorization URL."""
    oauth = get_google_oauth()
    client_id = request.args.get('client_id')
    redirect_uri = request.args.get('redirect_uri')
    if not client_id and request.is_json and request.json:
        client_id = request.json.get('client_id')
        if not redirect_uri:
            redirect_uri = request.json.get('redirect_uri')

    # Resolve authenticated user ID if caller is logged in
    auth_user_id = None
    if hasattr(request, 'auth_user') and request.auth_user:
        auth_user_id = request.auth_user.get('id')
    if not auth_user_id:
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            tok = auth[7:]
            from api.services.manager_service import get_supabase
            sm = get_supabase()
            u = sm.verify_token(tok) if tok else None
            if u:
                auth_user_id = u.get('id')
    if not auth_user_id and request.is_json and request.json:
        auth_user_id = request.json.get('user_id')
    if not auth_user_id:
        auth_user_id = request.args.get('user_id')

    redirect_uri = _build_redirect_uri(request, redirect_uri)

    valid_clients = oauth.get_valid_clients() if hasattr(oauth, 'get_valid_clients') else oauth._clients
    if not client_id or client_id not in valid_clients:
        if valid_clients:
            sorted_clients = sorted(valid_clients.values(), key=lambda x: x.get("created_at", ""), reverse=True)
            client_id = sorted_clients[0]["client_id"]
        else:
            client_id = None

    auth_url = oauth.get_authorization_url(client_id, redirect_uri=redirect_uri, auth_user_id=auth_user_id) if client_id else None
    if auth_url:
        return jsonify({
            "auth_url": auth_url,
            "client_id": client_id,
            "redirect_uri": redirect_uri
        })
    return jsonify({
        "error": "Google OAuth client is not configured yet. Please configure your Client ID and Client Secret first.",
        "needs_configuration": True
    }), 404


@youtube_bp.route('/api/youtube/oauth/callback', methods=['GET'])
@require_auth
def youtube_oauth_callback():
    """Handle Google OAuth2 callback and token exchange."""
    code = request.args.get('code')
    client_id = request.args.get('client_id')
    state = request.args.get('state')
    redirect_uri = _build_redirect_uri(request, request.args.get('redirect_uri'))

    if not code:
        return jsonify({"error": "No authorization code provided"}), 400

    oauth = get_google_oauth()
    token_data = oauth.exchange_code(code, client_id=client_id, redirect_uri=redirect_uri, state=state)

    wants_html = request.accept_mimetypes.accept_html and 'application/json' not in request.headers.get('Accept', '')

    if not token_data or "error" in token_data:
        err_msg = token_data.get("error", "Token exchange failed") if token_data else "Failed to exchange code"
        if wants_html:
            return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Connection Failed</title>
<style>body{{background:#0f172a;color:#f8fafc;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}}
.card{{background:#1e293b;border:1px solid #ef4444;border-radius:12px;padding:32px;text-align:center;max-width:440px;}}
h2{{color:#ef4444;margin:0 0 12px;}}p{{color:#94a3b8;font-size:14px;margin-bottom:20px;}}
a{{display:inline-block;background:#3b82f6;color:#fff;text-decoration:none;padding:10px 20px;border-radius:8px;}}</style></head>
<body><div class="card"><h2>Authentication Failed</h2><p>{err_msg}</p><a href="/">Return to Dashboard</a></div>
<script>
try {{ new BroadcastChannel('youtube_oauth_channel').postMessage({{type:'OAUTH_COMPLETE',status:'error',error:'{err_msg}'}}); }} catch(e){{}}
try {{ localStorage.setItem('youtube_oauth_status', JSON.stringify({{status:'error',error:'{err_msg}',ts:Date.now()}})); }} catch(e){{}}
try {{ if(window.opener) window.opener.postMessage({{type:'OAUTH_COMPLETE',status:'error',error:'{err_msg}'}}, '*'); }} catch(e){{}}
</script>
</body></html>""", 400
        return jsonify({"error": err_msg}), 400

    # Save tokens to account
    manager = get_oauth_manager()
    user_info = token_data.get("user_info", {})
    email = user_info.get("email", "")
    display_name = user_info.get("name", email)
    picture = user_info.get("picture", "")
    auth_user_id = token_data.get("auth_user_id")

    # Multi-channel fleet detection
    channels_list = token_data.get("youtube_channels") or []
    youtube_channel = token_data.get("youtube_channel")
    if not channels_list and youtube_channel:
        channels_list = [youtube_channel]

    account_id = f"oauth-{email}" if email else "oauth-default"
    manager.save_account_token(account_id, token_data)

    # Update channel manager with connected account
    channel_manager = get_channel_manager()
    acc = channel_manager.get_account(account_id)
    if not acc and email:
        for a in channel_manager.get_all_accounts():
            if a.email == email:
                acc = a
                break

    if acc:
        acc.display_name = display_name
        if picture:
            acc.google_profile_image = picture
        acc.access_token = token_data.get("access_token")
        acc.refresh_token = token_data.get("refresh_token") or acc.refresh_token
        acc.last_login = datetime.now().isoformat()
        channel_manager._save_accounts()
    else:
        acc = channel_manager.add_account(
            account_id=account_id,
            email=email,
            display_name=display_name,
            account_type='personal',
            google_profile_image=picture,
            access_token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token")
        )

    # Sync all YouTube Studio channels into ChannelManager
    primary_channel_name = display_name
    for ch in channels_list:
        cid = ch.get("id")
        if cid:
            manager.save_account_token(cid, token_data)
        saved_ch = _sync_channel_from_youtube_data(ch, account_id, channel_manager)
        if saved_ch and primary_channel_name == display_name:
            primary_channel_name = saved_ch.name

    channel_name = primary_channel_name

    # Persist account and channels to Supabase database
    try:
        from api.services.manager_service import get_supabase
        sm = get_supabase()
        if sm.is_connected():
            saved_supa_acc = sm.add_account(
                email=email,
                display_name=display_name,
                account_type='personal',
                google_access_token=token_data.get("access_token"),
                google_refresh_token=token_data.get("refresh_token"),
                google_profile_image=picture,
                auth_user_id=auth_user_id
            )
            if saved_supa_acc and saved_supa_acc.get('id'):
                supa_acc_id = saved_supa_acc['id']
                manager.save_account_token(supa_acc_id, token_data)
                for ch in channels_list:
                    sm.upsert_channel(supa_acc_id, ch)
    except Exception as e:
        logger.warning(f"Could not persist connected account to Supabase: {e}")

    if wants_html:
        return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>YouTube Connected</title>
<style>
body{{background:#0f172a;color:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}}
.card{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:32px;text-align:center;max-width:440px;box-shadow:0 10px 25px rgba(0,0,0,0.5);}}
.icon{{font-size:48px;color:#22c55e;margin-bottom:12px;}}
h2{{margin:0 0 8px;font-size:22px;}}
p{{color:#94a3b8;font-size:14px;margin:0 0 20px;}}
.btn{{display:inline-block;background:#3b82f6;color:#fff;text-decoration:none;padding:10px 20px;border-radius:8px;font-size:14px;font-weight:500;}}
</style></head>
<body>
<div class="card">
  <div class="icon">✓</div>
  <h2>YouTube Account Connected!</h2>
  <p>Connected as <b>{channel_name}</b> ({email or 'Authorized'}). Returning to dashboard...</p>
  <a href="/" class="btn">Return to Dashboard</a>
</div>
<script>
// Notify opener window via BroadcastChannel, localStorage, and postMessage
try {{ new BroadcastChannel('youtube_oauth_channel').postMessage({{type:'OAUTH_COMPLETE',status:'success',message:'YouTube account connected successfully!'}}); }} catch(e){{}}
try {{ localStorage.setItem('youtube_oauth_status', JSON.stringify({{status:'success',message:'YouTube account connected successfully!',ts:Date.now()}})); }} catch(e){{}}
try {{ if(window.opener) window.opener.postMessage({{type:'OAUTH_COMPLETE',status:'success',message:'YouTube account connected successfully!'}},'*'); }} catch(e){{}}
setTimeout(function(){{
  try {{ window.close(); }} catch(e){{}}
  setTimeout(function(){{ window.location.href='/'; }}, 1000);
}}, 1200);
</script>
</body></html>"""

    return jsonify({
        "message": "YouTube account connected successfully!",
        "account_id": account_id,
        "user_info": user_info,
        "youtube_channel": youtube_channel,
        "redirect": "/"
    })


@youtube_bp.route('/api/youtube/oauth/status', methods=['GET'])
@require_auth
def youtube_oauth_status():
    """Check if user has valid OAuth tokens for account."""
    manager = get_oauth_manager()
    account_id = request.args.get('account_id')
    if not account_id:
        return jsonify({"connected": False})
    connected = manager.is_token_valid(account_id)
    token = manager.get_account_token(account_id)
    return jsonify({
        "connected": connected,
        "account_id": account_id,
        "email": token.get("user_info", {}).get("email") if token else None,
        "channel_name": token.get("youtube_channel", {}).get("snippet", {}).get("title") if token else None
    })


@youtube_bp.route('/api/youtube/oauth/register', methods=['POST'])
@require_auth
def youtube_oauth_register():
    """Register or update a Google OAuth client."""
    data = request.json or {}
    client_id = str(data.get('client_id', '')).strip()
    client_secret = str(data.get('client_secret', '')).strip()
    name = str(data.get('name', 'YouTube Upload Pro')).strip()

    if not client_id or not client_secret:
        return jsonify({"error": "client_id and client_secret are required"}), 400

    oauth = get_google_oauth()
    oauth.register_client(
        client_id=client_id,
        client_secret=client_secret,
        name=name
    )
    redirect_uri = f"{request.host_url.rstrip('/')}/api/youtube/oauth/callback"
    return jsonify({
        "message": "Google OAuth client registered successfully",
        "client_id": client_id,
        "redirect_uri": redirect_uri
    })
