import binascii

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from blatann.gap.gap_types import PeerAddress

# Elliptic Curve used for LE Secure connections
_lesc_curve = ec.SECP256R1
_backend = default_backend()


def lesc_pubkey_to_raw(public_key: ec.EllipticCurvePublicKey, little_endian=True) -> bytearray:
    """
    Converts from a python public key to the raw (x, y) bytes for the nordic
    """
    pk = public_key.public_numbers()
    x = bytearray.fromhex("{:064x}".format(pk.x))
    y = bytearray.fromhex("{:064x}".format(pk.y))

    # Nordic requires keys in little-endian, rotate
    if little_endian:
        pubkey_raw = x[::-1] + y[::-1]
    else:
        pubkey_raw = x + y
    return pubkey_raw


def lesc_privkey_to_raw(private_key: ec.EllipticCurvePrivateKey, little_endian=True) -> bytearray:
    pk = private_key.private_numbers()
    x = bytearray.fromhex("{:064x}".format(pk.private_value))
    if little_endian:
        x = x[::-1]
    return x


def lesc_pubkey_from_raw(raw_key: bytes, little_endian=True) -> ec.EllipticCurvePublicKey:
    """
    Converts from raw (x, y) bytes to a public key that can be used for the DH request
    """
    key_len = len(raw_key)
    x_raw = raw_key[:key_len//2]
    y_raw = raw_key[key_len//2:]

    # Nordic transmits keys in little-endian, convert to big-endian
    if little_endian:
        x_raw = x_raw[::-1]
        y_raw = y_raw[::-1]

    x = int(binascii.hexlify(x_raw), 16)
    y = int(binascii.hexlify(y_raw), 16)
    public_numbers = ec.EllipticCurvePublicNumbers(x, y, _lesc_curve())
    return public_numbers.public_key(_backend)


def lesc_privkey_from_raw(raw_priv_key: bytes, raw_pub_key: bytes, little_endian=True) -> ec.EllipticCurvePrivateKey:
    key_len = len(raw_pub_key)
    x_raw = raw_pub_key[:key_len//2]
    y_raw = raw_pub_key[key_len//2:]

    if little_endian:
        x_raw = x_raw[::-1]
        y_raw = y_raw[::-1]
        raw_priv_key = raw_priv_key[::-1]

    x = int(binascii.hexlify(x_raw), 16)
    y = int(binascii.hexlify(y_raw), 16)
    priv = int(binascii.hexlify(raw_priv_key), 16)
    public_numbers = ec.EllipticCurvePublicNumbers(x, y, _lesc_curve())
    priv_numbers = ec.EllipticCurvePrivateNumbers(priv, public_numbers)
    return priv_numbers.private_key(_backend)


def lesc_generate_private_key() -> ec.EllipticCurvePrivateKey:
    """
    Generates a new private key that can be used for LESC pairing

    :return: The generated private key
    """
    return ec.generate_private_key(_lesc_curve, _backend)


def lesc_compute_dh_key(private_key: ec.EllipticCurvePrivateKey,
                        peer_public_key: ec.EllipticCurvePublicKey,
                        little_endian=False) -> bytes:
    """
    Computes the DH key for LESC pairing given our private key and the peer's public key

    :param private_key: Our private key
    :param peer_public_key: The peer's public key
    :param little_endian: whether or not to return the shared secret in little endian
    :return: The shared secret
    """
    dh_key = private_key.exchange(ec.ECDH(), peer_public_key)
    if little_endian:
        dh_key = dh_key[::-1]
    return dh_key


def ble_ah(key: bytes, p_rand: bytes) -> bytes:
    """
    Function for calculating the ah() hash function described in Bluetooth core specification 4.2 section 3.H.2.2.2.

    This is used for resolving private addresses where a private address
    is prand[3] || aes-128(irk, prand[3]) % 2^24

    :param key: the IRK to use, in big endian format
    :param p_rand: The random component, first 3 bytes of the address
    :return: The last 3 bytes of the encrypted hash
    """
    if len(p_rand) != 3:
        raise ValueError("Prand must be a str or bytes of length 3")

    # prepend the prand with 0's to fill up a 16-byte block
    p_rand = b"\x00" * 13 + p_rand

    cipher = Cipher(algorithms.AES(key), modes.ECB(), _backend)
    encryptor = cipher.encryptor()

    # Encrypt and return the last 3 bytes
    encrypted_hash = encryptor.update(p_rand) + encryptor.finalize()
    return encrypted_hash[-3:]


def private_address_resolves(peer_addr: PeerAddress, irk: bytes) -> bool:
    """
    Checks if the given peer address can be resolved with the IRK

    Private Resolvable Peer Addresses are in the format
    [4x:xx:xx:yy:yy:yy], where 4x:xx:xx is a random number hashed with the IRK to generate yy:yy:yy
    This function checks if the random number portion hashed with the IRK equals the hashed part of the address

    :param peer_addr: The peer address to check
    :param irk: The identity resolve key to try
    :return: True if it resolves, False if not
    """
    # prand consists of the first 3 MSB bytes of the peer address
    p_rand = bytes(peer_addr.addr[:3])
    # the calculated hash is the last 3 LSB bytes of the peer address
    addr_hash = bytes(peer_addr.addr[3:])
    # IRK is stored in little-endian bytearray, convert to string and reverse
    irk = bytes(irk)[::-1]
    local_hash = ble_ah(irk, p_rand)
    return local_hash == addr_hash


# BLE LESC Debug keys, defined in the Core Bluetooth Specification v4.2 Vol.3, Part H, Section 2.3.5.6.1
# Keys are in big-endian

_LESC_DEBUG_PRIVATE_KEY_RAW = binascii.unhexlify("3f49f6d4a3c55f3874c9b3e3d2103f504aff607beb40b7995899b8a6cd3c1abd")
_LESC_DEBUG_PUBLIC_KEY_X_RAW = binascii.unhexlify("20b003d2f297be2c5e2c83a7e9f9a5b9eff49111acf4fddbcc0301480e359de6")
_LESC_DEBUG_PUBLIC_KEY_Y_RAW = binascii.unhexlify("dc809c49652aeb6d63329abf5a52155c766345c28fed3024741c8ed01589d28b")
_LESC_DEBUG_PUBLIC_KEY_RAW = _LESC_DEBUG_PUBLIC_KEY_X_RAW + _LESC_DEBUG_PUBLIC_KEY_Y_RAW

LESC_DEBUG_PRIVATE_KEY = lesc_privkey_from_raw(_LESC_DEBUG_PRIVATE_KEY_RAW, _LESC_DEBUG_PUBLIC_KEY_RAW, little_endian=False)
LESC_DEBUG_PUBLIC_KEY = LESC_DEBUG_PRIVATE_KEY.public_key()
