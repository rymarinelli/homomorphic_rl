from Pyfhel import Pyfhel
import logging
from pathlib import Path


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HE:
    def __init__(self):
        self.he = Pyfhel()
        logger.info("Pyfhel instance created.")

    def load_context(self, context_path: str):
        """
        Loads the encryption context from a file.
        """
        self.he.load_context(context_path)
        logger.info(f"Encryption context loaded from {context_path}.")

    def load_public_key(self, public_key_path: str):
        """
        Loads the public key from a file.
        """
        self.he.load_public_key(public_key_path)
        logger.info(f"Public key loaded from {public_key_path}.")

    def load_secret_key(self, secret_key_path: str):
        """
        Loads the secret key from a file.
        """
        self.he.load_secret_key(secret_key_path)
        logger.info(f"Secret key loaded from {secret_key_path}.")

    def encrypt_value(self, value: float) -> bytes:
        """
        Encrypts a single float value and returns the ciphertext as bytes.
        """
        import numpy as np
        array = np.array([value], dtype=np.float64)
        ptxt = self.he.encodeFrac(array)
        ctxt = self.he.encryptPtxt(ptxt)
        return ctxt.to_bytes()

    def decrypt_value(self, ciphertext_bytes: bytes) -> float:
        """
        Decrypts a ciphertext (in bytes) and returns the float value.
        """
        ctxt = PyCtxt(pyfhel=self.he, bytestring=ciphertext_bytes)
        decrypted = self.he.decryptFrac(ctxt)
        return decrypted[0]

