import json
import random

# Load card data
with open("cards.json", "r", encoding="utf-8") as f:
    CARDS = json.load(f)

# Tier-based rarity chances (percent-like weights)
RARITY_CHANCES = {
    "Legendary": 999,
    "Epic": 5000,
    "Rare": 10000,
    "Uncommon": 30518,
    "Common": 53446,
    "Secret Rare": 37
}

RARITY_EMOJI = {
    "Legendary": "✨",
    "Epic": "🔮",
    "Rare": "💎",
    "Uncommon": "🟢",
    "Common": "⚪",
    "Secret Rare": "🔒"
}


def roll_rarity():
    rarities = list(RARITY_CHANCES.keys())
    weights = list(RARITY_CHANCES.values())
    return random.choices(rarities, weights=weights, k=1)[0]


def draw_cards(amount=5):
    """
    Returns: list of (card_dict, rarity)
    """
    pulls = []
    for _ in range(amount):
        rarity = roll_rarity()
        card = random.choice(CARDS[rarity])
        pulls.append((card, rarity))
    return pulls
