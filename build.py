#!/usr/bin/env python3
"""Build the MindYards site: assembles the pages under the repo root from src/.

    python build.py

Source of truth is src/ (layout.html, partials/, sections/, css/, js/).
Edit src/ and rebuild; do not hand-edit the generated index.html files.
"""
import datetime
import hashlib
import html as htmlmod
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
SITE = "https://mindyards.in"
BRAND = "MindYards"

# ---------------------------------------------------------------- content map
GROUPS = [
    dict(slug="services", label="Services",
         title="AI consulting services: strategy, build, govern, run",
         items=[("implementation", "Implementation & build"),
                ("agentic", "Agentic AI"),
                ("managed-ops", "Managed AI operations"),
                ("strategy", "Strategy & advisory"),
                ("governance", "Governance, risk & compliance"),
                ("data", "Data & enablement")]),
    dict(slug="industries", label="Industries",
         title="AI consulting by industry",
         items=[("bfsi", "Banking, financial services & insurance"),
                ("healthcare", "Healthcare & life sciences"),
                ("legal", "Legal"),
                ("manufacturing", "Manufacturing"),
                ("logistics", "Logistics & supply chain"),
                ("public-sector", "Public sector"),
                ("retail-cx", "Retail & customer experience"),
                ("aec", "AEC & engineering")]),
    dict(slug="solutions", label="Solutions",
         title="Packaged AI solutions and products",
         items=[("compliance-service", "Compliance as a service"),
                ("voice-agents", "Voice & sales agents"),
                ("ma-diligence", "AI M&A due diligence"),
                ("evals", "Evals & red-teaming"),
                ("cost-optimisation", "AI cost optimisation"),
                ("document-intelligence", "Document intelligence accelerator"),
                ("knowledge-assistant", "Enterprise knowledge assistant"),
                ("msoftai", "MsoftAI Manifold Designer"),
                ("advisor", "Insurance Advisor CRM")]),
    dict(slug="engagement", label="Engagement",
         title="Engagement models: assessment, build, operations, fractional CAIO",
         items=[("assessment", "Assessment"),
                ("build", "Fixed-scope build"),
                ("managed-operations", "Managed operations"),
                ("fractional-caio", "Fractional Chief AI Officer")]),
]

# Contact form: which <select> option to preselect when arriving from a page, and the label for the email.
TOPICS = {
    "implementation": ("Implementation & build", "Implementation & build"),
    "agentic": ("Agentic AI", "Agentic AI"),
    "managed-ops": ("Managed AI operations", "Managed AI operations"),
    "strategy": ("Strategy & advisory", "Strategy & advisory"),
    "governance": ("Governance, risk & compliance", "Governance, risk & compliance"),
    "data": ("Data & enablement", "Data & enablement"),
    "msoftai": ("MsoftAI Manifold Designer", "MsoftAI Manifold Designer"),
    "advisor": ("Insurance Advisor CRM", "Insurance Advisor CRM"),
    "fractional-caio": ("Fractional Chief AI Officer", "Fractional Chief AI Officer"),
    "assessment": ("Strategy & advisory", "Assessment"),
    "build": ("Implementation & build", "Fixed-scope build"),
    "managed-operations": ("Managed AI operations", "Managed operations"),
}
for _g in GROUPS:
    for _id, _label in _g["items"]:
        if _g["slug"] == "solutions" and _id not in TOPICS:
            TOPICS[_id] = ("A packaged solution", _label)
        if _g["slug"] == "industries":
            TOPICS[_id] = ("", _label)

# Old single-page anchors -> new URLs.
URL = {"top": "/", "contact": "/contact/", "about": "/about/", "faq": "/about/#faq",
       "approach": "/about/#approach", "platforms": "/#platforms"}
for _g in GROUPS:
    URL[_g["slug"]] = f"/{_g['slug']}/"
    for _id, _ in _g["items"]:
        URL[_id] = f"/{_g['slug']}/{_id}/"


# ---------------------------------------------------------------- helpers
def read(rel):
    return (SRC / rel).read_text(encoding="utf-8")


def section(sid):
    return read(f"sections/{sid}.html")


def relink(markup, contact_topic=None):
    """Rewrite single-page anchors to page URLs and make asset paths root-relative."""
    def sub(m):
        sid = m.group(1)
        if sid == "contact" and contact_topic:
            return f'href="/contact/?topic={contact_topic}"'
        return f'href="{URL[sid]}"' if sid in URL else m.group(0)
    markup = re.sub(r'href="#([A-Za-z0-9_-]+)"', sub, markup)
    markup = re.sub(r'(src|href)="assets/', r'\1="/assets/', markup)
    return markup


def promote_h1(markup):
    """Turn the first <h2> of a page's main section into the page <h1>."""
    markup = re.sub(r"<h2(\s|>)", r'<h1 class="pg"\1', markup, count=1)
    return markup.replace("</h2>", "</h1>", 1)


def text(fragment):
    return htmlmod.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def describe(markup, limit=158):
    """Meta description from the first intro/sec-head paragraph."""
    m = re.search(r'<div class="(?:intro|sec-head)">.*?<p[^>]*>(.*?)</p>', markup, re.S)
    t = re.sub(r"\s+", " ", text(m.group(1)))
    if len(t) <= limit:
        return t
    cut = t[:limit]
    dot = cut.rfind(". ")
    if dot > 100:
        return cut[:dot + 1]
    return cut[:cut.rfind(" ")].rstrip(",;:") + "."


def attr(s):
    return htmlmod.escape(s, quote=True)


def breadcrumb(crumbs):
    items = [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u}
             for i, (n, u) in enumerate(crumbs)]
    data = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>\n"


def subnav(group, current):
    hub_cls = "hub on" if current is None else "hub"
    links = [f'<a class="{hub_cls}" href="/{group["slug"]}/">{attr(group["label"])} overview</a>']
    for sid, label in group["items"]:
        cls = ' class="on"' if sid == current else ""
        links.append(f'<a{cls} href="{URL[sid]}">{attr(label)}</a>')
    return (f'<nav class="subnav" aria-label="{attr(group["label"])} pages"><div class="wrap">'
            + "".join(links) + "</div></nav>\n")


def pager(group, idx):
    items = group["items"]
    parts = []
    if idx > 0:
        sid, label = items[idx - 1]
        parts.append(f'<a class="prev" href="{URL[sid]}"><small>Previous</small>{attr(label)}</a>')
    if idx < len(items) - 1:
        sid, label = items[idx + 1]
        parts.append(f'<a class="next" href="{URL[sid]}"><small>Next</small>{attr(label)}</a>')
    else:
        parts.append(f'<a class="next" href="/{group["slug"]}/"><small>Back to</small>'
                     f'{attr(group["label"])} overview</a>')
    return '<div class="pager"><div class="wrap">' + "".join(parts) + "</div></div>\n"


# ---------------------------------------------------------------- assembly
LAYOUT = read("layout.html")
HEADER = relink(read("partials/header.html"))
FOOTER = relink(read("partials/footer.html"))
CTABAND = relink(read("partials/ctaband.html"))
CSS = read("css/site.css")
JS = read("js/site.js")
CSSV = hashlib.sha1(CSS.encode()).hexdigest()[:8]
JSV = hashlib.sha1(JS.encode()).hexdigest()[:8]

PAGES = []  # (path, priority) for the sitemap


def write_page(path, *, title, description, main, subnav_html="", jsonld="", body_class="",
               inline_js="", priority=0.7):
    out = (LAYOUT.replace("{{title}}", attr(title))
           .replace("{{description}}", attr(description))
           .replace("{{canonical}}", SITE + path)
           .replace("{{cssv}}", CSSV).replace("{{jsv}}", JSV)
           .replace("{{jsonld}}", jsonld)
           .replace("{{body_class}}", body_class)
           .replace("{{header}}", HEADER)
           .replace("{{subnav}}", subnav_html)
           .replace("{{main}}", main)
           .replace("{{footer}}", FOOTER)
           .replace("{{inline_js}}", inline_js))
    if path.endswith(".html"):
        target = ROOT / path.strip("/")
    elif path == "/":
        target = ROOT / "index.html"
    else:
        target = ROOT / path.strip("/") / "index.html"
        PAGES.append((path, priority))
    if path == "/":
        PAGES.append((path, priority))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(out, encoding="utf-8")


def build():
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets/site.css").write_text(CSS, encoding="utf-8")
    (ROOT / "assets/site.js").write_text(JS, encoding="utf-8")

    legacy_js = "<script>window.MY_LEGACY=" + json.dumps(URL, separators=(",", ":")) + "</script>\n"
    topics_js = ("<script>window.MY_TOPICS="
                 + json.dumps(TOPICS, ensure_ascii=False, separators=(",", ":")) + "</script>\n")

    # Home
    home = "".join([read("partials/hero.html"), read("partials/strip.html"),
                    section("services"), section("platforms"), section("approach"), CTABAND])
    write_page("/", title=f"{BRAND} — AI Consulting: Strategy, Build, Govern, Run",
               description=("MindYards is an AI consulting firm in Chennai serving India and the Middle East. "
                            "Six service lines: implementation and build, agentic AI, managed AI operations, "
                            "strategy and advisory, governance and compliance, data and enablement."),
               main=relink(home), jsonld=read("partials/jsonld-home.html"), inline_js=legacy_js, priority=1.0)

    # Group hubs and detail pages
    for g in GROUPS:
        hub = section(g["slug"])
        write_page(f"/{g['slug']}/", title=f"{g['title']} — {BRAND}", description=describe(hub),
                   main=relink(promote_h1(hub)) + CTABAND, subnav_html=subnav(g, None),
                   jsonld=breadcrumb([("Home", "/"), (g["label"], f"/{g['slug']}/")]), priority=0.8)
        for i, (sid, label) in enumerate(g["items"]):
            sec = section(sid)
            main = relink(promote_h1(sec), contact_topic=sid) + pager(g, i) + CTABAND
            write_page(URL[sid], title=f"{label} — {g['label']} — {BRAND}", description=describe(sec),
                       main=main, subnav_html=subnav(g, sid),
                       jsonld=breadcrumb([("Home", "/"), (g["label"], f"/{g['slug']}/"), (label, URL[sid])]))

    # About (with approach and FAQ) and contact
    about = promote_h1(section("about")) + section("approach") + section("faq") + CTABAND
    write_page("/about/", title=f"About {BRAND} — built by practitioners",
               description=("MindYards was founded by Selvakumar Dhanasekaran and is based in Chennai, working "
                            "with clients across India and the Middle East on short, well-defined AI engagements."),
               main=relink(about), jsonld=breadcrumb([("Home", "/"), ("About", "/about/")]), priority=0.6)
    write_page("/contact/", title=f"Contact {BRAND} — book a discovery call",
               description=("Tell us what you are trying to do. We reply within two working days with a call "
                            "slot and then a written proposal with scope, timeline and fixed price."),
               main=relink(promote_h1(section("contact"))), inline_js=topics_js,
               jsonld=breadcrumb([("Home", "/"), ("Contact", "/contact/")]), priority=0.6)

    # 404
    nf = """  <section class="sec nf">
    <div class="wrap">
      <div class="sec-head">
        <div class="tick"></div>
        <h1 class="pg">That page has moved or never existed</h1>
        <p>Use the menu above, or start from one of these.</p>
      </div>
      <div style="display:flex;gap:12px;flex-wrap:wrap">
        <a class="btn btn-fire" href="/">Home</a>
        <a class="btn btn-line" href="/services/">Services</a>
        <a class="btn btn-line" href="/solutions/">Solutions</a>
        <a class="btn btn-line" href="/contact/">Contact</a>
      </div>
    </div>
  </section>
"""
    write_page("/404.html", title=f"Page not found — {BRAND}",
               description="The page you asked for is not here.", main=nf, inline_js=legacy_js)

    # Sitemap
    today = datetime.date.today().isoformat()
    urls = "".join(f"  <url>\n    <loc>{SITE}{p}</loc>\n    <lastmod>{today}</lastmod>\n"
                   f"    <changefreq>monthly</changefreq>\n    <priority>{pr:.1f}</priority>\n  </url>\n"
                   for p, pr in PAGES)
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n",
        encoding="utf-8")
    print(f"built {len(PAGES)} pages + 404.html, sitemap.xml, assets/site.css, assets/site.js")


if __name__ == "__main__":
    build()
