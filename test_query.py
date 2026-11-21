import sys, os
sys.path.insert(0, r'C:\Users\Karan Ohol\.gemini\antigravity\scratch\ai-data-intelligence\backend')
from app.ai_engine.multi_agent import MultiAgentAnalyst
import duckdb

parquet_path = r'C:/Users/Karan Ohol/.gemini/antigravity/scratch/ai-data-intelligence/backend/storage/parquet/6bc626e7638448428aeae204b4e57f51.parquet'
con = duckdb.connect()
df = con.execute(f"SELECT * FROM read_parquet('{parquet_path}') LIMIT 5").df()
print('Parquet columns:', df.columns.tolist())
con.close()

analyst = MultiAgentAnalyst(parquet_path, {})
q = '1. Average total Red Bull Sales by number of Red Bull Coolers'
try:
    res = analyst.run_query(q)
    print('Result content:', res['content'])
    print('Generated SQL:', res['sql_query'])
except Exception as e:
    import traceback
    traceback.print_exc()
