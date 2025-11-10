"""Configuration settings for the Air Quality Prediction System."""

from typing import Final
from pathlib import Path

# Project paths
PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
RAW_DATA_DIR: Final[Path] = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Final[Path] = DATA_DIR / "processed"
MODELS_DIR: Final[Path] = DATA_DIR / "models"

# OpenAQ API configuration
OPENAQ_API_BASE_URL: Final[str] = "https://api.openaq.org/v3"
OPENAQ_API_KEY: Final[str] = ""  # Will be set from environment or user input

# Model parameters
KNN_NEIGHBORS: Final[int] = 5
RANDOM_FOREST_ESTIMATORS: Final[int] = 200
SVR_KERNEL: Final[str] = "rbf"
POLYNOMIAL_DEGREE: Final[int] = 2

# Pollutants to track
POLLUTANTS: Final[list[str]] = ["pm25", "pm10", "o3", "no2", "so2", "co"]

# AQI breakpoints (US EPA standard)
AQI_BREAKPOINTS: Final[dict[str, list[tuple[float, float, int, int]]]] = {
    "pm25": [  # µg/m³
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 500.4, 301, 500),
    ],
    "pm10": [  # µg/m³
        (0, 54, 0, 50),
        (55, 154, 51, 100),
        (155, 254, 101, 150),
        (255, 354, 151, 200),
        (355, 424, 201, 300),
        (425, 604, 301, 500),
    ],
    "o3": [  # ppm
        (0.000, 0.054, 0, 50),
        (0.055, 0.070, 51, 100),
        (0.071, 0.085, 101, 150),
        (0.086, 0.105, 151, 200),
        (0.106, 0.200, 201, 300),
    ],
    "no2": [  # ppb
        (0, 53, 0, 50),
        (54, 100, 51, 100),
        (101, 360, 101, 150),
        (361, 649, 151, 200),
        (650, 1249, 201, 300),
        (1250, 2049, 301, 500),
    ],
    "so2": [  # ppb
        (0, 35, 0, 50),
        (36, 75, 51, 100),
        (76, 185, 101, 150),
        (186, 304, 151, 200),
        (305, 604, 201, 300),
        (605, 1004, 301, 500),
    ],
    "co": [  # ppm
        (0.0, 4.4, 0, 50),
        (4.5, 9.4, 51, 100),
        (9.5, 12.4, 101, 150),
        (12.5, 15.4, 151, 200),
        (15.5, 30.4, 201, 300),
        (30.5, 50.4, 301, 500),
    ],
}

# AQI categories
AQI_CATEGORIES: Final[dict[str, tuple[int, int, str]]] = {
    "Good": (0, 50, "#00E400"),
    "Moderate": (51, 100, "#FFFF00"),
    "Unhealthy for Sensitive Groups": (101, 150, "#FF7E00"),
    "Unhealthy": (151, 200, "#FF0000"),
    "Very Unhealthy": (201, 300, "#8F3F97"),
    "Hazardous": (301, 500, "#7E0023"),
}

# Health recommendations
HEALTH_RECOMMENDATIONS: Final[dict[str, str]] = {
    "Good": "Air quality is satisfactory. Enjoy outdoor activities!",
    "Moderate": "Air quality is acceptable. Unusually sensitive people should consider limiting prolonged outdoor exertion.",
    "Unhealthy for Sensitive Groups": "Children, elderly, and people with respiratory conditions should limit outdoor exposure.",
    "Unhealthy": "Everyone should reduce prolonged outdoor exertion. Sensitive groups should avoid outdoor activities.",
    "Very Unhealthy": "Health alert! Everyone should avoid outdoor activities. Keep windows closed.",
    "Hazardous": "Health emergency! Stay indoors. Use air purifiers if available. Seek medical attention if experiencing symptoms.",
}

# Ensure directories exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
