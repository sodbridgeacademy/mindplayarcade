
from datetime import datetime, timedelta, timezone

from appwrite.query import Query
from appwrite.services.tables_db import TablesDB

from services.auth_service import get_admin_client
from utils.database import APPWRITE_DATABASE_ID


PAGE_SIZE = 100

GAME_CATEGORIES = {
    "Memory Sequence": "memory",
    "Number Detective": "number",
    "Codebreaker": "codebreaker",
    "Rock Paper Scissors": "rps",
}


def _get_all_rows(tables_db, table_id, filters=None):
    """Retrieve all rows from a table using pagination."""

    rows = []
    offset = 0

    while True:
        queries = list(filters or [])
        queries.extend([
            Query.limit(PAGE_SIZE),
            Query.offset(offset),
        ])

        result = tables_db.list_rows(
            database_id=APPWRITE_DATABASE_ID,
            table_id=table_id,
            queries=queries,
            total=True,
        )

        batch = result.rows
        rows.extend(row.data for row in batch)

        if len(batch) < PAGE_SIZE:
            break

        offset += len(batch)

    return rows


def _get_week_boundaries():
    """Return the current Monday and next Monday in UTC."""

    now = datetime.now(timezone.utc)

    monday = now.date() - timedelta(days=now.weekday())

    start = datetime(
        monday.year,
        monday.month,
        monday.day,
        tzinfo=timezone.utc,
    )

    end = start + timedelta(days=7)

    return start.isoformat(), end.isoformat()


def get_leaderboard_countries():
    """Return the countries represented in the player database."""

    tables_db = TablesDB(get_admin_client())

    player_rows = _get_all_rows(
        tables_db,
        "players",
    )

    countries = {
        str(player.get("country", "")).strip()
        for player in player_rows
        if str(player.get("country", "")).strip()
    }

    return sorted(countries, key=str.casefold)


def _build_rankings(players, scores, wins, games_played, limit):
    """Build rankings using points, win percentage and username."""

    rankings = []

    for user_id, points in scores.items():

        player = players.get(user_id)

        if not player:
            continue

        player_wins = wins.get(user_id, 0)
        player_games = games_played.get(user_id, 0)

        win_percentage = (
            round((player_wins / player_games) * 100, 1)
            if player_games > 0
            else 0.0
        )

        rankings.append({
            "user_id": user_id,
            "username": player.get(
                "username",
                "Unknown Player",
            ),
            "country": player.get("country") or "Not specified",
            "points": points,
            "games_played": player_games,
            "games_won": player_wins,
            "win_percentage": win_percentage,
        })

    rankings.sort(
        key=lambda item: (
            -item["points"],
            -item["win_percentage"],
            item["username"].casefold(),
        )
    )

    previous_points = None
    previous_win_percentage = None
    current_rank = 0

    for index, player in enumerate(rankings):

        if (
            player["points"] != previous_points
            or player["win_percentage"] != previous_win_percentage
        ):
            current_rank = index + 1
            previous_points = player["points"]
            previous_win_percentage = player["win_percentage"]

        player["rank"] = current_rank

    return rankings[:limit]


def get_leaderboard(
    period="All Time",
    category="Overall",
    limit=10,
    country=None,
):
    """
    Retrieve leaderboard rankings.

    All Time / Overall uses accumulated player statistics.

    Other rankings calculate points and win percentage
    from the filtered game history.
    """

    if period not in ("All Time", "This Week"):
        raise ValueError("Invalid leaderboard period.")

    if category != "Overall" and category not in GAME_CATEGORIES:
        raise ValueError("Invalid game category.")

    limit = max(1, int(limit))

    tables_db = TablesDB(get_admin_client())

    player_rows = _get_all_rows(
        tables_db,
        "players",
    )

    players = {
        player.get("user_id"): player
        for player in player_rows
        if player.get("user_id")
    }

    # Apply the optional country filter.
    if country and country != "All Countries":
        players = {
            user_id: player
            for user_id, player in players.items()
            if str(player.get("country", "")).strip().casefold()
            == country.strip().casefold()
        }

    # All-time overall rankings use accumulated player statistics.
    if period == "All Time" and category == "Overall":

        scores = {
            user_id: int(player.get("total_points", 0) or 0)
            for user_id, player in players.items()
        }

        wins = {
            user_id: int(player.get("games_won", 0) or 0)
            for user_id, player in players.items()
        }

        games_played = {
            user_id: int(player.get("games_played", 0) or 0)
            for user_id, player in players.items()
        }

        return _build_rankings(
            players,
            scores,
            wins,
            games_played,
            limit,
        )

    # Other rankings are calculated from filtered game history.
    filters = []

    if category != "Overall":
        filters.append(
            Query.equal(
                "game_id",
                GAME_CATEGORIES[category],
            )
        )

    if period == "This Week":

        week_start, next_week = _get_week_boundaries()

        filters.extend([
            Query.greater_than_equal("played_at", week_start),
            Query.less_than("played_at", next_week),
        ])

    history_rows = _get_all_rows(
        tables_db,
        "game_history",
        filters=filters,
    )

    scores = {}
    wins = {}
    games_played = {}

    for record in history_rows:

        user_id = record.get("user_id")

        if user_id not in players:
            continue

        score = int(record.get("score", 0) or 0)

        scores[user_id] = scores.get(user_id, 0) + score

        games_played[user_id] = (
            games_played.get(user_id, 0) + 1
        )

        if str(record.get("result", "")).lower() == "won":
            wins[user_id] = wins.get(user_id, 0) + 1

    return _build_rankings(
        players,
        scores,
        wins,
        games_played,
        limit,
    )
