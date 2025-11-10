"""Main prediction pipeline integrating all three cascade levels."""

from typing import Optional
import pandas as pd
from datetime import datetime
from src.data.openaq_client import OpenAQClient
from src.models.level1_imputation import DataPreprocessor
from src.models.level2_forecasting import PollutantForecaster
from src.models.level3_aqi import AQICalculator
from src.models.data_models import CityData, AQIResult
from src.config import POLLUTANTS, MODELS_DIR


class BreathInPipeline:
    """Complete cascaded prediction pipeline for BreathIn."""

    def __init__(self, api_key: str = "") -> None:
        """Initialize the prediction pipeline.

        Args:
            api_key: Optional OpenAQ API key.
        """
        self.api_client = OpenAQClient(api_key)
        self.preprocessor = DataPreprocessor()
        self.forecasters: dict[str, PollutantForecaster] = {}
        self.aqi_calculator = AQICalculator()
        self.is_trained = False

    def train(self, city_name: str = "New Delhi", country_code: str = "IN") -> dict[str, any]:
        """Train all models in the cascade.

        Args:
            city_name: City to use for training data.
            country_code: Country code.

        Returns:
            Dictionary with training statistics.
        """
        print(f"🔄 Training BreathIn models using data from {city_name}...")

        # Step 1: Fetch historical data
        print("📥 Fetching historical data...")
        historical_data = self.api_client.get_historical_data(
            city_name, country_code, days_back=90
        )

        # Step 2: Level 1 - Data preprocessing and imputation
        print("🧹 Level 1: Cleaning and imputing missing values...")
        validation_before = self.preprocessor.validate_data(historical_data)
        clean_data = self.preprocessor.fit_transform(historical_data)
        validation_after = self.preprocessor.validate_data(clean_data)

        # Step 3: Level 2 - Train pollutant-specific forecasters
        print("🎯 Level 2: Training pollutant forecasting models...")
        model_metrics = {}

        for pollutant in POLLUTANTS:
            if pollutant in clean_data.columns:
                print(f"  Training {pollutant.upper()} forecaster...")
                forecaster = PollutantForecaster(
                    pollutant=pollutant, model_type="random_forest"
                )
                forecaster.fit(clean_data)

                # Evaluate
                metrics = forecaster.evaluate(clean_data)
                model_metrics[pollutant] = metrics

                # Save model
                forecaster.save()

                self.forecasters[pollutant] = forecaster

        # Step 4: Level 3 is rule-based (AQI calculator), no training needed
        print("✅ Level 3: AQI calculator initialized (rule-based)")

        self.is_trained = True

        return {
            "validation_before": validation_before,
            "validation_after": validation_after,
            "model_metrics": model_metrics,
            "training_samples": len(clean_data),
        }

    def predict(
        self, city_name: str, country_code: str, hours_ahead: int = 24
    ) -> AQIResult:
        """Generate air quality predictions for a city.

        Args:
            city_name: Name of the city.
            country_code: Country code.
            hours_ahead: Number of hours to forecast.

        Returns:
            AQIResult with predictions and recommendations.
        """
        if not self.is_trained:
            print("⚠️  Models not trained. Training now...")
            self.train(city_name, country_code)

        # Step 1: Get current and recent data
        city_data = self.api_client.get_city_data(city_name, country_code)
        historical_data = self.api_client.get_historical_data(
            city_name, country_code, days_back=7
        )

        # Step 2: Level 1 - Clean data (fit_transform for new data)
        clean_data = self.preprocessor.fit_transform(historical_data)

        # Step 3: Level 2 - Forecast each pollutant
        pollutant_forecasts = {}
        current_values = {}

        for measurement in city_data.current_measurements:
            current_values[measurement.parameter] = measurement.value

        for pollutant in POLLUTANTS:
            if pollutant in self.forecasters:
                forecaster = self.forecasters[pollutant]
                predictions = forecaster.predict(clean_data, hours_ahead)
                pollutant_forecasts[pollutant] = predictions

        # Step 4: Level 3 - Calculate AQI and recommendations
        aqi_result = self.aqi_calculator.calculate_aqi(
            pollutant_forecasts, current_values
        )

        return aqi_result

    def load_models(self) -> bool:
        """Load pre-trained models from disk.

        Returns:
            True if models loaded successfully, False otherwise.
        """
        try:
            for pollutant in POLLUTANTS:
                model_path = MODELS_DIR / f"{pollutant}_random_forest.joblib"
                if model_path.exists():
                    self.forecasters[pollutant] = PollutantForecaster.load(model_path)

            if len(self.forecasters) > 0:
                self.is_trained = True
                return True

            return False

        except Exception as e:
            print(f"Error loading models: {e}")
            return False

    def get_hourly_forecast(
        self, city_name: str, country_code: str, hours: int = 24
    ) -> dict[int, dict[str, any]]:
        """Get hour-by-hour AQI forecast.

        Args:
            city_name: Name of the city.
            country_code: Country code.
            hours: Number of hours to forecast.

        Returns:
            Dictionary mapping hour to AQI information.
        """
        # Get predictions
        aqi_result = self.predict(city_name, country_code, hours)

        # Extract forecasts
        pollutant_forecasts = {}
        for pf in aqi_result.pollutant_forecasts:
            pollutant_forecasts[pf.parameter] = pf.forecasted_values

        # Calculate hourly AQI
        hourly_forecast = self.aqi_calculator.get_hourly_aqi_forecast(
            pollutant_forecasts, hours
        )

        return hourly_forecast
