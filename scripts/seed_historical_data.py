import pandas as pd
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

# Configuration
DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_j0M2OLgSsFRb@ep-proud-resonance-amtdhzcw-pooler.c-5.us-east-1.aws.neon.tech/neondb?ssl=require"
CSV_PATH = "Bangladesh-Crime-Dataset.csv"

TARGET_REGIONS = [
    "Adabar", "Aftabnagar", "Agargaon", "Airport", "Amin Bazar", "Anandabazar", "Aricha Highway",
    "Ashulia", "Azampur", "Azimpur", "Babubazar Bridge", "Badamtoli Ghat", "Badda", "Bailey Road",
    "Baitul Mukarram", "Banani", "Banasree", "Bandar", "Bangla Motor", "Bangladesh University Of Engineering And Technology",
    "Bangshal", "Baridhara", "Bashundhara Residential Area", "Bhasantek", "Bhatara", "Bheribandh",
    "Bijoy Sarani", "Bijoynagar", "Boroghortola", "Buriganga", "Cantonment", "Chankharpool",
    "Chawkbazar", "Companiganj", "Dakkhin Dania", "Dakkhinkhan", "Darus Salam", "Dayaganj",
    "Demra", "Dhaka", "Dhaka Commerce College", "Dhaka Medical College", "Dhaka University",
    "Dhakeshwari", "Dhalpur", "Dhamrai", "Dhanmondi", "Dholaikhal", "Dholaipar", "Dogair Noorbag",
    "Dohar", "Donia", "Eastern Plaza Market", "Eden Mohila College", "Elephant Road", "Eskaton",
    "Fakirapool", "Farmgate", "Fulbaria", "Gabtoli", "Gandaria", "Gausia", "Goran", "Green Road",
    "Gulistan", "Gulshan", "Hajipara", "Hatirjheel", "Hatirpool", "Hazaribagh",
    "Hazrat Shahjalal International Airport", "Hrishikesh Das Lane", "Ibrahimpur", "Ideal College",
    "Islambagh", "Jagannath University", "Jahangirnagar University", "Jamgora", "Jamtala",
    "Jatrabari", "Jigatola", "Jurain", "Kachukhet", "Kadamtali", "Kafrul", "Kakrail", "Kalabagan",
    "Kalachandpur", "Kalyanpur", "Kamalapur Railway Station", "Kamrangirchar", "Kaptan Bazar",
    "Karail", "Karwan Bazar", "Kathalbagan", "Keraniganj", "Khalek Market", "Khamarbari",
    "Khilgaon", "Khilkhet", "Kotwali", "Kuril", "Kurmitola", "Lalbagh", "Lalmatia", "Madhubagh",
    "Malibagh", "Manda", "Manik Mia Avenue", "Maniknagar", "Matikata", "Matuail", "Mirpur",
    "Moghbazar", "Mohakhali", "Mohammadpur", "Monipur", "Motijheel", "Mouchak", "Mugda",
    "Munda", "Munni Shoroni", "Muradpur", "Muslim Nagar", "Nababpur", "Nakhalpara", "Natunbazar",
    "Nawabganj", "New Eskaton", "New Market", "Niketan", "Nilkhet", "Old Dhaka", "Pallabi",
    "Paltan", "Panthapath", "Patuatuli", "Rajabazar", "Ramna", "Rampura", "Rayebazar", "Rayerbagh",
    "Rupnagar", "Sabujbagh", "Saidabad Bus Terminal", "Savar", "Sayedabad", "Segunbagicha",
    "Shah Ali", "Shahbagh", "Shaheed Suhrawardy Medical College Hospital", "Shahjahanpur",
    "Shanir Akhra", "Shankaribazar", "Shantibagh", "Shekhertek", "Sher-E-Bangla Nagar",
    "Shewrapara", "Shyamoli", "Shyampur", "Sir Salimullah Medical College", "Suhrawardy Udyan",
    "Sutrapur", "T And T Colony", "Taltola", "Tanti Bazar", "Tejgaon", "Tikatuli", "Topekhana Road",
    "Turag", "Uttara", "Uttarkhan", "Vatara", "Wari"
]

async def seed_dataset():
    print(f"Reading CSV: {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    
    # 1. Standardize and Filter
    df['incident_place_clean'] = df['incident_place'].str.strip().str.title()
    
    # Filter for Dhaka District + Target Regions
    mask = (df['incident_district'].str.contains('Dhaka', case=False, na=False)) & \
           (df['incident_place_clean'].isin(TARGET_REGIONS))
    
    filtered_df = df[mask].copy()
    print(f"Filtered {len(filtered_df)} rows matching the 182 target regions in Dhaka.")
    
    if len(filtered_df) == 0:
        print("No matching rows found. Exiting.")
        return

    # 2. Database Connection
    engine = create_async_engine(
        DATABASE_URL,
        connect_args={
            "statement_cache_size": 0,
            "command_timeout": 60
        }
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Clear existing historical data to avoid duplicates (optional but recommended for clean seed)
        print("Clearing public.dataset table...")
        await session.execute(text("TRUNCATE public.dataset RESTART IDENTITY;"))
        
        # Prepare for bulk insert
        # We only need the columns used by the repopulate_combined_table function
        # columns: incident_place, incident_district, crime, latitude, longitude
        print("Inserting data into public.dataset...")
        
        # Convert to list of dicts for SQLAlchemy core
        chunks = 1000
        total = len(filtered_df)
        
        for i in range(0, total, chunks):
            chunk_df = filtered_df.iloc[i : i + chunks]
            
            insert_data = [
                {
                    "incident_place": row["incident_place"],
                    "incident_district": row["incident_district"],
                    "crime": row["crime"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"]
                }
                for _, row in chunk_df.iterrows()
            ]
            
            await session.execute(
                text("""
                    INSERT INTO public.dataset (incident_place, incident_district, crime, latitude, longitude)
                    VALUES (:incident_place, :incident_district, :crime, :latitude, :longitude)
                """),
                insert_data
            )
            print(f"  -> Inserted {i + len(insert_data)} / {total}")
        
        await session.commit()
    
    print("✨ Seeding Complete!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_dataset())
