import sqlite3
import pytest
import numpy as np
from Pyfhel import Pyfhel, PyCtxt
import os
from pathlib import Path

def homomorphic_sum_py(he: Pyfhel, *ciphertexts: bytes) -> bytes:
    """
    Sums multiple encrypted ciphertexts using Pyfhel and returns the aggregated ciphertext.
    
    Parameters:
        he (Pyfhel): An initialized Pyfhel object with loaded context and keys.
        *ciphertexts (bytes): Variable number of ciphertexts in bytes format.
    
    Returns:
        bytes: The aggregated ciphertext as bytes.
    """
    if not ciphertexts:
        return None

    # Initialize the total ciphertext with the first ciphertext
    total_ctxt = PyCtxt(pyfhel=he, bytestring=ciphertexts[0])

    # Add the remaining ciphertexts
    for ct in ciphertexts[1:]:
        ctxt = PyCtxt(pyfhel=he, bytestring=ct)
        total_ctxt += ctxt  # Homomorphic addition

    return total_ctxt.to_bytes()

class HomomorphicSumAggregate:
    def __init__(self):
        self.he = Pyfhel()
        current_dir = Path(__file__).parent
        context_path = current_dir / "context.ckks"
        public_key_path = current_dir / "public_key.pk"
        
        # Load context and public key
        if not context_path.exists():
            raise FileNotFoundError(f"Context file not found at {context_path}")
        if not public_key_path.exists():
            raise FileNotFoundError(f"Public key file not found at {public_key_path}")
        
        self.he.load_context(str(context_path))
        self.he.load_public_key(str(public_key_path))
        self.total_ctxt = None
        print("HomomorphicSumAggregate initialized with context and public key.")

    def step(self, value):
        if value is None:
            print("HomomorphicSumAggregate: Received None value.")
            return
        if self.total_ctxt is None:
            self.total_ctxt = PyCtxt(pyfhel=self.he, bytestring=value)
            print("HomomorphicSumAggregate: Initialized total_ctxt with first ciphertext.")
        else:
            ctxt = PyCtxt(pyfhel=self.he, bytestring=value)
            self.total_ctxt += ctxt
            print("HomomorphicSumAggregate: Added ciphertext to total_ctxt.")

    def finalize(self):
        if self.total_ctxt is None:
            print("HomomorphicSumAggregate: No ciphertexts were aggregated.")
            return None
        print("HomomorphicSumAggregate: Finalizing aggregated ciphertext.")
        return self.total_ctxt.to_bytes()

# Pyfhel fixture
@pytest.fixture(scope='module')
def he():
    he_instance = Pyfhel()
    qi_sizes = [60, 30, 30, 30, 30, 30, 60]
    he_instance.contextGen(scheme='CKKS', n=2**14, scale=2**30, qi_sizes=qi_sizes)
    he_instance.keyGen()
    # Save context and keys in the current directory
    he_instance.save_context("context.ckks")
    he_instance.save_public_key("public_key.pk")
    he_instance.save_secret_key("secret_key.sk")
    print("Pyfhel instance initialized and context/keys saved.")
    return he_instance

# Setup database fixture
@pytest.fixture(scope='module')
def setup_database(he):
    conn = sqlite3.connect(':memory:')

    # Register homomorphic_sum as an aggregate function
    conn.create_aggregate("homomorphic_sum", 1, HomomorphicSumAggregate)
    print("homomorphic_sum aggregate function registered in SQLite.")
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE housing_encrypted (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            MedInc_enc BLOB,
            HouseAge_enc BLOB,
            AveRooms_enc BLOB,
            MedInc REAL
        )
    ''')
    print("Table housing_encrypted created.")

    SCALE = 2 ** 30  # Ensure this matches the scale in contextGen

    data = []
    for i in range(1, 4):
        # Prepare plaintext as NumPy array
        medinc_plain = float(i)
        medinc_array = np.array([medinc_plain], dtype=np.float64)
        ptxt_medinc = he.encodeFrac(medinc_array)
        medinc_enc = he.encryptPtxt(ptxt_medinc).to_bytes()

        houseage_plain = float(i + 1)
        houseage_array = np.array([houseage_plain], dtype=np.float64)
        ptxt_houseage = he.encodeFrac(houseage_array)
        houseage_enc = he.encryptPtxt(ptxt_houseage).to_bytes()

        averooms_plain = float(i + 2)
        averooms_array = np.array([averooms_plain], dtype=np.float64)
        ptxt_averooms = he.encodeFrac(averooms_array)
        averooms_enc = he.encryptPtxt(ptxt_averooms).to_bytes()

        data.append((medinc_enc, houseage_enc, averooms_enc, medinc_plain))

    cursor.executemany('''
        INSERT INTO housing_encrypted (MedInc_enc, HouseAge_enc, AveRooms_enc, MedInc)
        VALUES (?, ?, ?, ?)
    ''', data)

    print("\nOriginal data inserted into the database (before encryption):")
    for i in range(1, 4):
        print(f"Row {i}: MedInc = {i}, HouseAge = {i + 1}, AveRooms = {i + 2}")

    conn.commit()
    yield conn
    conn.close()
    print("In-memory SQLite database closed.")

def test_homomorphic_sum(setup_database, he):
    conn = setup_database
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT MedInc_enc, MedInc FROM housing_encrypted')
        rows = cursor.fetchall()
        print("\nVerifying individual ciphertexts:")
        for row in rows:
            enc, plain = row
            ctxt = PyCtxt(pyfhel=he, bytestring=enc)
            decrypted_ptxt = he.decryptFrac(ctxt)
            decrypted_val = decrypted_ptxt[0]
            print(f"Decrypted MedInc_enc: {decrypted_val} (expected: {plain})")
            np.testing.assert_almost_equal(decrypted_val, plain, decimal=1)

        cursor.execute('SELECT homomorphic_sum(MedInc_enc) FROM housing_encrypted')
        result = cursor.fetchone()[0]

        if result is None:
            raise ValueError("Query returned None.")

        # Decrypt the aggregated sum
        ctxt_result = PyCtxt(pyfhel=he, bytestring=result)
        decrypted_ptxt = he.decryptFrac(ctxt_result)
        decrypted_sum = decrypted_ptxt[0]  

        expected_sum = 6.0

        print(f"\nExpected sum: {expected_sum}")
        print(f"Decrypted result sum: {decrypted_sum}")

        # Validate that the decrypted result matches the expected sum
        np.testing.assert_almost_equal(decrypted_sum, expected_sum, decimal=1)

        
        cursor.execute('SELECT SUM(MedInc) FROM housing_encrypted')
        sqlite_sum = cursor.fetchone()[0]
        print(f"SQLite SUM result: {sqlite_sum}")

    except Exception as e:
        print(f"\nError during test_homomorphic_sum: {e}")
        raise  # Re-raise the exception to allow pytest to capture the traceback

if __name__ == "__main__":
    pytest.main()

