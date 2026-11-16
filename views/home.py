
import streamlit as st
from components.game_cards import render_game_cards


def show_home():
    st.title("Welcome to MindPlay Arcade 👋")

    st.markdown(
        """
        <p style="color: #BFC2C8; font-size: 17px;">
            Sharpen your mind, challenge yourself and have fun
            while developing your problem-solving skills.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    # Welcome banner
    st.markdown(
        """
        <div style="
            background: linear-gradient(120deg, #30343B, #263B5C);
            border: 1px solid #405577;
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 28px;
        ">
            <h2 style="margin: 0; color: white;">
                Your next challenge awaits.
            </h2>
            <p style="color: #D2DDF0; margin-bottom: 0;">
                Play games, build skills and climb the leaderboard.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Explore Games")
    st.caption("Choose a game and put your thinking skills to the test.")

    render_game_cards()
