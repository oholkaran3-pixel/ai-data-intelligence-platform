import duckdb
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, precision_score, recall_score, f1_score

class MachineLearningEngine:
    """
    Automated Machine Learning & Predictive Analytics Engine:
    Supports Regression, Classification, and Clustering on user-selected features and targets.
    """

    @staticmethod
    def train_regression(df: pd.DataFrame, target_col: str, feature_cols: List[str]) -> Dict[str, Any]:
        """Train and evaluate Linear and Random Forest regression models."""
        sub_df = df[feature_cols + [target_col]].dropna()
        if len(sub_df) < 10:
            raise ValueError("Insufficient rows (< 10) to train a regression model.")

        X = pd.get_dummies(sub_df[feature_cols], drop_first=True)
        y = sub_df[target_col]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Model 1: Linear Regression
        lr = LinearRegression()
        lr.fit(X_train, y_train)
        y_pred = lr.predict(X_test)

        r2 = round(float(r2_score(y_test, y_pred)), 3)
        mse = round(float(mean_squared_error(y_test, y_pred)), 3)
        rmse = round(float(np.sqrt(mse)), 3)

        # Feature Importance / Coefficients
        importance = {}
        for col, coef in zip(X.columns, lr.coef_):
            importance[col] = round(float(coef), 4)

        return {
            "task": "regression",
            "target": target_col,
            "algorithm": "Linear Regression (with Train/Test Split)",
            "metrics": {
                "r2_score": r2,
                "mean_squared_error": mse,
                "root_mean_squared_error": rmse
            },
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "feature_coefficients": importance,
            "insights": f"The model explains {max(0.0, r2 * 100):.1f}% of variance in '{target_col}'."
        }

    @staticmethod
    def train_classification(df: pd.DataFrame, target_col: str, feature_cols: List[str]) -> Dict[str, Any]:
        """Train and evaluate Classification models."""
        sub_df = df[feature_cols + [target_col]].dropna()
        if len(sub_df) < 10:
            raise ValueError("Insufficient rows (< 10) to train a classification model.")

        X = pd.get_dummies(sub_df[feature_cols], drop_first=True)
        y = sub_df[target_col].astype(str)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        clf = RandomForestClassifier(n_estimators=50, random_state=42)
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)

        acc = round(float(accuracy_score(y_test, y_pred)), 3)

        # Feature importances
        importance = {}
        for col, imp in zip(X.columns, clf.feature_importances_):
            importance[col] = round(float(imp), 4)

        return {
            "task": "classification",
            "target": target_col,
            "algorithm": "Random Forest Classifier",
            "metrics": {
                "accuracy": acc,
                "accuracy_percentage": f"{round(acc * 100, 1)}%"
            },
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "feature_importances": importance,
            "insights": f"Random Forest achieved an overall accuracy of {round(acc * 100, 1)}% on unseen test data."
        }

    @staticmethod
    def run_clustering(df: pd.DataFrame, feature_cols: List[str], n_clusters: int = 3) -> Dict[str, Any]:
        """Perform K-Means segmentation on numerical features."""
        sub_df = df[feature_cols].select_dtypes(include=[np.number]).dropna()
        if len(sub_df) < n_clusters * 2:
            raise ValueError(f"Insufficient data rows for {n_clusters} clusters.")

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
        clusters = kmeans.fit_predict(sub_df)
        
        counts = pd.Series(clusters).value_counts().to_dict()
        cluster_summary = []
        for i in range(n_clusters):
            center = {col: round(float(val), 2) for col, val in zip(sub_df.columns, kmeans.cluster_centers_[i])}
            cluster_summary.append({
                "cluster_id": i,
                "record_count": counts.get(i, 0),
                "centroid": center
            })

        return {
            "task": "clustering",
            "algorithm": f"K-Means Clustering (k={n_clusters})",
            "features_used": list(sub_df.columns),
            "clusters": cluster_summary,
            "inertia": round(float(kmeans.inertia_), 2),
            "insights": f"Segmented {len(sub_df)} records into {n_clusters} distinct behavioural cohorts."
        }
