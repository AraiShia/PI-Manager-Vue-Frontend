# -*- coding: utf-8 -*-
"""临时密钥生成脚本"""

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

def generate_keys():
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    print("=== PRIVATE KEY (keep secret) ===")
    print(private_pem.decode('utf-8'))
    print("=== PUBLIC KEY ===")
    print(public_pem.decode('utf-8'))

if __name__ == "__main__":
    generate_keys()
