import hashlib, json, struct, sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import pytest

TOOLS = Path(__file__).parents[1]; sys.path.insert(0, str(TOOLS))
import assemble_rt595_release_bundle as bundle
from package_rt595_signed_slot import create_package
from provision_rt595_trust_anchor import main as provision_main
from test_package_rt595_signed_slot import _keys

def _image(path, base, tail=b"image"):
    path.write_bytes(struct.pack("<II", 0x20020000, base + 9) + tail)

def _fixture(root):
    root.mkdir(parents=True, exist_ok=True)
    private, public = _keys(root)
    layout = root / "layout.json"
    layout.write_text(json.dumps({"flash_base":"0x08000000","flash_size":"0x200000","erase_bytes":"0x1000",
      "linked_image_partition":"bootstrap_xip","partitions":[
      {"name":"bootstrap_xip","role":"bootloader","base":"0x08000000","size":"0x40000","writable_by_application":False},
      {"name":"slot_a_manifest","role":"signed_manifest_commit","slot":"A","base":"0x08040000","size":"0x1000","writable_by_application":True},
      {"name":"slot_a_image","role":"candidate_image","slot":"A","base":"0x08041000","size":"0xbf000","writable_by_application":True},
      {"name":"slot_b_manifest","role":"signed_manifest_commit","slot":"B","base":"0x08100000","size":"0x1000","writable_by_application":True},
      {"name":"slot_b_image","role":"candidate_image","slot":"B","base":"0x08101000","size":"0xbf000","writable_by_application":True},
      {"name":"reserved","role":"reserved","base":"0x081c0000","size":"0x3c000","writable_by_application":False},
      {"name":"config_a","role":"configuration_record","base":"0x081fc000","size":"0x1000","writable_by_application":True},
      {"name":"config_b","role":"configuration_record","base":"0x081fd000","size":"0x1000","writable_by_application":True},
      {"name":"boot_state_a","role":"boot_state_record","base":"0x081fe000","size":"0x1000","writable_by_application":False},
      {"name":"boot_state_b","role":"boot_state_record","base":"0x081ff000","size":"0x1000","writable_by_application":False}]}))
    bootstrap=root/"bootstrap.bin"; app=root/"app.bin"
    _image(bootstrap,0x08000000); _image(app,0x08041000,b"application")
    package=root/"slot.bin"
    create_package(SimpleNamespace(layout=layout,slot="A",image=app,private_key=private,
      hardware_id="0x59500001",image_version="7",minimum_bootloader_version="1",
      maximum_bootloader_version="3",antirollback_floor="7",confirmed_image_version="6",
      release_id="00112233-4455-6677-8899-aabbccddeeff",output=package,metadata=None))
    trust=root/"trust.json"; header=root/"trust.h"; old=sys.argv
    try:
        sys.argv=["provision","--public-key",str(public),"--header",str(header),"--manifest",str(trust)]; provision_main()
    finally: sys.argv=old
    boot_report=root/"boot-report.txt"; app_report=root/"app-report.txt"
    layout_record={"path":layout.name,"bytes":layout.stat().st_size,"sha256":hashlib.sha256(layout.read_bytes()).hexdigest()}
    for report,name in ((boot_report,"bootstrap.map"),(app_report,"application.map")):
        report.write_text(json.dumps({"schema":"openref.rt595-flash-layout-validation.v1","status":"passed",
          "errors":[],"layout":layout_record,"map":{"path":name,"bytes":100,"sha256":"1"*64}}))
    critical=[bootstrap,app,package,package.with_suffix(".bin.json"),layout,boot_report,app_report,trust,public]; provenance=root/"provenance.json"
    provenance.write_text(json.dumps({"schema":"openref.release-provenance.v1",
      "artifacts":[{"role":f"r{i}","sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for i,p in enumerate(critical)],
      "claims":{"release_ready":False}}))
    return {"bootstrap_binary":bootstrap,"application_binary":app,"signed_slot_package":package,
      "signed_slot_metadata":package.with_suffix(".bin.json"),"flash_layout":layout,
      "bootstrap_layout_report":boot_report,"application_layout_report":app_report,
      "trust_anchor_manifest":trust,"trust_anchor_public_key":public,"release_provenance":provenance}

def _args(paths, output, review=None): return SimpleNamespace(**paths,output=output,reviewed_evidence=review)

def test_assemble_verify_fail_closed_without_review(tmp_path):
    paths=_fixture(tmp_path); output=tmp_path/"release"; doc=bundle.assemble(_args(paths,output))
    assert doc["release_ready"] is False
    assert all("private" not in p.name.lower() for p in output.iterdir())
    assert bundle.verify(output)["subject"]==doc["subject"]

def test_exact_independent_review_promotes(tmp_path):
    paths=_fixture(tmp_path); subject=bundle.validate_files(paths)["subject"]; review=tmp_path/"review.json"
    review.write_text(json.dumps({"schema":bundle.REVIEW_SCHEMA,"verdict":"approved",
      "reviewer":{"name":"Independent Reviewer","organization":"External Lab","independent":True},
      "reviewed_at":datetime.now(timezone.utc).isoformat(),"bundle_subject":subject}))
    output=tmp_path/"release"; assert bundle.assemble(_args(paths,output,review))["release_ready"] is True
    assert bundle.verify(output)["release_ready"] is True

@pytest.mark.parametrize("role",["application_binary","signed_slot_package","trust_anchor_manifest","release_provenance"])
def test_verify_rejects_tamper(tmp_path,role):
    paths=_fixture(tmp_path); output=tmp_path/"release"; bundle.assemble(_args(paths,output))
    target=output/bundle.REQUIRED[role]; target.write_bytes(target.read_bytes()+b"tamper")
    with pytest.raises(ValueError,match="hash/size"): bundle.verify(output)

def test_rejects_address_and_provenance_mismatch(tmp_path):
    paths=_fixture(tmp_path); metadata=json.loads(paths["signed_slot_metadata"].read_text())
    metadata["image_base"]="0x08101000"; paths["signed_slot_metadata"].write_text(json.dumps(metadata))
    with pytest.raises(ValueError,match="image_base"): bundle.validate_files(paths)
    paths=_fixture(tmp_path/"again"); provenance=json.loads(paths["release_provenance"].read_text())
    provenance["artifacts"]=[]; paths["release_provenance"].write_text(json.dumps(provenance))
    with pytest.raises(ValueError,match="provenance"): bundle.validate_files(paths)

def test_rejects_wrong_review_and_existing_output(tmp_path):
    paths=_fixture(tmp_path); subject=bundle.validate_files(paths)["subject"]; subject["image_version"]+=1
    review=tmp_path/"review.json"; review.write_text(json.dumps({"schema":bundle.REVIEW_SCHEMA,"verdict":"approved",
      "reviewer":{"name":"R","organization":"Lab","independent":True},
      "reviewed_at":datetime.now(timezone.utc).isoformat(),"bundle_subject":subject}))
    with pytest.raises(ValueError,match="exact release"): bundle.validate_files(paths,review)
    output=tmp_path/"exists"; output.mkdir()
    with pytest.raises(ValueError,match="already exists"): bundle.assemble(_args(paths,output))
