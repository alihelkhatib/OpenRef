import base64,json,tempfile,unittest
from pathlib import Path
from provision_rt595_trust_anchor import parse_pem,render_header
G=bytes.fromhex("6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c2964fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5")
ALG=bytes.fromhex("301306072a8648ce3d020106082a8648ce3d030107")
DER=b"\x30\x59"+ALG+b"\x03\x42\x00\x04"+G
def pem(label="PUBLIC KEY",der=DER):return f"-----BEGIN {label}-----\n{base64.b64encode(der).decode()}\n-----END {label}-----\n"
class Test(unittest.TestCase):
 def test_valid(self):
  der,raw=parse_pem(pem());self.assertEqual(raw,G);self.assertIn("openref_trust_anchor_public_key",render_header(raw,b"12345678",b"x"*32))
 def test_private_rejected(self):
  with self.assertRaisesRegex(ValueError,"private"):parse_pem(pem("PRIVATE KEY"))
 def test_wrong_curve_rejected(self):
  bad=DER.replace(bytes.fromhex("2a8648ce3d030107"),bytes.fromhex("2b81040022")+b"\x00\x00")
  with self.assertRaises(ValueError):parse_pem(pem(der=bad))
 def test_malformed_and_off_curve(self):
  with self.assertRaises(ValueError):parse_pem("garbage")
  bad=DER[:-1]+bytes([DER[-1]^1])
  with self.assertRaisesRegex(ValueError,"not on"):parse_pem(pem(der=bad))
if __name__=="__main__":unittest.main()
