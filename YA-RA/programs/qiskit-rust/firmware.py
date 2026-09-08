"""Qiskit-side firmware stub. It calls across the plane by name."""
from ctypes import CDLL, c_char_p, c_size_t

def submit(lib: CDLL, circuit: bytes) -> int:
    return lib.yara_qpu_submit(c_char_p(circuit), c_size_t(len(circuit)))
