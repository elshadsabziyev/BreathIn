"""Level 2: Pollutant-Specific Forecasting Models."""

from typing import Optional, Literal
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
from pathlib import Path
from src.config import (
    POLLUTANTS,
    RANDOM_FOREST_ESTIMATORS,
    SVR_KERNEL,
    POLYNOMIAL_DEGREE,
    MODELS_DIR,
)


ModelType = Literal["linear", "polynomial", "svr", "random_forest"]


class PollutantForecaster:
    """Level 2 of cascade: Forecast individual pollutant concentrations."""

    def __init__(
        self,
        pollutant: str,
        model_type: ModelType = "random_forest",
    ) -> None:
        """Initialize the pollutant forecaster.

        Args:
            pollutant: Name of the pollutant to forecast.
            model_type: Type of regression model to use.
        """
        if pollutant not in POLLUTANTS:
            raise ValueError(f"Invalid pollutant: {pollutant}")

        self.pollutant = pollutant
        self.model_type = model_type
        self.model: Optional[any] = None
        self.scaler: Optional[StandardScaler] = None
        self.poly_features: Optional[PolynomialFeatures] = None
        self.feature_names: list[str] = []

        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize the regression model based on model_type."""
        if self.model_type == "linear":
            self.model = LinearRegression()

        elif self.model_type == "polynomial":
            self.poly_features = PolynomialFeatures(
                degree=POLYNOMIAL_DEGREE, include_bias=False
            )
            self.model = Ridge(alpha=1.0)  # Ridge for regularization

        elif self.model_type == "svr":
            self.model = SVR(kernel=SVR_KERNEL, C=1.0, gamma="scale", epsilon=0.1)

        elif self.model_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=RANDOM_FOREST_ESTIMATORS,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            )

        self.scaler = StandardScaler()

    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features for forecasting.

        Args:
            df: DataFrame with timestamp and pollutant columns.

        Returns:
            DataFrame with engineered features.
        """
        df = df.copy()

        # Temporal features
        df["hour"] = df["timestamp"].dt.hour
        df["day_of_week"] = df["timestamp"].dt.dayofweek
        df["month"] = df["timestamp"].dt.month
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

        # Cyclical encoding
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
        df["day_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
        df["day_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

        # Lag features for the target pollutant
        for lag in [1, 3, 6, 12, 24]:
            df[f"{self.pollutant}_lag_{lag}"] = df[self.pollutant].shift(lag)

        # Rolling statistics
        for window in [3, 6, 12, 24]:
            df[f"{self.pollutant}_rolling_mean_{window}"] = (
                df[self.pollutant].rolling(window=window, min_periods=1).mean()
            )
            df[f"{self.pollutant}_rolling_std_{window}"] = (
                df[self.pollutant].rolling(window=window, min_periods=1).std()
            )

        # Cross-pollutant features (current values of other pollutants)
        for other_pollutant in POLLUTANTS:
            if other_pollutant != self.pollutant and other_pollutant in df.columns:
                df[f"{other_pollutant}_current"] = df[other_pollutant]

        return df

    def _get_feature_columns(self, df: pd.DataFrame) -> list[str]:
        """Get list of feature columns for modeling.

        Args:
            df: DataFrame with all features.

        Returns:
            List of feature column names.
        """
        # Exclude timestamp, target, and intermediate columns
        exclude = ["timestamp", self.pollutant, "hour", "day_of_week", "month"]
        features = [col for col in df.columns if col not in exclude]
        return features

    def fit(self, df: pd.DataFrame) -> "PollutantForecaster":
        """Train the forecasting model.

        Args:
            df: Training DataFrame with timestamp and pollutant columns.

        Returns:
            Self for method chaining.
        """
        # Create features
        df_features = self._create_features(df)

        # Drop rows with NaN in target (from initial lags)
        df_features = df_features.dropna(subset=[self.pollutant])

        # Get feature columns
        self.feature_names = self._get_feature_columns(df_features)

        # Prepare X and y
        X = df_features[self.feature_names].fillna(0)  # Fill remaining NaNs with 0
        y = df_features[self.pollutant]

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Apply polynomial features if needed
        if self.poly_features is not None:
            X_scaled = self.poly_features.fit_transform(X_scaled)

        # Train model
        self.model.fit(X_scaled, y)

        return self

    def predict(
        self, df: pd.DataFrame, hours_ahead: int = 24
    ) -> dict[int, float]:
        """Predict pollutant concentrations for future hours.

        Args:
            df: Historical DataFrame with timestamp and pollutant columns.
            hours_ahead: Number of hours to forecast ahead.

        Returns:
            Dictionary mapping hour offset to predicted concentration.
        """
        if self.model is None or self.scaler is None:
            raise ValueError("Model not fitted. Call fit() first.")

        predictions = {}

        # Use the last 24 hours of data for prediction
        df_recent = df.tail(48).copy()  # Use more history for stability

        for hour in range(1, hours_ahead + 1):
            # Create features
            df_features = self._create_features(df_recent)

            # Get the last row for prediction
            X_last = df_features[self.feature_names].iloc[[-1]].fillna(0)

            # Scale
            X_scaled = self.scaler.transform(X_last)

            # Apply polynomial features if needed
            if self.poly_features is not None:
                X_scaled = self.poly_features.transform(X_scaled)

            # Predict
            pred_value = self.model.predict(X_scaled)[0]
            
            # Apply bounds based on recent data statistics
            recent_mean = df_recent[self.pollutant].mean()
            recent_std = df_recent[self.pollutant].std()
            
            # Clip prediction to reasonable range (within 3 std devs)
            min_val = max(0, recent_mean - 3 * recent_std)
            max_val = recent_mean + 3 * recent_std
            pred_value = np.clip(pred_value, min_val, max_val)
            
            predictions[hour] = max(0, float(pred_value))

            # Add prediction to dataframe for next iteration
            last_timestamp = df_recent["timestamp"].iloc[-1]
            new_timestamp = last_timestamp + pd.Timedelta(hours=1)

            new_row = {col: df_recent[col].iloc[-1] for col in df_recent.columns}
            new_row["timestamp"] = new_timestamp
            new_row[self.pollutant] = pred_value

            df_recent = pd.concat(
                [df_recent, pd.DataFrame([new_row])], ignore_index=True
            ).tail(48)  # Keep only recent data

        return predictions

    def evaluate(self, df: pd.DataFrame) -> dict[str, float]:
        """Evaluate model performance using time series cross-validation.

        Args:
            df: DataFrame with timestamp and pollutant columns.

        Returns:
            Dictionary with evaluation metrics.
        """
        # Create features
        df_features = self._create_features(df)
        df_features = df_features.dropna(subset=[self.pollutant])

        X = df_features[self.feature_names].fillna(0)
        y = df_features[self.pollutant]

        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        rmse_scores = []
        mae_scores = []
        r2_scores = []

        for train_idx, test_idx in tscv.split(X):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            # Scale
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Polynomial features
            if self.poly_features is not None:
                X_train_scaled = self.poly_features.fit_transform(X_train_scaled)
                X_test_scaled = self.poly_features.transform(X_test_scaled)

            # Train and predict
            self.model.fit(X_train_scaled, y_train)
            y_pred = self.model.predict(X_test_scaled)

            # Calculate metrics
            rmse_scores.append(np.sqrt(mean_squared_error(y_test, y_pred)))
            mae_scores.append(mean_absolute_error(y_test, y_pred))
            r2_scores.append(r2_score(y_test, y_pred))

        return {
            "rmse": float(np.mean(rmse_scores)),
            "mae": float(np.mean(mae_scores)),
            "r2": float(np.mean(r2_scores)),
        }

    def save(self, filepath: Optional[Path] = None) -> Path:
        """Save the trained model to disk.

        Args:
            filepath: Path to save the model. If None, uses default path.

        Returns:
            Path where model was saved.
        """
        if filepath is None:
            filepath = MODELS_DIR / f"{self.pollutant}_{self.model_type}.joblib"

        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "poly_features": self.poly_features,
            "feature_names": self.feature_names,
            "pollutant": self.pollutant,
            "model_type": self.model_type,
        }

        joblib.dump(model_data, filepath)
        return filepath

    @classmethod
    def load(cls, filepath: Path) -> "PollutantForecaster":
        """Load a trained model from disk.

        Args:
            filepath: Path to the saved model.

        Returns:
            Loaded PollutantForecaster instance.
        """
        model_data = joblib.load(filepath)

        forecaster = cls(
            pollutant=model_data["pollutant"],
            model_type=model_data["model_type"],
        )

        forecaster.model = model_data["model"]
        forecaster.scaler = model_data["scaler"]
        forecaster.poly_features = model_data["poly_features"]
        forecaster.feature_names = model_data["feature_names"]

        return forecaster
