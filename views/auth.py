
import streamlit as st

from services.registration_service import register_player
from services.auth_service import login_auth_user
from services.player_service import (
    get_player_profile,
    create_player_profile,
)


def show_auth():

    st.title("Welcome to MindPlay Arcade")
    st.caption("Create an account or sign in to save your progress.")

    register_tab, login_tab = st.tabs(
        ["Create Account", "Sign In"]
    )

    # -------------------------
    # REGISTRATION
    # -------------------------

    with register_tab:

        st.subheader("Create your player account")

        with st.form("registration_form"):

            username = st.text_input("Username")
            email = st.text_input("Email address", key="register_email")
            password = st.text_input(
                "Password",
                type="password",
                key="register_password",
            )
            confirm_password = st.text_input(
                "Confirm password",
                type="password",
            )

            st.markdown("#### Location")

            country = st.text_input("Country *")
            state = st.text_input("State / Region (optional)")
            city = st.text_input("City (optional)")

            st.markdown("#### About you")

            gender = st.selectbox(
                "Gender (optional)",
                [
                    "Prefer not to disclose",
                    "Male",
                    "Female",
                ],
            )

            profile = st.text_area(
                "Short profile description (optional)",
                max_chars=255,
            )

            submitted = st.form_submit_button(
                "Create Account",
                use_container_width=True,
            )

        if submitted:

            if not all([username.strip(), email.strip(), password, country.strip()]):
                st.error("Please complete all required fields.")

            elif password != confirm_password:
                st.error("Your passwords do not match.")

            elif len(password) < 8:
                st.error("Your password must contain at least 8 characters.")

            else:

                selected_gender = (
                    "" if gender == "Prefer not to disclose" else gender
                )

                try:
                    result = register_player(
                        username=username,
                        email=email,
                        password=password,
                        country=country,
                        state=state,
                        city=city,
                        gender=selected_gender,
                        profile=profile,
                    )

                    if result["success"]:

                        st.session_state["auth_user"] = result["user"]
                        st.session_state["player_profile"] = result["profile"]

                        st.success("Your MindPlay account has been created!")
                        st.rerun()

                    else:
                        st.error(result["message"])

                        if result.get("error"):
                            st.caption(result["error"])

                except Exception as error:
                    st.error(f"Registration failed: {error}")

       

    # -------------------------
    # LOGIN
    # -------------------------

    with login_tab:
        st.subheader("Welcome back")

        with st.form("login_form"):
            login_email = st.text_input(
                "Email address",
                key="login_email",
            )

            login_password = st.text_input(
                "Password",
                type="password",
                key="login_password",
            )

            login_submitted = st.form_submit_button(
                "Sign In",
                use_container_width=True,
            )

        if login_submitted:
            if not login_email.strip() or not login_password:
                st.error("Please enter your email and password.")

            else:
                try:
                    user = login_auth_user(
                        email=login_email,
                        password=login_password,
                    )

                    st.session_state["auth_user"] = user

                    try:
                        player_profile = get_player_profile(
                            session_secret=user["session_secret"],
                            user_id=user["user_id"],
                        )

                        st.session_state["player_profile"] = player_profile
                        st.session_state["profile_missing"] = False

                        st.session_state["redirect_to_profile"] = True

                        st.success("You are now signed in!")
                        st.rerun()

                    except ValueError as error:
                        if str(error) == "Player profile not found.":
                            st.session_state["profile_missing"] = True
                        else:
                            raise

                except Exception as error:
                    st.error(f"Sign-in failed: {error}")

    # -------------------------
    # COMPLETE MISSING PROFILE
    # -------------------------

    if (
        st.session_state.get("auth_user")
        and st.session_state.get("profile_missing")
    ):
        user = st.session_state["auth_user"]

        st.divider()
        st.subheader("Complete your player profile")

        st.info(
            "Your account already exists. Complete your profile "
            "to finish setting up MindPlay Arcade."
        )

        st.write(f"**Username:** {user['username']}")
        st.write(f"**Email:** {user['email']}")

        with st.form("complete_profile_form"):
            country = st.text_input("Country *")
            state = st.text_input("State / Region (optional)")
            city = st.text_input("City (optional)")

            gender = st.selectbox(
                "Gender (optional)",
                [
                    "Prefer not to disclose",
                    "Male",
                    "Female",
                ],
                key="complete_profile_gender",
            )

            profile = st.text_area(
                "Short profile description (optional)",
                max_chars=255,
                key="complete_profile_description",
            )

            profile_submitted = st.form_submit_button(
                "Complete Profile",
                use_container_width=True,
            )

        if profile_submitted:
            if not country.strip():
                st.error("Please enter your country.")

            else:
                selected_gender = (
                    "" if gender == "Prefer not to disclose" else gender
                )

                try:
                    create_player_profile(
                        session_secret=user["session_secret"],
                        user_id=user["user_id"],
                        username=user["username"],
                        email=user["email"],
                        country=country,
                        state=state,
                        city=city,
                        gender=selected_gender,
                        profile=profile,
                    )

                    player_profile = get_player_profile(
                        session_secret=user["session_secret"],
                        user_id=user["user_id"],
                    )

                    st.session_state["player_profile"] = player_profile
                    st.session_state["profile_missing"] = False

                    st.success("Your player profile has been completed!")
                    st.rerun()

                except Exception as error:
                    st.error(f"Profile completion failed: {error}")


    st.caption(
        "You can still enjoy MindPlay Arcade as a guest without creating an account."
    )
