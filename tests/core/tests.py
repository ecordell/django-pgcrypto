from django.test import TestCase
from Crypto.Cipher import Blowfish, AES
from pgcrypto import pad, unpad, armor, dearmor, aes_pad_key
from .models import Employee
import unittest
import decimal

class CryptoTests (unittest.TestCase):

    def setUp(self):
        # This is the expected Blowfish-encrypted value, according to the following pgcrypto call:
        #     select encrypt('sensitive information', 'pass', 'bf');
        self.encrypt_bf = b"x\364r\225\356WH\347\240\205\211a\223I{~\233\034\347\217/f\035\005"
        # The basic "encrypt" call assumes an all-NUL IV of the appropriate block size.
        self.iv_blowfish = b"\0" * Blowfish.block_size
        # This is the expected AES-encrypted value, according to the following pgcrypto call:
        #     select encrypt('sensitive information', 'pass', 'aes');
        self.encrypt_aes = b"\263r\011\033]Q1\220\340\247\317Y,\321q\224KmuHf>Z\011M\032\316\376&z\330\344"
        # The basic "encrypt" call assumes an all-NUL IV of the appropriate block size.
        self.iv_aes = b"\0" * AES.block_size
        # When encrypting a string whose length is a multiple of the block size, pgcrypto
        # tacks on an extra block of padding, so it can reliably unpad afterwards. This
        # data was generated from the following query (string length = 16):
        #     select encrypt('xxxxxxxxxxxxxxxx', 'secret', 'aes');
        self.encrypt_aes_padded = b"5M\304\316\240B$Z\351\021PD\317\213\213\234f\225L \342\004SIX\030\331S\376\371\220\\"

    def test_encrypt(self):
        c = Blowfish.new('pass', Blowfish.MODE_CBC, self.iv_blowfish)
        self.assertEqual(c.encrypt(pad('sensitive information', c.block_size)), self.encrypt_bf)

    def test_decrypt(self):
        c = Blowfish.new('pass', Blowfish.MODE_CBC, self.iv_blowfish)
        self.assertEqual(unpad(c.decrypt(self.encrypt_bf), c.block_size), b'sensitive information')

    def test_armor_dearmor(self):
        a = armor(self.encrypt_bf)
        self.assertEqual(dearmor(a), self.encrypt_bf)

    def test_aes(self):
        c = AES.new(aes_pad_key('pass'), AES.MODE_CBC, self.iv_aes)
        self.assertEqual(c.encrypt(pad('sensitive information', c.block_size)), self.encrypt_aes)

    def test_aes_pad(self):
        c = AES.new(aes_pad_key('secret'), AES.MODE_CBC, self.iv_aes)
        self.assertEqual(unpad(c.decrypt(self.encrypt_aes_padded), c.block_size), b'xxxxxxxxxxxxxxxx')

class FieldTests (TestCase):
    fixtures = ('employees',)

    def setUp(self):
        from django.db import connections
        c = connections['default'].cursor()
        c.execute('CREATE EXTENSION pgcrypto')

    def test_query(self):
        self.assertEqual(Employee.objects.get(ssn='999-05-6728').pk, 1)

    def test_decimal(self):
        self.assertEqual(Employee.objects.filter(salary=decimal.Decimal('75248.77')).count(), 1)
        self.assertEqual(Employee.objects.filter(salary__gte=decimal.Decimal('75248.77')).count(), 1)
        self.assertEqual(Employee.objects.filter(salary__gt=decimal.Decimal('75248.77')).count(), 0)
        self.assertEqual(Employee.objects.filter(salary__gte=decimal.Decimal('70000.00')).count(), 1)
        self.assertEqual(Employee.objects.filter(salary__lte=decimal.Decimal('70000.00')).count(), 1)
        self.assertEqual(Employee.objects.filter(salary__lt=decimal.Decimal('52000')).count(), 0)