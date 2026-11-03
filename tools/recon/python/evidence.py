"""Encrypt research artifacts to a local recipient; no decryption key on runners."""
import argparse
import base64
import json
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def keygen(private_path: Path, public_path: Path):
    if private_path.exists() or public_path.exists():
        raise FileExistsError("refusing to overwrite recipient keys")
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    with private_path.open("xb") as output:
        output.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                       serialization.NoEncryption()))
    with public_path.open("xb") as output:
        output.write(key.public_key().public_bytes(serialization.Encoding.PEM,
                                                  serialization.PublicFormat.SubjectPublicKeyInfo))


def oaep():
    return padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=b"nasklab-evidence-v1")


def encrypt(data: bytes, public_pem: bytes) -> bytes:
    recipient = serialization.load_pem_public_key(public_pem)
    if not isinstance(recipient, rsa.RSAPublicKey) or recipient.key_size < 2048:
        raise ValueError("recipient must be RSA >=2048 bits")
    key = Fernet.generate_key()
    return json.dumps({"version": 1, "wrapped_key": base64.b64encode(recipient.encrypt(key, oaep())).decode(),
                       "ciphertext": Fernet(key).encrypt(data).decode()}).encode()


def decrypt(envelope: bytes, private_pem: bytes) -> bytes:
    value = json.loads(envelope)
    if value.get("version") != 1 or set(value) != {"version", "wrapped_key", "ciphertext"}:
        raise ValueError("unknown evidence format")
    recipient = serialization.load_pem_private_key(private_pem, password=None)
    key = recipient.decrypt(base64.b64decode(value["wrapped_key"], validate=True), oaep())
    return Fernet(key).decrypt(value["ciphertext"].encode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["keygen", "encrypt", "decrypt"])
    parser.add_argument("--private", type=Path)
    parser.add_argument("--public", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "keygen":
        if args.private is None or args.public is None:
            parser.error("keygen requires --private and --public")
        keygen(args.private, args.public)
    else:
        if args.input is None or args.output is None:
            parser.error("input and output are required")
        key_path = args.public if args.mode == "encrypt" else args.private
        if key_path is None:
            parser.error("the corresponding key is required")
        operation = encrypt if args.mode == "encrypt" else decrypt
        result = operation(args.input.read_bytes(), key_path.read_bytes())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as output:
            output.write(result)
    print("Evidence operation completed; no key material printed")


if __name__ == "__main__":
    main()
