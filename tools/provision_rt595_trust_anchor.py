#!/usr/bin/env python3
"""Convert a PEM P-256 SubjectPublicKeyInfo into OpenRef build artifacts."""
import argparse, base64, hashlib, json, re
from pathlib import Path

EC_PUBLIC_KEY=bytes.fromhex("06072a8648ce3d0201")
PRIME256V1=bytes.fromhex("06082a8648ce3d030107")
P=0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
A=P-3
B=int("5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b",16)

def tlv(data,off,tag):
    if off>=len(data) or data[off]!=tag: raise ValueError("unexpected DER tag")
    off+=1
    if off>=len(data): raise ValueError("truncated DER length")
    n=data[off];off+=1
    if n&0x80:
        k=n&0x7f
        if k==0 or k>2 or off+k>len(data): raise ValueError("invalid DER length")
        n=int.from_bytes(data[off:off+k],"big");off+=k
        if n<128: raise ValueError("non-canonical DER length")
    end=off+n
    if end>len(data): raise ValueError("truncated DER value")
    return data[off:end],end

def parse_pem(text):
    if "PRIVATE KEY" in text: raise ValueError("private keys are forbidden")
    m=re.fullmatch(r"\s*-----BEGIN PUBLIC KEY-----\s*([A-Za-z0-9+/=\s]+)-----END PUBLIC KEY-----\s*",text)
    if not m: raise ValueError("expected one PEM PUBLIC KEY (SubjectPublicKeyInfo)")
    try: der=base64.b64decode("".join(m.group(1).split()),validate=True)
    except Exception as e: raise ValueError("invalid PEM base64") from e
    outer,end=tlv(der,0,0x30)
    if end!=len(der): raise ValueError("trailing DER data")
    alg,pos=tlv(outer,0,0x30)
    oid1,q=tlv(alg,0,0x06);oid2,q=tlv(alg,q,0x06)
    if q!=len(alg) or bytes([0x06,len(oid1)])+oid1!=EC_PUBLIC_KEY or bytes([0x06,len(oid2)])+oid2!=PRIME256V1: raise ValueError("key must be EC prime256v1/P-256")
    bits,pos=tlv(outer,pos,0x03)
    if pos!=len(outer) or len(bits)!=66 or bits[0]!=0 or bits[1]!=4: raise ValueError("expected uncompressed P-256 public point")
    raw=bits[2:]
    x=int.from_bytes(raw[:32],"big");y=int.from_bytes(raw[32:],"big")
    if x>=P or y>=P or (y*y-(x*x*x+A*x+B))%P: raise ValueError("public point is not on P-256")
    return der,raw

def render_header(raw,key_id,raw_hash):
    vals=lambda b:", ".join(f"0x{x:02x}" for x in b)
    return f"""#ifndef OPENREF_TRUST_ANCHOR_GENERATED_H\n#define OPENREF_TRUST_ANCHOR_GENERATED_H\n#include <stdint.h>\n#define OPENREF_TRUST_ANCHOR_KEY_ID_HEX \"{key_id.hex()}\"\n#define OPENREF_TRUST_ANCHOR_RAW_SHA256_HEX \"{raw_hash.hex()}\"\nstatic const uint8_t openref_trust_anchor_key_id[8] = {{{vals(key_id)}}};\nstatic const uint8_t openref_trust_anchor_public_key[64] = {{{vals(raw)}}};\n#endif\n"""

def main():
    p=argparse.ArgumentParser();p.add_argument("--public-key",type=Path,required=True);p.add_argument("--header",type=Path,required=True);p.add_argument("--manifest",type=Path,required=True);a=p.parse_args()
    der,raw=parse_pem(a.public_key.read_text(encoding="ascii"));rh=hashlib.sha256(raw).digest();kid=rh[:8]
    manifest={"schema":1,"algorithm":"ECDSA-P256-SHA256","key_id_hex":kid.hex(),"key_id_derivation":"first-8-bytes-of-SHA256(raw-x-concat-y)","public_key_format":"raw-X||Y-big-endian","public_key_sha256":rh.hex(),"spki_der_sha256":hashlib.sha256(der).hexdigest(),"source_file":a.public_key.name}
    a.header.parent.mkdir(parents=True,exist_ok=True);a.manifest.parent.mkdir(parents=True,exist_ok=True)
    a.header.write_text(render_header(raw,kid,rh),encoding="ascii",newline="\n");a.manifest.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="ascii",newline="\n")
    print(f"key_id={kid.hex()} raw_sha256={rh.hex()}")
if __name__=="__main__":
    try: main()
    except (OSError,ValueError) as e: raise SystemExit(f"error: {e}")
