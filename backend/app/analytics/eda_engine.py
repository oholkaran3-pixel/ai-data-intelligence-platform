import duckdb
import pandas as pd
import numpy as np
from typing import Dict, Any, List

class DuckDBAnalyticsEngine:
    """
    DuckDB SQL Analytics Engine:
    Executes high-performance SQL analytical queries directly on Parquet files,
    supporting aggregations, group-by, windowing, and safe read-only execution.
    """

    @staticmethod
    def execute_query(parquet_path: str, sql_query: str, limit: int = 100) -> Dict[str, Any]:
        """
        Safely execute a read-only query against the dataset Parquet file.
        The virtual table is accessible as 'data'.
        """
        # Security: Enforce read-only operations
        forbidden_keywords = ["drop", "delete", "insert", "update", "alter", "create", "truncate", "copy"]
        clean_sql = sql_query.strip().lower()
        
        for kw in forbidden_keywords:
            if kw in clean_sql.split():
                raise ValueError(f"Permission denied: Mutating statement '{kw}' is not permitted.")

        con = duckdb.connect(database=':memory:')
        try:
            # Register parquet file as view 'data'
            con.execute(f"CREATE VIEW data AS SELECT * FROM read_parquet('{parquet_path}')")
            
            # Execute user/agent query
            res = con.execute(sql_query).df()
            
            total_records = len(res)
            limited_res = res.head(limit)
            
            # Replace NaNs for JSON safety
            clean_records = limited_res.replace({np.nan: None, np.inf: None, -np.inf: None}).to_dict(orient="records")
            
            return {
                "success": True,
                "total_rows": total_records,
                "columns": list(res.columns),
                "data": clean_records
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            con.close()

    @staticmethod
    def generate_eda_report(parquet_path: str) -> Dict[str, Any]:
        """Generate comprehensive exploratory data analysis with distributions and correlations."""
        con = duckdb.connect(database=':memory:')
        try:
            df = con.execute(f"SELECT * FROM read_parquet('{parquet_path}')").df()
            
            # Numeric descriptive statistics
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            desc_stats = {}
            if numeric_cols:
                desc = df[numeric_cols].describe().to_dict()
                desc_stats = {k: {stat: round(val, 2) if isinstance(val, (int, float)) else val for stat, val in v.items()} for k, v in desc.items()}

            # Correlation matrix for numerical fields
            correlation_matrix = {}
            if len(numeric_cols) >= 2:
                corr = df[numeric_cols].corr().fillna(0).round(2).to_dict()
                correlation_matrix = corr

            # Categorical frequency distributions (top 5 values per category)
            cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            categorical_breakdown = {}
            for col in cat_cols[:10]: # limit to first 10 for performance
                top_counts = df[col].value_counts().head(5).to_dict()
                categorical_breakdown[col] = top_counts

            return {
                "row_count": len(df),
                "column_count": len(df.columns),
                "numeric_columns": numeric_cols,
                "categorical_columns": cat_cols,
                "descriptive_statistics": desc_stats,
                "correlation_matrix": correlation_matrix,
                "categorical_breakdown": categorical_breakdown
            }
        finally:
            con.close()
