"""Balanced crossed variable Gauge R&R, retained interaction, Python standard library."""
import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import sys

class StudyError(ValueError):
    pass

def number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise StudyError(label + " must be a finite number")
    try:
        value = float(value)
    except (ValueError, OverflowError):
        raise StudyError(label + " must be a finite number")
    if not math.isfinite(value):
        raise StudyError(label + " must be a finite number")
    return value

def square(value):
    if 0 < abs(value) < 1e-140:
        raise StudyError("Nonzero ANOVA residual below supported numerical scale; rescale units")
    return value * value

def analyze(data):
    if not isinstance(data, dict):
        raise StudyError("Input must be an object")
    if data.get("attribute_study"):
        raise StudyError("Attribute studies are unsupported; provide variable measurements only")
    rows = data.get("raw_data")
    if not isinstance(rows, list) or not rows or len(rows) > 100000:
        raise StudyError("raw_data must contain 1 to 100000 measurements")
    cells = {}
    original_by_center = {}
    parts, operators, trials = set(), set(), set()
    origin = None
    for row in rows:
        if not isinstance(row, dict):
            raise StudyError("Each measurement must be an object")
        part, operator, trial = row.get("part_id"), row.get("operator"), row.get("trial")
        if any(not isinstance(x, str) or not x.strip() or len(x) > 200 for x in (part, operator)):
            raise StudyError("part_id and operator must be nonempty strings of at most 200 characters")
        if type(trial) is not int or trial < 1:
            raise StudyError("trial must be a positive integer")
        value = number(row.get("measurement_value"), "measurement_value")
        if origin is None:
            origin = value
        centered = value - origin
        if not math.isfinite(centered) or abs(centered) > 1e140:
            raise StudyError("Measurement range exceeds supported numerical scale")
        if centered in original_by_center and original_by_center[centered] != value:
            raise StudyError("Centering loses distinct measurements; rescale or recenter input units")
        original_by_center[centered] = value
        key = (part, operator, trial)
        if key in cells:
            raise StudyError("Duplicate part/operator/trial measurement")
        cells[key] = centered
        parts.add(part); operators.add(operator); trials.add(trial)
    spread = max(abs(value) for value in cells.values())
    if 0 < spread < 1e-140:
        raise StudyError("Measurement range below supported numerical scale; rescale units")
    parts, operators = sorted(parts), sorted(operators)
    p, o, r = len(parts), len(operators), len(trials)
    if min(p, o, r) < 2:
        raise StudyError("Need at least 2 parts, 2 operators and 2 trials")
    if trials != set(range(1, r + 1)) or len(cells) != p * o * r:
        raise StudyError("Study must be balanced and crossed with trials 1..num_trials in every cell")
    design = data.get("study_design", {})
    if not isinstance(design, dict):
        raise StudyError("study_design must be an object")
    for key, observed in (("num_parts", p), ("num_operators", o), ("num_trials", r)):
        if key in design and (type(design[key]) is not int or design[key] != observed):
            raise StudyError("Declared " + key + " does not match observed data")
    gage = data.get("gage", {})
    if not isinstance(gage, dict) or any(not isinstance(v, (str, int, float, bool, type(None), list)) for v in gage.values()):
        raise StudyError("gage must be a descriptive metadata object")
    tolerance = data.get("tolerance")
    width = None
    if tolerance is not None:
        if not isinstance(tolerance, dict) or set(tolerance) != {"lower", "upper"}:
            raise StudyError("tolerance requires exactly lower and upper limits")
        lower = number(tolerance["lower"], "lower limit"); upper = number(tolerance["upper"], "upper limit")
        width = upper - lower
        if not math.isfinite(width) or width <= 0:
            raise StudyError("Upper tolerance limit must exceed lower limit with finite width")
    average = lambda values: math.fsum(values) / len(values)
    grand = average(list(cells.values()))
    cm = {(i,j): average([cells[i,j,t] for t in range(1,r+1)]) for i in parts for j in operators}
    pm = {i: average([cm[i,j] for j in operators]) for i in parts}
    om = {j: average([cm[i,j] for i in parts]) for j in operators}
    ss = {
        "part": o*r*math.fsum(square(pm[i]-grand) for i in parts),
        "operator": p*r*math.fsum(square(om[j]-grand) for j in operators),
        "interaction": r*math.fsum(square(cm[i,j]-pm[i]-om[j]+grand) for i in parts for j in operators),
        "repeatability": math.fsum(square(v-cm[i,j]) for (i,j,t),v in cells.items()),
    }
    total_ss = math.fsum(square(v-grand) for v in cells.values())
    if not math.isclose(math.fsum(ss.values()), total_ss, rel_tol=1e-10, abs_tol=1e-20):
        raise StudyError("ANOVA decomposition failed numerical reconciliation")
    df = {"part":p-1,"operator":o-1,"interaction":(p-1)*(o-1),"repeatability":p*o*(r-1)}
    ms = {key:ss[key]/df[key] for key in ss}
    raw = {"repeatability":ms["repeatability"],"operator":(ms["operator"]-ms["interaction"])/(p*r),
           "interaction":(ms["interaction"]-ms["repeatability"])/r,"part":(ms["part"]-ms["interaction"])/(o*r)}
    variance = {key:max(value,0.0) for key,value in raw.items()}
    variance["reproducibility"] = variance["operator"]+variance["interaction"]
    variance["gage_rr"] = variance["repeatability"]+variance["reproducibility"]
    variance["total"] = variance["gage_rr"]+variance["part"]
    warnings = [key+" variance estimate was negative and clipped to zero" for key,value in raw.items() if value < 0]
    if variance["total"] == 0:
        warnings.append("All observations are constant; percentage variation is undefined")
    if variance["gage_rr"] == 0:
        warnings.append("Estimated gage R&R is zero; ndc is undefined rather than infinite")
    components = {}
    total_sd = math.sqrt(variance["total"])
    for key,value in variance.items():
        sd = math.sqrt(value)
        components[key] = {"variance":value,"standard_deviation":sd,"study_variation":6*sd,
            "percent_contribution":100*(value/variance["total"]) if variance["total"] else None,
            "percent_study_variation":100*(sd/total_sd) if total_sd else None,
            "percent_tolerance":100*(6*sd/width) if width else None}
    ndc = None
    if variance["gage_rr"] > 0:
        ratio = 1.41 * (math.sqrt(variance["part"]) / math.sqrt(variance["gage_rr"]))
        if math.isfinite(ratio):
            ndc = max(1, math.floor(ratio))
        else:
            warnings.append("ndc ratio exceeds numerical range")
    result = {"schema_version":1,"method":"balanced crossed random-effects ANOVA; interaction retained",
        "gage":gage,"design":{"parts":p,"operators":o,"trials":r,"measurements":len(rows)},
        "anova":{key:{"sum_of_squares":ss[key],"degrees_of_freedom":df[key],"mean_square":ms[key]} for key in ss},
        "total_sum_of_squares":total_ss,"raw_variance_estimates":raw,"components":components,"ndc":ndc,
        "tolerance":tolerance,"warnings":warnings,
        "limitations":["No interaction pooling, significance tests or confidence intervals.",
            "No attribute agreement, bias, linearity, calibration certification or automatic acceptance decision.",
            "Representative parts, independent repetitions and randomized measurement order require study-owner review.",
            "Results depend on measurement units, study sampling and random-effects assumptions."]}
    # Require all output numbers to be JSON finite even under extreme tolerance/ratios.
    try:
        json.dumps(result, allow_nan=False)
    except ValueError:
        raise StudyError("Result exceeds supported numerical scale")
    return result

def render(result):
    esc = lambda value: html.escape(str(value), quote=True)
    fmt = lambda value: "Undefined" if value is None else format(value, ".6g")
    rows = "".join("<tr><th scope='row'>"+esc(k.replace("_"," ").title())+"</th>"+
        "".join("<td>"+fmt(v[field])+"</td>" for field in ("variance","standard_deviation","percent_study_variation","percent_tolerance"))+"</tr>"
        for k,v in result["components"].items())
    warnings = "".join("<li>"+esc(x)+"</li>" for x in result["warnings"])
    limits = "".join("<li>"+esc(x)+"</li>" for x in result["limitations"])
    gage = esc(json.dumps(result["gage"],ensure_ascii=False))
    design = result["design"]
    return """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Gauge R&amp;R study</title><style>
body{font:17px/1.5 system-ui,sans-serif;background:#f3f6fc;color:#17243b;margin:0}
main{max-width:1000px;margin:40px auto;padding:28px;background:white;border-radius:18px;box-shadow:0 8px 32px #192b4512}
h1{font-size:2.2rem;margin:.3em 0}h2{margin-top:1.5em}.eyebrow{color:#3153a5;font-weight:700}
.cards{display:flex;gap:18px;flex-wrap:wrap}.card{background:#eef3fd;border-radius:12px;padding:16px;flex:1;min-width:150px}
strong{display:block;font-size:1.6rem}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:.94rem}
th,td{text-align:left;padding:12px;border-bottom:1px solid #d7dfed}thead{background:#ecf1fa}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f6fc;padding:12px}li{margin:.5em 0}
@media(max-width:600px){main{margin:10px;padding:16px}h1{font-size:1.7rem}}
</style><main><div class="eyebrow">MEASUREMENT SYSTEM ANALYSIS</div><h1>Gauge R&amp;R study</h1>
<p>Balanced crossed ANOVA with part × operator interaction retained. Study variation uses 6 standard deviations.</p>
<div class="cards"><div class="card">Measurements<strong>"""+str(design["measurements"])+"""</strong></div>
<div class="card">% study variation · Gage R&amp;R<strong>"""+fmt(result["components"]["gage_rr"]["percent_study_variation"])+"""</strong></div>
<div class="card">Distinct categories<strong>"""+esc(result["ndc"] if result["ndc"] is not None else "Undefined")+"""</strong></div></div>
<h2>Study design</h2><p>"""+f'{design["parts"]} parts · {design["operators"]} operators · {design["trials"]} repetitions'+"""</p>
<h2>Variance results</h2><div class="scroll"><table><caption>Variance components; aggregate rows overlap. % study variation does not sum to 100.</caption>
<thead><tr><th scope="col">Source</th><th scope="col">Variance</th><th scope="col">Std. deviation</th><th scope="col">% study variation</th><th scope="col">% tolerance</th></tr></thead><tbody>"""+rows+"""</tbody></table></div>
<h2>Warnings</h2><ul>"""+(warnings or "<li>No numerical warnings.</li>")+"""</ul>
<h2>Interpretation boundary</h2><ul>"""+limits+"""</ul><p>These results describe this study. The responsible study owner decides suitability for the intended process.</p>
<details><summary>Gage metadata supplied by study owner</summary><pre>"""+gage+"""</pre></details></main></html>"""

def unique_object(pairs):
    result = {}
    for key,value in pairs:
        if key in result:
            raise StudyError("Duplicate JSON key: "+key)
        result[key] = value
    return result

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True, help="A new directory; existing paths are refused")
    args = parser.parse_args(argv)
    try:
        raw = args.input.read_bytes()
        if len(raw) > 20_000_000:
            raise StudyError("Input exceeds 20 MB")
        data = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique_object)
        result = analyze(data)
        result["input_sha256"] = hashlib.sha256(raw).hexdigest()
        result["software_version"] = "0.1.0"
        encoded = json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n"
        document = render(result)
        args.output_dir.mkdir(parents=True,exist_ok=False)
        (args.output_dir/"results.json").write_text(encoded,encoding="utf-8")
        (args.output_dir/"report.html").write_text(document,encoding="utf-8")
        print("Validated study; wrote results.json and report.html")
        return 0
    except (StudyError, OSError, UnicodeError, json.JSONDecodeError, OverflowError) as exc:
        print("ERROR: "+str(exc),file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
