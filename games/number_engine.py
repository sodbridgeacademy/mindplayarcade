
import random


MIN_NUMBER = 1
MAX_NUMBER = 100
MAX_ATTEMPTS = 7


def generate_number():
    """Generate the secret number."""
    return random.randint(MIN_NUMBER, MAX_NUMBER)


def evaluate_guess(guess, secret_number):
    """Compare a guess with the secret number."""
    if guess < secret_number:
        return "higher"

    if guess > secret_number:
        return "lower"

    return "correct"


def calculate_score(attempts_used):
    """Award more points for solving the puzzle quickly."""
    if attempts_used < 1 or attempts_used > MAX_ATTEMPTS:
        return 0

    return max(40, 110 - (attempts_used * 10))
