import unittest
from Crypto.Cipher import AES, PKCS1_v1_5
from uber.braintree import Braintree, unpad
from Crypto.PublicKey import RSA

public_key = "MIIBCgKCAQEA8wQ3PXFYuBn9RBtOK3lW4V+7HNjik7FFd0qpPsCVd4KeiIfhuzupSevHUOLjbRSqwvAaZK3/icbBaM7CMAR5y0OjAR5lmmEEkcw+A7pmKQK6XQ8j3fveJCzC3MPiNiFfr+vER7O4diTxGhoXjFFJQpzKkCwFgwhKrW8uJLmWqVhQRVNphii1GpxI4fjFNc4h1w2W2CJ9kkv+9e3BnCpdVe1w7gBQZMkgjCzxbuAg8XaKlKD48M9kr8iE8kNt1eXV0jbmhCY3vZrckCUv26r2X4cD5lDvUtC1Gj6jBFobm/MelAfoFqNeq+/9VyMdYfhIecQimiBYr7Vm5VH9m69TXwIDAQAB"
private_key = "MIIEowIBAAKCAQEA8wQ3PXFYuBn9RBtOK3lW4V+7HNjik7FFd0qpPsCVd4KeiIfhuzupSevHUOLjbRSqwvAaZK3/icbBaM7CMAR5y0OjAR5lmmEEkcw+A7pmKQK6XQ8j3fveJCzC3MPiNiFfr+vER7O4diTxGhoXjFFJQpzKkCwFgwhKrW8uJLmWqVhQRVNphii1GpxI4fjFNc4h1w2W2CJ9kkv+9e3BnCpdVe1w7gBQZMkgjCzxbuAg8XaKlKD48M9kr8iE8kNt1eXV0jbmhCY3vZrckCUv26r2X4cD5lDvUtC1Gj6jBFobm/MelAfoFqNeq+/9VyMdYfhIecQimiBYr7Vm5VH9m69TXwIDAQABAoIBAEvL/9LJPKvHZ2hLv/jtUrze2ASqXRlFzG3lup4ZAUWSVxIsl6qHdEjbIoLHEbpfHNfKfeDzKGX3uTGQc574dmiAwyHBMl2RbxRuiNUu2VhnQmtuInjFa0cLMwgajL7nb+n19nWKx7kJ0q2af8fDPr9pGgEXyexRtMEdkV3hCO3uQxA0MlX/61LK4Gssk7hlXcNw6k4fIRt9xANnN3KUrGIYtmaCk9kKsX8HhW9yrVm0WWXHnzm6o5O+3BeP+3cWe+NHeRJEVEXwIPqWtdQa6e0hDtLpCQPOSlpr4yJHssT2BHpkPaHi6OnGIHa0HD7ibyfwc1KQjcwA8jg4OabmT7ECgYEA/2Y1m1zG5B0nB9Mixu/3K7d+FYpBrlTKElJ0rFNcNBgvt32dPBD6E6ZrL8MokXSy8HrhhR4epQYolyfHHtpzva1gZ8XRO1wZO++TfJwfUd1epDGcdMOfw++dZFW1EaWrnC3YPxrvfd/DuilwXg1QUb9aIiXCMpmQw/sm0VNk2ycCgYEA85aMzCSR2pMNip9WDQnsrP+6nYhST3BrJlJAwLNrWS9zQFfXLvufIJ0OQkdP2mAM9yN9vV8FmAt7CSAPY2UsMvKpriyv5vlqZZF7VwMr1bOaIOllBA+IIY/x3c7iF5Ezt1hJyNegjmts+Fz39G6PN1WDrCGcmcZbXOEYhs2eyQkCgYEAgANqITpqkpIuKxTgHJjQ6j+p2gAXldr4AiEETA/oalApMq6qrh3QSyMiHKmUXvwAaNseyMtlDtA8bi9I9iUG2G7boIgdrMQn/cvCwDW82Rq9Qk1/n2MiZGJpII55GKRSlRDBkDffDNeo0lnM8cd4l9Dyy6TjZttkHWd4eHl1VwcCgYAt9VC5T4kJUUdzyR5GNYInHdTK1iaZgF9nCovXD8MIP7CiCjC6V5UtZRSEosnJLOglVNfre9slVb0v+pGMslEFh81F5H6HuLU/VpSL1ThXCJzi6sY5XujTVEJRFDCKO8YjKJA7SZusY05bCcdqodV5njPKrUjLpqYkPwAOpwr3aQKBgGie+R5Xk1t0IEdTnnY/aZHNHR6fn5elFArgRN6fixx82kQDfgMaeQbtOW4Z8RxDDUeGhc11S1filfVZT2DHayoQLr6ORU/nODhHe6KedsUNFy1IRgoR1Si+2Y1g3IjrxqAFFdmgBNsxc1JMoFUDMJe2KlaF3nEk3OWuPc/A5G12"

class TestBraintree(unittest.TestCase):
    def test_aes(self):
        bt = Braintree(public_key)
        key, payload = bt._aes_encrypt('hello world')

        iv = payload[:Braintree.IV_LENGTH]
        encrypted_data = payload[Braintree.IV_LENGTH:]

        aes = AES.new(key, AES.MODE_CBC, iv)
        decrypted_data = aes.decrypt(encrypted_data)
        decrypted_data = unpad(decrypted_data)
        self.assertEqual(decrypted_data, 'hello world')

    def test_rsa(self):
        bt = Braintree(public_key)
        encrypted = bt._rsa_encrypt('hello world')
        self.assertEqual(self._decrypt_rsa(encrypted), 'hello world')

    def test_full(self):
        bt = Braintree(public_key)
        full_message = bt.encrypt('hello world')

        _, prefix, encrypted_key, encrypted_payload = full_message.split('$')
        self.assertEqual(_ + '$' + prefix, Braintree.PREFIX)

        # strip rsa
        encrypted_payload = encrypted_payload.decode('base64')
        decrypted_key = self._decrypt_rsa(encrypted_key.decode('base64')).decode('base64')

        # strip aes
        iv = encrypted_payload[:Braintree.IV_LENGTH]
        encrypted_data = encrypted_payload[Braintree.IV_LENGTH:]

        aes = AES.new(decrypted_key, AES.MODE_CBC, iv)
        decrypted_data = aes.decrypt(encrypted_data)
        decrypted_data = unpad(decrypted_data)

        self.assertEqual(decrypted_data, 'hello world')

    def _decrypt_rsa(self, data):
        rsa = RSA.importKey(private_key.decode('base64'))
        cipher = PKCS1_v1_5.new(rsa)
        return cipher.decrypt(data, Exception())


if __name__ == '__main__':
    unittest.main()
