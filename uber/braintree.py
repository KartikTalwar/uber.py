"""
Braintree client-side encryption
"""

from Crypto.Cipher import AES
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

# PKCS#5 padding. Thanks https://gist.github.com/crmccreary/5610068
BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s: s[0:-ord(s[-1])]


class Braintree(object):
    """
    Implements the Braintree client-side encryption. Used iOS code for reference.
    """

    PREFIX = '$bt3|ios_1_0_1'
    KEY_LENGTH = 32
    IV_LENGTH = 16

    def __init__(self, pubkey):
        self._rsa = RSA.importKey(pubkey.decode('base64'))

    def _aes_encrypt(self, payload):
        payload = pad(payload)
        key = Random.get_random_bytes(self.KEY_LENGTH)
        iv = Random.get_random_bytes(self.IV_LENGTH)
        cipher = AES.new(key, AES.MODE_CBC, iv)

        encrypted = cipher.encrypt(payload)
        return key, (iv + encrypted)

    def _rsa_encrypt(self, payload):
        cipher = PKCS1_v1_5.new(self._rsa)
        return cipher.encrypt(payload)

    def encrypt(self, payload):
        key, encrypted_payload = self._aes_encrypt(payload)
        encrypted_key = self._rsa_encrypt(key.encode('base64'))  # why is bt doing a base64 here???

        return '$'.join([
            self.PREFIX,
            encrypted_key.encode('base64'),
            encrypted_payload.encode('base64'),
        ]).replace('\n', '')
