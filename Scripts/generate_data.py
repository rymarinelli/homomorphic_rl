from encryption import HE  
import sqlite3
import logging
import sys
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('generate_data.log')
    ]
)
logger = logging.getLogger(__name__)

def create_encrypted_db_with_dummy_data():
    he_instance = HE()
    current_dir = Path(__file__).parent
    context_path = current_dir / "context.ckks"
    public_key_path = current_dir / "public_key.pk"
    secret_key_path = current_dir / "secret_key.sk"

    he_instance.load_context(str(context_path))
    he_instance.load_public_key(str(public_key_path))
    he_instance.load_secret_key(str(secret_key_path))  # Ensure this file exists

    
    db_path = 'california_housing.db'
    try:
        conn = sqlite3.connect(db_path)
        logger.info(f"Connected to SQLite database '{db_path}'.")
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to the database: {e}")
        sys.exit(1)

    cursor = conn.cursor()

    
    try:
        cursor.execute("DROP TABLE IF EXISTS housing_encrypted;")
        logger.info("Dropped existing 'housing_encrypted' table if it existed.")

        cursor.execute("""
            CREATE TABLE housing_encrypted (
                MedInc_enc BLOB,
                HouseAge_enc BLOB,
                Population_enc BLOB,
                AveRooms_enc BLOB,
                AveOccup_enc BLOB,
                Longitude_enc BLOB,
                Latitude_enc BLOB,
                MedHouseVal_enc BLOB,
                AveBedrms_enc BLOB
            );
        """)
        logger.info("'housing_encrypted' table created successfully.")
    except sqlite3.Error as e:
        logger.error(f"Failed to create 'housing_encrypted' table: {e}")
        sys.exit(1)

    # Sample data to insert
    sample_data = [
        (8.3252, 41, 880, 6.9841, 1.0238, -122.23, 37.88, 452600, 2.555),
        (8.3014, 21, 1262, 6.2381, 0.9719, -122.22, 37.86, 358500, 2.109),
        
    ]

    
    for idx, row in enumerate(sample_data, start=1):
        encrypted_row = []
        for value in row:
            encrypted_bytes = he_instance.encrypt_value(value)
            encrypted_row.append(encrypted_bytes)
        try:
            cursor.execute("""
                INSERT INTO housing_encrypted (
                    MedInc_enc,
                    HouseAge_enc,
                    Population_enc,
                    AveRooms_enc,
                    AveOccup_enc,
                    Longitude_enc,
                    Latitude_enc,
                    MedHouseVal_enc,
                    AveBedrms_enc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, encrypted_row)
            logger.info(f"Inserted encrypted row {idx} into 'housing_encrypted' table.")
        except sqlite3.Error as e:
            logger.error(f"Failed to insert encrypted row {idx}: {e}")
            continue

    conn.commit()
    logger.info("All sample data encrypted and inserted successfully.")
    conn.close()
    logger.info(f"Database connection to '{db_path}' closed.")

if __name__ == "__main__":
    create_encrypted_db_with_dummy_data()

