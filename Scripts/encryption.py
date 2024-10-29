from pathlib import Path
import logging
import sys
from typing import Union

import numpy as np
from Pyfhel import Pyfhel, PyCtxt


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('encryption.log')
    ]
)
logger = logging.getLogger(__name__)


class HE:
    """
    Homomorphic Encryption (HE) handler using the CKKS scheme.
    Provides functionalities to encrypt and decrypt numerical and string data.
    """

    def __init__(self) -> None:
        self.he = Pyfhel()
        logger.info("Pyfhel instance created.")

    def load_context(self, context_path: str) -> None:
        """
        Loads the HE encryption context from a specified file.

        Args:
            context_path (str): Path to the HE context file.
        """
        try:
            self.he.load_context(context_path)
            logger.info(f"Encryption context loaded from '{context_path}'.")
        except Exception as e:
            logger.error(f"Failed to load context from '{context_path}': {e}")
            sys.exit(1)

    def load_public_key(self, public_key_path: str) -> None:
        """
        Loads the public key from a specified file.

        Args:
            public_key_path (str): Path to the public key file.
        """
        try:
            self.he.load_public_key(public_key_path)
            logger.info(f"Public key loaded from '{public_key_path}'.")
        except Exception as e:
            logger.error(f"Failed to load public key from '{public_key_path}': {e}")
            sys.exit(1)

    def load_secret_key(self, secret_key_path: str) -> None:
        """
        Loads the secret key from a specified file.

        Args:
            secret_key_path (str): Path to the secret key file.
        """
        try:
            self.he.load_secret_key(secret_key_path)
            logger.info(f"Secret key loaded from '{secret_key_path}'.")
        except Exception as e:
            logger.error(f"Failed to load secret key from '{secret_key_path}': {e}")
            sys.exit(1)

    def encrypt_value(self, value: Union[float, int, str]) -> bytes:
        """
        Encrypts a numerical or string value and returns the ciphertext as bytes.

        Args:
            value (Union[float, int, str]): The value to encrypt.

        Returns:
            bytes: The encrypted ciphertext.
        """
        try:
            if isinstance(value, (int, float)):
                array = np.array([value], dtype=np.float64)
                ptxt = self.he.encodeFrac(array)
                ctxt = self.he.encryptPtxt(ptxt)
            elif isinstance(value, str):
                self.he.encryptStr(value)
                ctxt = self.he.get_ctxt()
            else:
                raise ValueError(f"Unsupported data type for encryption: {type(value)}")

            ciphertext_bytes = ctxt.to_bytes()
            logger.debug(f"Encrypted value '{value}' to ciphertext bytes.")
            return ciphertext_bytes
        except Exception as e:
            logger.error(f"Encryption failed for value '{value}': {e}")
            return b''

    def decrypt_value(self, ciphertext_bytes: bytes) -> Union[float, str, None]:
        """
        Decrypts a ciphertext and returns the original value.

        Args:
            ciphertext_bytes (bytes): The encrypted ciphertext.

        Returns:
            Union[float, str, None]: The decrypted value or None if decryption fails.
        """
        try:
            ctxt = PyCtxt(pyfhel=self.he, bytestring=ciphertext_bytes)
            scheme = self.he.get_ciphertext_scheme()
            if scheme == 'CKKS':
                decrypted = self.he.decryptFrac(ctxt)
                decrypted_value = decrypted[0] if decrypted.size > 0 else None
            elif scheme == 'BFV':
                decrypted_value = self.he.decryptStr(ctxt)
            else:
                raise ValueError("Unsupported encryption scheme for decryption.")

            logger.debug(f"Decrypted ciphertext bytes to value '{decrypted_value}'.")
            return decrypted_value
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None


if __name__ == "__main__":
    main()

