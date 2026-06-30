"""Constants for the Rinnai Water Heater Integration integration."""

from datetime import timedelta

DOMAIN = "rinnai"
UPDATE_INTERVAL = timedelta(seconds=5)

SUPPORTED_TEMPS = [
    35.0,
    36.0,
    37.0,
    38.0,
    39.0,
    40.0,
    41.0,
    42.0,
    43.0,
    44.0,
    45.0,
    46.0,
    47.0,
    48.0,
    50.0,
    55.0,
    60.0,
]

RAW_TO_TEMP = {
    3: 35.0,
    4: 36.0,
    5: 37.0,
    6: 38.0,
    7: 39.0,
    8: 40.0,
    9: 41.0,
    10: 42.0,
    11: 43.0,
    12: 44.0,
    13: 45.0,
    14: 46.0,
    15: 47.0,
    16: 48.0,
    18: 50.0,
    19: 55.0,
    20: 60.0,
}
