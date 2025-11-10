"""Level 1: Data Preprocessing and kNN-based Missing Value Imputation."""

from typing import Optional
import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler
from src.config import KNN_NEIGHBORS, POLLUTANTS


class DataPreprocessor:
    """Level 1 of cascade: Clean and impute missing values in air quality data."""

    def __init__(self, n_neighbors: int = KNN_NEIGHBORS) -> None:
        """Initialize the data preprocessor.

        Args:
            n_neighbors: Number of neighbors to use for kNN imputation.
        """
        self.n_neighbors = n_neighbors
        self.imputer: Optional[KNNImputer] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_columns: list[str] = []

    def _create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create temporal features for better imputation.

        Args:
            df: DataFrame with timestamp column.

        Returns:
            DataFrame with added temporal features.
        """
        df = df.copy()
        df["hour"] = df["timestamp"].dt.hour
        df["day_of_week"] = df["timestamp"].dt.dayofweek
        df["month"] = df["timestamp"].dt.month
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

        # Cyclical encoding for hour (24-hour cycle)
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

        # Cyclical encoding for day of week (7-day cycle)
        df["day_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
        df["day_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)

        return df

    def fit(self, df: pd.DataFrame) -> "DataPreprocessor":
        """Fit the imputer on training data.

        Args:
            df: Training DataFrame with timestamp and pollutant columns.

        Returns:
            Self for method chaining.
        """
        # Create temporal features
        df_features = self._create_temporal_features(df)

        # Select features for imputation
        self.feature_columns = (
            POLLUTANTS
            + ["hour_sin", "hour_cos", "day_sin", "day_cos", "is_weekend"]
        )

        # Initialize and fit the scaler
        self.scaler = StandardScaler()
        X = df_features[self.feature_columns].copy()
        self.scaler.fit(X)

        # Initialize and fit the kNN imputer
        self.imputer = KNNImputer(
            n_neighbors=self.n_neighbors,
            weights="distance",  # Weight by inverse distance
        )
        X_scaled = self.scaler.transform(X)
        self.imputer.fit(X_scaled)

        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Impute missing values in the data.

        Args:
            df: DataFrame with timestamp and pollutant columns.

        Returns:
            DataFrame with imputed values.
        """
        if self.imputer is None or self.scaler is None:
            raise ValueError("Imputer not fitted. Call fit() first.")

        # Create temporal features
        df_features = self._create_temporal_features(df)

        # Scale features
        X = df_features[self.feature_columns].copy()
        X_scaled = self.scaler.transform(X)

        # Impute missing values
        X_imputed = self.imputer.transform(X_scaled)

        # Create result DataFrame
        result = df.copy()
        for i, col in enumerate(self.feature_columns):
            if col in POLLUTANTS:
                result[col] = X_imputed[:, i]

        return result

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fit the imputer and transform the data in one step.

        Args:
            df: DataFrame with timestamp and pollutant columns.

        Returns:
            DataFrame with imputed values.
        """
        return self.fit(df).transform(df)

    def validate_data(self, df: pd.DataFrame) -> dict[str, any]:
        """Validate data quality and return statistics.

        Args:
            df: DataFrame to validate.

        Returns:
            Dictionary with validation statistics.
        """
        stats = {
            "total_rows": len(df),
            "missing_by_pollutant": {},
            "outliers_by_pollutant": {},
        }

        for pollutant in POLLUTANTS:
            if pollutant in df.columns:
                # Missing values
                missing_count = df[pollutant].isna().sum()
                missing_pct = (missing_count / len(df)) * 100
                stats["missing_by_pollutant"][pollutant] = {
                    "count": int(missing_count),
                    "percentage": round(missing_pct, 2),
                }

                # Outliers (using IQR method)
                Q1 = df[pollutant].quantile(0.25)
                Q3 = df[pollutant].quantile(0.75)
                IQR = Q3 - Q1
                outliers = (
                    (df[pollutant] < (Q1 - 1.5 * IQR))
                    | (df[pollutant] > (Q3 + 1.5 * IQR))
                ).sum()
                stats["outliers_by_pollutant"][pollutant] = int(outliers)

        return stats
