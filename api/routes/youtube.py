"""YouTube Data API and Google OAuth2 integration routes."""
from flask import Blueprint, request, jsonify
from api.services.manager_service import (
    get_classes,
    get_google_oauth,
    get_oauth_manager,
    get_channel_manager,
)

youtube_bp = Blueprint('youtube', __name__)


# ============ YOUTUBE API ENDPOINTS ============

@youtube_bp.route('/api/youtube/auth', methods=['POST'])
def youtube_auth():
    """Authenticate and test connection to YouTube Data API."""
    _, _, _, _, _, _, _, YouTubeAPI, _, _, _, _, _, _ = get_classes()
    data = request.json or {}
    api_key = data.get('api_key')
    access_token = data.get('access_token')

    api = YouTubeAPI(access_token=access_token)
    if api_key:
        api.save_api_key(api_key)

    channels = api.get_my_channels()
    return jsonify({"message": "YouTube API connected", "channels": channels})


@youtube_bp.route('/api/youtube/channels', methods=['GET'])
def youtube_get_channels():
    """Fetch current user channels from YouTube API."""
    _, _, _, _, _, _, _, YouTubeAPI, _, _, _, _, _, _ = get_classes()
    api = YouTubeAPI()
    channels = api.get_my_channels()
    return jsonify(channels)


@youtube_bp.route('/api/youtube/channels/<channel_id>', methods=['GET'])
def youtube_get_channel_details(channel_id: str):
    """Fetch specific channel details from YouTube API."""
    _, _, _, _, _, _, _, YouTubeAPI, _, _, _, _, _, _ = get_classes()
    api = YouTubeAPI()
    details = api.get_channel_details(channel_id)
    if details:
        return jsonify(details)
    return jsonify({"error": "Channel not found"}), 404


@youtube_bp.route('/api/youtube/channels/<channel_id>/videos', methods=['GET'])
def youtube_get_channel_videos(channel_id: str):
    """Fetch videos for a given channel."""
    _, _, _, _, _, _, _, YouTubeAPI, _, _, _, _, _, _ = get_classes()
    api = YouTubeAPI()
    max_results = int(request.args.get('max_results', 50))
    videos = api.get_channel_videos(channel_id, max_results)
    return jsonify(videos)


@youtube_bp.route('/api/youtube/search', methods=['GET'])
def youtube_search():
    """Search videos or channels via YouTube API."""
    _, _, _, _, _, _, _, YouTubeAPI, _, _, _, _, _, _ = get_classes()
    api = YouTubeAPI()
    query = request.args.get('q', '')
    max_results = int(request.args.get('max_results', 10))
    search_type = request.args.get('type', 'video')
    if search_type == 'channel':
        results = api.search_channels(query)
    else:
        results = api.search_videos(query, max_results)
    return jsonify(results)


@youtube_bp.route('/api/youtube/analytics/<channel_id>', methods=['GET'])
def youtube_analytics(channel_id: str):
    """Fetch analytics for a channel via YouTube API."""
    _, _, _, _, _, _, _, YouTubeAPI, _, _, _, _, _, _ = get_classes()
    api = YouTubeAPI()
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
def youtube_oauth_connect():
    """Generate Google OAuth2 authorization URL."""
    oauth = get_google_oauth()
    client_id = request.args.get('client_id')
    redirect_uri = request.args.get('redirect_uri')
    if not client_id and request.is_json and request.json:
        client_id = request.json.get('client_id')
        if not redirect_uri:
            redirect_uri = request.json.get('redirect_uri')

    redirect_uri = _build_redirect_uri(request, redirect_uri)

    valid_clients = oauth.get_valid_clients() if hasattr(oauth, 'get_valid_clients') else oauth._clients
    if not client_id or client_id not in valid_clients:
        if valid_clients:
            sorted_clients = sorted(valid_clients.values(), key=lambda x: x.get("created_at", ""), reverse=True)
            client_id = sorted_clients[0]["client_id"]
        else:
            client_id = None

    auth_url = oauth.get_authorization_url(client_id, redirect_uri=redirect_uri) if client_id else None
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
    youtube_channel = token_data.get("youtube_channel", {})
    channel_id = youtube_channel.get("id", "") if youtube_channel else ""

    account_id = f"oauth-{email}" if email else "oauth-default"
    manager.save_account_token(account_id, token_data)

    # Update channel manager with connected account
    channel_manager = get_channel_manager()
    acc = channel_manager.get_account(account_id)
    if not acc and email:
        channel_manager.add_account(
            email=email,
            display_name=display_name,
            account_type='personal',
            access_token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token")
        )

    channel_name = youtube_channel.get("snippet", {}).get("title", display_name) if youtube_channel else display_name
    existing = channel_manager.get_channel(channel_id) if channel_id else None
    if not existing and channel_id:
        channel_manager.add_channel(
            account_id=account_id,
            channel_id=channel_id,
            name=channel_name,
            handle=youtube_channel.get("snippet", {}).get("customUrl", ""),
            description=youtube_channel.get("snippet", {}).get("description", ""),
            is_managed=True
        )

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
