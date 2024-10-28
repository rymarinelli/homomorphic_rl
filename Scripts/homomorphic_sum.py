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

  
    total = HE.encryptFrac(np.array([0.0], dtype=np.float64))


    for value in values:
        ctxt = PyCtxt(pyfhel=HE, bytestring=value)  # Convert bytes back to ciphertext
        total += ctxt  # Add ciphertexts

    # Convert result to bytes for output
    return total.to_bytes()

