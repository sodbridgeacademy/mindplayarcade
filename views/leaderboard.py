
import streamlit as st

from services.leaderboard_service import (
    get_leaderboard,
    get_leaderboard_countries,
)


def show_leaderboard():

    st.title("Leaderboard 🏆")

    st.caption(
        "See how you rank against other MindPlay players."
    )

    col1, col2 = st.columns(2)

    with col1:
        period = st.selectbox(
            "Leaderboard Period",
            ["All Time", "This Week"],
        )

    with col2:
        category = st.selectbox(
            "Game Category",
            [
                "Overall",
                "Memory Sequence",
                "Number Detective",
                "Codebreaker",
                "Rock Paper Scissors",
            ],
        )

    try:
        countries = get_leaderboard_countries()

        country_options = ["All Countries"] + countries

        country = st.selectbox(
            "Filter by Country",
            country_options,
        )

    except Exception as error:
        st.error("We couldn't load the country filter.")
        st.caption(str(error))
        return

    st.divider()

    try:

        with st.spinner("Loading leaderboard..."):

            rankings = get_leaderboard(
                period=period,
                category=category,
                limit=10,
                country=country,
            )

        if not rankings:

            st.info(
                "No leaderboard results yet. "
                "Complete a game to start earning points!"
            )

            return

        country_label = (
            country
            if country != "All Countries"
            else "Global"
        )

        st.subheader(
            f"Top 10 Players — {category} "
            f"({period}) · {country_label}"
        )

        leaderboard_data = []

        for player in rankings:

            leaderboard_data.append({
                "Rank": player["rank"],
                "Player": player["username"],
                "Country": player["country"],
                "Points": player["points"],
                "Games Played": player["games_played"],
                "Games Won": player["games_won"],
                "Win %": f"{player['win_percentage']:.1f}%",
            })

        st.dataframe(
            leaderboard_data,
            hide_index=True,
            use_container_width=True,
        )

        st.caption(
            f"Showing {len(rankings)} registered players."
        )

    except Exception as error:

        st.error("We couldn't load the leaderboard.")
        st.caption(str(error))
