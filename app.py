import os
import streamlit as st

from dotenv import load_dotenv

load_dotenv()

try:
    for key in (
        "APPWRITE_ENDPOINT",
        "APPWRITE_PROJECT_ID",
        "APPWRITE_API_KEY",
    ):
        if key in st.secrets:
            os.environ[key] = st.secrets[key]

except st.errors.StreamlitSecretNotFoundError:
    pass


from components.sidebar import render_sidebar
from views.home import show_home
from views.profile import show_profile
from views.leaderboard import show_leaderboard

from views.memory_game import show_memory_game
from views.number_game import show_number_game
from views.codebreaker_game import show_codebreaker_game
from views.rps_game import show_rps_game
from views.auth import show_auth


st.set_page_config(
    page_title="MindPlay Arcade",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Global styling
st.markdown(
    """
    <style>
    .stApp {
        background-color: #202124;
    }

    section[data-testid="stSidebar"] {
        background-color: #181A1D;
        border-right: 1px solid #30343B;
    }

    h1, h2, h3 {
        color: #FFFFFF;
    }

    div[data-testid="stMetric"] {
        background-color: #30343B;
        border: 1px solid #41464F;
        padding: 15px;
        border-radius: 12px;
    }

    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


## Navigation
selected_page = render_sidebar()

# Normal page navigation takes priority over active games.

if selected_page == "Home":
    selected_game = st.session_state.get("selected_game")

    if selected_game == "memory":
        show_memory_game()
    elif selected_game == "number":
        show_number_game()
    elif selected_game == "codebreaker":
        show_codebreaker_game()
    elif selected_game == "rps":
        show_rps_game()
    else:
        show_home()

elif selected_page == "Leaderboard":
    st.session_state["selected_game"] = None
    show_leaderboard()

elif selected_page == "My Profile":
    st.session_state["selected_game"] = None
    show_profile()

elif selected_page == "Sign in / Register":
    st.session_state["selected_game"] = None
    show_auth()
