"""Shared constants: categories, units, priorities.

The frontend reads these through GET /api/meta/options so the lists exist in
one place only.
"""

CATEGORIES = [
    "Rice and Grains",
    "Pulses and Dal",
    "Vegetables",
    "Fruits",
    "Dairy",
    "Cooking Oil",
    "Spices",
    "Snacks",
    "Household Essentials",
    "Other",
]

UNITS = ["kg", "g", "litre", "ml", "piece", "packet"]

# Units that can only be bought in whole numbers.
INDIVISIBLE_UNITS = {"piece", "packet", "g", "ml"}

# Smallest quantity step used when rounding / reducing each unit.
UNIT_STEP = {
    "kg": "0.1",
    "litre": "0.1",
    "g": "1",
    "ml": "1",
    "piece": "1",
    "packet": "1",
}

PRIORITIES = ["Essential", "Important", "Optional"]

SHOPPING_FREQUENCIES = ["Weekly", "Fortnightly", "Monthly"]

# Default planning period (days) for each shopping frequency.
FREQUENCY_DAYS = {"Weekly": 7, "Fortnightly": 14, "Monthly": 30}

# A "month" for prediction purposes is a rolling 30-day period.
DAYS_PER_PERIOD = 30
