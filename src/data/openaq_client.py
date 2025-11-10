"""OpenAQ API client for fetching air quality data."""

import requests
from typing import Optional
from datetime import datetime, timedelta
import pandas as pd
from src.config import OPENAQ_API_BASE_URL, POLLUTANTS
from src.models.data_models import Location, Measurement, CityData


class OpenAQClient:
    """Client for interacting with the OpenAQ API v3."""

    def __init__(self, api_key: str = "") -> None:
        """Initialize the OpenAQ client.

        Args:
            api_key: OpenAQ API key for authentication.
        """
        self.base_url = OPENAQ_API_BASE_URL
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"X-API-Key": api_key})

    def search_cities(self, query: str, limit: int = 10) -> list[dict[str, str]]:
        """Search for cities with air quality monitoring stations.

        Args:
            query: City name to search for.
            limit: Maximum number of results to return.

        Returns:
            List of dictionaries containing city information.
        """
        try:
            # For demo purposes, we'll use a predefined list of major cities
            # In production, this would query the OpenAQ locations endpoint
            major_cities = [
                {"name": "New Delhi", "country": "India", "country_code": "IN"},
                {"name": "Los Angeles", "country": "United States", "country_code": "US"},
                {"name": "London", "country": "United Kingdom", "country_code": "GB"},
                {"name": "Beijing", "country": "China", "country_code": "CN"},
                {"name": "Mexico City", "country": "Mexico", "country_code": "MX"},
                {"name": "São Paulo", "country": "Brazil", "country_code": "BR"},
                {"name": "Tokyo", "country": "Japan", "country_code": "JP"},
                {"name": "Paris", "country": "France", "country_code": "FR"},
                {"name": "Mumbai", "country": "India", "country_code": "IN"},
                {"name": "Bangkok", "country": "Thailand", "country_code": "TH"},
            ]

            # Filter cities based on query
            query_lower = query.lower()
            filtered = [
                city
                for city in major_cities
                if query_lower in city["name"].lower()
            ]
            return filtered[:limit]

        except Exception as e:
            print(f"Error searching cities: {e}")
            return []

    def get_city_locations(self, city_name: str, country_code: str) -> list[Location]:
        """Get all monitoring locations for a city.

        Args:
            city_name: Name of the city.
            country_code: ISO country code.

        Returns:
            List of Location objects.
        """
        # For demo purposes, return synthetic location data
        # In production, this would query the OpenAQ /v3/locations endpoint
        return [
            Location(
                id=1,
                name=f"{city_name} Central",
                locality=city_name,
                country_code=country_code,
                country_name=country_code,
                latitude=0.0,
                longitude=0.0,
                timezone="UTC",
            )
        ]

    def get_latest_measurements(
        self, city_name: str, country_code: str
    ) -> list[Measurement]:
        """Get latest measurements for a city.

        Args:
            city_name: Name of the city.
            country_code: ISO country code.

        Returns:
            List of Measurement objects.
        """
        # Generate synthetic current measurements for demo
        # In production, this would query the OpenAQ /v3/latest endpoint
        import random

        measurements = []
        now = datetime.now()

        # Generate realistic values for each pollutant
        pollutant_ranges = {
            "pm25": (5.0, 150.0, "µg/m³"),
            "pm10": (10.0, 200.0, "µg/m³"),
            "o3": (0.02, 0.08, "ppm"),
            "no2": (10.0, 100.0, "ppb"),
            "so2": (5.0, 50.0, "ppb"),
            "co": (0.5, 8.0, "ppm"),
        }

        for param in POLLUTANTS:
            if param in pollutant_ranges:
                min_val, max_val, unit = pollutant_ranges[param]
                value = random.uniform(min_val, max_val)
                measurements.append(
                    Measurement(
                        parameter=param,
                        value=round(value, 2),
                        unit=unit,
                        datetime_utc=now,
                        datetime_local=now,
                    )
                )

        return measurements

    def get_historical_data(
        self,
        city_name: str,
        country_code: str,
        days_back: int = 30,
    ) -> pd.DataFrame:
        """Get historical air quality data for model training.

        Args:
            city_name: Name of the city.
            country_code: ISO country code.
            days_back: Number of days of historical data to fetch.

        Returns:
            DataFrame with historical measurements.
        """
        # Generate synthetic historical data for demo
        # In production, this would query the OpenAQ /v3/sensors/{id}/hours endpoint
        import random
        import numpy as np

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Generate hourly timestamps
        timestamps = pd.date_range(start=start_date, end=end_date, freq="H")

        data = {"timestamp": timestamps}

        # Generate synthetic time series for each pollutant with realistic patterns
        for param in POLLUTANTS:
            # Base values with diurnal and weekly patterns
            hours = np.array([t.hour for t in timestamps])
            days = np.array([t.dayofweek for t in timestamps])

            if param == "pm25":
                # Higher in morning/evening rush hours
                base = 30 + 15 * np.sin(2 * np.pi * hours / 24)
                base += 5 * (days < 5)  # Higher on weekdays
                noise = np.random.normal(0, 5, len(timestamps))
                data[param] = np.maximum(5, base + noise)

            elif param == "pm10":
                base = 50 + 20 * np.sin(2 * np.pi * hours / 24)
                base += 8 * (days < 5)
                noise = np.random.normal(0, 8, len(timestamps))
                data[param] = np.maximum(10, base + noise)

            elif param == "o3":
                # Higher in afternoon due to photochemical reactions
                base = 0.04 + 0.02 * np.sin(2 * np.pi * (hours - 6) / 24)
                noise = np.random.normal(0, 0.005, len(timestamps))
                data[param] = np.maximum(0.01, base + noise)

            elif param == "no2":
                # Traffic-related, higher during rush hours
                base = 40 + 20 * np.sin(2 * np.pi * hours / 24)
                base += 10 * (days < 5)
                noise = np.random.normal(0, 8, len(timestamps))
                data[param] = np.maximum(5, base + noise)

            elif param == "so2":
                base = 20 + 10 * np.sin(2 * np.pi * hours / 24)
                noise = np.random.normal(0, 5, len(timestamps))
                data[param] = np.maximum(2, base + noise)

            elif param == "co":
                base = 2.5 + 1.5 * np.sin(2 * np.pi * hours / 24)
                base += 0.5 * (days < 5)
                noise = np.random.normal(0, 0.3, len(timestamps))
                data[param] = np.maximum(0.3, base + noise)

        df = pd.DataFrame(data)

        # Introduce some missing values (5-10%)
        for param in POLLUTANTS:
            mask = np.random.random(len(df)) < 0.07
            df.loc[mask, param] = np.nan

        return df

    def get_city_data(self, city_name: str, country_code: str) -> CityData:
        """Get complete air quality data for a city.

        Args:
            city_name: Name of the city.
            country_code: ISO country code.

        Returns:
            CityData object with all relevant information.
        """
        locations = self.get_city_locations(city_name, country_code)
        measurements = self.get_latest_measurements(city_name, country_code)

        return CityData(
            city_name=city_name,
            country=country_code,
            locations=locations,
            current_measurements=measurements,
        )
