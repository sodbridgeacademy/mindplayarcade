
import streamlit as st
from config import GAMES


def render_game_cards():
    st.markdown(
        """
        <style>
        .game-card {
            background: #30343B;
            border: 1px solid #41464F;
            border-radius: 14px;
            padding: 22px;
            min-height: 205px;
            margin-bottom: 12px;
        }

        .game-icon {
            font-size: 34px;
            margin-bottom: 12px;
        }

        .game-title {
            color: #FFFFFF;
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .game-description {
            color: #BFC2C8;
            font-size: 14px;
            min-height: 42px;
        }

        .game-category {
            color: #8EB2FF;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    game_ids = list(GAMES.keys())

    for start in range(0, len(game_ids), 2):
        columns = st.columns(2)

        for column, game_id in zip(columns, game_ids[start:start + 2]):
            game = GAMES[game_id]

            with column:
                st.markdown(
                    f"""
                    <div class="game-card">
                        <div class="game-icon">{game["icon"]}</div>
                        <div class="game-category">{game["category"]}</div>
                        <div class="game-title">{game["name"]}</div>
                        <div class="game-description">
                            {game["description"]}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if game["status"] == "Available":
                    if st.button(
                        "Play Now",
                        key=f"play_{game_id}",
                        use_container_width=True,
                    ):
                        st.session_state["selected_game"] = game_id
                        st.rerun()
                else:
                    st.button(
                        "Coming Soon",
                        key=f"soon_{game_id}",
                        disabled=True,
                        use_container_width=True,
                    )
