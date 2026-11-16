
import streamlit as st

from services.sound_service import queue_sound, play_pending_sound
from services.scoring_service import save_game_result
from appwrite.id import ID

from games.codebreaker_engine import (
    MAX_ATTEMPTS,
    is_valid_guess,
    generate_code,
    evaluate_guess,
    calculate_score,
)


def initialize_game():
    defaults = {
        "codebreaker_secret": None,
        "codebreaker_attempts": 0,
        "codebreaker_history": [],
        "codebreaker_phase": "ready",
        "codebreaker_score": 0,
        "codebreaker_history_id": None,
        "codebreaker_result_saved": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def start_game():
    st.session_state.codebreaker_secret = generate_code()
    st.session_state.codebreaker_attempts = 0
    st.session_state.codebreaker_history = []
    st.session_state.codebreaker_phase = "playing"
    st.session_state.codebreaker_score = 0
    st.session_state.codebreaker_history_id = ID.unique()
    st.session_state.codebreaker_result_saved = False


def reset_game():
    keys = [
        "codebreaker_secret",
        "codebreaker_attempts",
        "codebreaker_history",
        "codebreaker_phase",
        "codebreaker_score",
    ]

    for key in keys:
        st.session_state.pop(key, None)

    initialize_game()


def save_codebreaker_result():
    """Save a completed Codebreaker attempt for registered players."""

    auth_user = st.session_state.get("auth_user")

    # Guests can play without saving official scores.
    if not auth_user:
        return

    if st.session_state.get("codebreaker_result_saved", False):
        return

    result = (
        "won"
        if st.session_state.codebreaker_phase == "success"
        else "lost"
    )

    save_game_result(
        session_secret=auth_user["session_secret"],
        user_id=auth_user["user_id"],
        game_id="codebreaker",
        game_name="Codebreaker",
        score=st.session_state.codebreaker_score,
        result=result,
        history_row_id=st.session_state.codebreaker_history_id,
    )

    st.session_state.codebreaker_result_saved = True


def process_guess(guess):
    guess = guess.strip()

    if not is_valid_guess(guess):
        st.warning(
            "Enter exactly four different digits from 1 to 6."
        )
        return

    previous_guesses = [
        item["guess"]
        for item in st.session_state.codebreaker_history
    ]

    if guess in previous_guesses:
        st.warning("You've already tried that code. Try another.")
        return

    feedback = evaluate_guess(
        guess,
        st.session_state.codebreaker_secret,
    )

    st.session_state.codebreaker_attempts += 1

    st.session_state.codebreaker_history.append({
        "guess": guess,
        "correct_position": feedback["correct_position"],
        "wrong_position": feedback["wrong_position"],
    })

    if feedback["solved"]:
        st.session_state.codebreaker_score = calculate_score(
            st.session_state.codebreaker_attempts
        )
        st.session_state.codebreaker_phase = "success"

    elif st.session_state.codebreaker_attempts >= MAX_ATTEMPTS:
        st.session_state.codebreaker_phase = "failed"


def show_history():
    st.subheader("Your Attempts")

    for index, item in enumerate(
        st.session_state.codebreaker_history,
        start=1,
    ):
        col1, col2, col3 = st.columns([1, 2, 2])

        col1.write(f"**#{index}**")
        col2.write(f"🔢 `{item['guess']}`")
        col3.write(
            f"🟢 {item['correct_position']} correct position"
            f" · 🟡 {item['wrong_position']} wrong position"
        )


def show_codebreaker_game():
    initialize_game()
    play_pending_sound()

    st.title("🔐 Codebreaker")
    st.caption(
        "Crack the secret code using logic, deduction and clues."
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Attempts Used",
        f"{st.session_state.codebreaker_attempts}/{MAX_ATTEMPTS}",
    )

    col2.metric(
        "Points Earned",
        st.session_state.codebreaker_score,
    )

    st.divider()

    phase = st.session_state.codebreaker_phase

    if phase in ("success", "failed"):
        try:
            save_codebreaker_result()
        except Exception as error:
            st.error("Your game result could not be saved.")
            st.caption(str(error))

    if phase == "ready":
        st.subheader("Can you crack the code?")

        st.write(
            "I'm thinking of a secret four-digit code."
        )

        st.info(
            "Your code will contain four different digits "
            "selected from 1, 2, 3, 4, 5 and 6. "
            "You have eight attempts."
        )

        st.markdown(
            """
            **Understanding the clues**

            - 🟢 Correct position: A digit belongs in that exact position.
            - 🟡 Wrong position: A digit belongs in the code, but elsewhere.
            """
        )

        if st.button("Start Challenge", type="primary"):
            queue_sound("click")
            start_game()
            st.rerun()

    elif phase == "playing":
        st.subheader("Enter your guess")

        remaining = (
            MAX_ATTEMPTS - st.session_state.codebreaker_attempts
        )

        st.write(f"You have **{remaining} attempts remaining**.")

        with st.form("codebreaker_guess_form"):
            guess = st.text_input(
                "Your four-digit code",
                placeholder="Example: 1436",
                max_chars=4,
                key=f"codebreaker_guess_{st.session_state.codebreaker_attempts}",
            )

            submitted = st.form_submit_button(
                "Submit Code",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            previous_guesses = [
                item["guess"]
                for item in st.session_state.codebreaker_history
            ]

            if not is_valid_guess(guess.strip()):
                st.warning(
                    "Enter exactly four different digits from 1 to 6."
                )

            elif guess.strip() in previous_guesses:
                st.warning(
                    "You've already tried that code. Try another."
                )

            else:
                process_guess(guess)

                if st.session_state.codebreaker_phase == "success":
                    queue_sound("success")

                elif st.session_state.codebreaker_phase == "failed":
                    queue_sound("failure")

                else:
                    queue_sound("wrong")

                st.rerun()

        if st.session_state.codebreaker_history:
            st.divider()
            show_history()

    elif phase == "success":
        st.success("Outstanding! You've cracked the secret code.")

        st.markdown(
            f"# 🔓 {st.session_state.codebreaker_secret}"
        )

        st.write(
            f"You solved the code in "
            f"**{st.session_state.codebreaker_attempts} attempts**."
        )

        st.metric(
            "Points Earned",
            st.session_state.codebreaker_score,
        )

        show_history()

        if st.button("Play Again", type="primary"):
            queue_sound("click")
            reset_game()
            st.rerun()

    elif phase == "failed":
        st.error("You've used all eight attempts!")

        st.markdown(
            f"### The secret code was {st.session_state.codebreaker_secret}."
        )

        st.write("Review your clues and see what you can learn.")

        show_history()

        if st.button("Try Again", type="primary"):
            queue_sound("click")
            reset_game()
            st.rerun()

    st.divider()

    if st.button("← Back to Home"):
        queue_sound("click")
        st.session_state["selected_game"] = None
        st.rerun()
