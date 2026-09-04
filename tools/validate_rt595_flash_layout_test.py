import copy, json, subprocess, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import validate_rt595_flash_layout as validator

LAYOUT=Path(__file__).parents[1]/"firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_flash_layout.json"
class LayoutTest(unittest.TestCase):
    def setUp(self): self.doc=json.loads(LAYOUT.read_text())
    def test_canonical(self): self.assertEqual(validator.validate_layout(self.doc)[0],[])
    def test_overlap(self):
        bad=copy.deepcopy(self.doc);bad["partitions"][2]["base"]="0x08040000"
        self.assertTrue(any("overlap" in e for e in validator.validate_layout(bad)[0]))
    def test_overflow(self):
        bad=copy.deepcopy(self.doc);bad["partitions"][-1]["size"]="0xffffffff"
        self.assertTrue(any("outside flash" in e for e in validator.validate_layout(bad)[0]))
    def test_map_escape(self):
        errors,parts=validator.validate_layout(self.doc)
        text=".text 0x0803fff0 0x40\n.data 0x20280000 0x10 load address 0x08001000\n"
        self.assertTrue(any("escapes" in e for e in validator.validate_map(text,self.doc,parts)))
    def test_ram_nobits_synthetic_load_is_ignored(self):
        errors,parts=validator.validate_layout(self.doc)
        text=".text 0x08001000 0x40\n.bss 0x20280000 0x90000 load address 0x0803fff0\n.heap 0x20500000 0x10000 load address 0x08050000\n"
        self.assertEqual(validator.validate_map(text,self.doc,parts),[])
    def test_initialized_ram_load_escape_is_rejected(self):
        errors,parts=validator.validate_layout(self.doc)
        text=".text 0x08001000 0x40\n.data 0x20280000 0x40 load address 0x0803fff0\n"
        self.assertTrue(any("escapes" in e for e in validator.validate_map(text,self.doc,parts)))
    def test_slot_link_override_accepts_only_selected_candidate(self):
        errors,parts=validator.validate_layout(self.doc)
        self.assertEqual(errors,[])
        slot_a=".interrupts 0x08041000 0x180\n.text 0x08041180 0x200\n"
        self.assertEqual(validator.validate_map(slot_a,self.doc,parts,"slot_a_image"),[])
        self.assertTrue(any("escapes slot_b_image" in e for e in
            validator.validate_map(slot_a,self.doc,parts,"slot_b_image")))
    def test_unknown_link_override_fails_closed(self):
        errors,parts=validator.validate_layout(self.doc)
        self.assertTrue(any("missing" in e for e in
            validator.validate_map(".text 0x08041000 0x20\n",self.doc,parts,"typo")))
    def test_cli_report_is_hash_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            report=Path(directory)/"report.json"
            result=subprocess.run([sys.executable,str(Path(validator.__file__)),str(LAYOUT),"--report",str(report)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            doc=json.loads(report.read_text())
            self.assertEqual(doc["status"],"passed")
            self.assertEqual(doc["layout"]["bytes"],LAYOUT.stat().st_size)
            self.assertEqual(len(doc["layout"]["sha256"]),64)
if __name__=="__main__": unittest.main()
