import sqlite3
import pytest
import numpy as np
from Pyfhel import Pyfhel, PyCtxt

# Define the aggregate class
class HomomorphicSumAggregate:
    def __init__(self):
        self.he = Pyfhel()
        self.he.load_context("context.ckks")
        self.he.load_public_key("public_key.pk")
        self.total_ctxt = None

    def step(self, value):
        if value is None:
            return
        if self.total_ctxt is None:
            self.total_ctxt = PyCtxt(pyfhel=self.he, bytestring=value)
        else:
            ctxt = PyCtxt(pyfhel=self.he, bytestring=value)
            self.total_ctxt += ctxt  # Homomorphic addition

    def finalize(self):
        if self.total_ctxt is None:
            return None
        return self.total_ctxt.to_bytes()

def homomorphic_sum(*values):
    if not values:
        return None

    he = Pyfhel()
    he.load_context("context.ckks")
    he.load_public_key("public_key.pk")

    # Initialize total_ctxt with the first ciphertext
    first_value = values[0].tobytes() if isinstance(values[0], memoryview) else values[0]
    total_ctxt = PyCtxt(pyfhel=he, bytestring=first_value)

    # Sum the remaining ciphertexts
    for value in values[1:]:
        value_bytes = value.tobytes() if isinstance(value, memoryview) else value
        ctxt = PyCtxt(pyfhel=he, bytestring=value_bytes)
        total_ctxt += ctxt  # Homomorphic addition

    return total_ctxt.to_bytes()

@pytest.fixture(scope='module')
def he():
    he_instance = Pyfhel()
    qi_sizes = [60, 30, 30, 30, 30, 30, 60]
    he_instance.contextGen(scheme='CKKS', n=2**14, scale=2**30, qi_sizes=qi_sizes)
    he_instance.keyGen()
    # Correct method names with underscores
    he_instance.save_context("context.ckks")
    he_instance.save_public_key("public_key.pk")
    he_instance.save_secret_key("secret_key.sk")
    return he_instance

@pytest.fixture(scope='module')
def setup_database(he):
    conn = sqlite3.connect(':memory:')

    # Register homomorphic_sum as an aggregate function
    conn.create_aggregate("homomorphic_sum", 1, HomomorphicSumAggregate)
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

def test_homomorphic_sum(setup_database, he):
    conn = setup_database
    cursor = conn.cursor()

    try:
        # Step 1: Verify individual ciphertexts
        cursor.execute('SELECT MedInc_enc, MedInc FROM housing_encrypted')
        rows = cursor.fetchall()
        for row in rows:
            enc, plain = row
            ctxt = PyCtxt(pyfhel=he, bytestring=enc)
            decrypted_ptxt = he.decryptFrac(ctxt)
            decrypted_val = decrypted_ptxt[0]
            print(f"Decrypted MedInc_enc: {decrypted_val} (expected: {plain})")
            np.testing.assert_almost_equal(decrypted_val, plain, decimal=1)

        # Step 2: Perform homomorphic sum
        cursor.execute('SELECT homomorphic_sum(MedInc_enc) FROM housing_encrypted')
        result = cursor.fetchone()[0]

        if result is None:
            raise ValueError("Query returned None.")

        # Decrypt the aggregated sum
        ctxt_result = PyCtxt(pyfhel=he, bytestring=result)
        decrypted_ptxt = he.decryptFrac(ctxt_result)
        decrypted_sum = decrypted_ptxt[0]  # Access the first element

        expected_sum = 6.0

        print(f"\nExpected sum: {expected_sum}")
        print(f"Decrypted result sum: {decrypted_sum}")

        # Validate that the decrypted result matches the expected sum
        np.testing.assert_almost_equal(decrypted_sum, expected_sum, decimal=1)

        # Optional: Compare with SQLite's SUM
        cursor.execute('SELECT SUM(MedInc) FROM housing_encrypted')
        sqlite_sum = cursor.fetchone()[0]
        print(f"SQLite SUM result: {sqlite_sum}")

    except Exception as e:
        print(f"\nError during test_homomorphic_sum: {e}")
        raise  # Re-raise the exception to allow pytest to capture the traceback

if __name__ == "__main__":
    pytest.main()

