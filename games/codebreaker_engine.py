
import random


CODE_LENGTH = 4
AVAILABLE_DIGITS = "123456"
MAX_ATTEMPTS = 8


def generate_code():
    """Generate a four-digit code without repeated digits."""
    return "".join(
        random.sample(AVAILABLE_DIGITS, CODE_LENGTH)
    )


def is_valid_guess(guess):
    """Check that a guess contains four unique digits from 1 to 6."""
    if not isinstance(guess, str):
        return False

    if len(guess) != CODE_LENGTH:
        return False

    if not all(digit in AVAILABLE_DIGITS for digit in guess):
        return False

    if len(set(guess)) != CODE_LENGTH:
        return False

    return True


def evaluate_guess(guess, secret_code):
    """Count exact-position and wrong-position matches."""
    correct_position = sum(
        guess[i] == secret_code[i]
        for i in range(CODE_LENGTH)
    )

    correct_digits = len(
        set(guess) & set(secret_code)
    )

    wrong_position = correct_digits - correct_position

    return {
        "correct_position": correct_position,
        "wrong_position": wrong_position,
        "solved": correct_position == CODE_LENGTH,
    }


def calculate_score(attempts_used):
    """Award more points for solving the code quickly."""
    if attempts_used < 1 or attempts_used > MAX_ATTEMPTS:
        return 0

    return max(40, 160 - (attempts_used * 15))
