# BreathIn - Technical Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Machine Learning Models](#machine-learning-models)
4. [Data Flow](#data-flow)
5. [API Reference](#api-reference)
6. [Deployment](#deployment)
7. [Testing](#testing)

---

## Overview

BreathIn is a real-time air quality prediction system that uses a cascaded multi-model machine learning architecture to forecast air quality up to 24 hours in advance for any city worldwide.

### Key Features
- **City-Specific Predictions**: Works with any major city globally
- **Real-Time Data**: Integrates with OpenAQ API for current measurements
- **Multi-Pollutant Tracking**: Monitors PM2.5, PM10, O₃, NO₂, SO₂, CO
- **Cascaded ML Pipeline**: Three-level architecture for optimal accuracy
- **Health Recommendations**: Actionable advice based on EPA AQI standards

---

## System Architecture

### Three-Level Cascade

```
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 1: Data Preprocessing & Imputation                   │
│ Model: k-Nearest Neighbors (kNN)                            │
│ Purpose: Clean data and fill missing values                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 2: Pollutant-Specific Forecasting                    │
│ Models: Linear Regression, Polynomial Regression,          │
│         SVR, Random Forest                                  │
│ Purpose: Predict individual pollutant concentrations       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 3: AQI Calculation & Health Assessment               │
│ Model: Decision Tree                                        │
│ Purpose: Calculate AQI and generate recommendations        │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
BreathIn/
├── app.py                      # Main NiceGUI application
├── src/
│   ├── config.py               # Configuration and constants
│   ├── models/
│   │   ├── data_models.py      # Pydantic data models
│   │   ├── level1_imputation.py    # kNN imputation
│   │   ├── level2_forecasting.py   # Pollutant forecasters
│   │   ├── level3_aqi.py          # AQI calculator
│   │   └── prediction_pipeline.py  # Main pipeline
│   ├── data/
│   │   └── openaq_client.py    # OpenAQ API client
│   └── utils/
├── data/
│   ├── raw/                    # Raw API data
│   ├── processed/              # Cleaned datasets
│   └── models/                 # Trained model files
├── tests/
└── test_pipeline.py            # Integration tests
```

---

## Machine Learning Models

### Level 1: k-Nearest Neighbors Imputation

**Purpose**: Fill missing values in air quality time series data

**Algorithm**: kNN with distance weighting
- `n_neighbors`: 5
- `weights`: "distance"

**Features Used**:
- Temporal features (hour, day of week, month)
- Cyclical encoding (sin/cos transformations)
- All pollutant concentrations

**Validation**: Missing value statistics before/after imputation

### Level 2: Pollutant Forecasting

**Purpose**: Predict future concentrations for each pollutant

**Model Selection**:
- **Default**: Random Forest (best overall performance)
- **Alternatives**: Linear Regression, Polynomial Regression, SVR

**Random Forest Configuration**:
- `n_estimators`: 200
- `max_depth`: 15
- `min_samples_split`: 5
- `min_samples_leaf`: 2

**Feature Engineering**:
1. **Temporal Features**:
   - Hour, day of week, month (cyclical encoding)
   - Weekend indicator

2. **Lag Features**:
   - Lags: 1, 3, 6, 12, 24 hours

3. **Rolling Statistics**:
   - Windows: 3, 6, 12, 24 hours
   - Mean and standard deviation

4. **Cross-Pollutant Features**:
   - Current values of other pollutants

**Evaluation Metrics**:
- RMSE (Root Mean Squared Error)
- MAE (Mean Absolute Error)
- R² Score

**Typical Performance** (on synthetic data):
```
PM2.5:  R² = 0.91, RMSE = 0.30
PM10:   R² = 0.87, RMSE = 0.35
O₃:     R² = 0.94, RMSE = 0.25
NO₂:    R² = 0.89, RMSE = 0.34
SO₂:    R² = 0.82, RMSE = 0.42
CO:     R² = 0.96, RMSE = 0.20
```

### Level 3: AQI Calculation

**Purpose**: Convert pollutant concentrations to AQI and health categories

**Algorithm**: Rule-based with Decision Tree classifier

**AQI Calculation**:
Uses EPA breakpoint formula:
```
AQI = ((I_high - I_low) / (C_high - C_low)) * (C - C_low) + I_low
```

Where:
- `C`: Pollutant concentration
- `C_low`, `C_high`: Breakpoint concentrations
- `I_low`, `I_high`: Breakpoint AQI values

**Health Categories**:
- 0-50: Good (Green)
- 51-100: Moderate (Yellow)
- 101-150: Unhealthy for Sensitive Groups (Orange)
- 151-200: Unhealthy (Red)
- 201-300: Very Unhealthy (Purple)
- 301-500: Hazardous (Maroon)

---

## Data Flow

### Training Phase

1. **Data Acquisition**:
   ```python
   historical_data = client.get_historical_data(city, country, days_back=90)
   ```

2. **Level 1 Processing**:
   ```python
   clean_data = preprocessor.fit_transform(historical_data)
   ```

3. **Level 2 Training**:
   ```python
   for pollutant in POLLUTANTS:
       forecaster = PollutantForecaster(pollutant, "random_forest")
       forecaster.fit(clean_data)
       forecaster.save()
   ```

4. **Level 3 Initialization**:
   ```python
   aqi_calculator = AQICalculator()  # Rule-based, no training
   ```

### Prediction Phase

1. **Get Current Data**:
   ```python
   city_data = client.get_city_data(city_name, country_code)
   historical = client.get_historical_data(city_name, country_code, days_back=7)
   ```

2. **Clean Data**:
   ```python
   clean_data = preprocessor.transform(historical)
   ```

3. **Forecast Pollutants**:
   ```python
   for pollutant in POLLUTANTS:
       predictions = forecaster.predict(clean_data, hours_ahead=24)
   ```

4. **Calculate AQI**:
   ```python
   aqi_result = aqi_calculator.calculate_aqi(pollutant_forecasts, current_values)
   ```

---

## API Reference

### BreathInPipeline

Main prediction pipeline class.

#### Methods

**`train(city_name: str, country_code: str) -> dict`**
- Trains all models using historical data
- Returns training statistics and model metrics

**`predict(city_name: str, country_code: str, hours_ahead: int = 24) -> AQIResult`**
- Generates air quality predictions
- Returns AQI result with forecasts and recommendations

**`load_models() -> bool`**
- Loads pre-trained models from disk
- Returns True if successful

**`get_hourly_forecast(city_name: str, country_code: str, hours: int = 24) -> dict`**
- Returns hour-by-hour AQI forecast
- Dictionary mapping hour to AQI information

### OpenAQClient

Client for OpenAQ API integration.

#### Methods

**`search_cities(query: str, limit: int = 10) -> list[dict]`**
- Searches for cities with air quality data
- Returns list of city information

**`get_city_data(city_name: str, country_code: str) -> CityData`**
- Gets complete air quality data for a city
- Returns CityData object with measurements

**`get_historical_data(city_name: str, country_code: str, days_back: int = 30) -> pd.DataFrame`**
- Fetches historical air quality data
- Returns DataFrame with time series data

---

## Deployment

### Local Development

```bash
# Clone repository
git clone https://github.com/elshadsabziyev/BreathIn.git
cd BreathIn

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

Access at: `http://localhost:8080`

### Production Deployment

**Requirements**:
- Python 3.11+
- 2GB RAM minimum
- Internet connection for API access

**Environment Variables**:
```bash
OPENAQ_API_KEY=your_key_here  # Optional
APP_PORT=8080
DEBUG=False
```

**Docker Deployment** (future):
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

---

## Testing

### Run Integration Tests

```bash
python test_pipeline.py
```

### Expected Output

```
✅ All tests passed successfully!

Model Performance:
  PM2.5:  RMSE: 0.30, R²: 0.91
  PM10:   RMSE: 0.35, R²: 0.87
  O₃:     RMSE: 0.25, R²: 0.94
  NO₂:    RMSE: 0.34, R²: 0.89
  SO₂:    RMSE: 0.42, R²: 0.82
  CO:     RMSE: 0.20, R²: 0.96
```

### Unit Tests (future enhancement)

```bash
pytest tests/
```

---

## Common ML Pitfalls Addressed

### 1. Data Leakage
✅ **Solution**: Time series cross-validation with proper train/test splits

### 2. Missing Values
✅ **Solution**: kNN imputation with temporal features

### 3. Overfitting
✅ **Solution**: 
- Regularization (Ridge for polynomial)
- Max depth limits for Random Forest
- Cross-validation

### 4. Imbalanced Data
✅ **Solution**: Regression problem (not classification), no class imbalance

### 5. Feature Scaling
✅ **Solution**: StandardScaler applied to all features

### 6. Temporal Dependencies
✅ **Solution**: 
- Lag features
- Rolling statistics
- Time series cross-validation

---

## Future Enhancements

1. **Real OpenAQ API Integration**: Replace synthetic data with live API calls
2. **Weather Data**: Integrate temperature, humidity, wind speed
3. **Model Ensemble**: Combine predictions from multiple model types
4. **Uncertainty Quantification**: Provide confidence intervals
5. **Mobile App**: React Native or Flutter frontend
6. **Alert System**: Email/SMS notifications for poor air quality
7. **Historical Analysis**: Trend analysis and seasonal patterns
8. **Multi-City Comparison**: Compare air quality across cities

---

## References

1. U.S. EPA Air Quality Index: https://www.airnow.gov/aqi/
2. OpenAQ Platform: https://openaq.org
3. scikit-learn Documentation: https://scikit-learn.org
4. NiceGUI Documentation: https://nicegui.io

---

**Version**: 1.0.0  
**Last Updated**: November 2025  
**Author**: Elshad Sabziyev
