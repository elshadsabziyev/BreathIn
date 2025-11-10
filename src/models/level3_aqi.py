"""Level 3: AQI Calculation and Health Risk Assessment."""

from typing import Optional
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from src.config import AQI_BREAKPOINTS, AQI_CATEGORIES, HEALTH_RECOMMENDATIONS
from src.models.data_models import AQIResult, PollutantForecast


class AQICalculator:
    """Level 3 of cascade: Calculate AQI and provide health recommendations."""

    def __init__(self) -> None:
        """Initialize the AQI calculator."""
        self.decision_tree: Optional[DecisionTreeClassifier] = None
        self._train_decision_tree()

    def _calculate_subindex(self, pollutant: str, concentration: float) -> int:
        """Calculate AQI sub-index for a single pollutant.

        Args:
            pollutant: Name of the pollutant.
            concentration: Measured concentration.

        Returns:
            AQI sub-index value.
        """
        if pollutant not in AQI_BREAKPOINTS:
            return 0

        breakpoints = AQI_BREAKPOINTS[pollutant]

        # Find the appropriate breakpoint range
        for c_low, c_high, i_low, i_high in breakpoints:
            if c_low <= concentration <= c_high:
                # Linear interpolation formula
                aqi = ((i_high - i_low) / (c_high - c_low)) * (
                    concentration - c_low
                ) + i_low
                return int(round(aqi))

        # If concentration exceeds all breakpoints, use the highest category
        if concentration > breakpoints[-1][1]:
            return 500

        return 0

    def _get_category_from_aqi(self, aqi: int) -> tuple[str, str]:
        """Get AQI category and color from AQI value.

        Args:
            aqi: AQI value.

        Returns:
            Tuple of (category_name, color_hex).
        """
        for category, (min_aqi, max_aqi, color) in AQI_CATEGORIES.items():
            if min_aqi <= aqi <= max_aqi:
                return category, color

        # Default to Hazardous if AQI is very high
        return "Hazardous", "#7E0023"

    def _train_decision_tree(self) -> None:
        """Train a simple decision tree for health recommendations.

        This creates a rule-based classifier that maps AQI ranges to
        health recommendation categories.
        """
        # Create synthetic training data based on AQI categories
        X_train = []
        y_train = []

        category_mapping = {
            "Good": 0,
            "Moderate": 1,
            "Unhealthy for Sensitive Groups": 2,
            "Unhealthy": 3,
            "Very Unhealthy": 4,
            "Hazardous": 5,
        }

        # Generate samples for each category
        for category, (min_aqi, max_aqi, _) in AQI_CATEGORIES.items():
            # Create samples across the range
            for aqi in range(min_aqi, max_aqi + 1, 5):
                X_train.append([aqi])
                y_train.append(category_mapping[category])

        # Train the decision tree
        self.decision_tree = DecisionTreeClassifier(
            max_depth=6, random_state=42, min_samples_split=5
        )
        self.decision_tree.fit(X_train, y_train)

    def _get_health_recommendation(
        self, aqi: int, category: str, primary_pollutant: str
    ) -> str:
        """Get health recommendation based on AQI and primary pollutant.

        Args:
            aqi: Overall AQI value.
            category: AQI category name.
            primary_pollutant: Primary pollutant driving the AQI.

        Returns:
            Health recommendation text.
        """
        base_recommendation = HEALTH_RECOMMENDATIONS.get(
            category, "No recommendation available."
        )

        # Add pollutant-specific advice for certain categories
        pollutant_advice = {
            "o3": "Ozone levels are elevated. Limit outdoor activities during peak afternoon hours.",
            "pm25": "Fine particulate matter is elevated. Consider wearing a mask if outdoors for extended periods.",
            "pm10": "Coarse particulate matter is elevated. Avoid dusty areas and outdoor exercise.",
            "no2": "Nitrogen dioxide levels are high. Avoid areas with heavy traffic.",
        }

        if category in ["Unhealthy for Sensitive Groups", "Unhealthy", "Very Unhealthy"]:
            if primary_pollutant in pollutant_advice:
                base_recommendation += f" {pollutant_advice[primary_pollutant]}"

        return base_recommendation

    def calculate_aqi(
        self,
        pollutant_forecasts: dict[str, dict[int, float]],
        current_values: Optional[dict[str, float]] = None,
    ) -> AQIResult:
        """Calculate overall AQI from pollutant forecasts.

        Args:
            pollutant_forecasts: Dictionary mapping pollutant names to
                                 dictionaries of hour -> concentration.
            current_values: Optional dictionary of current pollutant values.

        Returns:
            AQIResult with overall AQI and health recommendations.
        """
        # Calculate sub-indices for each pollutant
        pollutant_results = []

        for pollutant, forecasts in pollutant_forecasts.items():
            # Get current value
            current_val = None
            if current_values and pollutant in current_values:
                current_val = current_values[pollutant]

            # Calculate AQI sub-index for current value
            aqi_subindex = None
            if current_val is not None:
                aqi_subindex = self._calculate_subindex(pollutant, current_val)

            # Get unit
            unit = "µg/m³"
            if pollutant in ["o3", "co"]:
                unit = "ppm"
            elif pollutant in ["no2", "so2"]:
                unit = "ppb"

            pollutant_results.append(
                PollutantForecast(
                    parameter=pollutant,
                    current_value=current_val,
                    forecasted_values=forecasts,
                    unit=unit,
                    aqi_subindex=aqi_subindex,
                )
            )

        # Find the maximum AQI sub-index (primary pollutant)
        max_aqi = 0
        primary_pollutant = "pm25"

        for result in pollutant_results:
            if result.aqi_subindex is not None and result.aqi_subindex > max_aqi:
                max_aqi = result.aqi_subindex
                primary_pollutant = result.parameter

        # Get category and color
        category, color = self._get_category_from_aqi(max_aqi)

        # Get health recommendation
        health_recommendation = self._get_health_recommendation(
            max_aqi, category, primary_pollutant
        )

        return AQIResult(
            overall_aqi=max_aqi,
            category=category,
            color=color,
            primary_pollutant=primary_pollutant,
            health_recommendation=health_recommendation,
            pollutant_forecasts=pollutant_results,
        )

    def predict_category(self, aqi: int) -> int:
        """Use decision tree to predict category from AQI.

        Args:
            aqi: AQI value.

        Returns:
            Category index (0-5).
        """
        if self.decision_tree is None:
            raise ValueError("Decision tree not trained.")

        return int(self.decision_tree.predict([[aqi]])[0])

    def get_hourly_aqi_forecast(
        self, pollutant_forecasts: dict[str, dict[int, float]], hours: int = 24
    ) -> dict[int, dict[str, any]]:
        """Calculate AQI forecast for each hour.

        Args:
            pollutant_forecasts: Dictionary mapping pollutant names to
                                 dictionaries of hour -> concentration.
            hours: Number of hours to forecast.

        Returns:
            Dictionary mapping hour to AQI information.
        """
        hourly_forecast = {}

        for hour in range(1, hours + 1):
            # Get concentrations for this hour
            hour_concentrations = {}
            for pollutant, forecasts in pollutant_forecasts.items():
                if hour in forecasts:
                    hour_concentrations[pollutant] = forecasts[hour]

            # Calculate AQI for this hour
            max_aqi = 0
            primary_pollutant = "pm25"

            for pollutant, concentration in hour_concentrations.items():
                aqi_subindex = self._calculate_subindex(pollutant, concentration)
                if aqi_subindex > max_aqi:
                    max_aqi = aqi_subindex
                    primary_pollutant = pollutant

            category, color = self._get_category_from_aqi(max_aqi)

            hourly_forecast[hour] = {
                "aqi": max_aqi,
                "category": category,
                "color": color,
                "primary_pollutant": primary_pollutant,
            }

        return hourly_forecast
