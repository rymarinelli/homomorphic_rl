from pathlib import Path
from Pyfhel import Pyfhel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_keys():
    """
    Generates a CKKS encryption context and keys, saving them to the root directory.
    """
    he = Pyfhel()
    logger.info("Pyfhel instance created.")

    # Generating CKKS context
    try:
        he.contextGen(scheme='CKKS', n=2**14, scale=2**30, qi_sizes=[60, 30, 30, 30, 30, 30, 60])
        he.keyGen()
        
        # Specify the root directory for the context and keys
        root_dir = Path(__file__).parent.parent  # Adjust path to root directory
        he.save_context(str(root_dir / "context.ckks"))
        he.save_public_key(str(root_dir / "public_key.pk"))
        he.save_secret_key(str(root_dir / "secret_key.sk"))

        logger.info(f"Keys and context saved to {root_dir}")
    except Exception as e:
        logger.error(f"Failed to generate HE context and keys: {e}")
        raise

if __name__ == "__main__":
    generate_keys()

