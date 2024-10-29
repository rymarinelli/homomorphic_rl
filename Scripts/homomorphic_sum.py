# Scripts/homomorphic_sum.py

import os
from pathlib import Path
from Pyfhel import Pyfhel, PyCtxt
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_pyfhel(context_path: str, public_key_path: str) -> Pyfhel:
    """
    Initializes a Pyfhel instance with the given context and public key.

    Parameters:
        context_path (str): Path to the context file.
        public_key_path (str): Path to the public key file.

    Returns:
        Pyfhel: An initialized Pyfhel instance.

    Raises:
        FileNotFoundError: If the context or public key files are not found.
    """
    he = Pyfhel()

    # Check if context and public key files exist
    if not Path(context_path).exists():
        logger.error(f"Context file not found at {context_path}")
        raise FileNotFoundError(f"Context file not found at {context_path}")
    if not Path(public_key_path).exists():
        logger.error(f"Public key file not found at {public_key_path}")
        raise FileNotFoundError(f"Public key file not found at {public_key_path}")

    he.load_context(context_path)
    he.load_public_key(public_key_path)
    logger.info("Pyfhel instance initialized with context and public key.")

    return he

def homomorphic_sum_py(he: Pyfhel, *ciphertexts: bytes) -> bytes:
    """
    Sums multiple encrypted ciphertexts using Pyfhel and returns the aggregated ciphertext.

    Parameters:
        he (Pyfhel): An initialized Pyfhel object with loaded context and keys.
        *ciphertexts (bytes): Variable number of ciphertexts in bytes format.

    Returns:
        bytes: The aggregated ciphertext as bytes.

    Raises:
        ValueError: If no ciphertexts are provided.
    """
    if not ciphertexts:
        logger.error("No ciphertexts provided for homomorphic summation.")
        raise ValueError("At least one ciphertext is required for summation.")

    # Initialize the total ciphertext with the first ciphertext
    total_ctxt = PyCtxt(pyfhel=he, bytestring=ciphertexts[0])
    logger.debug("Initialized total_ctxt with the first ciphertext.")

    # Add the remaining ciphertexts
    for ct in ciphertexts[1:]:
        ctxt = PyCtxt(pyfhel=he, bytestring=ct)
        total_ctxt += ctxt  # Homomorphic addition
        logger.debug("Added a ciphertext to total_ctxt.")

    aggregated_ctxt_bytes = total_ctxt.to_bytes()
    logger.info("Homomorphic summation completed.")

    return aggregated_ctxt_bytes

class HomomorphicSumAggregate:
    """
    SQLite aggregate function class for homomorphic summation.
    """
    def __init__(self):
        self.he = Pyfhel()
        # Determine the absolute path to context.ckks and public_key.pk
        current_dir = Path(__file__).parent.parent  # Adjust based on directory structure
        context_path = current_dir / "context.ckks"
        public_key_path = current_dir / "public_key.pk"

        # Load context and public key
        try:
            self.he = initialize_pyfhel(str(context_path), str(public_key_path))
            self.total_ctxt = None
            logger.info("HomomorphicSumAggregate initialized with context and public key.")
        except FileNotFoundError as e:
            logger.error(f"Initialization failed: {e}")
            raise

    def step(self, value):
        """
        Process each row's value.

        Parameters:
            value (bytes): The ciphertext in bytes format.
        """
        if value is None:
            logger.warning("HomomorphicSumAggregate: Received None value.")
            return
        if self.total_ctxt is None:
            self.total_ctxt = PyCtxt(pyfhel=self.he, bytestring=value)
            logger.debug("HomomorphicSumAggregate: Initialized total_ctxt with first ciphertext.")
        else:
            ctxt = PyCtxt(pyfhel=self.he, bytestring=value)
            self.total_ctxt += ctxt
            logger.debug("HomomorphicSumAggregate: Added ciphertext to total_ctxt.")

    def finalize(self):
        """
        Finalize the aggregation and return the aggregated ciphertext.

        Returns:
            bytes: The aggregated ciphertext as bytes, or None if no data was aggregated.
        """
        if self.total_ctxt is None:
            logger.warning("HomomorphicSumAggregate: No ciphertexts were aggregated.")
            return None
        aggregated_ctxt_bytes = self.total_ctxt.to_bytes()
        logger.info("HomomorphicSumAggregate: Finalizing aggregated ciphertext.")
        return aggregated_ctxt_bytes

