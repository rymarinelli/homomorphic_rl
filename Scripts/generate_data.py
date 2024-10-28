import sqlite3
import random
from Scripts.ckks import HE  # Import HE from your ckks script
from Scripts.encryption import encrypt_value  # Import your encrypt_value function
from Scripts.homomorphic_sum import homomorphic_sum  # Import your homomorphic_sum function

def create_encrypted_db_with_dummy_data(db_name='california_housing.db'):
    """Creates an SQLite database with encrypted dummy data for testing purposes."""
    
    # Drop the existing table if it exists and recreate with the correct schema
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        cursor.execute('DROP TABLE IF EXISTS housing_encrypted')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS housing_encrypted (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                MedInc_enc BLOB,
                HouseAge_enc BLOB,
                AveRooms_enc BLOB,
                AveBedrms_enc BLOB,
                Population_enc BLOB,
                AveOccup_enc BLOB,
                Latitude_enc BLOB,
                Longitude_enc BLOB,
                MedHouseVal_enc BLOB
            )
        ''')

        # Register the custom SQL function
        conn.create_function("homomorphic_sum", -1, homomorphic_sum)

        conn.commit()
        print("Table recreated with all necessary columns and functions registered.")

    # Insert dummy data with encryption for all columns
    data = [
        (
            encrypt_value(random.uniform(1.0, 10.0)),   # MedInc_enc
            encrypt_value(random.uniform(1.0, 100.0)),  # HouseAge_enc
            encrypt_value(random.uniform(1.0, 10.0)),   # AveRooms_enc
            encrypt_value(random.uniform(1.0, 5.0)),    # AveBedrms_enc
            encrypt_value(random.uniform(100.0, 2000.0)), # Population_enc
            encrypt_value(random.uniform(1.0, 10.0)),   # AveOccup_enc
            encrypt_value(random.uniform(32.0, 42.0)),  # Latitude_enc
            encrypt_value(random.uniform(-124.0, -114.0)), # Longitude_enc
            encrypt_value(random.uniform(100000.0, 500000.0)) # MedHouseVal_enc
        )
        for _ in range(10)
    ]

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT INTO housing_encrypted (
                MedInc_enc, HouseAge_enc, AveRooms_enc, AveBedrms_enc, Population_enc,
                AveOccup_enc, Latitude_enc, Longitude_enc, MedHouseVal_enc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)

        conn.commit()
        print("Data inserted into the newly created table.")

