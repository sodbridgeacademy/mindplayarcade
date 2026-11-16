import streamlit as st
from services.sound_service import queue_sound, play_pending_sound
from services.scoring_service import save_game_result
from appwrite.id import ID

from games.memory_engine import (
    SYMBOLS,
    generate_sequence,
    check_sequence,
    calculate_score,
    get_symbol_sequence,
)


def initialize_game():
    """Set up the game session."""
    defaults = {
        "memory_level": 1,
        "memory_score": 0,
        "memory_target": [],
        "memory_input": [],
        "memory_phase": "ready",
        "memory_rounds": 0,
        "memory_history_id": None,
        "memory_result_saved": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def start_game():
    st.session_state.memory_level = 1
    st.session_state.memory_score = 0
    st.session_state.memory_rounds = 0
    st.session_state.memory_history_id = ID.unique()
    st.session_state.memory_result_saved = False
    start_round()


def start_round():
    length = st.session_state.memory_level + 2

    st.session_state.memory_target = generate_sequence(length)
    st.session_state.memory_input = []
    st.session_state.memory_phase = "memorize"


def hide_sequence():
    st.session_state.memory_phase = "recall"


def select_symbol(colour):
    if len(st.session_state.memory_input) < len(
        st.session_state.memory_target
    ):
        st.session_state.memory_input.append(colour)


def reset_game():
    keys = [
        "memory_level",
        "memory_score",
        "memory_target",
        "memory_input",
        "memory_phase",
        "memory_rounds",
        "memory_history_id",
        "memory_result_saved",
    ]

    for key in keys:
        if key in st.session_state:
            del st.session_state[key]

    initialize_game()


def save_memory_result():
    """Save one completed Memory Sequence run."""

    auth_user = st.session_state.get("auth_user")

    if not auth_user:
        return

    if st.session_state.memory_result_saved:
        return

    save_game_result(
        session_secret=auth_user["session_secret"],
        user_id=auth_user["user_id"],
        game_id="memory",
        game_name="Memory Sequence",
        score=st.session_state.memory_score,
        result="completed",
        history_row_id=st.session_state.memory_history_id,
    )

    st.session_state.memory_result_saved = True


def show_memory_game():
    initialize_game()
    play_pending_sound()

    st.title("🧠 Memory Sequence")
    st.caption(
        "Train your memory. Follow the sequence and reproduce it correctly."
    )

    # Game statistics
    col1, col2, col3 = st.columns(3)

    col1.metric("Level", st.session_state.memory_level)
    col2.metric("Score", st.session_state.memory_score)
    col3.metric("Rounds Completed", st.session_state.memory_rounds)

    st.divider()

    phase = st.session_state.memory_phase


    if phase == "failed":
        try:
            save_memory_result()
        except Exception as error:
            st.error("Your game result could not be saved.")
            st.write("Error type:", type(error).__name__)
            st.write("Error code:", getattr(error, "code", None))
            st.write("Error response:", getattr(error, "response", None))
            st.caption(str(error))

    if phase == "ready":
        st.subheader("Ready for a challenge?")

        st.write(
            "You'll be shown a sequence of coloured symbols. "
            "Memorize their order, hide the sequence, and reproduce it."
        )

        st.info(
            f"Your first challenge will contain "
            f"{st.session_state.memory_level + 2} symbols."
        )

        if st.button("Start Game", type="primary"):
            queue_sound("click")
            start_game()
            st.rerun()

    elif phase == "memorize":
        st.subheader("Memorize this sequence!")

        symbols = get_symbol_sequence(
            st.session_state.memory_target
        )

        st.markdown(
            f"<div style='font-size: 42px; text-align: center; "
            f"padding: 25px;'>{' '.join(symbols)}</div>",
            unsafe_allow_html=True,
        )

        st.warning("Study the sequence carefully.")

        if st.button("I've memorized it", type="primary"):
            queue_sound("click")
            hide_sequence()
            st.rerun()

    elif phase == "recall":
        st.subheader("Reproduce the sequence")

        st.write(
            "Select the colours in the same order as the sequence "
            "you just memorized."
        )

        selected_symbols = get_symbol_sequence(
            st.session_state.memory_input
        )

        st.markdown(
            f"<div style='font-size: 38px; text-align: center; "
            f"padding: 15px;'>{' '.join(selected_symbols) or '—'}</div>",
            unsafe_allow_html=True,
        )

        st.caption(
            f"{len(st.session_state.memory_input)} of "
            f"{len(st.session_state.memory_target)} selected"
        )

        columns = st.columns(4)

        for column, (colour, symbol) in zip(
            columns, SYMBOLS.items()
        ):
            with column:
                if st.button(
                    symbol,
                    key=f"memory_{colour}",
                    use_container_width=True,
                ):
                    if len(st.session_state.memory_input) < len(
                        st.session_state.memory_target
                    ):
                        select_symbol(colour)
                        queue_sound("click")

                    st.rerun()

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Undo last selection", use_container_width=True):
                if st.session_state.memory_input:
                    st.session_state.memory_input.pop()
                    queue_sound("click")
                    st.rerun()

        with col2:
            if st.button(
                "Clear selections",
                use_container_width=True,
            ):
                st.session_state.memory_input = []
                queue_sound("click")
                st.rerun()

        if len(st.session_state.memory_input) == len(
            st.session_state.memory_target
        ):
            if st.button(
                "Submit Sequence",
                type="primary",
                use_container_width=True,
            ):
                correct = check_sequence(
                    st.session_state.memory_input,
                    st.session_state.memory_target,
                )

                st.session_state.memory_rounds += 1

                if correct:
                    points = calculate_score(
                        st.session_state.memory_level
                    )

                    st.session_state.memory_score += points
                    st.session_state.memory_level += 1
                    st.session_state.memory_phase = "success"

                    queue_sound("success")

                else:
                    st.session_state.memory_phase = "failed"
                    queue_sound("failure")

                st.rerun()

    elif phase == "success":
        st.success("Excellent! You remembered the sequence correctly.")

        st.write(
            f"You earned {calculate_score(st.session_state.memory_level - 1)} points!"
        )

        if st.button("Next Level", type="primary"):
            start_round()
            queue_sound("click")
            st.rerun()

    elif phase == "failed":
        st.error("Not quite! The sequence didn't match.")

        st.write("The correct sequence was:")

        correct_symbols = get_symbol_sequence(
            st.session_state.memory_target
        )

        st.markdown(
            f"<div style='font-size: 38px; text-align: center; "
            f"padding: 15px;'>{' '.join(correct_symbols)}</div>",
            unsafe_allow_html=True,
        )

        st.write(
            f"Your final score: **{st.session_state.memory_score}**"
        )

        if st.button("Play Again", type="primary"):
            queue_sound("click")
            reset_game()
            st.rerun()

    st.divider()

    if st.button("← Back to Home"):
        queue_sound("click")
        st.session_state["selected_game"] = None
        st.rerun()

