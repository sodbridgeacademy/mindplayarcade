from appwrite.id import ID
from appwrite.permission import Permission
from appwrite.role import Role
from appwrite.services.tables_db import TablesDB

from services.auth_service import (
    get_admin_client,
    get_authenticated_client,
)
from utils.database import APPWRITE_DATABASE_ID
from appwrite.query import Query


def create_player_profile(
    session_secret,
    user_id,
    username,
    email,
    country,
    state="",
    city="",
    gender="",
    profile="",
):
    """Create a private player profile linked to an Appwrite account."""

    # Use the server-side client to create the profile row.
    client = get_admin_client()
    tables_db = TablesDB(client)

    data = {
        "user_id": user_id,
        "username": username.strip(),
        "country": country.strip(),
        "email": email.strip().lower(),
        "state": state.strip(),
        "city": city.strip(),
        "profile": profile.strip(),
        "total_points": 0,
        "games_played": 0,
        "games_won": 0,
    }

    if gender:
        data["gender"] = gender

    # Only this player can read or update their profile.
    permissions = [
        Permission.read(Role.user(user_id)),
        Permission.update(Role.user(user_id)),
    ]

    row = tables_db.create_row(
        database_id=APPWRITE_DATABASE_ID,
        table_id="players",
        row_id=ID.unique(),
        data=data,
        permissions=permissions,
    )

    return row

def get_player_profile_record(session_secret, user_id):
    """Retrieve the authenticated player's complete profile row."""

    client = get_authenticated_client(session_secret)
    tables_db = TablesDB(client)

    result = tables_db.list_rows(
        database_id=APPWRITE_DATABASE_ID,
        table_id="players",
        queries=[
            Query.equal("user_id", user_id),
            Query.limit(1),
        ],
    )

    if not result.rows:
        raise ValueError("Player profile not found.")

    return result.rows[0]


def get_player_profile(session_secret, user_id):
    """Retrieve the authenticated player's profile data."""

    row = get_player_profile_record(session_secret, user_id)

    return row.data



def get_player_game_history(session_secret, user_id, page=1, page_size=10):
    """Retrieve one page of the authenticated player's game history."""
    page = max(1, int(page))
    page_size = max(1, int(page_size))

    client = get_authenticated_client(session_secret)
    tables_db = TablesDB(client)

    result = tables_db.list_rows(
        database_id=APPWRITE_DATABASE_ID,
        table_id="game_history",
        queries=[
            Query.equal("user_id", user_id),
            Query.order_desc("played_at"),
            Query.limit(page_size),
            Query.offset((page - 1) * page_size),
        ],
        total=True,
    )

    history = [row.data for row in result.rows]
    return history, result.total
