import random

CHOICES = ["rock", "paper", "scissors"]

def get_computer_choice():
    return random.choice(CHOICES)


def evaluate_round(player_choice, computer_choice):
    if player_choice == computer_choice:
        return "draw"

    winning_combinations = {
        "rock": "scissors",
        "paper": "rock",
        "scissors": "paper",
    }

    if winning_combinations[player_choice] == computer_choice:
        return "win"

    return "lose"


def calculate_score(player_wins, match_won=False):
    score = player_wins * 20

    if match_won:
        score += 50

    return score