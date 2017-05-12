# This file implements the crypto parts of SecFS

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
from secfs.types import I, Principal, User, Group

keys = {}

def register_keyfile(user, f):
    """
    Register the private key for the given user for use in signing/decrypting.
    """
    if not isinstance(user, User):
        raise TypeError("{} is not a User, is a {}".format(user, type(user)))

    with open(f, "rb") as key_file:
        k=key_file.read()
        keys[user] = serialization.load_pem_private_key(
            k,
            password=None,
            backend=default_backend()
        )

def decrypt_sym(key, data):
    """
    Decrypt the given data with the given key.
    """
    f = Fernet(key)
    return f.decrypt(data)

def encrypt_sym(key, data):
    """
    Encrypt the given data with the given key.
    """
    f = Fernet(key)
    return f.encrypt(data)

def generate_key(user):
    """
    Ensure that a private/public keypair exists in user-$uid-key.pem for the
    given user. If it does not, create one, and store the private key on disk.
    Finally, return the user's PEM-encoded public key.
    """
    if not isinstance(user, User):
        raise TypeError("{} is not a User, is a {}".format(user, type(user)))

    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend

    f = "user-{}-key.pem".format(user.id)

    import os.path
    if not os.path.isfile(f):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        pem = private_key.private_bytes(
           encoding=serialization.Encoding.PEM,
           format=serialization.PrivateFormat.TraditionalOpenSSL,
           encryption_algorithm=serialization.NoEncryption()
        )

        with open(f, "wb") as key_file:
            key_file.write(pem)

        public_key = private_key.public_key()
    else:
        with open(f, "rb") as key_file:
            public_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            ).public_key()

    return public_key.public_bytes(
       encoding=serialization.Encoding.PEM,
       format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

## functionality to support the cryptographic
## signing and verification of VSes
def sign(private_key, data):
    signer = private_key.signer(
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    signer.update(data)
    return signer.finalize()

def verify(public_key, sig, data):
    verifier = public_key.verifier(
        sig,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    verifier.update(data)

    #TODO figure out why verifier.verify() fails?
    try:
        b = verifier.verify()
    except:
        return False
    return True # verify() worked

def encrypt_asym(public_key, data):
    # construct ciphertext with padding & return
    return public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=SHA1()),
            algorithm=hashes.SHA1(),
            label=None
        )
    )

def decrypt_asym(private_key, data):
    # decrypt into plaintext & return
    return private_key.decrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None
        )
    )
