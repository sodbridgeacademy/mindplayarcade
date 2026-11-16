
import random


SYMBOLS = {
    "red": "🔴",
    "blue": "🔵",
    "green": "🟢",
    "yellow": "🟡",
}


def generate_sequence(length=3):
    """Generate a random sequence of coloured symbols."""
    return [
        random.choice(list(SYMBOLS.keys()))
        for _ in range(length)
    ]


def check_sequence(player_sequence, target_sequence):
    """Check whether the player's sequence is correct."""
    return player_sequence == target_sequence


def calculate_score(level, correct=True):
    """Calculate points earned for a completed round."""
    if not correct:
        return 0

    return level * 10


def get_symbol_sequence(sequence):
    """Convert colour names into their visual symbols."""
    return [SYMBOLS[colour] for colour in sequence]
