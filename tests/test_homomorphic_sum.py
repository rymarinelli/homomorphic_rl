import pytest
import numpy as np
from Pyfhel import Pyfhel
from Scripts.homomorphic_sum import homomorphic_sum
from Scripts.encryption import encrypt_value, decrypt_value

@pytest.fixture(scope='module')
def he():
    """Fixture to initialize Pyfhel for use in tests."""
    he_instance = Pyfhel()
    qi_sizes = [60, 30, 30, 30, 30, 30, 60]
    he_instance.contextGen(scheme='ckks', n=2**14, scale=2**30, qi_sizes=qi_sizes)
    he_instance.keyGen()
    return he_instance

def test_homomorphic_sum_basic(he):
    encrypted_val1 = encrypt_value(10.0)
    encrypted_val2 = encrypt_value(5.0)
    
    encrypted_sum = homomorphic_sum(encrypted_val1, encrypted_val2)
    
    decrypted_sum = decrypt_value(encrypted_sum)
    expected_sum = 10.0 + 5.0
    assert decrypted_sum == pytest.approx(expected_sum, rel=1e-2), f"Expected {expected_sum}, got {decrypted_sum}"

def test_homomorphic_sum_empty(he):
    encrypted_sum = homomorphic_sum()
    assert encrypted_sum is None, "Expected None when no values are provided"

