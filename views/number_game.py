import streamlit as st
from services.sound_service import queue_sound, play_pending_sound
from services.scoring_service import save_game_result
from appwrite.id import ID

from games.number_engine import (
    MIN_NUMBER,
    MAX_NUMBER,
    MAX_ATTEMPTS,
    generate_number,
    evaluate_guess,
    calculate_score,
)


def initialize_game():
    defaults = {
        "number_secret": None,
        "number_attempts": 0,
        "number_history": [],
        "number_phase": "ready",
        "number_score": 0,
        "number_feedback": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def start_game():
    st.session_state.number_secret = generate_number()
    st.session_state.number_attempts = 0
    st.session_state.number_history = []
    st.session_state.number_phase = "playing"
    st.session_state.number_score = 0
    st.session_state.number_feedback = ""
    st.session_state.number_history_id = ID.unique()
    st.session_state.number_result_saved = False


def reset_game():
    keys = [
        "number_secret",
        "number_attempts",
        "number_history",
        "number_phase",
        "number_score",
        "number_feedback",
        "number_history_id",
        "number_result_saved",
    ]

    for key in keys:
        st.session_state.pop(key, None)

    initialize_game()



def save_number_result():
    """Save a completed Number Detective attempt for registered players."""

    auth_user = st.session_state.get("auth_user")

    # Guests can play without saving official scores.
    if not auth_user:
        return

    if st.session_state.get("number_result_saved", False):
        return

    result = (
        "won"
        if st.session_state.number_phase == "success"
        else "lost"
    )

    save_game_result(
        session_secret=auth_user["session_secret"],
        user_id=auth_user["user_id"],
        game_id="number",
        game_name="Number Detective",
        score=st.session_state.number_score,
        result=result,
        history_row_id=st.session_state.number_history_id,
    )

    st.session_state.number_result_saved = True



def process_guess(guess):
    if guess < MIN_NUMBER or guess > MAX_NUMBER:
        st.warning(
            f"Choose a number between {MIN_NUMBER} and {MAX_NUMBER}."
        )
        return

    if guess in [
        item["guess"] for item in st.session_state.number_history
    ]:
        st.warning("You've already tried that number. Try another.")
        return

    result = evaluate_guess(
        guess,
        st.session_state.number_secret,
    )

    st.session_state.number_attempts += 1

    st.session_state.number_history.append({
        "guess": guess,
        "result": result,
    })

    if result == "correct":
        st.session_state.number_score = calculate_score(
            st.session_state.number_attempts
        )
        st.session_state.number_phase = "success"
        st.session_state.number_feedback = (
            "Brilliant! You found the secret number."
        )

    elif st.session_state.number_attempts >= MAX_ATTEMPTS:
        st.session_state.number_phase = "failed"
        st.session_state.number_feedback = (
            "Out of attempts! Better luck next time."
        )

    elif result == "higher":
        st.session_state.number_feedback = (
            f"Too low! The secret number is higher than {guess}."
        )

    else:
        st.session_state.number_feedback = (
            f"Too high! The secret number is lower than {guess}."
        )


def show_number_game():
    initialize_game()
    play_pending_sound()

    st.title("🔢 Number Detective")
    st.caption(
        "Find the hidden number using logic, clues and smart guesses."
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Attempts Used",
        f"{st.session_state.number_attempts}/{MAX_ATTEMPTS}",
    )

    col2.metric(
        "Points Earned",
        st.session_state.number_score,
    )

    st.divider()

    phase = st.session_state.number_phase

    if phase in ("success", "failed"):
        try:
            save_number_result()
        except Exception as error:
            st.error("Your game result could not be saved.")
            st.caption(str(error))

    if phase == "ready":
        st.subheader("Can you crack the number?")

        st.write(
            f"I'm thinking of a number between "
            f"**{MIN_NUMBER} and {MAX_NUMBER}**."
        )

        st.info(
            f"You have {MAX_ATTEMPTS} attempts to find it. "
            "I'll tell you whether your guess is too high or too low."
        )

        if st.button("Start Challenge", type="primary"):
            queue_sound("click")
            start_game()
            st.rerun()
    elif phase == "playing":
        st.subheader("Make your guess")

        remaining = MAX_ATTEMPTS - st.session_state.number_attempts
        st.write(f"You have **{remaining} attempts remaining**.")

        with st.form("number_guess_form"):
            guess = st.number_input(
                "Enter a number",
                min_value=MIN_NUMBER,
                max_value=MAX_NUMBER,
                value=50,
                step=1,
                key="number_guess_input",
            )

            submitted = st.form_submit_button(
                "Submit Guess",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            previous_phase = st.session_state.number_phase

            process_guess(int(guess))

            if st.session_state.number_phase == "success":
                queue_sound("success")

            elif st.session_state.number_phase == "failed":
                queue_sound("failure")

            elif st.session_state.number_phase == "playing":
                queue_sound("wrong")

            st.rerun()

        if st.session_state.number_feedback:
            st.info(st.session_state.number_feedback)

        if st.session_state.number_history:
            st.subheader("Your Guess History")

            for item in reversed(st.session_state.number_history):
                if item["result"] == "higher":
                    st.write(f"🔻 **{item['guess']}** — Too low")
                elif item["result"] == "lower":
                    st.write(f"🔺 **{item['guess']}** — Too high")

    elif phase == "success":
        st.success(st.session_state.number_feedback)

        st.markdown(
            f"## 🎉 {st.session_state.number_secret}"
        )

        st.write(
            f"You found the number in "
            f"**{st.session_state.number_attempts} attempts**!"
        )

        st.metric("Points Earned", st.session_state.number_score)

        if st.button("Play Again", type="primary"):
            queue_sound("click")
            reset_game()
            st.rerun()
    elif phase == "failed":
        st.error(st.session_state.number_feedback)

        st.markdown(
            f"### The secret number was {st.session_state.number_secret}."
        )

        st.write("Don't give up. Try another challenge!")

        if st.button("Try Again", type="primary"):
            queue_sound("click")
            reset_game()
            st.rerun()
    st.divider()

    if st.button("← Back to Home"):
        queue_sound("click")
        st.session_state["selected_game"] = None
        st.rerun()