"""Build the SYNTHETIC test documents (invented content, every page bannered as a fixture) by
printing HTML to PDF with a headless Chromium browser. They stand in for licensed documents the
tests cannot hold (a SemiAnalysis paid post, a Morgan Stanley report) and for a scanned page.
Never presented as research by any publisher.

    CHROMIUM="/path/to/chrome-or-brave" python make_fixtures.py <out_dir>

Needs Pillow (the scanned page's image). Not collected by pytest; the committed bytes are what
the tests read — regenerate only to change a fixture, then re-run the ingestion tests.
"""
import base64
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

BROWSER = os.environ.get("CHROMIUM", "/Applications/Brave Browser.app/Contents/MacOS/"
                                       "Brave Browser")
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
BANNER = ("<p><b>[SYNTHETIC TEST FIXTURE — invented content for automated tests; not "
          "research by any publisher]</b></p>")
CSS = ("<style>body{font-family:Helvetica,Arial,sans-serif;font-size:11pt;margin:2cm}"
       "h1{font-size:22pt}h2{font-size:15pt}table{border-collapse:collapse}"
       "td,th{border:1px solid #333;padding:4px 8px}.fn{font-size:8pt}"
       ".pb{page-break-before:always}</style>")

PREVIEW = [
    "Synthetic memory demand keeps rising as inference workloads scale across hyperscale "
    "clusters, and the operators we spoke with expect the tightness to persist into next year.",
    "Our synthetic channel checks point to HBM supply that stays allocated well ahead of "
    "shipments, with contract terms lengthening at every major supplier.",
]
FULL_MORE = [
    "Conventional DRAM contract prices are projected to rise 14% QoQ in 4Q26 in our synthetic "
    "model, the third consecutive quarterly increase.",
    "HBM shipments are projected to grow 35% YoY in 2026 as accelerator volumes ramp, while "
    "the share of HBM in total DRAM revenue climbs above one third.",
    "Server DRAM inventory at the hyperscalers fell to four weeks in 3Q26, the lowest level in "
    "our synthetic series, which leaves little buffer against further demand surprises.",
    "Memory makers' capital expenditure is projected to rise 20% in 2026, with most of the "
    "increase directed at advanced DRAM nodes and HBM packaging capacity.",
    "Spot prices for DDR5 modules rose 8% in September in our synthetic tracker, while module "
    "makers reported that hyperscale customers were placing orders two quarters ahead of need.",
    "We expect suppliers to keep capacity additions disciplined, because the last downturn left "
    "balance sheets stretched and investors rewarded restraint over share gains.",
    "The main risk to this view is a pause in accelerator deployments, which would release HBM "
    "capacity back into conventional DRAM and loosen the market within two quarters.",
]


def html_semianalysis_full() -> str:
    paras = "".join(f"<p>{p}</p>" for p in PREVIEW + FULL_MORE)
    return (f"<html><head><title>Synthetic Memory Note: Inference Keeps Memory Tight</title>"
            f"{CSS}</head><body>{BANNER}<h1>Synthetic Memory Note: Inference Keeps Memory "
            f"Tight</h1><p>By Synthetic Analyst One and Synthetic Analyst Two</p>"
            f"<p>September 28, 2026</p>{paras}</body></html>")


def html_ms_report() -> str:
    rows = "".join(f"<tr><td>{q}</td><td>{a}</td><td>{b}</td></tr>" for q, a, b in (
        ("1Q26", "$41.2bn", "38%"), ("2Q26", "$44.9bn", "39%"), ("3Q26", "$48.3bn", "41%"),
        ("4Q26E", "$52.0bn", "42%")))
    body = (
        "<p>We expect hyperscaler capital expenditure on AI data centres to rise 24% in 2027, "
        "led by power and cooling, as the synthetic survey of 40 operators shows budgets still "
        "expanding.</p>"
        "<p>Grid interconnection queues reached 2,600 GW in our synthetic dataset, and the median "
        "wait for a large-load connection lengthened to 48 months, which pushes operators "
        "towards on-site generation.<sup>1</sup></p>"
        "<h2>Exhibit 1: Synthetic AI capex by quarter</h2>"
        f"<table><tr><th>Quarter</th><th>Capex</th><th>AI share</th></tr>{rows}</table>"
        "<p>On-site gas turbine orders are projected to grow 30% in 2027 as operators bypass "
        "constrained grids, a shift we expect to benefit turbine and fuel-cell suppliers.</p>"
        "<p class='fn'>1 Synthetic interconnection data, compiled for this test fixture only.</p>")
    page2 = ("<div class='pb'></div><h2>Risks</h2><p>A slowdown in AI model adoption could "
             "reduce data-centre budgets by 15% from our base case in a synthetic downside "
             "scenario.</p>")
    return (f"<html><head><title>Synthetic Utilities Note: AI Power Demand</title>{CSS}</head>"
            f"<body>{BANNER}<h1>Synthetic Utilities Note: AI Power Demand Moves On-Site</h1>"
            f"<p>Synthetic Strategist, Equity Research</p><p>October 1, 2026</p>{body}{page2}"
            f"</body></html>")


def html_scanned() -> str:
    img = Image.new("RGB", (1200, 1600), "white")
    d = ImageDraw.Draw(img)
    for i in range(40):
        d.rectangle([80, 80 + i * 36, 1100, 96 + i * 36], fill=(60, 60, 60))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    page1 = ("<h1>Synthetic Scanned Note</h1><p>Synthetic text page: memory contract prices "
             "rose 9% QoQ in 3Q26 according to this invented fixture, which exists only to test "
             "how a document with a scanned page is flagged and never silently dropped.</p>"
             "<p>October 3, 2026</p>")
    page2 = f"<div class='pb'></div><img src='data:image/png;base64,{b64}' style='width:16cm'>"
    return f"<html><head>{CSS}</head><body>{BANNER}{page1}{page2}</body></html>"


def html_undated() -> str:
    paras = "".join(f"<p>{p}</p>" for p in FULL_MORE[:2])
    return (f"<html><head><title>Synthetic Undated Note</title>{CSS}</head><body>{BANNER}"
            f"<h1>Synthetic Undated Note</h1>{paras}</body></html>")


(OUT / "ms_report_synthetic.html").write_text(html_ms_report())
for name, html in (("semianalysis_full_synthetic.pdf", html_semianalysis_full()),
                   ("ms_report_synthetic.pdf", html_ms_report()),
                   ("scanned_page_synthetic.pdf", html_scanned()),
                   ("undated_synthetic.pdf", html_undated())):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as fh:
        fh.write(html)
    target = OUT / name
    subprocess.run([BROWSER, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={target}", f"file://{fh.name}"], check=True,
                   capture_output=True, timeout=120)
    print(name, target.stat().st_size)
(OUT / "semianalysis_preview_synthetic.txt").write_text("\n\n".join(PREVIEW) + "\n")
print("preview text written")
