
import os
import rsa
import pyaes

from .asn1 import decode
from .asn1 import encode

def decrypt_session_key(eKey,keydata=None,filename='~/.eyaml/private_key.pkcs7.pem',format='PEM'):
    if keydata is None:
        with open(os.path.expanduser(filename),'rb') as fp:
            keydata = fp.read()
    privkey = rsa.PrivateKey.load_pkcs1(keydata,format=format)
    return rsa.decrypt(eKey, privkey)

def decrypt_bytes(value,keydata=None,key_filename='~/.eyaml/private_key.pkcs7.pem',format='PEM'):
    eKey, sKeyIV, edata = decode(value)
    sKey = decrypt_session_key(eKey,keydata,key_filename,format=format)
    aes = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(sKey,iv=sKeyIV))
    return aes.feed(edata) + aes.feed()

def decrypt(value,keydata=None,key_filename='~/.eyaml/private_key.pkcs7.pem',format='PEM'):
    return decrypt_bytes(value,keydata=keydata,key_filename=key_filename,format=format).decode()

def encrypt_session_key(sKey,keydata=None,filename='~/.eyaml/public_key.pkcs7.pem',format='PEM'):
    if keydata is None:
        with open(os.path.expanduser(filename),'rb') as fp:
            keydata = fp.read()
    pubkey = rsa.PublicKey.load_pkcs1(keydata,format=format)
    return rsa.encrypt(sKey, pubkey)

def encrypt_bytes(value,keydata=None,key_filename='~/.eyaml/public_key.pkcs7.pem',sKey=None,sKeyIV=None,format='PEM'):
    sKey = os.urandom(32) if sKey is None else sKey
    sKeyIV = os.urandom(16) if sKeyIV is None else sKeyIV
    eKey = encrypt_session_key(sKey,keydata,key_filename,format=format)
    aes = pyaes.Encrypter(pyaes.AESModeOfOperationCBC(sKey,iv=sKeyIV))
    edata = aes.feed(value) + aes.feed()
    return encode(eKey, sKeyIV, edata)

def encrypt(value,keydata=None,key_filename='~/.eyaml/public_key.pkcs7.pem',sKey=None,sKeyIV=None,format='PEM'):
    return encrypt_bytes(value.encode(),keydata=keydata,key_filename=key_filename,sKey=sKey,sKeyIV=sKeyIV,format=format)
