
from services.auth_service import register_auth_user
from services.player_service import create_player_profile


def register_player(
    username,
    email,
    password,
    country,
    state="",
    city="",
    gender="",
    profile="",
):
    """Register an Appwrite account and create its player profile."""

    # Basic validation
    username = username.strip()
    email = email.strip().lower()
    country = country.strip()

    if not username:
        raise ValueError("Username is required.")

    if not email:
        raise ValueError("Email address is required.")

    if not password:
        raise ValueError("Password is required.")

    if not country:
        raise ValueError("Country is required.")

    # Step 1: Create the authentication account and session
    auth_result = register_auth_user(
        email=email,
        password=password,
        username=username,
    )

    # Step 2: Create the player's private profile
    try:
        player_profile = create_player_profile(
            session_secret=auth_result["session_secret"],
            user_id=auth_result["user_id"],
            email=email,
            username=username,
            country=country,
            state=state,
            city=city,
            gender=gender,
            profile=profile,
        )

    except Exception as error:
        # Keep the authenticated account details so profile
        # creation can be retried without registering again.
        return {
            "success": False,
            "account_created": True,
            "profile_created": False,
            "message": (
                "Your account was created, but your player profile "
                "could not be completed. Please try again."
            ),
            "error": str(error),
            "user": auth_result,
            "profile": None,
        }

    return {
        "success": True,
        "account_created": True,
        "profile_created": True,
        "message": "Registration completed successfully!",
        "error": None,
        "user": auth_result,
        "profile": player_profile,
    }
