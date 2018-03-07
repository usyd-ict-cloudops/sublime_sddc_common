import base64
from pyasn1.codec.der import decoder as der_decoder
from pyasn1.codec.der import encoder as der_encoder
from pyasn1.codec.native import decoder as py_decoder
from pyasn1.codec.native import encoder as py_encoder
from pyasn1.type import constraint
from pyasn1.type import namedtype
from pyasn1.type import tag
from pyasn1.type import univ


class ContentType(univ.ObjectIdentifier):
    pass


class Version(univ.Integer):
    pass


class AttributeValue(univ.Any):
    pass


class AttributeType(univ.ObjectIdentifier):
    pass


class AttributeTypeAndValue(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('type', AttributeType()),
        namedtype.NamedType('value', AttributeValue())
    )


class RelativeDistinguishedName(univ.SetOf):
    componentType = AttributeTypeAndValue()


class RDNSequence(univ.SequenceOf):
    componentType = RelativeDistinguishedName()


class Name(univ.Choice):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('', RDNSequence())
    )


class RSA_Encryption(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('algorithm', univ.ObjectIdentifier('1.2.840.113549.1.1.1')),
        namedtype.NamedType('parameters', univ.Null())
    )


class AES_256_CBC(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('algorithm', univ.ObjectIdentifier('2.16.840.1.101.3.4.1.42')),
        namedtype.NamedType('iv', univ.OctetString().subtype(subtypeSpec=constraint.ValueSizeConstraint(16, 16)))
    )


class IssuerAndSerialNumber(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('issuer', Name()),
        namedtype.NamedType('serialNumber', univ.Integer(1))
    )


class EYAMLContentInfo(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('contentType', ContentType('1.2.840.113549.1.7.1')),
        namedtype.NamedType('contentEncryptionAlgorithm', AES_256_CBC()),
        namedtype.NamedType('encryptedContent', univ.OctetString().subtype(
            implicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatConstructed, 0)))
    )


class EYAMLInfo(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('version', Version()),
        namedtype.NamedType('issuerAndSerialNumber', IssuerAndSerialNumber()),
        namedtype.NamedType('keyEncryptionAlgorithm', RSA_Encryption()),
        namedtype.NamedType('encryptedKey', univ.OctetString())
    )


class EYAMLInfos(univ.SetOf):
    componentType = EYAMLInfo()


class EYAMLData(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('version', Version()),
        namedtype.NamedType('eyamlInfos', EYAMLInfos()),
        namedtype.NamedType('eyamlContentInfo', EYAMLContentInfo())
    )


class EYAML(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('contentType', ContentType('1.2.840.113549.1.7.3')),
        namedtype.NamedType('content', EYAMLData().subtype(
            explicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatConstructed, 0)))
    )


def get_substrate(eyaml_value):
    return base64.b64decode((eyaml_value[10:-1] if eyaml_value.startswith('ENC[PKCS7,') else eyaml_value).encode())

def decode(eyaml_value, asn1Spec=EYAML(), decodeOpenTypes=True):
    substrate = get_substrate(eyaml_value)
    asn1Object, rest = der_decoder.decode(substrate, asn1Spec=asn1Spec, decodeOpenTypes=decodeOpenTypes)
    if rest:
        return (rest,None,asn1Object)
    d = py_encoder.encode(asn1Object, encodeOpenTypes=True)
    eKey = d['content']['eyamlInfos'][0]['encryptedKey']
    sKeyIV = d['content']['eyamlContentInfo']['contentEncryptionAlgorithm']['iv']
    edata = d['content']['eyamlContentInfo']['encryptedContent']
    return eKey, sKeyIV, edata

def make_value(substrate):
    return 'ENC[PKCS7,'+base64.b64encode(substrate).decode()+']'

def make_asn1(eKey, sKeyIV, edata, asn1Spec=EYAML(), decodeOpenTypes=True):
    return py_decoder.decode({
        "contentType": "1.2.840.113549.1.7.3",
        "content": {
            "version": 0, 
            "eyamlInfos": [
                {
                    "version": 0, 
                    "issuerAndSerialNumber": {
                        "issuer": {
                            "": []
                        },
                        "serialNumber": 1
                    }, 
                    "keyEncryptionAlgorithm": {
                        "algorithm": "1.2.840.113549.1.1.1",
                        "parameters": None
                    }, 
                    "encryptedKey": eKey
                }
            ],
            "eyamlContentInfo": {
                "contentType": "1.2.840.113549.1.7.1", 
                "contentEncryptionAlgorithm": {
                    "algorithm": "2.16.840.1.101.3.4.1.42",
                    "iv": sKeyIV
                }, 
                "encryptedContent": edata
            }
        }
    }, asn1Spec=asn1Spec)

def encode(eKey, sKeyIV, edata, asn1Spec=EYAML(), encodeOpenTypes=True):
    asn1Object = make_asn1(eKey, sKeyIV, edata)
    substrate = der_encoder.encode(asn1Object, asn1Spec=asn1Spec, encodeOpenTypes=encodeOpenTypes)
    return make_value(substrate)

def pkcs7_pad(b,BS=16):
    return b + (BS - len(b) % BS) * chr(BS - len(b) % BS).encode()

def pkcs7_unpad(b):
    return b[0:-b[-1]]
