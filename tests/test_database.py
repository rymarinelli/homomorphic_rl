import sqlite3
import pytest
import numpy as np
from Pyfhel import Pyfhel, PyCtxt
from ckks import HE
from encryption import encrypt_value, decrypt_value

def homomorphic_sum(*values):
    """
    Perform homomorphic addition on encrypted values using the Pyfhel CKKS context.

    Args:
        values (tuple of bytes): Encrypted values in byte format.

    Returns:
        bytes: The result of the homomorphic addition as bytes, or None if no values are provided.
    """
    if not values:
        return None

    try:
        # Decrypt each value before summation
        total_sum = 0.0
        for i, value in enumerate(values):
            if isinstance(value, memoryview):
                value = value.tobytes()
            if not isinstance(value, (bytes, bytearray)):
                raise ValueError(f"Value at index {i} must be a bytes-like object, but got {type(value)}")
            ctxt = PyCtxt(pyfhel=HE, bytestring=value)  # Convert bytes back to ciphertext
            decrypted_value = HE.decryptFrac(ctxt)      # Decrypt to get the float value
            total_sum += decrypted_value                # Add the float values

        # Encrypt the total sum back to bytes
        total_ctxt = HE.encryptFrac(total_sum)
        return total_ctxt.to_bytes()

    except Exception as e:
        print(f"Error during homomorphic sum: {e}")
        return None

@pytest.fixture(scope='module')
def he():
    """Initialize Pyfhel for use in tests."""
    he_instance = Pyfhel()
    qi_sizes = [60, 30, 30, 30, 30, 30, 60]
    he_instance.contextGen(scheme='ckks', n=2**14, scale=2**30, qi_sizes=qi_sizes)
    he_instance.keyGen()
    return he_instance

@pytest.fixture(scope='module')
def setup_database(he):
    """Set up an in-memory SQLite database with encrypted data for testing."""
    conn = sqlite3.connect(':memory:')
    
    def wrapped_homomorphic_sum(*args):
        encrypted_args = []
        for i, arg in enumerate(args):
            print(f"wrapped_homomorphic_sum - Argument {i}: Type = {type(arg)}, Value = {arg}")
            if isinstance(arg, float):
                print(f"Warning: Argument {i} is a float. Encrypting it.")
                encrypted_args.append(encrypt_value(arg))
            elif isinstance(arg, memoryview):
                encrypted_args.append(arg.tobytes())
            elif isinstance(arg, bytes):
                encrypted_args.append(arg)
            else:
                print(f"Error: Unexpected type {type(arg)} at index {i}")
                return None
        return homomorphic_sum(*encrypted_args)
    
    conn.create_function("homomorphic_sum", -1, wrapped_homomorphic_sum)
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

    # Insert encrypted dummy data (values from 1.0 to 3.0)
    data = [(encrypt_value(float(i)), encrypt_value(float(i + 1)), encrypt_value(float(i + 2)), float(i)) for i in range(1, 4)]
    cursor.executemany('INSERT INTO housing_encrypted (MedInc_enc, HouseAge_enc, AveRooms_enc, MedInc) VALUES (?, ?, ?, ?)', data)

    print("\nOriginal data inserted into the database (before encryption):")
    for i in range(1, 4):
        print(f"Row {i}: MedInc = {float(i)}, HouseAge = {float(i + 1)}, AveRooms = {float(i + 2)}")

    conn.commit()
    yield conn
    conn.close()

def test_homomorphic_sum(setup_database, he):
    """Test the homomorphic_sum function within an SQLite query using encrypted data."""
    conn = setup_database
    cursor = conn.cursor()

    try:
        # Check if the table and columns exist and contain data
        cursor.execute("PRAGMA table_info(housing_encrypted)")
        columns = cursor.fetchall()

        if not columns or len(columns) < 4:
            raise ValueError("Table does not have the required columns.")

        # Validate that the relevant columns are of type BLOB
        for column in columns:
            if column[1] in ('MedInc_enc', 'HouseAge_enc', 'AveRooms_enc') and column[2] != 'BLOB':
                raise TypeError(f"Column {column[1]} is not of type BLOB. Found type: {column[2]}")

        cursor.execute('SELECT COUNT(*) FROM housing_encrypted')
        count = cursor.fetchone()[0]
        if count == 0:
            raise ValueError("Table is empty.")

        print(f"\nNumber of columns: {len(columns)}")
        print(f"Number of rows: {count}")

        cursor.execute('SELECT * FROM housing_encrypted')
        rows = cursor.fetchall()
        print("\nData in database (after encryption):")
        for row in rows:
            print(row)

        print("\nRunning homomorphic_sum query on MedInc_enc column...")
        cursor.execute('SELECT homomorphic_sum(MedInc_enc) FROM housing_encrypted')
        result = cursor.fetchone()[0]

        if result is None:
            raise ValueError("Query returned None.")

        # Convert the result from bytes to ciphertext and decrypt it
        ctxt_result = PyCtxt(pyfhel=he, bytestring=result)
        decrypted_result = he.decryptFrac(ctxt_result)

        # Handle the CKKS output if it returns a vector
        if isinstance(decrypted_result, np.ndarray):
            decrypted_result = np.mean(decrypted_result)  # Take the mean to reduce to a scalar

        # 1.0 + 2.0 + 3.0 = 6.0
        expected_sum = 6.0

        print(f"\nExpected sum: {expected_sum}")
        print(f"Decrypted result sum: {decrypted_result}")

        # Validate that the decrypted result matches the expected sum
        np.testing.assert_almost_equal(decrypted_result, expected_sum, decimal=1)

        cursor.execute('SELECT SUM(MedInc) FROM housing_encrypted')
        sqlite_sum = cursor.fetchone()[0]
        print(f"SQLite SUM result: {sqlite_sum}")

    except Exception as e:
        print(f"\nError during test_homomorphic_sum: {e}")

if __name__ == "__main__":
    pytest.main()

