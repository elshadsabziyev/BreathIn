"""Test script to verify the BreathIn pipeline works correctly."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.prediction_pipeline import BreathInPipeline
from src.data.openaq_client import OpenAQClient


def test_pipeline():
    """Test the complete prediction pipeline."""
    print("=" * 60)
    print("🧪 Testing BreathIn Prediction Pipeline")
    print("=" * 60)

    # Initialize pipeline
    print("\n1️⃣ Initializing pipeline...")
    pipeline = BreathInPipeline()
    print("✅ Pipeline initialized")

    # Test data acquisition
    print("\n2️⃣ Testing data acquisition...")
    client = OpenAQClient()
    cities = client.search_cities("New Delhi")
    print(f"✅ Found {len(cities)} cities")

    if cities:
        city = cities[0]
        print(f"   City: {city['name']}, {city['country']}")

        # Get current measurements
        measurements = client.get_latest_measurements(
            city["name"], city["country_code"]
        )
        print(f"✅ Retrieved {len(measurements)} current measurements")

        for m in measurements[:3]:
            print(f"   {m.parameter.upper()}: {m.value} {m.unit}")

    # Train the pipeline
    print("\n3️⃣ Training the pipeline...")
    training_stats = pipeline.train("New Delhi", "IN")
    print("✅ Training complete!")
    print(f"   Training samples: {training_stats['training_samples']}")

    # Show model metrics
    print("\n📊 Model Performance Metrics:")
    for pollutant, metrics in training_stats["model_metrics"].items():
        print(f"\n   {pollutant.upper()}:")
        print(f"      RMSE: {metrics['rmse']:.4f}")
        print(f"      MAE:  {metrics['mae']:.4f}")
        print(f"      R²:   {metrics['r2']:.4f}")

    # Generate predictions
    print("\n4️⃣ Generating predictions...")
    result = pipeline.predict("New Delhi", "IN", hours_ahead=24)
    print("✅ Predictions generated!")

    print(f"\n🌍 Air Quality in New Delhi")
    print(f"   Overall AQI: {result.overall_aqi}")
    print(f"   Category: {result.category}")
    print(f"   Primary Pollutant: {result.primary_pollutant.upper()}")
    print(f"   Health Recommendation: {result.health_recommendation}")

    print("\n📊 Current Pollutant Levels:")
    for pf in result.pollutant_forecasts:
        if pf.current_value:
            print(
                f"   {pf.parameter.upper()}: {pf.current_value:.2f} {pf.unit} "
                f"(AQI: {pf.aqi_subindex})"
            )

    # Test hourly forecast
    print("\n5️⃣ Testing hourly forecast...")
    hourly = pipeline.get_hourly_forecast("New Delhi", "IN", 24)
    print("✅ Hourly forecast generated!")

    print("\n🔮 Next 6 Hours Forecast:")
    for hour in range(1, 7):
        h = hourly[hour]
        print(f"   Hour {hour}: AQI {h['aqi']} ({h['category']}) - {h['primary_pollutant'].upper()}")

    print("\n" + "=" * 60)
    print("✅ All tests passed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_pipeline()
