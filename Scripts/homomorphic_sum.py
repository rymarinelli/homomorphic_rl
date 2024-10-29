import numpy as np
from Pyfhel import PyCtxt
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
