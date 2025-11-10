"""Data models for the Air Quality Prediction System using Pydantic."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Location(BaseModel):
    """Air quality monitoring location."""

    id: int
    name: str
    locality: str
    country_code: str
    country_name: str
    latitude: float
    longitude: float
    timezone: str


class Measurement(BaseModel):
    """Single air quality measurement."""

    parameter: str
    value: float
    unit: str
    datetime_utc: datetime
    datetime_local: datetime


class PollutantForecast(BaseModel):
    """Forecast for a single pollutant."""

    parameter: str
    current_value: Optional[float] = None
    forecasted_values: dict[int, float] = Field(default_factory=dict)  # hour -> value
    unit: str
    aqi_subindex: Optional[int] = None


class AQIResult(BaseModel):
    """Air Quality Index calculation result."""

    overall_aqi: int
    category: str
    color: str
    primary_pollutant: str
    health_recommendation: str
    pollutant_forecasts: list[PollutantForecast]
    timestamp: datetime = Field(default_factory=datetime.now)


class CityData(BaseModel):
    """Complete air quality data for a city."""

    city_name: str
    country: str
    locations: list[Location]
    current_measurements: list[Measurement]
    forecast: Optional[AQIResult] = None
