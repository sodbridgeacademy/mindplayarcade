
import streamlit as st

from services.auth_service import logout_auth_user


def render_sidebar():

    # Initialize shared sound preference
    if "sound_enabled" not in st.session_state:
        st.session_state.sound_enabled = True

    auth_user = st.session_state.get("auth_user")
    is_logged_in = bool(auth_user)

    with st.sidebar:

        st.markdown(
            """
            <div style="padding: 12px 0 24px 0;">
                <div style="font-size: 28px;">🎮</div>
                <h2 style="margin: 0;">MindPlay</h2>
                <p style="color: #BFC2C8; margin-top: 4px;">
                    Think. Play. Outsmart.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # Handle redirects before rendering navigation.
        if st.session_state.pop("redirect_to_profile", False):
            st.session_state["navigation"] = "My Profile"

        # Different navigation for guests and registered players.
        if is_logged_in:
            navigation_options = [
                "Home",
                "Leaderboard",
                "My Profile",
                "Log Out",
            ]
        else:
            navigation_options = [
                "Home",
                "Leaderboard",
                "Sign in / Register",
            ]

            # Prevent a stale authenticated navigation selection.
            if st.session_state.get("navigation") == "My Profile":
                st.session_state["navigation"] = "Home"

        page = st.radio(
            "NAVIGATION",
            navigation_options,
            label_visibility="visible",
            key="navigation",
        )

        # Handle logout.
        if page == "Log Out":
            try:
                logout_auth_user(
                    session_secret=auth_user["session_secret"]
                )

                # Clear authenticated player data.
                for key in [
                    "auth_user",
                    "player_profile",
                    "profile_missing",
                    "redirect_to_profile",
                    "navigation",
                    "selected_game",
                ]:
                    st.session_state.pop(key, None)

                st.session_state["navigation"] = "Home"

                st.success("You have been logged out successfully.")
                st.rerun()

            except Exception as error:
                st.error(f"Logout failed: {error}")

        st.divider()

        st.markdown("**PLAYER STATUS**")

        if is_logged_in:
            st.success(f"Welcome, {auth_user['username']}!")
            st.caption("Registered Player")
        else:
            st.caption("Guest Player")
            st.caption("Sign in to save your scores and progress.")

        st.divider()

        st.markdown("**GAME SETTINGS**")

        st.checkbox(
            "🔊 Sound Effects",
            key="sound_enabled",
            help="Turn game sound effects on or off.",
        )

        st.divider()

        st.caption("MindPlay Arcade · 2026")
        st.caption("From Sodbridge")

    return page
