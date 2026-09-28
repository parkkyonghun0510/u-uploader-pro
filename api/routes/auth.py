"""Authentication routes for signup, login, logout, and current user info."""
from flask import Blueprint, request, jsonify
from api.auth import require_auth
from api.services.manager_service import get_supabase

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/signup', methods=['POST'])
def auth_signup():
    """Register a new user account with Supabase."""
    supabase = get_supabase()
    if not supabase.is_connected():
        return jsonify({"error": "Not connected"}), 503

    data = request.json or {}
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''
    display_name = (data.get('display_name') or '').strip() or email.split('@')[0]

    if not email or '@' not in email:
        return jsonify({"error": "Valid email required"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    result = supabase.sign_up(email, password, display_name)
    if not result:
        err = getattr(supabase, 'last_auth_error', None)
        msg = "Signup failed. The email may already be registered or invalid."
        if err:
            if "already registered" in err.lower():
                msg = "This email is already registered. Please switch to the Sign In tab."
            elif "rate limit" in err.lower():
                msg = "Supabase email rate limit reached. Please wait a few minutes before trying again, or try signing in if you already registered."
            elif "invalid" in err.lower() and "email" in err.lower():
                msg = "Please enter a valid, deliverable email address."
            else:
                msg = f"Signup error: {err}"
        return jsonify({"error": msg}), 400
    if result.get('needs_email_confirm'):
        return jsonify({"message": "Check your email to confirm the account", "needs_email_confirm": True})

    user = result.get('user') or {}
    if user.get('id'):
        supabase.ensure_profile(user['id'], email, display_name)
    return jsonify(result), 201


@auth_bp.route('/login', methods=['POST'])
def auth_login():
    """Authenticate user with email and password."""
    supabase = get_supabase()
    if not supabase.is_connected():
        return jsonify({"error": "Supabase authentication is not connected"}), 503

    data = request.json or {}
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    result = supabase.sign_in(email, password)
    if not result:
        err = getattr(supabase, 'last_auth_error', None)
        msg = "Invalid email or password. If you don't have an account, please switch to Sign Up."
        if err:
            if "invalid login credentials" in err.lower():
                msg = "Invalid credentials. Please check your password, or switch to Sign Up if you have not registered yet."
            elif "email not confirmed" in err.lower():
                msg = "Email not confirmed. Please check your inbox to confirm your account."
            else:
                msg = f"Login failed: {err}"
        return jsonify({"error": msg}), 401

    user = result.get('user') or {}
    if user.get('id'):
        supabase.ensure_profile(user['id'], user.get('email') or email)
    return jsonify(result)


@auth_bp.route('/logout', methods=['POST'])
def auth_logout():
    """Log out current user."""
    return jsonify({"message": "Logged out"})


@auth_bp.route('/me', methods=['GET'])
@require_auth
def auth_me():
    """Get current authenticated user info and profile."""
    supabase = get_supabase()
    user_id = request.auth_user['id']
    profile = supabase.ensure_profile(user_id, request.auth_user.get('email'))
    return jsonify({"user": request.auth_user, "profile": profile})


@auth_bp.route('/forgot-password', methods=['POST'])
def auth_forgot_password():
    """Send a password recovery email to the user."""
    supabase = get_supabase()
    if not supabase.is_connected():
        return jsonify({"error": "Supabase authentication is not connected"}), 503

    data = request.json or {}
    email = (data.get('email') or '').strip()
    if not email or '@' not in email:
        return jsonify({"error": "A valid email address is required"}), 400

    success = supabase.reset_password_for_email(email)
    if not success:
        err = getattr(supabase, 'last_auth_error', None)
        msg = "Unable to process password reset."
        if err:
            if "rate limit" in err.lower():
                msg = "Email rate limit reached. Please wait a few minutes before requesting another reset link."
            else:
                msg = f"Reset error: {err}"
        return jsonify({"error": msg}), 400

    return jsonify({"message": "Password reset instructions have been sent to your email."})

