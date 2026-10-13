import copy
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("analyzer", SKILL/"scripts/analyze_msa.py")
analyzer = importlib.util.module_from_spec(spec); spec.loader.exec_module(analyzer)
def sample():
    return json.loads((SKILL/"examples/balanced-study.json").read_text())

class AnalysisTests(unittest.TestCase):
    def test_hand_derived_anova(self):
        result = analyzer.analyze(sample())
        for key,ss,df,ms in [("part",800,2,400),("operator",12,1,12),("interaction",24,2,12),("repeatability",3,6,.5)]:
            self.assertAlmostEqual(result["anova"][key]["sum_of_squares"],ss)
            self.assertEqual(result["anova"][key]["degrees_of_freedom"],df)
            self.assertAlmostEqual(result["anova"][key]["mean_square"],ms)
        self.assertAlmostEqual(result["total_sum_of_squares"],839)
        for key,var in {"part":97,"operator":0,"interaction":5.75,"repeatability":.5,"gage_rr":6.25,"total":103.25}.items():
            self.assertAlmostEqual(result["components"][key]["variance"],var)
        self.assertEqual(result["ndc"],5)
        self.assertAlmostEqual(result["components"]["gage_rr"]["percent_tolerance"],37.5)
        self.assertAlmostEqual(result["components"]["gage_rr"]["percent_study_variation"],100*2.5/math.sqrt(103.25))
    def test_scale_and_offset_invariance(self):
        data = sample(); baseline = analyzer.analyze(data)
        for row in data["raw_data"]:
            row["measurement_value"] = row["measurement_value"]*2+10000
        data["tolerance"] = {"lower":9960,"upper":10040}
        result = analyzer.analyze(data)
        self.assertEqual(result["ndc"],baseline["ndc"])
        for key in result["components"]:
            self.assertAlmostEqual(result["components"][key]["variance"],4*baseline["components"][key]["variance"])
            self.assertAlmostEqual(result["components"][key]["percent_tolerance"],baseline["components"][key]["percent_tolerance"])
    def test_row_order_invariance(self):
        data=sample(); expected=analyzer.analyze(data)
        data["raw_data"].reverse()
        self.assertEqual(analyzer.analyze(data)["components"],expected["components"])

    def test_tiny_scale_is_rejected_instead_of_false_constant(self):
        data=sample()
        for row in data["raw_data"]: row["measurement_value"] *= 1e-170
        data["tolerance"]={"lower":-20e-170,"upper":20e-170}
        with self.assertRaisesRegex(analyzer.StudyError, "rescale units"):
            analyzer.analyze(data)

    def test_mixed_scale_centering_loss_is_rejected(self):
        data=sample()
        for row in data["raw_data"]:
            row["measurement_value"] = {"P1":-10,"P3":10}.get(row["part_id"], (-1 if row["trial"]==1 else 1)*1e-100)
        with self.assertRaisesRegex(analyzer.StudyError, "loses distinct"):
            analyzer.analyze(data)

    def test_local_residual_underflow_is_rejected(self):
        data=sample()
        for row in data["raw_data"]:
            row["measurement_value"]={"P1":-10,"P3":10}.get(row["part_id"],(-1 if row["trial"]==1 else 1)*1e-170)
        data["raw_data"].sort(key=lambda row:row["part_id"]!="P2")
        with self.assertRaisesRegex(analyzer.StudyError,"ANOVA residual"):
            analyzer.analyze(data)

    def test_constant_study(self):
        data=sample()
        for row in data["raw_data"]: row["measurement_value"]=2
        result=analyzer.analyze(data)
        self.assertIsNone(result["ndc"])
        self.assertIsNone(result["components"]["total"]["percent_study_variation"])
        json.dumps(result,allow_nan=False)
    def test_zero_gage_variance(self):
        data=sample()
        for row in data["raw_data"]: row["measurement_value"]=int(row["part_id"][1:])
        result=analyzer.analyze(data)
        self.assertEqual(result["components"]["gage_rr"]["variance"],0)
        self.assertIsNone(result["ndc"])
    def test_negative_interaction_clipped(self):
        data={"raw_data":[{"part_id":str(i),"operator":str(j),"trial":t,"measurement_value":i+j+e}
                         for i in [-1,1] for j in [-.25,.25] for t,e in enumerate([-.1,.1],1)]}
        result=analyzer.analyze(data)
        self.assertAlmostEqual(result["components"]["part"]["variance"],2)
        self.assertAlmostEqual(result["components"]["operator"]["variance"],.125)
        self.assertAlmostEqual(result["components"]["repeatability"]["variance"],.02)
        self.assertLess(result["raw_variance_estimates"]["interaction"],0)
        self.assertEqual(result["components"]["interaction"]["variance"],0)
        self.assertTrue(result["warnings"])
    def test_minimum_ndc_one(self):
        data=sample()
        for row in data["raw_data"]: row["measurement_value"]=row["trial"]*100
        self.assertEqual(analyzer.analyze(data)["ndc"],1)
    def test_invalid_measurements(self):
        for value in [None,True,"3",float("nan"),float("inf"),1e308]:
            with self.subTest(value=value):
                data=sample();data["raw_data"][0]["measurement_value"]=value
                with self.assertRaises(analyzer.StudyError): analyzer.analyze(data)
    def test_incomplete_and_duplicate_design(self):
        for change in ["missing","duplicate","trial","counts","single"]:
            with self.subTest(change=change):
                data=sample()
                if change=="missing": data["raw_data"].pop()
                if change=="duplicate": data["raw_data"].append(copy.deepcopy(data["raw_data"][0]))
                if change=="trial": data["raw_data"][0]["trial"]=3
                if change=="counts": data["study_design"]["num_parts"]=10
                if change=="single": data["raw_data"]=[r for r in data["raw_data"] if r["operator"]=="A"]
                with self.assertRaises(analyzer.StudyError): analyzer.analyze(data)
    def test_invalid_tolerance(self):
        for tolerance in [{"lower":0},{"lower":2,"upper":1},{"lower":True,"upper":5},{"lower":0,"upper":float("inf")},[]]:
            with self.subTest(tolerance=tolerance):
                data=sample();data["tolerance"]=tolerance
                with self.assertRaises(analyzer.StudyError): analyzer.analyze(data)
    def test_unsupported_attribute_study(self):
        data=sample();data["attribute_study"]=[{"part":"P1","pass":True}]
        with self.assertRaises(analyzer.StudyError): analyzer.analyze(data)
    def test_optional_tolerance(self):
        data=sample();del data["tolerance"]
        self.assertIsNone(analyzer.analyze(data)["components"]["gage_rr"]["percent_tolerance"])
    def test_html_escapes_metadata(self):
        data=sample();data["gage"]["id"]="<script>alert(1)</script>"
        output=analyzer.render(analyzer.analyze(data))
        self.assertNotIn("<script>",output);self.assertIn("&lt;script&gt;",output)
    def test_cli_reports_and_overwrite_refusal(self):
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary)/"results"
            command=[sys.executable,"-B",str(SKILL/"scripts/analyze_msa.py"),str(SKILL/"examples/balanced-study.json"),"--output-dir",str(out)]
            first=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(first.returncode,0,first.stderr)
            self.assertEqual(json.loads((out/"results.json").read_text())["ndc"],5)
            content=(out/"results.json").read_bytes()
            self.assertEqual(subprocess.run(command,capture_output=True).returncode,2)
            self.assertEqual((out/"results.json").read_bytes(),content)
    def test_cli_invalid_input_creates_no_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            source=Path(temporary)/"bad.json";out=Path(temporary)/"report"
            for content in ['{"raw_data": [], "raw_data": []}','{"raw_data": []}','not-json']:
                source.write_text(content)
                proc=subprocess.run([sys.executable,"-B",str(SKILL/"scripts/analyze_msa.py"),str(source),"--output-dir",str(out)],capture_output=True)
                self.assertEqual(proc.returncode,2);self.assertFalse(out.exists())

if __name__=="__main__": unittest.main()
