import csv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import asyncio
import os

DATABASE_URL = os.getenv("DATABASE_URL")
CSV_PATH = "Bangladesh-Crime-Dataset.csv"

async def ingest_csv():
    if not os.path.exists(CSV_PATH):
        print(f"File {CSV_PATH} not found.")
        return

    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        with open(CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            records = []
            batch_size = 500
            count = 0
            
            for row in reader:
                # Map empty string key to 'index' if necessary
                if "" in row:
                    row["index"] = row.pop("")
                
                # Cleanup: Convert types and handle missing fields
                processed_row = {}
                for k, v in row.items():
                    key = "index" if k == "" else k
                    if v == "" or v is None:
                        processed_row[key] = None
                    else:
                        try:
                            if "." in v:
                                processed_row[key] = float(v)
                            else:
                                processed_row[key] = int(v)
                        except ValueError:
                            processed_row[key] = v
                
                records.append(processed_row)
                
                if len(records) >= batch_size:
                    cols = ", ".join(records[0].keys())
                    placeholders = ", ".join([f":{k}" for k in records[0].keys()])
                    query = text(f"INSERT INTO dataset ({cols}) VALUES ({placeholders})")
                    await conn.execute(query, records)
                    records = []
                    count += batch_size
                    print(f"Inserted {count} records...")

            if records:
                cols = ", ".join(records[0].keys())
                placeholders = ", ".join([f":{k}" for k in records[0].keys()])
                query = text(f"INSERT INTO dataset ({cols}) VALUES ({placeholders})")
                await conn.execute(query, records)
                count += len(records)
                print(f"Inserted final {len(records)} records. Total: {count}")

    await engine.dispose()
    print("Ingestion complete.")

if __name__ == "__main__":
    asyncio.run(ingest_csv())
