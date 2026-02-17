from nacl.signing import SigningKey
from nacl.encoding import HexEncoder

class Identity:
    def __init__(self, name: str, private_key_hex: str = None):
        self.name = name
        if private_key_hex:
            self.signing_key = SigningKey(private_key_hex, encoder=HexEncoder)
        else:
            self.signing_key = SigningKey.generate()

    @property
    def private_key(self) -> str:
        return self.signing_key.encode(encoder=HexEncoder).decode('utf-8')

    @property
    def public_key(self) -> str:
        return self.signing_key.verify_key.encode(encoder=HexEncoder).decode('utf-8')

    def sign(self, message: str) -> str:
        """Sign a message and return the hex signature."""
        signed = self.signing_key.sign(message.encode('utf-8'))
        return signed.signature.hex()

def generate_identity(name: str) -> Identity:
    return Identity(name)
