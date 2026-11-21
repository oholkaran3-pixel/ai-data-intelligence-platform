import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

class DataCleaner:
    """
    Automated Data Cleaning Engine:
    Executes governed, non-destructive transformations, preserving data lineage.
    """

    @staticmethod
    def drop_duplicates(df: pd.DataFrame, subset=None) -> Tuple[pd.DataFrame, int, str]:
        initial_count = len(df)
        cleaned_df = df.drop_duplicates(subset=subset, keep="first")
        affected = initial_count - len(cleaned_df)
        reason = f"Removed {affected} duplicate rows (kept first occurrence)."
        return cleaned_df, affected, reason

    @staticmethod
    def impute_missing(df: pd.DataFrame, column: str, strategy: str = "mean", fill_value: Any = None) -> Tuple[pd.DataFrame, int, str]:
        if column not in df.columns:
            return df, 0, f"Column '{column}' not found."
            
        cleaned_df = df.copy()
        affected = int(cleaned_df[column].isnull().sum())
        if affected == 0:
            return df, 0, f"No missing values in '{column}'."

        if strategy == "mean" and pd.api.types.is_numeric_dtype(cleaned_df[column]):
            val = cleaned_df[column].mean()
            cleaned_df[column] = cleaned_df[column].fillna(val)
            reason = f"Imputed {affected} missing values in '{column}' with mean ({round(val, 2)})."
        elif strategy == "median" and pd.api.types.is_numeric_dtype(cleaned_df[column]):
            val = cleaned_df[column].median()
            cleaned_df[column] = cleaned_df[column].fillna(val)
            reason = f"Imputed {affected} missing values in '{column}' with median ({round(val, 2)})."
        elif strategy == "mode":
            mode_val = cleaned_df[column].mode()
            val = mode_val[0] if len(mode_val) > 0 else "Unknown"
            cleaned_df[column] = cleaned_df[column].fillna(val)
            reason = f"Imputed {affected} missing values in '{column}' with mode ('{val}')."
        elif strategy == "drop":
            cleaned_df = cleaned_df.dropna(subset=[column])
            reason = f"Dropped {affected} rows with missing values in '{column}'."
        elif strategy == "constant":
            val = fill_value if fill_value is not None else "N/A"
            cleaned_df[column] = cleaned_df[column].fillna(val)
            reason = f"Filled {affected} missing values in '{column}' with '{val}'."
        else:
            cleaned_df[column] = cleaned_df[column].fillna("Missing")
            reason = f"Marked {affected} missing values in '{column}' as 'Missing'."

        return cleaned_df, affected, reason

    @staticmethod
    def type_cast(df: pd.DataFrame, column: str, target_type: str) -> Tuple[pd.DataFrame, int, str]:
        if column not in df.columns:
            return df, 0, f"Column '{column}' not found."
            
        cleaned_df = df.copy()
        affected = len(cleaned_df)
        
        try:
            if target_type == "numeric":
                cleaned_df[column] = pd.to_numeric(cleaned_df[column], errors='coerce')
                reason = f"Converted '{column}' to numeric format."
            elif target_type == "datetime":
                cleaned_df[column] = pd.to_datetime(cleaned_df[column], errors='coerce')
                reason = f"Parsed '{column}' as ISO datetime."
            elif target_type == "string":
                cleaned_df[column] = cleaned_df[column].astype(str)
                reason = f"Cast '{column}' to string."
            elif target_type == "integer":
                cleaned_df[column] = pd.to_numeric(cleaned_df[column], errors='coerce').fillna(0).astype(int)
                reason = f"Cast '{column}' to integer."
            else:
                return df, 0, f"Unsupported target type '{target_type}'."
        except Exception as e:
            return df, 0, f"Failed type casting: {str(e)}"

        return cleaned_df, affected, reason

    @staticmethod
    def standardize_text(df: pd.DataFrame, column: str, case: str = "title") -> Tuple[pd.DataFrame, int, str]:
        if column not in df.columns:
            return df, 0, f"Column '{column}' not found."
            
        cleaned_df = df.copy()
        cleaned_df[column] = cleaned_df[column].astype(str).str.strip()
        
        if case == "lower":
            cleaned_df[column] = cleaned_df[column].str.lower()
        elif case == "upper":
            cleaned_df[column] = cleaned_df[column].str.upper()
        elif case == "title":
            cleaned_df[column] = cleaned_df[column].str.title()
            
        reason = f"Standardized text casing and stripped whitespace in '{column}'."
        return cleaned_df, len(cleaned_df), reason

    @staticmethod
    def handle_outliers_iqr(df: pd.DataFrame, column: str, method: str = "cap") -> Tuple[pd.DataFrame, int, str]:
        if column not in df.columns or not np.issubdtype(df[column].dtype, np.number):
            return df, 0, f"Column '{column}' is not numeric."
            
        cleaned_df = df.copy()
        q25 = cleaned_df[column].quantile(0.25)
        q75 = cleaned_df[column].quantile(0.75)
        iqr = q75 - q25
        lower = q25 - 1.5 * iqr
        upper = q75 + 1.5 * iqr
        
        outliers_mask = (cleaned_df[column] < lower) | (cleaned_df[column] > upper)
        affected = int(outliers_mask.sum())
        
        if affected == 0:
            return df, 0, f"No IQR outliers detected in '{column}'."
            
        if method == "cap":
            cleaned_df[column] = cleaned_df[column].clip(lower=lower, upper=upper)
            reason = f"Capped {affected} outliers in '{column}' to [{round(lower, 2)}, {round(upper, 2)}]."
        elif method == "drop":
            cleaned_df = cleaned_df[~outliers_mask]
            reason = f"Removed {affected} outlier rows from '{column}'."
        else:
            return df, 0, "Unknown outlier method."
            
        return cleaned_df, affected, reason
