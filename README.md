# BreathIn 🌍💨

**Real-Time City-Specific Air Quality Prediction System**

BreathIn is an advanced machine learning application that provides accurate, city-specific air quality predictions using a cascaded multi-model architecture. Get real-time air quality data and 24-hour forecasts to make informed decisions about outdoor activities and protect your health.

## Features

- 🌆 **City-Specific Predictions**: Select any major city worldwide
- 📊 **Real-Time Data**: Current air quality measurements from global monitoring networks
- 🔮 **24-Hour Forecasts**: Predict air quality up to 24 hours in advance
- 🧠 **Cascaded ML Architecture**: Three-level model pipeline for maximum accuracy
- 🎨 **Modern UI**: Clean, intuitive interface built with NiceGUI
- 📈 **Health Recommendations**: Actionable advice based on AQI levels

## Architecture

BreathIn uses a sophisticated three-level cascaded machine learning architecture:

### Level 1: Data Preprocessing & Imputation
- **Model**: k-Nearest Neighbors (kNN)
- **Purpose**: Clean data and fill missing values using temporal patterns

### Level 2: Pollutant-Specific Forecasting
- **Models**: Linear Regression, Polynomial Regression, SVR, Random Forest
- **Purpose**: Predict concentrations for PM2.5, PM10, O₃, NO₂, SO₂, CO

### Level 3: AQI Calculation & Health Assessment
- **Model**: Decision Tree
- **Purpose**: Calculate Air Quality Index and generate health recommendations

## Installation

```bash
# Clone the repository
git clone https://github.com/elshadsabziyev/BreathIn.git
cd BreathIn

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the application
python app.py
```

Then open your browser and navigate to `http://localhost:8080`

## Configuration

Create a `.env` file in the project root (optional):

```env
OPENAQ_API_KEY=your_api_key_here  # Optional: for higher rate limits
```

## Project Structure

```
BreathIn/
├── src/
│   ├── models/          # ML models and data models
│   ├── data/            # Data acquisition and processing
│   └── utils/           # Utility functions
├── data/
│   ├── raw/             # Raw data from APIs
│   ├── processed/       # Processed datasets
│   └── models/          # Trained model files
├── tests/               # Unit tests
├── app.py               # Main application entry point
├── requirements.txt     # Python dependencies
└── README.md
```

## Technologies

- **Frontend**: NiceGUI
- **ML Framework**: scikit-learn
- **Data Processing**: pandas, numpy
- **API**: OpenAQ Platform
- **Type Safety**: Pydantic, mypy

## Data Source

BreathIn uses data from the [OpenAQ Platform](https://openaq.org), a non-profit organization providing open access to global air quality data from over 30,000 monitoring stations in 100+ countries.

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Developed by Elshad Sabziyev

## Acknowledgments

- OpenAQ Platform for providing open air quality data
- U.S. EPA for AQI calculation standards
