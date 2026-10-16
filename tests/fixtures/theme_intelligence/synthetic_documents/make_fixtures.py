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
import re
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


def html_semianalysis_saved_preview() -> str:
    """A paid post's page SAVED AS PDF without a paid sign-in: the free preview, then the
    subscriber notice — what an operator supplies when the browser was not signed in."""
    paras = "".join(f"<p>{p}</p>" for p in PREVIEW + FULL_MORE[:2])
    return (f"<html><head><title>Synthetic Memory Note: Inference Keeps Memory Tight</title>"
            f"{CSS}</head><body>{BANNER}<h1>Synthetic Memory Note: Inference Keeps Memory "
            f"Tight</h1><p>By Synthetic Analyst One and Synthetic Analyst Two</p>"
            f"<p>September 28, 2026</p>{paras}<h2>This post is for paid subscribers</h2>"
            f"<p>Subscribe</p><p>Already a paid subscriber? Sign in</p></body></html>")


def html_web_page_dated_in_a_box() -> str:
    """A research WEB PAGE saved as PDF whose site lays the headline and date out in boxes the PDF
    reader detects as a table (as morganstanley.com's article pages print)."""
    paras = "".join(f"<p>{p}</p>" for p in FULL_MORE[:4])
    box = ("<table style='width:100%;border:1px solid #333'><tr><td>RESEARCH</td>"
           "<td>Synthetic Memory Note: A Dated Web Page</td></tr><tr><td>September 14, 2026</td>"
           "<td>A one-line standfirst for the invented page.</td></tr></table>")
    return (f"<html><head><title>Synthetic Memory Note: A Dated Web Page | Synthetic Bank"
            f"</title>{CSS}</head><body>{BANNER}{box}{paras}</body></html>")


def html_overprinted_chart_labels() -> str:
    """A web page saved as PDF whose chart labels are printed three times over themselves (a
    faux-bold effect, as morganstanley.com's Caffeine chart printed "Need more energy 666111%%%"
    for 61%), beside a body figure whose digits legitimately repeat (1100) and must stay."""
    label = "Synthetic survey: need more energy 61%"
    stack = "".join(f"<div style='position:absolute;left:0;top:0'>{label}</div>" for _ in range(3))
    return (f"<html><head><title>Synthetic Overprinted Chart</title>{CSS}</head><body>{BANNER}"
            f"<h1>Synthetic Overprinted Chart</h1><p>Published September 2, 2026. The invented "
            f"survey counted 1100 respondents.</p><div style='position:relative;height:24px'>"
            f"{stack}</div><p>{FULL_MORE[0]}</p></body></html>")


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


def html_two_column() -> str:
    """A report page set in TWO COLUMNS (as bank research prints): each printed line runs across
    both, so a reader taking whole lines interleaves the two columns' sentences. Then two
    ONE-column pages whose lines also hold a wide gap mid-page, as a Citi report's do: a contents
    page (each title, then its page number at the right edge) and a bulleted list set right of a
    margin (each bullet 14pt or more before its text) — neither is a gutter."""
    left = ["Left column paragraph one: synthetic memory demand rose 12% in the quarter as "
            "hyperscale clusters expanded and contract terms lengthened at every supplier we "
            "track.",
            "Left column paragraph two: synthetic HBM allocation stays tight through next year, "
            "with lead times near 30 weeks and buyers prepaying for capacity they need later."]
    right = ["Right column paragraph one: synthetic grid queues reached 2,600 GW as "
             "interconnection studies slowed and transformer deliveries stretched beyond two "
             "years.",
             "Right column paragraph two: synthetic utilities plan capex up 18% this year, the "
             "largest rise in a decade, much of it for transmission upgrades and substations."]
    cols = ("<div style='column-count:2;column-gap:1.2cm'>"
            + "".join(f"<p style='margin:0 0 10pt 0'>{p}</p>" for p in left)
            + "<p style='break-before:column;margin:0'></p>"
            + "".join(f"<p style='margin:0 0 10pt 0'>{p}</p>" for p in right) + "</div>")
    contents = "".join(
        f"<p style='display:flex;justify-content:space-between;margin:0 0 6pt 0'>"
        f"<span>{title}</span><span>{page}</span></p>"
        for title, page in (("Synthetic Executive Summary", 3), ("Synthetic Memory Outlook", 9),
                            ("Synthetic Grid Bottlenecks", 18), ("Synthetic Transformers", 19),
                            ("Synthetic Regional Views", 26)))
    bullets = "".join(
        f"<p style='margin:0 0 8pt 40%'><span style='display:inline-block;width:20pt'>"
        f"&#8226;</span>{item}</p>"
        for item in ("Synthetic lead times: two-year backlogs.",
                     "Synthetic customisation: built to order.",
                     "Synthetic labour: short of skilled staff.",
                     "Synthetic delays: permits outlast the build."))
    return (f"<html><head><title>Synthetic Two-Column Note</title>{CSS}</head><body>{BANNER}"
            f"<h1>Synthetic Two-Column Note</h1>{cols}"
            f"<div class='pb'></div><h2>Contents</h2>{contents}"
            f"<div class='pb'></div><h2>Synthetic Constraints</h2>{bullets}</body></html>")


def html_office_export() -> str:
    """A three-page report as an office suite exports it: a sentence that OPENS "By 2030, …" (no
    byline), words hyphenated at a line's end ("AI-" / "driven" is a compound, "sig-" / "nal" a
    split word), a pull-quote printed twice on ONE page, and a footer on EVERY page. The
    placeholder Author metadata is added after printing (`with_author`)."""
    footer = "<p>Synthetic Office Export, internal draft</p>"
    quote = "<p><b>Grid queues doubled in two synthetic years.</b></p>"
    page1 = ("<h1>Synthetic Office Export Note</h1>"
             "<p>By 2030, synthetic data-centre demand doubles in this invented model, and the "
             "grid queues that serve it lengthen every year.</p>"
             "<p>Operators describe an AI-<br>driven build-out that strains the grid, and the "
             "sig-<br>nal from interconnection studies is that waits are lengthening.</p>"
             + footer)
    page2 = ("<div class='pb'></div><h2>Grid queues</h2>" + quote
             + "<p>Interconnection studies slowed in every synthetic region we model, and "
               "transformer deliveries stretched beyond two years.</p>" + quote + footer)
    page3 = ("<div class='pb'></div><h2>Outlook</h2><p>Synthetic utilities plan capex up 18% "
             "this year, much of it for transmission upgrades.</p>" + footer)
    return (f"<html><head><title>Synthetic Office Export Note</title>{CSS}</head><body>{BANNER}"
            f"{page1}{page2}{page3}</body></html>")


def with_author(path: Path, title: str, author: str) -> None:
    """Give a printed PDF an Info dictionary with an Author, by an INCREMENTAL UPDATE appended to
    the file (Chromium writes no Author; an office suite writes its placeholder user)."""
    data = path.read_bytes()
    prev = int(re.findall(rb"startxref\s+(\d+)", data)[-1])
    trailer = re.findall(rb"trailer\s*<<(.*?)>>", data, re.S)[-1]
    size = int(re.search(rb"/Size\s+(\d+)", trailer).group(1))  # type: ignore[union-attr]
    root = re.search(rb"/Root\s+(\d+ \d+ R)", trailer).group(1)  # type: ignore[union-attr]
    pad = b"" if data.endswith(b"\n") else b"\n"
    at = len(data) + len(pad)
    obj = b"%d 0 obj\n<< /Title (%s) /Author (%s) >>\nendobj\n" % (size, title.encode(),
                                                                  author.encode())
    xref = at + len(obj)
    path.write_bytes(data + pad + obj + b"xref\n%d 1\n%010d 00000 n \n" % (size, at)
                     + b"trailer\n<< /Size %d /Root %s /Info %d 0 R /Prev %d >>\n"
                       b"startxref\n%d\n%%%%EOF\n" % (size + 1, root, size, prev, xref))


(OUT / "ms_report_synthetic.html").write_text(html_ms_report())
for name, html in (("semianalysis_full_synthetic.pdf", html_semianalysis_full()),
                   ("semianalysis_preview_saved_synthetic.pdf", html_semianalysis_saved_preview()),
                   ("web_page_dated_in_a_box_synthetic.pdf", html_web_page_dated_in_a_box()),
                   ("overprinted_chart_synthetic.pdf", html_overprinted_chart_labels()),
                   ("ms_report_synthetic.pdf", html_ms_report()),
                   ("scanned_page_synthetic.pdf", html_scanned()),
                   ("undated_synthetic.pdf", html_undated()),
                   ("two_column_synthetic.pdf", html_two_column()),
                   ("office_export_synthetic.pdf", html_office_export())):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as fh:
        fh.write(html)
    target = OUT / name
    subprocess.run([BROWSER, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={target}", f"file://{fh.name}"], check=True,
                   capture_output=True, timeout=120)
    if name == "office_export_synthetic.pdf":
        with_author(target, "Synthetic Office Export Note", "Microsoft Office User")
    print(name, target.stat().st_size)
(OUT / "semianalysis_preview_synthetic.txt").write_text("\n\n".join(PREVIEW) + "\n")
print("preview text written")
