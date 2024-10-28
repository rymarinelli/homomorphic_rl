import numpy as np
from Pyfhel import PyCtxt
from ckks import HE  

def encrypt_value(value):
    """
    Encrypt a float value using CKKS encryption and return it as bytes.
    
    Args:
        value (float): The value to encrypt.
        
    Returns:
        bytes: Encrypted value in byte format.
    """
    plaintext = HE.encodeFrac(np.array([value], dtype=np.float64))  # Encode for CKKS
    encrypted_value = HE.encryptPtxt(plaintext).to_bytes()  # Encrypt and convert to bytes
    return encrypted_value

def decrypt_value(value):
    """
    Decrypt bytes back into a float value.
    
    Args:
        value (bytes): Encrypted value in byte format.
        
    Returns:
        float: The decrypted float value.
    """
    ctxt = PyCtxt(pyfhel=HE, bytestring=value)  # Convert bytes back to ciphertext
    decrypted_value = HE.decryptFrac(ctxt)  # Decrypt
    return decrypted_value[0]  # Return the first element from decrypted array

