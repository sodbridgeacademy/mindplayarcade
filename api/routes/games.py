# Game routing
selected_game = st.session_state.get("selected_game")

if selected_game == "memory":
    show_memory_game()

elif selected_game == "number":
    st.title("🔢 Number Detective")
    st.info("Number Detective is coming in the next development stage.")

elif selected_game == "codebreaker":
    st.title("🔐 Codebreaker")
    st.info("Codebreaker is coming soon.")

elif selected_game == "rps":
    st.title("✊ Rock Paper Scissors")
    st.info("Rock Paper Scissors is coming soon.")

# Normal page navigation
elif selected_page == "Home":
    show_home()

elif selected_page == "Leaderboard":
    show_leaderboard()

elif selected_page == "My Profile":
    show_profile()