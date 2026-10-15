"""Precise Telegram reports. Network delivery requires --send and env opt-in."""
import argparse
import hashlib
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit
from .tool import Invalid, read_json, write_json

ROOT = Path(__file__).resolve().parents[1]
OUTCOMES = {"rejected", "deferred", "migrated", "release-ready", "published"}
STATES = ROOT / "evidence/telegram"


def validate_report(report):
    if not isinstance(report, dict):
        raise Invalid("Report must be an object")
    for key in ("run_id", "date", "measurement_scope", "next_step"):
        if not isinstance(report.get(key), str) or not report[key].strip():
            raise Invalid(f"Report requires {key}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", report["run_id"]):
        raise Invalid("run_id must be a portable slug")
    duration = report.get("duration_seconds")
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration < 0:
        raise Invalid("Duration must be measured and nonnegative")
    for key in ("repositories_discovered", "skills_reviewed", "migrations_completed"):
        if type(report.get(key)) is not int or report[key] < 0:
            raise Invalid(f"{key} must be a nonnegative integer")
    items = report.get("skills")
    if not isinstance(items, list) or len(items) != report["skills_reviewed"]:
        raise Invalid("skills_reviewed differs from the distinct skill decisions")
    names, completed = set(), 0
    for item in items:
        for key in ("name", "usefulness", "audience", "impact", "impact_evidence", "changes", "validation", "limitations", "learning"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise Invalid(f"Skill report requires {key}")
        if item["name"] in names:
            raise Invalid("Duplicate skill decision")
        names.add(item["name"])
        if item.get("outcome") not in OUTCOMES:
            raise Invalid("Unknown outcome; publication cannot be inferred")
        completed += item["outcome"] in {"migrated", "release-ready", "published"}
        if item["outcome"] == "published":
            publication = item.get("publication", {})
            repo = publication.get("repository_url", "")
            if not re.fullmatch(r"https://github[.]com/gkmraju/codex-skill-[a-z0-9-]+", repo):
                raise Invalid("Published outcome requires an individual public repository URL")
            if not re.fullmatch(r"[a-f0-9]{40}", publication.get("commit_sha", "")):
                raise Invalid("Published outcome requires the actual pushed commit")
            if publication.get("ci_conclusion") != "success" or not re.fullmatch(re.escape(repo) + r"/actions/runs/\d+", publication.get("ci_url", "")):
                raise Invalid("Published outcome requires completed successful CI evidence")
        if not isinstance(item.get("links"), list) or not item["links"]:
            raise Invalid("Every decision requires inspectable links")
        for link in item["links"]:
            parsed = urlsplit(link["url"])
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
                raise Invalid("Report links must use public HTTPS URLs")
            if not isinstance(link.get("label"), str) or not link["label"].strip():
                raise Invalid("Links need labels")
    if completed != report["migrations_completed"]:
        raise Invalid("Migration count differs from the recorded outcomes")


def render(report):
    """Keep outward messages concise; retain full evidence in the JSON report."""
    validate_report(report)
    def brief(value, limit=150):
        value = " ".join(str(value).split())
        if len(value) > limit:
            value = value[:limit - 3].rsplit(" ", 1)[0] + "..."
        return html.escape(value, quote=True)
    minutes, seconds = divmod(round(report["duration_seconds"]), 60)
    published = sum(x["outcome"] == "published" for x in report["skills"])
    lines = ["\U0001f9e9 <b>CODEX SKILL LAB</b> \u00b7 " + brief(report["date"], 45),
             f"<b>{published} published</b> \u00b7 {report['skills_reviewed']} checked \u00b7 {minutes}m {seconds}s",
             "<i>" + brief(report["measurement_scope"], 65) + "</i>"]
    rank = {"published": 4, "release-ready": 3, "migrated": 2, "deferred": 1, "rejected": 0}
    ordered = sorted(report["skills"], key=lambda x: rank[x["outcome"]], reverse=True)
    if ordered:
        item = ordered[0]
        label = "PUBLISHED" if item["outcome"] == "published" else "UNFINISHED" if item["outcome"] != "rejected" else "REJECTED"
        lines += ["", f"<b>{brief(item['name'], 70)}</b> \u00b7 {label}",
                  brief(item["usefulness"], 110) + " For " + brief(item["audience"], 70),
                  "\U0001f9ea " + brief(item["validation"], 100)]
        if item["outcome"] == "published":
            lines += ["Expected benefit: " + brief(item["impact"], 100),
                      '<a href="' + html.escape(item["publication"]["repository_url"], quote=True) + '">Get the skill</a>']
        else:
            lines += ["\U0001f6a7 Not release-ready. " + brief(item["limitations"], 110)]
            source = item["links"][0]
            lines.append('<a href="' + html.escape(source["url"], quote=True) + '">' + brief(source["label"], 45) + "</a>")
    manual = report.get("manual_intervention")
    if manual and not ordered:
        row = manual.get("csv_row")
        lines += ["", "\U0001f6a7 <b>Manual intervention</b>",
                  (f"CSV row {row}: " if row else "") + brief(manual["name"], 80),
                  brief(manual["reason"], 220)]
        if manual.get("repository"):
            lines.append('<a href="' + html.escape(manual["repository"], quote=True) + '">Source repository</a>')
    if not published:
        lines += ["\u27a1 " + brief(report["next_step"], 100)]
    message = "\n".join(lines)
    parsed = html.unescape(re.sub(r"<[^>]+>", "", message))
    if len(parsed) > 1800:
        raise Invalid("Compact message is too long; reduce the reported summary")
    return message


def preview(message):
    return """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Codex Skill Lab - Telegram report preview</title>
<style>
*{box-sizing:border-box}body{margin:0;padding:36px 16px;background:#e5edf4;color:#182637;font:15px/1.65 system-ui,sans-serif}
main{max-width:650px;margin:auto}.label{color:#5b6e82;font-size:12px;letter-spacing:.13em;margin:0 0 18px}
article{background:white;border-radius:22px 22px 22px 4px;padding:28px 30px;box-shadow:0 12px 36px #19344d12;border-top:5px solid #2788c8}
b{color:#123d60}code{font-size:11px;background:#e9f3fb;color:#176696;padding:4px 7px;border-radius:6px}
a{color:#1c7fbb;text-decoration:none}i{color:#677b8d;font-size:13px}footer{font-size:12px;color:#65778a;padding:16px 4px}
@media(max-width:480px){body{padding:20px 12px}article{padding:22px 20px}}
</style><main><p class="label">CODEX SKILL LAB - MESSAGE PREVIEW</p><article>""" + message.replace("\n", "<br>\n") + """</article><footer>Preview only. Delivery is recorded separately after Telegram confirms success.</footer></main></html>"""


def load_env(path):
    values = {}
    if Path(path).exists():
        for raw in Path(path).read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise Invalid("Malformed Telegram env line")
            key, value = line.split("=", 1)
            value = value.strip()
            if len(value) > 1 and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1]
            values[key.strip()] = value
    for key in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "TELEGRAM_ENABLED"):
        if key in os.environ:
            values[key] = os.environ[key]
    return values


def send(message, run_id, settings, state_dir=STATES, opener=None):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", run_id):
        raise Invalid("Invalid run id")
    if settings.get("TELEGRAM_ENABLED", "").lower() != "true":
        raise Invalid("Telegram disabled; configure the destination and set TELEGRAM_ENABLED=true")
    token, chat = settings.get("TELEGRAM_BOT_TOKEN", ""), settings.get("TELEGRAM_CHAT_ID", "")
    if not re.fullmatch(r"\d{5,}:[A-Za-z0-9_-]{20,}", token) or not re.fullmatch(r"(?:-?\d+|@[A-Za-z][A-Za-z0-9_]{4,})", chat):
        raise Invalid("Configure a bot token and numeric chat ID or public @channel username")
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    receipt = state_dir / (run_id + ".json")
    destination = hashlib.sha256(chat.encode()).hexdigest()
    if receipt.exists() and read_json(receipt).get("destination_sha256") == destination:
        raise Invalid("A delivery attempt already exists; inspect its receipt before retrying")
    state = {"run_id": run_id, "destination_sha256": destination,
             "message_sha256": hashlib.sha256(message.encode()).hexdigest(), "status": "attempted"}
    write_json(receipt, state)
    payload = {"chat_id": chat, "text": message, "parse_mode": "HTML",
               "link_preview_options": {"is_disabled": True}}
    request = urllib.request.Request("https://api.telegram.org/bot" + token + "/sendMessage",
        data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with (opener or urllib.request.urlopen)(request, timeout=30) as response:
            result = json.load(response)
        if result.get("ok") is not True:
            raise Invalid("Telegram did not confirm delivery; inspect the destination before retrying")
        message_id = result["result"]["message_id"]
        state.update(status="confirmed", message_id=message_id)
        write_json(receipt, state)
        return message_id
    except urllib.error.HTTPError as e:
        raise Invalid(f"Telegram HTTP {e.code}; credentials and request URL withheld") from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError):
        raise Invalid("Delivery unconfirmed; do not automatically retry. Inspect the receipt and destination.") from None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--env", type=Path, default=ROOT / ".env.telegram")
    parser.add_argument("--preview", type=Path)
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = read_json(args.report)
        message = render(report)
        if args.preview:
            args.preview.parent.mkdir(parents=True, exist_ok=True)
            args.preview.write_text(preview(message), encoding="utf-8")
            print(f"Preview written: {args.preview}")
        elif not args.send:
            print(message)
        if args.send:
            print(f"Telegram confirmed message {send(message, report['run_id'], load_env(args.env))}")
        return 0
    except (Invalid, OSError, ValueError, TypeError, KeyError, AttributeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
