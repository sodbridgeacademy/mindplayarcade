from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
from services.player_service import (
    get_player_profile,
    get_player_game_history,
)

from services.achievement_service import (
    get_player_achievements,
    get_player_achievement_progress,
)

def show_profile():

    st.title("My Profile")
    st.caption("Your personal gaming dashboard.")

    auth_user = st.session_state.get("auth_user")

    if not auth_user:
        st.info("Please sign in to view your player profile.")
        return

    try:
        player = get_player_profile(
            session_secret=auth_user["session_secret"],
            user_id=auth_user["user_id"],
        )

        st.session_state["player_profile"] = player

    except Exception as error:
        st.error("Your player profile could not be refreshed.")
        st.caption(str(error))
        return

    # -------------------------
    # PLAYER INFORMATION
    # -------------------------

    st.subheader(f"Welcome back, {player.get('username', 'Player')}! 👋")

    st.caption(
        f"{player.get('city', '')}"
        f"{', ' if player.get('city') and player.get('country') else ''}"
        f"{player.get('country', '')}"
    )

    st.divider()

    st.subheader("Player Statistics")

    games_played = int(player.get("games_played", 0) or 0)
    games_won = int(player.get("games_won", 0) or 0)

    win_percentage = (
        (games_won / games_played) * 100
        if games_played > 0
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Points",
        f"{player.get('total_points', 0):,}",
    )

    col2.metric(
        "Games Played",
        f"{games_played:,}",
    )

    col3.metric(
        "Games Won",
        f"{games_won:,}",
    )

    col4.metric(
        "Win Percentage",
        f"{win_percentage:.1f}%",
    )

    st.divider()

    # -------------------------
    # PERSONAL INFORMATION
    # -------------------------

    st.subheader("Player Information")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Username**")
        st.write(player.get("username", "—"))

        st.markdown("**Email**")
        st.write(player.get("email", "—"))

        st.markdown("**Country**")
        st.write(player.get("country", "—"))

    with col2:
        st.markdown("**State / Region**")
        st.write(player.get("state") or "—")

        st.markdown("**City**")
        st.write(player.get("city") or "—")

        st.markdown("**Gender**")
        st.write(player.get("gender") or "Not disclosed")

    if player.get("profile"):
        st.markdown("**About Me**")
        st.write(player["profile"])

    st.divider()

    # -------------------------
    # ACHIEVEMENTS
    # -------------------------

    st.subheader("Achievements")

    try:
        achievements = get_player_achievement_progress(
            session_secret=auth_user["session_secret"],
            user_id=auth_user["user_id"],
        )

        unlocked_count = sum(
            1 for achievement in achievements
            if achievement["unlocked"]
        )

        st.caption(
            f"You have unlocked {unlocked_count} "
            f"of {len(achievements)} achievements."
        )

        achievement_icons = {
            "first_victory": "🏆",
            "on_a_roll": "🔥",
            "unstoppable": "⚡",
            "point_collector": "💎",
            "elite_scorer": "👑",
            "getting_started": "🎮",
            "dedicated_player": "🌟",
            "veteran": "🏅",
        }

        columns = st.columns(2)

        for index, achievement in enumerate(achievements):
            achievement_id = achievement["achievement_id"]
            icon = achievement_icons.get(
                achievement_id,
                "🏅",
            )

            current = achievement["current"]
            target = achievement["target"]
            unlocked = achievement["unlocked"]

            with columns[index % 2]:
                with st.container(border=True):

                    if unlocked:
                        st.markdown(
                            f"### {icon} "
                            f"{achievement['achievement_name']}"
                        )
                        st.success("✓ Achievement Unlocked")

                        unlocked_at = achievement.get("unlocked_at")

                        if unlocked_at:
                            unlocked_datetime = datetime.fromisoformat(
                                unlocked_at.replace("Z", "+00:00")
                            )

                            local_datetime = unlocked_datetime.astimezone(
                                ZoneInfo("Africa/Lagos")
                            )

                            formatted_date = local_datetime.strftime(
                                "%d %b %Y, %I:%M %p"
                            )
                        else:
                            formatted_date = "—"

                        st.caption(
                            f"Unlocked: {formatted_date}"
                        )

                    else:
                        st.markdown(
                            f"### 🔒 "
                            f"{achievement['achievement_name']}"
                        )
                        st.caption("🔒 Not unlocked yet")

                        st.caption(
                            achievement["description"]
                        )

                    progress_fraction = current / target

                    st.progress(
                        progress_fraction,
                        text=f"{current:,} / {target:,}",
                    )

    except Exception as error:
        st.error("Your achievements could not be loaded.")
        st.caption(str(error))

    st.divider()


    # -------------------------
    # GAME HISTORY
    # -------------------------

    st.subheader("Game History")

    page_size = 10

    if "history_page" not in st.session_state:
        st.session_state["history_page"] = 1

    current_page = st.session_state["history_page"]

    try:
        history, total_records = get_player_game_history(
            session_secret=auth_user["session_secret"],
            user_id=auth_user["user_id"],
            page=current_page,
            page_size=page_size,
        )

        total_pages = max(1, (total_records + page_size - 1) // page_size)

        if current_page > total_pages:
            st.session_state["history_page"] = total_pages
            st.rerun()

        if history:
            import pandas as pd

            history_data = []

            for record in history:

                played_at = record.get("played_at")

                if played_at:
                    played_datetime = datetime.fromisoformat(
                        played_at.replace("Z", "+00:00")
                    )

                    local_datetime = played_datetime.astimezone(
                        ZoneInfo("Africa/Lagos")
                    )

                    formatted_date = local_datetime.strftime(
                        "%d %b %Y, %I:%M %p"
                    )
                else:
                    formatted_date = "—"

                history_data.append({
                    "Date": formatted_date,
                    "Game": record.get("game_name", "—"),
                    "Score": record.get("score", 0),
                    "Result": record.get("result", "—").title(),
                })

            history_df = pd.DataFrame(history_data)

            st.dataframe(
                history_df,
                use_container_width=True,
                hide_index=True,
            )

            st.caption(
                f"Showing {(current_page - 1) * page_size + 1}"
                f"–{(current_page - 1) * page_size + len(history)}"
                f" of {total_records} games"
            )

            col1, col2, col3 = st.columns([1, 2, 1])

            with col1:
                if st.button(
                    "← Previous",
                    disabled=current_page <= 1,
                    use_container_width=True,
                ):
                    st.session_state["history_page"] -= 1
                    st.rerun()

            with col2:
                st.markdown(
                    f"<div style='text-align:center'>"
                    f"Page {current_page} of {total_pages}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            with col3:
                if st.button(
                    "Next →",
                    disabled=current_page >= total_pages,
                    use_container_width=True,
                ):
                    st.session_state["history_page"] += 1
                    st.rerun()

        else:
            st.info("You haven't played any games yet.")

    except Exception as error:
        st.error("Your game history could not be loaded.")
        st.caption(str(error))