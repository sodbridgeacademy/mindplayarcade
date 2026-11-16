
from datetime import datetime, timezone
import logging

from appwrite.id import ID
from appwrite.permission import Permission
from appwrite.role import Role
from appwrite.services.tables_db import TablesDB

from services.auth_service import get_admin_client
from services.player_service import get_player_profile_record
from utils.database import APPWRITE_DATABASE_ID




def save_game_result(
    session_secret,
    user_id,
    game_id,
    game_name,
    score,
    result,
    history_row_id,
):
    """
    Save a completed game and update player statistics atomically.

    A single transaction ensures that the history record and
    player statistics are committed together.
    """

    if not isinstance(score, int) or score < 0:
        raise ValueError("Score must be a non-negative integer.")

    if result not in ("won", "lost", "completed"):
        raise ValueError("Invalid game result.")

    if not history_row_id:
        raise ValueError("A unique game history ID is required.")

    # Retrieve the player's existing profile row.
    player_row = get_player_profile_record(
        session_secret=session_secret,
        user_id=user_id,
    )

    # Use the administrative client for controlled database writes.
    tables_db = TablesDB(get_admin_client())

    transaction = tables_db.create_transaction()
    transaction_id = transaction.id

    try:
        # Create the game history record.
        history = tables_db.create_row(
            database_id=APPWRITE_DATABASE_ID,
            table_id="game_history",
            row_id=history_row_id,
            data={
                "user_id": user_id,
                "game_id": game_id,
                "game_name": game_name,
                "score": score,
                "result": result,
                "played_at": datetime.now(timezone.utc).isoformat(),
            },
            permissions=[
                Permission.read(Role.user(user_id)),
            ],
            transaction_id=transaction_id,
        )

           # Update total points only when the player earned points.
        if score > 0:
            tables_db.increment_row_column(
                database_id=APPWRITE_DATABASE_ID,
                table_id="players",
                row_id=player_row.id,
                column="total_points",
                value=score,
                transaction_id=transaction_id,
            )

        # Update games played.
        tables_db.increment_row_column(
            database_id=APPWRITE_DATABASE_ID,
            table_id="players",
            row_id=player_row.id,
            column="games_played",
            value=1,
            transaction_id=transaction_id,
        )

        # Update games won only when the player wins.
        if result == "won":
            tables_db.increment_row_column(
                database_id=APPWRITE_DATABASE_ID,
                table_id="players",
                row_id=player_row.id,
                column="games_won",
                value=1,
                transaction_id=transaction_id,
            )

        # Commit all changes together.
        committed_transaction = tables_db.update_transaction(
            transaction_id=transaction_id,
            commit=True,
        )

     
        # Evaluate achievements only after the game is committed.
        newly_unlocked = []

        try:
            from services.achievement_service import evaluate_achievements

            newly_unlocked = evaluate_achievements(
                session_secret=session_secret,
                user_id=user_id,
            )

        except Exception:
            logging.exception(
                "Achievement evaluation failed for user %s",
                user_id,
            )

        return {
            "history": history,
            "transaction": committed_transaction,
            "achievements": newly_unlocked,
        }

    except Exception:
        # Attempt to roll back any staged operations.
        try:
            tables_db.update_transaction(
                transaction_id=transaction_id,
                rollback=True,
            )
        except Exception:
            pass

        raise

