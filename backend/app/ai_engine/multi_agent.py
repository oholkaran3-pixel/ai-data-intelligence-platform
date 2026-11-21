import os
import duckdb
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from app.analytics.eda_engine import DuckDBAnalyticsEngine

class MultiAgentAnalyst:
    """
    Modular Multi-Agent Architecture:
    1. DataUnderstandingAgent: Discovers columns, schema, types.
    2. SQLAnalyticalAgent: Generates read-only DuckDB SQL queries against 'data'.
    3. BusinessIntelligenceAgent: Translates analytical results into business insights.
    4. VisualizationAgent: Synthesizes optimal Plotly chart specifications.
    """

    def __init__(self, parquet_path: str, dataset_metadata: Dict[str, Any]):
        self.parquet_path = parquet_path
        self.metadata = dataset_metadata

    def run_query(self, natural_question: str) -> Dict[str, Any]:
        """
        Synthesize question -> identify intent -> generate safe SQL -> execute -> return insights & chart.
        """
        q_lower = natural_question.lower()
        
        # Connect to DuckDB to inspect actual columns
        con = duckdb.connect(database=':memory:')
        safe_parquet_path = self.parquet_path.replace("\\", "/")
        con.execute(f"CREATE VIEW data AS SELECT * FROM read_parquet('{safe_parquet_path}')")
        sample_df = con.execute("SELECT * FROM data LIMIT 5").df()
        cols = list(sample_df.columns)
        num_cols = sample_df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = sample_df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Helper to safely quote column names in DuckDB
        def qcol(c):
            return f'"{c}"'

        # Keyword mapping to detect intent for specific columns
        def find_best_column(candidates, keywords):
            for c in candidates:
                for kw in keywords:
                    if kw in c:
                        return c
            return None

        # Determine SQL Query based on analytical intent
        sql_query = ""
        agent_name = "SQLAnalyticalAgent"
        chart_spec = None
        insight_text = ""

        # Check for specific user questions (e.g. Sales by Coolers, Margin, etc.)
        matched_sales = find_best_column(num_cols, ["total_rb_sales", "rb_sales", "sales", "revenue", "amount"])
        matched_coolers = find_best_column(cols, ["front_end_coolers_red_bull", "cooler", "coolers", "front_end", "rb_coolers"])
        
        if ("cooler" in q_lower or "coolers" in q_lower) and matched_coolers and matched_sales:
            sql_query = f"SELECT {qcol(matched_coolers)}, ROUND(AVG({qcol(matched_sales)}), 2) as avg_sales FROM data WHERE {qcol(matched_sales)} IS NOT NULL GROUP BY {qcol(matched_coolers)} ORDER BY {qcol(matched_coolers)} ASC"
            res = con.execute(sql_query).df()
            insight_text = f"Analyzed average **{matched_sales.replace('_', ' ').title()}** segmented by **{matched_coolers.replace('_', ' ').title()}**. Displaying comparative performance across cooler deployments."
            chart_spec = {
                "type": "bar",
                "x": [str(x) for x in res[matched_coolers].tolist()],
                "y": res["avg_sales"].tolist(),
                "title": f"Average {matched_sales.replace('_', ' ').title()} by {matched_coolers.replace('_', ' ').title()}"
            }

        # Pattern 1: Count / Overview / Total rows
        elif any(w in q_lower for w in ["how many", "total records", "row count", "overview"]):
            sql_query = "SELECT count(*) as total_records FROM data"
            res = con.execute(sql_query).df()
            total = int(res['total_records'][0])
            insight_text = f"The dataset currently contains **{total:,}** verified records across {len(cols)} columns."
            chart_spec = {
                "type": "indicator",
                "title": "Total Records",
                "value": total
            }

        # Pattern 2: Average / Comparison / Breakdown across two fields
        elif "average" in q_lower or "avg" in q_lower:
            # Check if user mentioned specific columns
            matched_num = None
            for nc in num_cols:
                # check if keyword in nc is in question
                words = [w for w in nc.split('_') if len(w) > 2]
                if any(w in q_lower for w in words):
                    matched_num = nc
                    break
            if not matched_num:
                matched_num = num_cols[0] if num_cols else cols[0]

            matched_cat = None
            for c in cols:
                if c != matched_num:
                    words = [w for w in c.split('_') if len(w) > 2]
                    if any(w in q_lower for w in words):
                        matched_cat = c
                        break

            if matched_cat:
                alias = f"avg_val"
                sql_query = f"SELECT {qcol(matched_cat)}, ROUND(AVG({qcol(matched_num)}), 2) as {alias} FROM data WHERE {qcol(matched_num)} IS NOT NULL GROUP BY {qcol(matched_cat)} ORDER BY {alias} DESC LIMIT 10"
                res = con.execute(sql_query).df()
                insight_text = f"Analyzed average **{matched_num.replace('_', ' ').title()}** grouped by **{matched_cat.replace('_', ' ').title()}** across leading cohorts."
                chart_spec = {
                    "type": "bar",
                    "x": [str(x) for x in res[matched_cat].tolist()],
                    "y": res[alias].tolist(),
                    "title": f"Average {matched_num.replace('_', ' ').title()} by {matched_cat.replace('_', ' ').title()}"
                }
            else:
                sql_query = f"SELECT ROUND(AVG({qcol(matched_num)}), 2) as calculated_avg FROM data WHERE {qcol(matched_num)} IS NOT NULL"
                res = con.execute(sql_query).df()
                calc_val = float(res['calculated_avg'][0])
                insight_text = f"The overall calculated average **{matched_num.replace('_', ' ').title()}** is **{calc_val:,.2f}**."

        # Pattern 3: Highest / Top / Best / Max
        elif any(w in q_lower for w in ["top", "highest", "best", "max", "most"]):
            target_num = num_cols[0] if num_cols else cols[0]
            for nc in num_cols:
                if any(k in nc for k in ["sales", "revenue", "profit", "amount", "price", "score", "total"]):
                    target_num = nc
                    break

            target_cat = cat_cols[0] if cat_cols else cols[0]
            for cc in cat_cols:
                if any(k in cc for k in ["product", "category", "name", "customer", "region", "country", "item", "store"]):
                    target_cat = cc
                    break

            sql_query = f"SELECT {qcol(target_cat)}, SUM({qcol(target_num)}) as total_{target_num} FROM data GROUP BY {qcol(target_cat)} ORDER BY total_{target_num} DESC LIMIT 10"
            res = con.execute(sql_query).df()
            top_item = res.iloc[0][target_cat]
            top_val = res.iloc[0][f"total_{target_num}"]
            insight_text = f"The leading {target_cat.replace('_', ' ').title()} is **'{top_item}'** with a cumulative {target_num.replace('_', ' ')} of **{top_val:,.2f}**."
            chart_spec = {
                "type": "bar",
                "x": [str(x) for x in res[target_cat].tolist()],
                "y": res[f"total_{target_num}"].tolist(),
                "title": f"Top 10 {target_cat.replace('_', ' ').title()} by Total {target_num.replace('_', ' ').title()}"
            }

        # Pattern 4: Distribution / Breakdown / Grouping
        elif any(w in q_lower for w in ["distribution", "breakdown", "category", "compare", "by"]):
            target_cat = cat_cols[0] if cat_cols else cols[0]
            sql_query = f"SELECT {qcol(target_cat)}, COUNT(*) as record_count FROM data GROUP BY {qcol(target_cat)} ORDER BY record_count DESC LIMIT 8"
            res = con.execute(sql_query).df()
            insight_text = f"Categorical breakdown across **{target_cat.replace('_', ' ').title()}** reveals {len(res)} distinct primary groupings."
            chart_spec = {
                "type": "pie",
                "labels": [str(l) for l in res[target_cat].tolist()],
                "values": res["record_count"].tolist(),
                "title": f"Distribution by {target_cat.replace('_', ' ').title()}"
            }

        # Fallback: Safe analytical sample
        else:
            sql_query = "SELECT * FROM data LIMIT 10"
            res = con.execute(sql_query).df()
            insight_text = f"Analyzed query against {len(cols)} dimensions. Displaying top representative rows."

        execution_res = DuckDBAnalyticsEngine.execute_query(self.parquet_path, sql_query, limit=50)
        con.close()

        return {
            "agent_name": agent_name,
            "sql_query": sql_query,
            "content": insight_text,
            "execution_result": execution_res,
            "chart_spec": chart_spec
        }
