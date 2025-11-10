"""BreathIn - Real-Time Air Quality Prediction System.

Main application using NiceGUI for the frontend interface.
"""

from nicegui import ui, app
from typing import Optional
import asyncio
from datetime import datetime
from src.models.prediction_pipeline import BreathInPipeline
from src.data.openaq_client import OpenAQClient
from src.models.data_models import AQIResult


class BreathInApp:
    """Main BreathIn application with NiceGUI interface."""

    def __init__(self) -> None:
        """Initialize the BreathIn application."""
        self.pipeline = BreathInPipeline()
        self.api_client = OpenAQClient()
        self.current_city: Optional[str] = None
        self.current_country: Optional[str] = None
        self.current_result: Optional[AQIResult] = None
        self.is_loading = False

        # Try to load pre-trained models
        models_loaded = self.pipeline.load_models()
        if models_loaded:
            print("✅ Pre-trained models loaded successfully")
        else:
            print("⚠️  No pre-trained models found. Will train on first prediction.")

    def get_aqi_color(self, aqi: int) -> str:
        """Get color for AQI value.

        Args:
            aqi: AQI value.

        Returns:
            Hex color code.
        """
        if aqi <= 50:
            return "#00E400"
        elif aqi <= 100:
            return "#FFFF00"
        elif aqi <= 150:
            return "#FF7E00"
        elif aqi <= 200:
            return "#FF0000"
        elif aqi <= 300:
            return "#8F3F97"
        else:
            return "#7E0023"

    async def search_and_predict(
        self, city_input: str, result_container: ui.column
    ) -> None:
        """Search for city and generate predictions.

        Args:
            city_input: City name entered by user.
            result_container: UI container to display results.
        """
        if not city_input or self.is_loading:
            return

        self.is_loading = True
        result_container.clear()

        with result_container:
            ui.spinner(size="lg")
            ui.label("🔄 Generating predictions...").classes("text-lg")

        # Search for city
        cities = self.api_client.search_cities(city_input, limit=1)

        if not cities:
            result_container.clear()
            with result_container:
                ui.label("❌ City not found. Try another city.").classes(
                    "text-red-600 text-lg"
                )
            self.is_loading = False
            return

        city = cities[0]
        self.current_city = city["name"]
        self.current_country = city["country_code"]

        # Generate predictions
        try:
            result = await asyncio.to_thread(
                self.pipeline.predict, self.current_city, self.current_country, 24
            )
            self.current_result = result

            # Display results
            self.display_results(result_container, result)

        except Exception as e:
            result_container.clear()
            with result_container:
                ui.label(f"❌ Error generating predictions: {str(e)}").classes(
                    "text-red-600"
                )

        self.is_loading = False

    def display_results(self, container: ui.column, result: AQIResult) -> None:
        """Display prediction results.

        Args:
            container: UI container to display results.
            result: AQI prediction result.
        """
        container.clear()

        with container:
            # Header
            ui.label(f"Air Quality in {self.current_city}").classes(
                "text-3xl font-bold mb-4"
            )

            # Current AQI Card
            with ui.card().classes("w-full p-6 mb-4"):
                ui.label("Current Air Quality").classes("text-xl font-semibold mb-2")

                # AQI Gauge
                aqi_color = result.color
                with ui.row().classes("items-center gap-4 mb-4"):
                    # Large AQI number
                    ui.label(str(result.overall_aqi)).classes(
                        f"text-6xl font-bold"
                    ).style(f"color: {aqi_color}")

                    with ui.column():
                        ui.label(result.category).classes("text-2xl font-semibold")
                        ui.label(f"Primary: {result.primary_pollutant.upper()}").classes(
                            "text-gray-600"
                        )

                # AQI Scale
                with ui.row().classes("w-full gap-1 mb-4"):
                    colors = ["#00E400", "#FFFF00", "#FF7E00", "#FF0000", "#8F3F97", "#7E0023"]
                    for color in colors:
                        ui.element("div").classes("h-4 flex-1").style(
                            f"background-color: {color}"
                        )

                ui.label("0 - Good | 50 - Moderate | 100 - Unhealthy for Sensitive | 150 - Unhealthy | 200 - Very Unhealthy | 300+ - Hazardous").classes(
                    "text-xs text-gray-500"
                )

            # Health Recommendations
            with ui.card().classes("w-full p-6 mb-4").style(
                f"border-left: 4px solid {aqi_color}"
            ):
                ui.label("🏥 Health Recommendations").classes(
                    "text-xl font-semibold mb-2"
                )
                ui.label(result.health_recommendation).classes("text-base")

            # Pollutant Details
            with ui.card().classes("w-full p-6 mb-4"):
                ui.label("📊 Pollutant Levels").classes("text-xl font-semibold mb-4")

                # Create grid for pollutants
                with ui.grid(columns=3).classes("w-full gap-4"):
                    for pf in result.pollutant_forecasts:
                        if pf.current_value is not None:
                            with ui.card().classes("p-4"):
                                ui.label(pf.parameter.upper()).classes(
                                    "font-bold text-lg"
                                )
                                ui.label(f"{pf.current_value:.2f} {pf.unit}").classes(
                                    "text-2xl"
                                )
                                if pf.aqi_subindex:
                                    sub_color = self.get_aqi_color(pf.aqi_subindex)
                                    ui.label(f"AQI: {pf.aqi_subindex}").classes(
                                        "text-sm"
                                    ).style(f"color: {sub_color}")

            # 24-Hour Forecast
            with ui.card().classes("w-full p-6"):
                ui.label("🔮 24-Hour Forecast").classes("text-xl font-semibold mb-4")

                # Get hourly forecast
                hourly = self.pipeline.get_hourly_forecast(
                    self.current_city, self.current_country, 24
                )

                # Create chart data
                hours = list(range(1, 25))
                aqi_values = [hourly[h]["aqi"] for h in hours]

                # Simple bar chart using HTML/CSS
                max_aqi = max(aqi_values) if aqi_values else 100

                with ui.column().classes("w-full"):
                    for i, (hour, aqi) in enumerate(zip(hours, aqi_values)):
                        with ui.row().classes("items-center gap-2 mb-1"):
                            ui.label(f"{hour}h").classes("w-12 text-sm")

                            # Bar
                            bar_width = (aqi / max_aqi) * 100 if max_aqi > 0 else 0
                            bar_color = self.get_aqi_color(aqi)

                            ui.element("div").classes("h-6 rounded").style(
                                f"width: {bar_width}%; background-color: {bar_color}; min-width: 30px"
                            )

                            ui.label(str(aqi)).classes("w-12 text-sm font-semibold")

            # Timestamp
            ui.label(
                f"Last updated: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            ).classes("text-xs text-gray-500 mt-4")

    def create_ui(self) -> None:
        """Create the main UI layout."""
        # Page configuration
        ui.page_title("BreathIn - Air Quality Prediction")

        # Custom CSS
        ui.add_head_html("""
            <style>
                .q-page {
                    padding: 2rem;
                    max-width: 1200px;
                    margin: 0 auto;
                }
            </style>
        """)

        # Header
        with ui.header().classes("items-center justify-between bg-blue-600"):
            with ui.row().classes("items-center gap-2"):
                ui.label("🌍").classes("text-3xl")
                ui.label("BreathIn").classes("text-2xl font-bold")
            ui.label("Real-Time Air Quality Prediction").classes("text-sm")

        # Main content
        with ui.column().classes("w-full gap-4 p-4"):
            # Welcome section
            with ui.card().classes("w-full p-6 bg-gradient-to-r from-blue-50 to-blue-100"):
                ui.label("Welcome to BreathIn").classes("text-3xl font-bold mb-2")
                ui.label(
                    "Get real-time air quality data and 24-hour forecasts for any city worldwide."
                ).classes("text-lg text-gray-700 mb-4")

                # Search bar
                with ui.row().classes("w-full gap-2 items-center"):
                    city_input = ui.input(
                        label="Enter city name",
                        placeholder="e.g., New Delhi, Los Angeles, London",
                    ).classes("flex-grow")

                    result_container = ui.column().classes("w-full mt-4")

                    async def on_search():
                        await self.search_and_predict(
                            city_input.value, result_container
                        )

                    ui.button("Get Air Quality", on_click=on_search).classes(
                        "bg-blue-600 text-white"
                    )

                    # Allow Enter key to search
                    city_input.on("keydown.enter", on_search)

            # Results container
            # (will be populated by search)

            # Footer
            with ui.card().classes("w-full p-4 mt-8 bg-gray-50"):
                ui.label("About BreathIn").classes("font-semibold mb-2")
                ui.label(
                    "BreathIn uses a cascaded machine learning architecture with kNN imputation, "
                    "pollutant-specific forecasting (Linear/Polynomial Regression, SVR, Random Forest), "
                    "and decision tree-based health recommendations."
                ).classes("text-sm text-gray-600 mb-2")

                ui.label("Data source: OpenAQ Platform | Created by Elshad Sabziyev").classes(
                    "text-xs text-gray-500"
                )


def main() -> None:
    """Main entry point for the application."""
    breath_app = BreathInApp()
    breath_app.create_ui()

    # Run the app
    ui.run(
        title="BreathIn - Air Quality Prediction",
        port=8080,
        reload=False,
        show=False,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
