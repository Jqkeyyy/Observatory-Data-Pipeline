"""Google sign-in, and who's allowed to do what.

How login works (Flask never sees a password):
  1. The frontend links to /api/auth/login
  2. We send the browser to Google's sign-in page
  3. Google sends it back to /api/auth/callback with a one-time code
  4. We trade that code for the person's verified email, find or create their row in users,
     and put their user id in a signed session cookie
  5. On every request after that, the cookie tells us who's asking

Protect a route with @login_required (any signed-in user) or @admin_required.
Inside the route, g.user is the signed-in User.

Setup and the full list of .env settings are in AUTH.md.
"""

import os
import secrets
from datetime import timedelta
from functools import wraps
from urllib.parse import urlsplit

from authlib.integrations.base_client import OAuthError
from authlib.integrations.flask_client import OAuth
from flask import Blueprint, abort, current_app, g, jsonify, redirect, request, session
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from db.models import User
from db.session import SessionLocal

ROLES = {"user", "admin"}
DEFAULT_REDIRECT_URI = "http://localhost:5173/api/auth/callback"  # through the Vite proxy

bp = Blueprint("auth", __name__)
oauth = OAuth()


def _env_set(name):
    """A comma-separated .env setting as a lowercase set, e.g. ADMIN_EMAILS=a@uww.edu, b@uww.edu"""
    return {v.strip().lower() for v in os.environ.get(name, "").split(",") if v.strip()}


def init_auth(app):
    secret = os.environ.get("SECRET_KEY")
    if not secret:
        # Lets the server start without auth set up; everyone gets signed out whenever it restarts
        app.logger.warning("SECRET_KEY isn't set in backend/.env, using a temporary one (see AUTH.md)")
        secret = secrets.token_hex(32)

    app.config.update(
        SECRET_KEY=secret,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",  # cookie isn't sent on cross-site POST/PATCH/DELETE, which blocks CSRF
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE") == "1",  # set to 1 once the site is on https
        PERMANENT_SESSION_LIFETIME=timedelta(days=14),
        OAUTH_REDIRECT_URI=os.environ.get("OAUTH_REDIRECT_URI", DEFAULT_REDIRECT_URI),
    )

    oauth.init_app(app)
    if os.environ.get("GOOGLE_CLIENT_ID") and os.environ.get("GOOGLE_CLIENT_SECRET"):
        oauth.register(
            name="google",
            client_id=os.environ["GOOGLE_CLIENT_ID"],
            client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
    else:
        app.logger.warning("GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET aren't set, so login is off (see AUTH.md)")

    app.register_blueprint(bp)


# ---------- who's asking ----------

def current_user():
    """The signed-in User, or None. Looked up fresh each request, so role changes and deletes apply right away."""
    if "user" not in g:
        g.user = None
        if (user_id := session.get("user_id")) is not None:
            with SessionLocal() as db:
                g.user = db.get(User, user_id)
            if g.user is None:  # their account was deleted
                session.clear()
    return g.user


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            return jsonify({"error": "sign in first"}), 401
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            return jsonify({"error": "sign in first"}), 401
        if user.role != "admin":
            return jsonify({"error": "admins only"}), 403
        return view(*args, **kwargs)
    return wrapper


def is_permanent_admin(user):
    """People listed in ADMIN_EMAILS (e.g. Dr. Nine). Always admins, and nobody can demote or delete
    them from the website. The only way to remove one is to edit the server's .env."""
    return user.email in _env_set("ADMIN_EMAILS")


def user_json(user):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture_url": user.picture_url,
        "role": user.role,
        "permanent_admin": is_permanent_admin(user),
        "created_at": user.created_at.isoformat(),
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
    }


# ---------- login / logout ----------

def _safe_next(url):
    """Only send people back to a page on our own site, never to another domain."""
    if not url or not url.startswith("/") or url.startswith("//") or "\\" in url:
        return "/"
    parts = urlsplit(url)
    return "/" if parts.scheme or parts.netloc else url


def _login_failed(reason):
    # The sign-in page reads ?login_error= and shows a message
    return redirect(f"/signin.html?login_error={reason}")


@bp.get("/api/auth/login")
def login():
    """Link here to sign in. Optional ?next=/admin.html to land somewhere other than the home page."""
    if oauth.create_client("google") is None:
        return jsonify({"error": "login isn't set up on this server (see backend/AUTH.md)"}), 503
    session["next"] = _safe_next(request.args.get("next"))
    # select_account: shows the account picker, so a shared lab computer doesn't silently reuse someone's login
    return oauth.google.authorize_redirect(current_app.config["OAUTH_REDIRECT_URI"], prompt="select_account")


@bp.get("/api/auth/callback")
def callback():
    """Google sends the browser here after sign-in. Not called by the frontend directly."""
    if oauth.create_client("google") is None:
        abort(404)
    try:
        token = oauth.google.authorize_access_token()
    except OAuthError:  # they hit Cancel, or the link was stale or reused
        return _login_failed("cancelled")

    info = token.get("userinfo") or {}
    email = (info.get("email") or "").strip().lower()
    if not email or not info.get("email_verified"):
        return _login_failed("unverified_email")
    allowed_domains = _env_set("ALLOWED_EMAIL_DOMAINS")
    if allowed_domains and email.rpartition("@")[2] not in allowed_domains:
        return _login_failed("domain_not_allowed")

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.google_sub == info["sub"]))
        if user is None:
            # First Google sign-in. If an account with this email already exists
            # (e.g. made with scripts/create_user.py), link it instead of making a second one.
            user = db.scalar(select(User).where(User.email == email))
            if user is None:
                user = User(email=email)
                db.add(user)
            elif user.google_sub is not None:  # that email belongs to a different Google account
                return _login_failed("email_in_use")
            user.google_sub = info["sub"]
        user.email = email
        user.name = info.get("name") or user.name or email.partition("@")[0]
        user.picture_url = info.get("picture")
        user.last_login_at = func.now()
        if email in _env_set("ADMIN_EMAILS"):  # bootstraps the first admins; everyone else is set from the Admin page
            user.role = "admin"
        try:
            db.commit()
        except IntegrityError:  # their Google email changed to one another account already has
            return _login_failed("email_in_use")
        user_id = user.id

    next_url = session.get("next", "/")
    session.clear()  # fresh session on login, so a session id planted before login is useless
    session["user_id"] = user_id
    session.permanent = True
    return redirect(next_url)


@bp.post("/api/auth/logout")
def logout():
    session.clear()
    return "", 204


@bp.get("/api/auth/me")
def me():
    """The signed-in user, or null if nobody's signed in."""
    user = current_user()
    return jsonify(user_json(user) if user else None)


# ---------- user management (Admin page) ----------

@bp.get("/api/users")
@admin_required
def list_users():
    with SessionLocal() as db:
        return jsonify([user_json(u) for u in db.scalars(select(User).order_by(User.email))])


@bp.patch("/api/users/<int:user_id>")
@admin_required
def update_user(user_id):
    """Change someone's role: {"role": "admin"} or {"role": "user"}"""
    data = request.get_json(silent=True)
    role = data.get("role") if isinstance(data, dict) else None
    if role not in ROLES:
        return jsonify({"error": 'send {"role": "admin"} or {"role": "user"}'}), 400
    if user_id == g.user.id:
        return jsonify({"error": "you can't change your own role (ask another admin)"}), 400
    with SessionLocal() as db:
        user = db.get(User, user_id) or abort(404)
        if is_permanent_admin(user):
            return jsonify({"error": f"{user.name} is a permanent admin, so their role can't be changed here"}), 403
        user.role = role
        db.commit()
        return jsonify(user_json(user))


@bp.delete("/api/users/<int:user_id>")
@admin_required
def delete_user(user_id):
    """Removes the account and signs them out. Sessions they booked stay, with no name on them.
    They can still sign in again later as a new normal user.
    Admins can't be deleted directly: change them to "user" first, so removing an admin takes two steps."""
    if user_id == g.user.id:
        return jsonify({"error": "you can't delete yourself"}), 400
    with SessionLocal() as db:
        user = db.get(User, user_id) or abort(404)
        if is_permanent_admin(user):
            return jsonify({"error": f"{user.name} is a permanent admin, so they can't be deleted here"}), 403
        if user.role == "admin":
            return jsonify({"error": f"{user.name} is an admin. Change their role to User first, then delete them"}), 400
        db.delete(user)
        db.commit()
    return "", 204
