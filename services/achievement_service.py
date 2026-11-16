
from datetime import datetime, timezone
import hashlib

from appwrite.permission import Permission
from appwrite.role import Role
from appwrite.query import Query
from appwrite.services.tables_db import TablesDB
from appwrite.exception import AppwriteException

from services.player_service import get_player_profile_record
from utils.database import APPWRITE_DATABASE_ID


from services.auth_service import (
    get_admin_client,
    get_authenticated_client,
)


ACHIEVEMENTS = {
    "first_victory": {
        "name": "First Victory",
        "description": "Win your first game.",
    },
    "on_a_roll": {
        "name": "On a Roll",
        "description": "Win 5 consecutive games.",
    },
    "unstoppable": {
        "name": "Unstoppable",
        "description": "Win 10 consecutive games.",
    },
    "point_collector": {
        "name": "Point Collector",
        "description": "Reach 1,000 total points.",
    },
    "elite_scorer": {
        "name": "Elite Scorer",
        "description": "Reach 10,000 total points.",
    },
    "getting_started": {
        "name": "Getting Started",
        "description": "Complete 10 games.",
    },
    "dedicated_player": {
        "name": "Dedicated Player",
        "description": "Complete 50 games.",
    },
    "veteran": {
        "name": "Veteran",
        "description": "Complete 100 games.",
    },
}


def _get_recent_game_history(tables_db, user_id, limit=10):
    """Retrieve a player's most recent games."""
    result = tables_db.list_rows(
        database_id=APPWRITE_DATABASE_ID,
        table_id="game_history",
        queries=[
            Query.equal("user_id", user_id),
            Query.order_desc("played_at"),
            Query.limit(limit),
        ],
        total=False,
    )

    return [row.data for row in result.rows]


def _get_unlocked_achievement_ids(tables_db, user_id):
    """Retrieve achievements already earned by a player."""
    result = tables_db.list_rows(
        database_id=APPWRITE_DATABASE_ID,
        table_id="player_achievements",
        queries=[
            Query.equal("user_id", user_id),
            Query.limit(100),
        ],
        total=False,
    )

    return {
        row.data.get("achievement_id")
        for row in result.rows
    }


def _get_eligible_achievements(player, recent_history):
    """Determine which achievements the player has earned."""
    eligible = set()

    games_played = int(player.get("games_played", 0) or 0)
    games_won = int(player.get("games_won", 0) or 0)
    total_points = int(player.get("total_points", 0) or 0)

    if games_won >= 1:
        eligible.add("first_victory")

    consecutive_wins = 0

    for game in recent_history:
        if game.get("result") == "won":
            consecutive_wins += 1
        else:
            break

    if consecutive_wins >= 5:
        eligible.add("on_a_roll")

    if consecutive_wins >= 10:
        eligible.add("unstoppable")

    if total_points >= 1000:
        eligible.add("point_collector")

    if total_points >= 10000:
        eligible.add("elite_scorer")

    if games_played >= 10:
        eligible.add("getting_started")

    if games_played >= 50:
        eligible.add("dedicated_player")

    if games_played >= 100:
        eligible.add("veteran")

    return eligible


def _create_achievement_record(tables_db, user_id, achievement_id):
    """Persist one achievement with owner-only read access."""
    achievement = ACHIEVEMENTS[achievement_id]

    row_id = hashlib.sha256(
        f"{user_id}:{achievement_id}".encode("utf-8")
    ).hexdigest()[:36]

    return tables_db.create_row(
        database_id=APPWRITE_DATABASE_ID,
        table_id="player_achievements",
        row_id=row_id,
        data={
            "user_id": user_id,
            "achievement_id": achievement_id,
            "achievement_name": achievement["name"],
            "unlocked_at": datetime.now(timezone.utc).isoformat(),
        },
        permissions=[
            Permission.read(Role.user(user_id)),
        ],
    )


def evaluate_achievements(session_secret, user_id):
    """
    Check and persist newly earned achievements.

    Returns the achievements unlocked during this evaluation.
    """
    player_row = get_player_profile_record(
        session_secret=session_secret,
        user_id=user_id,
    )

    player = player_row.data

    tables_db = TablesDB(get_admin_client())

    recent_history = _get_recent_game_history(
        tables_db,
        user_id,
        limit=10,
    )

    eligible = _get_eligible_achievements(
        player,
        recent_history,
    )

    already_unlocked = _get_unlocked_achievement_ids(
        tables_db,
        user_id,
    )

    newly_unlocked = []

    for achievement_id in sorted(eligible - already_unlocked):
        try:
            record = _create_achievement_record(
                tables_db,
                user_id,
                achievement_id,
            )

        except AppwriteException as error:
            if error.code == 409:
                continue

            raise

        newly_unlocked.append({
            "achievement_id": achievement_id,
            "achievement_name": ACHIEVEMENTS[achievement_id]["name"],
            "unlocked_at": record.data.get("unlocked_at"),
        })

    return newly_unlocked



def get_player_achievements(session_secret, user_id):
    """Retrieve the authenticated player's unlocked achievements."""
    client = get_authenticated_client(session_secret)
    tables_db = TablesDB(client)

    result = tables_db.list_rows(
        database_id=APPWRITE_DATABASE_ID,
        table_id="player_achievements",
        queries=[
            Query.equal("user_id", user_id),
            Query.order_desc("unlocked_at"),
            Query.limit(100),
        ],
        total=True,
    )

    return [
        row.data for row in result.rows
    ]



def get_player_achievement_progress(session_secret, user_id):
    """Return progress for all achievements, including locked ones."""

    player_row = get_player_profile_record(
        session_secret=session_secret,
        user_id=user_id,
    )
    player = player_row.data

    client = get_authenticated_client(session_secret)
    tables_db = TablesDB(client)

    recent_history = _get_recent_game_history(
        tables_db,
        user_id,
        limit=10,
    )

    unlocked_records = get_player_achievements(
        session_secret=session_secret,
        user_id=user_id,
    )

    unlocked_by_id = {
        record.get("achievement_id"): record
        for record in unlocked_records
    }

    games_played = int(player.get("games_played", 0) or 0)
    games_won = int(player.get("games_won", 0) or 0)
    total_points = int(player.get("total_points", 0) or 0)

    consecutive_wins = 0

    for game in recent_history:
        if game.get("result") == "won":
            consecutive_wins += 1
        else:
            break

    progress_values = {
        "first_victory": (min(games_won, 1), 1),
        "on_a_roll": (min(consecutive_wins, 5), 5),
        "unstoppable": (min(consecutive_wins, 10), 10),
        "point_collector": (min(total_points, 1000), 1000),
        "elite_scorer": (min(total_points, 10000), 10000),
        "getting_started": (min(games_played, 10), 10),
        "dedicated_player": (min(games_played, 50), 50),
        "veteran": (min(games_played, 100), 100),
    }

    progress = []

    for achievement_id, achievement in ACHIEVEMENTS.items():
        current, target = progress_values[achievement_id]
        unlocked_record = unlocked_by_id.get(achievement_id)

        progress.append({
            "achievement_id": achievement_id,
            "achievement_name": achievement["name"],
            "description": achievement["description"],
            "current": current,
            "target": target,
            "unlocked": unlocked_record is not None,
            "unlocked_at": (
                unlocked_record.get("unlocked_at")
                if unlocked_record
                else None
            ),
        })

    return progress

