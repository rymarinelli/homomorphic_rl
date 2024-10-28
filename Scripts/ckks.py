from Pyfhel import Pyfhel

def initialize_pyfhel():
    """Initializes Pyfhel with parameters for CKKS encryption."""
    HE = Pyfhel()
    qi_sizes = [60, 30, 30, 30, 30, 30, 60]
    HE.contextGen(scheme='ckks', n=2**14, scale=2**30, qi_sizes=qi_sizes)
    HE.keyGen()
    return HE

HE = initialize_pyfhel()
