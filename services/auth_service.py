
import os

from appwrite.client import Client
from appwrite.services.account import Account
from appwrite.id import ID


def get_auth_client():
    """Create a client for authenticated player requests."""

    client = Client()
    client.set_endpoint(os.getenv("APPWRITE_ENDPOINT"))
    client.set_project(os.getenv("APPWRITE_PROJECT_ID"))

    return client


def get_admin_client():
    """Create an admin client for account and session management."""

    client = get_auth_client()
    client.set_key(os.getenv("APPWRITE_API_KEY"))

    return client


def get_auth_service():
    """Return the Appwrite Account service using the admin client."""

    return Account(get_admin_client())


def get_authenticated_client(session_secret):
    """Create a client using an individual player's session."""

    client = get_auth_client()
    client.set_session(session_secret)

    return client


def register_auth_user(email, password, username):
    """Create an Appwrite account and establish a session."""

    email = email.strip().lower()
    username = username.strip()

    account = get_auth_service()

    user = account.create(
        user_id=ID.unique(),
        email=email,
        password=password,
        name=username,
    )

    try:
        session = account.create_email_password_session(
            email=email,
            password=password,
        )

        if not session.secret:
            raise RuntimeError("Appwrite did not return a session secret.")

    except Exception as error:
        raise RuntimeError(
            "Your account was created, but automatic sign-in failed. "
            "Please try signing in with your new account."
        ) from error

    return {
        "user_id": user.id,
        "username": user.name,
        "email": user.email,
        "session_secret": session.secret,
    }


def login_auth_user(email, password):
    """Sign in an existing Appwrite user."""

    email = email.strip().lower()

    account = get_auth_service()

    session = account.create_email_password_session(
        email=email,
        password=password,
    )

    if not session.secret:
        raise RuntimeError("Appwrite did not return a session secret.")

    authenticated_client = get_authenticated_client(session.secret)
    authenticated_account = Account(authenticated_client)

    user = authenticated_account.get()

    return {
        "user_id": user.id,
        "username": user.name,
        "email": user.email,
        "session_secret": session.secret,
    }


def logout_auth_user(session_secret):
    """Terminate the current player's Appwrite session."""

    client = get_authenticated_client(session_secret)
    account = Account(client)

    account.delete_session(session_id="current")
