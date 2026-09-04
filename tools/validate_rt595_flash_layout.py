#!/usr/bin/env python3
import argparse, hashlib, json, re, sys
from pathlib import Path

def number(value):
    if isinstance(value, int): return value
    if isinstance(value, str): return int(value, 0)
    raise ValueError(f"not an integer: {value!r}")

def validate_layout(doc):
    errors=[]; base=number(doc["flash_base"]); size=number(doc["flash_size"])
    erase=number(doc["erase_bytes"]); end=base+size; parts=[]; names=set()
    if size <= 0 or erase <= 0 or base > 0xffffffff-size: errors.append("invalid flash range")
    for raw in doc["partitions"]:
        name=raw["name"]; start=number(raw["base"]); length=number(raw["size"])
        if name in names: errors.append(f"duplicate partition {name}")
        names.add(name)
        if length <= 0 or start % erase or length % erase: errors.append(f"{name}: not erase aligned")
        if start < base or start > end or length > end-start: errors.append(f"{name}: outside flash")
        parts.append((start,start+length,name,raw))
    parts.sort()
    for left,right in zip(parts,parts[1:]):
        if left[1] > right[0]: errors.append(f"overlap: {left[2]} and {right[2]}")
        if left[1] < right[0]: errors.append(f"unassigned gap: 0x{left[1]:08x}..0x{right[0]:08x}")
    if parts and (parts[0][0] != base or parts[-1][1] != end): errors.append("partitions do not cover flash exactly")
    for slot in ("A","B"):
        manifests=[p for p in parts if p[3].get("slot")==slot and p[3]["role"]=="signed_manifest_commit"]
        images=[p for p in parts if p[3].get("slot")==slot and p[3]["role"]=="candidate_image"]
        if len(manifests)!=1 or len(images)!=1 or (manifests and images and manifests[0][1]!=images[0][0]): errors.append(f"slot {slot}: requires adjacent manifest then image")
        if manifests and not manifests[0][3].get("writable_by_application"): errors.append(f"slot {slot}: manifest commit must be writable by authenticated stager")
    images=[p for p in parts if p[3]["role"]=="candidate_image"]
    if len(images)!=2 or (len(images)==2 and images[0][1]-images[0][0] != images[1][1]-images[1][0]): errors.append("candidate image slots must have equal capacity")
    if len([p for p in parts if p[3]["role"]=="configuration_record"])!=2: errors.append("requires two configuration sectors")
    if len([p for p in parts if p[3]["role"]=="boot_state_record"])!=2: errors.append("requires two boot-state sectors")
    if doc.get("linked_image_partition") not in names: errors.append("linked_image_partition is missing")
    elif next(p for p in parts if p[2]==doc["linked_image_partition"])[3].get("writable_by_application"): errors.append("linked XIP partition must not be application-writable")
    return errors,parts

SECTION=re.compile(r"^\.(\S+)\s+0x([0-9a-fA-F]+)\s+0x([0-9a-fA-F]+)(?:\s+load address 0x([0-9a-fA-F]+))?")
NOBITS_PREFIXES=("bss","heap","stack","noinit","uninit","tbss")
def validate_map(text, doc, parts, linked_partition=None):
    errors=[]; flash=number(doc["flash_base"]); flash_end=flash+number(doc["flash_size"])
    target_name=linked_partition or doc["linked_image_partition"]
    matches=[p for p in parts if p[2]==target_name]
    if len(matches)!=1: return [f"linked partition {target_name!r} is missing"]
    target=matches[0]
    seen=0
    for line in text.splitlines():
        m=SECTION.match(line)
        if not m: continue
        length=int(m.group(3),16)
        if not length: continue
        # GNU ld can print a synthetic load address for RAM reservations even
        # though NOBITS sections occupy no bytes in the flash image.
        section=m.group(1).lower()
        if section.startswith(NOBITS_PREFIXES): continue
        vma=int(m.group(2),16); load=int(m.group(4),16) if m.group(4) else vma
        for address,label in ((vma,"VMA"),(load,"load")):
            if flash <= address < flash_end:
                seen+=1
                if address < target[0] or length > target[1]-address:
                    errors.append(f"section .{m.group(1)} {label} 0x{address:08x}+0x{length:x} escapes {target[2]}")
    if not seen: errors.append("map contains no recognized flash-resident output sections")
    return errors

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("layout",type=Path); ap.add_argument("--map",dest="map_file",type=Path); ap.add_argument("--linked-partition"); ap.add_argument("--report",type=Path)
    args=ap.parse_args(); doc=json.loads(args.layout.read_text(encoding="utf-8")); errors,parts=validate_layout(doc)
    if args.map_file: errors += validate_map(args.map_file.read_text(encoding="utf-8",errors="replace"),doc,parts,args.linked_partition)
    if args.report:
        def record(path):
            data=path.read_bytes(); return {"path":path.name,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}
        report={"schema":"openref.rt595-flash-layout-validation.v1","status":"failed" if errors else "passed","errors":errors,"layout":record(args.layout)}
        if args.map_file: report["map"]=record(args.map_file)
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    if errors:
        for error in errors: print(f"ERROR: {error}",file=sys.stderr)
        return 1
    print(f"RT595 flash layout valid: {len(parts)} partitions" + ("; link map contained" if args.map_file else ""))
    return 0
if __name__=="__main__": raise SystemExit(main())
