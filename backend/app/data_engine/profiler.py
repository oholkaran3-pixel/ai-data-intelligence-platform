import os
import io
import pandas as pd
import numpy as np
import duckdb
from typing import Dict, Any, List, Tuple
from fastapi import UploadFile, HTTPException

def _detect_and_clean_header(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Auto-detect real table headers if the file has leading title or instructional rows."""
    if len(df_raw) == 0:
        return df_raw
    
    # Check if first row is already mostly valid names
    named_cols = [c for c in df_raw.columns if not str(c).startswith("Unnamed:")]
    if len(named_cols) >= max(2, len(df_raw.columns) * 0.5):
        return df_raw

    # Scan the first 15 rows for the best candidate header row
    best_row_idx = None
    max_text_cells = 0
    for idx in range(min(15, len(df_raw))):
        row = df_raw.iloc[idx]
        non_null_texts = [val for val in row if pd.notnull(val) and isinstance(val, str) and len(val.strip()) > 0]
        if len(non_null_texts) > max_text_cells:
            max_text_cells = len(non_null_texts)
            best_row_idx = idx

    if best_row_idx is not None and max_text_cells >= 2:
        new_headers = df_raw.iloc[best_row_idx].fillna("col").astype(str).tolist()
        df_cleaned = df_raw.iloc[best_row_idx + 1:].copy().reset_index(drop=True)
        # Deduplicate & sanitize column headers
        seen = {}
        clean_headers = []
        for h in new_headers:
            name = h.strip()
            if not name or name.lower() == "nan":
                name = "col"
            if name in seen:
                seen[name] += 1
                clean_headers.append(f"{name}_{seen[name]}")
            else:
                seen[name] = 0
                clean_headers.append(name)
        df_cleaned.columns = clean_headers
        # Drop rows that are completely empty
        df_cleaned = df_cleaned.dropna(how='all').reset_index(drop=True)
        return df_cleaned

    return df_raw

def inspect_and_read_file(file_path: str, file_ext: str) -> pd.DataFrame:
    """Read multiple file types safely into Pandas dataframe with intelligent multi-sheet and header detection."""
    ext = file_ext.lower().replace(".", "")
    try:
        if ext == "csv":
            try:
                df = pd.read_csv(file_path, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding="latin1")
            return _detect_and_clean_header(df)
            
        elif ext in ["xlsx", "xls"]:
            xl = pd.ExcelFile(file_path)
            # Find the best sheet with the most tabular data
            best_sheet = xl.sheet_names[0]
            max_records = -1
            for sheet_name in xl.sheet_names:
                candidate_df = xl.parse(sheet_name)
                valid_cells = int(candidate_df.notnull().sum().sum())
                # Prioritize 'raw data' or sheets with higher data density
                bonus = 1000 if 'raw' in sheet_name.lower() or 'data' in sheet_name.lower() else 0
                score = valid_cells + bonus
                if score > max_records:
                    max_records = score
                    best_sheet = sheet_name

            df = xl.parse(best_sheet)
            return _detect_and_clean_header(df)

        elif ext == "json":
            return pd.read_json(file_path)
        elif ext == "parquet":
            return pd.read_parquet(file_path)
        elif ext == "txt":
            try:
                df = pd.read_csv(file_path, sep=None, engine='python')
                return _detect_and_clean_header(df)
            except Exception:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = [line.strip() for line in f.readlines()]
                return pd.DataFrame({"text_content": lines})
        else:
            raise ValueError(f"Unsupported file format: .{ext}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

def profile_dataset(df: pd.DataFrame) -> Tuple[float, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Automated Data Profiling Engine:
    Calculates transparent Data Quality Score (0-100), statistical summary,
    and column schema metrics.
    """
    row_count, col_count = df.shape
    if row_count == 0:
        return 0.0, {"error": "Empty dataset"}, []

    # 1. Missing Values & Duplicate Records
    total_cells = row_count * col_count
    missing_cells = int(df.isnull().sum().sum())
    missing_ratio = missing_cells / total_cells if total_cells > 0 else 0.0
    
    duplicate_rows = int(df.duplicated().sum())
    duplicate_ratio = duplicate_rows / row_count if row_count > 0 else 0.0

    # 2. Column Profiling
    columns_meta = []
    num_outliers_detected = 0
    inconsistent_cols = 0

    for col in df.columns:
        col_series = df[col]
        null_count = int(col_series.isnull().sum())
        null_pct = round((null_count / row_count) * 100, 2)
        unique_count = int(col_series.nunique(dropna=True))
        
        dtype_str = str(col_series.dtype)
        inferred_type = "string"
        stats = {}

        is_numeric = pd.api.types.is_numeric_dtype(col_series)
        is_datetime = pd.api.types.is_datetime64_any_dtype(col_series)

        if is_numeric:
            inferred_type = "numeric"
            non_null = col_series.dropna()
            if len(non_null) > 0:
                q25 = float(non_null.quantile(0.25))
                q75 = float(non_null.quantile(0.75))
                iqr = q75 - q25
                lower_bound = q25 - 1.5 * iqr
                upper_bound = q75 + 1.5 * iqr
                outliers = int(((non_null < lower_bound) | (non_null > upper_bound)).sum())
                num_outliers_detected += outliers
                
                stats = {
                    "mean": round(float(non_null.mean()), 2),
                    "std": round(float(non_null.std()) if len(non_null) > 1 else 0.0, 2),
                    "min": round(float(non_null.min()), 2),
                    "max": round(float(non_null.max()), 2),
                    "median": round(float(non_null.median()), 2),
                    "outliers_count": outliers
                }
        elif is_datetime:
            inferred_type = "datetime"
        else:
            # Check if it could be a date or categorical
            inferred_type = "categorical" if unique_count < (row_count * 0.2) else "text"
            sample_vals = col_series.dropna().head(5).astype(str).tolist()
            stats = {
                "top_values": col_series.value_counts().head(5).to_dict()
            }

        columns_meta.append({
            "name": str(col),
            "data_type": dtype_str,
            "inferred_type": inferred_type,
            "null_count": null_count,
            "null_percentage": null_pct,
            "unique_count": unique_count,
            "stats": stats
        })

    # 3. Transparent Data Quality Score Formula:
    # 100 - (Missing Penalty max 40) - (Duplicate Penalty max 30) - (Outlier Penalty max 30)
    missing_penalty = min(40.0, missing_ratio * 100.0 * 1.5)
    duplicate_penalty = min(30.0, duplicate_ratio * 100.0 * 2.0)
    outlier_ratio = num_outliers_detected / row_count if row_count > 0 else 0
    outlier_penalty = min(30.0, outlier_ratio * 10.0)
    
    quality_score = max(0.0, round(100.0 - missing_penalty - duplicate_penalty - outlier_penalty, 1))

    quality_summary = {
        "score": quality_score,
        "grade": "Excellent" if quality_score >= 85 else ("Good" if quality_score >= 70 else "Needs Attention"),
        "total_rows": row_count,
        "total_columns": col_count,
        "total_missing_cells": missing_cells,
        "missing_ratio_pct": round(missing_ratio * 100, 2),
        "duplicate_rows": duplicate_rows,
        "duplicate_ratio_pct": round(duplicate_ratio * 100, 2),
        "total_outliers_detected": num_outliers_detected,
        "score_breakdown": {
            "base_score": 100.0,
            "missing_penalty": round(missing_penalty, 1),
            "duplicate_penalty": round(duplicate_penalty, 1),
            "outlier_penalty": round(outlier_penalty, 1)
        }
    }

    return quality_score, quality_summary, columns_meta

def convert_to_parquet(df: pd.DataFrame, parquet_target_path: str) -> str:
    """Save dataframe as compressed parquet file with sanitized alphanumeric column names for DuckDB."""
    import re
    clean_cols = []
    seen = {}
    for c in df.columns:
        # replace non-alphanumeric with underscore and lowercase
        clean = re.sub(r'[^a-zA-Z0-9]+', '_', str(c)).strip('_').lower()
        if not clean:
            clean = "col"
        if clean in seen:
            seen[clean] += 1
            clean = f"{clean}_{seen[clean]}"
        else:
            seen[clean] = 0
        clean_cols.append(clean)

    df_copy = df.copy()
    df_copy.columns = clean_cols
    
    con = duckdb.connect(database=':memory:')
    try:
        con.register('df_source', df_copy)
        safe_path = parquet_target_path.replace("\\", "/")
        con.execute(f"COPY df_source TO '{safe_path}' (FORMAT PARQUET)")
    finally:
        con.close()
        
    return parquet_target_path
