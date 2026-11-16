import streamlit as st
from services.sound_service import queue_sound, play_pending_sound, play_sound
from services.scoring_service import save_game_result
from appwrite.id import ID

from games.rps_engine import (
    CHOICES,
    get_computer_choice,
    evaluate_round,
    calculate_score,
)

EMOJIS = {
    "rock": "🪨",
    "paper": "📄",
    "scissors": "✂️",
}

def initialize_game():
    defaults = {
        "rps_player_wins": 0,
        "rps_computer_wins": 0,
        "rps_rounds_played": 0,
        "rps_history": [],
        "rps_phase": "ready",
        "rps_score": 0,
        "rps_last_result": None,
        "rps_history_id": None,
        "rps_result_saved": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def start_game():
    st.session_state.rps_player_wins = 0
    st.session_state.rps_computer_wins = 0
    st.session_state.rps_rounds_played = 0
    st.session_state.rps_history = []
    st.session_state.rps_score = 0
    st.session_state.rps_last_result = None
    st.session_state.rps_phase = "playing"
    st.session_state.rps_history_id = ID.unique()
    st.session_state.rps_result_saved = False


def reset_game():
    keys = [
        "rps_player_wins",
        "rps_computer_wins",
        "rps_rounds_played",
        "rps_history",
        "rps_phase",
        "rps_score",
        "rps_last_result",
    ]

    for key in keys:
        st.session_state.pop(key, None)

    initialize_game()


def save_rps_result():
    """Save a completed Rock Paper Scissors match for registered players."""

    auth_user = st.session_state.get("auth_user")

    # Guests can play without saving official scores.
    if not auth_user:
        return

    if st.session_state.get("rps_result_saved", False):
        return

    result = (
        "won"
        if st.session_state.rps_phase == "success"
        else "lost"
    )

    save_game_result(
        session_secret=auth_user["session_secret"],
        user_id=auth_user["user_id"],
        game_id="rps",
        game_name="Rock Paper Scissors",
        score=st.session_state.rps_score,
        result=result,
        history_row_id=st.session_state.rps_history_id,
    )

    st.session_state.rps_result_saved = True


def play_round(player_choice):
    computer_choice = get_computer_choice()
    result = evaluate_round(player_choice, computer_choice)

    st.session_state.rps_rounds_played += 1

    if result == "win":
        st.session_state.rps_player_wins += 1
        message = "You won this round! 🎉"
        sound_event = "correct"

    elif result == "lose":
        st.session_state.rps_computer_wins += 1
        message = "The computer won this round!"
        sound_event = "wrong"

    else:
        message = "It's a draw! No points awarded."
        sound_event = "draw"

    st.session_state.rps_last_result = {
        "player": player_choice,
        "computer": computer_choice,
        "result": result,
        "message": message,
    }

    st.session_state.rps_history.append({
        "round": st.session_state.rps_rounds_played,
        "player": player_choice,
        "computer": computer_choice,
        "result": result,
    })

    if st.session_state.rps_player_wins == 3:
        st.session_state.rps_phase = "success"
        sound_event = "win"

        st.session_state.rps_score = calculate_score(
            st.session_state.rps_player_wins,
            match_won=True,
        )

    elif st.session_state.rps_computer_wins == 3:
        st.session_state.rps_phase = "failed"
        sound_event = "failure"

        st.session_state.rps_score = calculate_score(
            st.session_state.rps_player_wins,
            match_won=False,
        )

    st.session_state.rps_sound_event = sound_event



def show_history():
    if not st.session_state.rps_history:
        return

    st.markdown("### Round History")

    for item in reversed(st.session_state.rps_history):
        player = EMOJIS[item["player"]]
        computer = EMOJIS[item["computer"]]

        if item["result"] == "win":
            result_label = "You won"
        elif item["result"] == "lose":
            result_label = "Computer won"
        else:
            result_label = "Draw"

        st.markdown(
            f"**Round {item['round']}** — "
            f"You: {player} | Computer: {computer} | "
            f"{result_label}"
        )


def show_rps_game():
    initialize_game()

    sound_event = st.session_state.pop("rps_sound_event", None)

    if sound_event:
        play_sound(sound_event)

    st.title("✊ Rock Paper Scissors")
    st.caption("Can you outsmart the computer?")

    st.divider()

    st.markdown(
        """
        ### How to play
        Choose your move. The first player to win **3 rounds**
        wins the match. Draws don't count towards either player's score.
        """
    )

    if st.button("← Back to Home"):
        queue_sound("click")
        st.session_state["selected_game"] = None
        st.rerun()

    st.divider()

    phase = st.session_state.rps_phase

    if phase in ("success", "failed"):
        try:
            save_rps_result()
        except Exception as error:
            st.error("Your game result could not be saved.")
            st.caption(str(error))

    if phase == "ready":
        st.markdown("### Ready for a challenge?")
        st.write("Your opponent is waiting.")

        if st.button("Start Match", type="primary"):
            start_game()
            st.rerun()

    elif phase == "playing":
        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Your Wins",
                st.session_state.rps_player_wins,
            )

        with col2:
            st.metric(
                "Computer Wins",
                st.session_state.rps_computer_wins,
            )

        st.caption(
            f"Rounds played: {st.session_state.rps_rounds_played}"
        )

        st.markdown("### Make your move")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🪨 Rock", use_container_width=True):
                play_round("rock")
                st.rerun()

        with col2:
            if st.button("📄 Paper", use_container_width=True):
                play_round("paper")
                st.rerun()

        with col3:
            if st.button("✂️ Scissors", use_container_width=True):
                play_round("scissors")
                st.rerun()

        last_result = st.session_state.rps_last_result

        if last_result:
            st.divider()
            st.markdown("### Round Result")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Your Choice**")
                st.title(EMOJIS[last_result["player"]])

            with col2:
                st.markdown("**Computer's Choice**")
                st.title(EMOJIS[last_result["computer"]])

            if last_result["result"] == "win":
                st.success(last_result["message"])
            elif last_result["result"] == "lose":
                st.error(last_result["message"])
            else:
                st.info(last_result["message"])

        show_history()

    elif phase in ["success", "failed"]:
        if phase == "success":
            st.success("🏆 You won the match! Excellent work!")
        else:
            st.error("The computer won this match. Better luck next time!")

        st.markdown("### Final Score")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Your Wins",
                st.session_state.rps_player_wins,
            )

        with col2:
            st.metric(
                "Computer Wins",
                st.session_state.rps_computer_wins,
            )

        st.metric("Points Earned", st.session_state.rps_score)

        show_history()

        if st.button("Play Again", type="primary"):
            start_game()
            st.rerun()

        if st.button("Back to Home"):
            st.session_state["selected_game"] = None
            st.rerun()