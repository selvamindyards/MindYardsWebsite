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

# Optional services. Fill in a value, rebuild, and the feature switches on; leave empty to keep the fallback.
CONFIG = {
    "booking": "https://cal.id/selva-mindyards",  # Cal ID, Cal.com or Calendly link -> "Book a call" opens it in a popup, contact page embeds it
    "whatsapp": "916385872400",    # e.g. "919876543210" (country code + number, digits only) -> floating WhatsApp chat button
    "formKey": "",     # Web3Forms access key (free, https://web3forms.com) -> contact and newsletter forms submit directly
    "ga": "",          # GA4 measurement ID, e.g. "G-XXXXXXXXXX"
    "plausible": "",   # Plausible site domain, e.g. "mindyards.in" (alternative to GA)
    "assistant": "",   # URL of the deployed assistant worker (see worker/README.md) -> "Ask MindYards" chat widget
}

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

# Photographs: page id -> alt text (files live in src/img, sized copies in assets/img via build_images.py).
IMAGES = {
    "bfsi": "Glass office towers in a financial district",
    "healthcare": "An empty hospital corridor with waiting benches",
    "legal": "Shelves of bound law reports in a library",
    "manufacturing": "Robotic arms assembling a car body on a production line",
    "logistics": "Cranes loading containers onto a ship at a port at dusk",
    "public-sector": "Classical stone columns on a government building",
    "retail-cx": "A stocked aisle in a retail store",
    "aec": "Tower cranes over a steel building frame on a construction site",
    "solutions": "Rows of server cabinets in a modern data centre",
    "services": "Close-up of a dark blue circuit board",
    "implementation": "Source code on a laptop screen",
    "agentic": "A glowing network of connected nodes",
    "managed-ops": "An industrial control room lined with panels and gauges",
    "strategy": "An empty boardroom overlooking a city at sunset",
    "governance": "A brass combination padlock resting on a keyboard",
    "data": "A bundle of fibre-optic strands glowing blue",
    "compliance-service": "Hands signing a printed document",
    "voice-agents": "Microphones and headphones on a studio desk",
    "ma-diligence": "Bar and pie charts printed on a report",
    "evals": "Laboratory dispensers filling a row of sample vials",
    "cost-optimisation": "A calculator, pencil and printed charts on a desk",
    "document-intelligence": "Stacks of paper files on an office desk",
    "knowledge-assistant": "Rows of shelves in a modern library",
    "msoftai": "A hydraulic pump with a hose fitting",
    "advisor": "An insurance policy document under a magnifying glass",
    "engagement": "A long meeting table in a bright office",
    "assessment": "Sticky notes arranged on a planning board",
    "build": "Architectural drawings with drafting pencils and a ruler",
    "managed-operations": "An analytics dashboard on a monitor",
    "fractional-caio": "A chair facing a window over a city skyline",
}


def banner(sid, img=None):
    img = img or sid
    if img not in IMAGES:
        return ""
    return (f'<div class="banner"><img src="/assets/img/{img}.webp" alt="{attr(IMAGES[img])}" '
            f'width="1600" height="720"></div>\n')


def og(img):
    """Absolute URL of the 1200x630 share image for a page (falls back to the hero)."""
    if img and (ROOT / "assets/og" / f"{img}.jpg").exists():
        return f"{SITE}/assets/og/{img}.jpg"
    return f"{SITE}/assets/og/hero.jpg"


# Old single-page anchors -> new URLs.
URL = {"top": "/", "contact": "/contact/", "about": "/about/", "faq": "/about/#faq",
       "approach": "/about/#approach", "platforms": "/#platforms", "insights": "/insights/",
       "estimate": "/estimate/", "checklist": "/resources/ai-readiness-checklist/"}
LABEL = {}
for _g in GROUPS:
    URL[_g["slug"]] = f"/{_g['slug']}/"
    for _id, _label in _g["items"]:
        URL[_id] = f"/{_g['slug']}/{_id}/"
        LABEL[_id] = _label


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


def nice_date(d):
    return d.strftime("%d %B %Y").lstrip("0")


def load_posts():
    """Articles in src/posts/<slug>.html, each starting with a <!--meta ... --> block."""
    posts = []
    for f in sorted((SRC / "posts").glob("*.html")):
        raw = f.read_text(encoding="utf-8")
        m = re.match(r"<!--meta\n(.*?)\n-->\n?(.*)$", raw, re.S)
        meta = {}
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
        body = m.group(2).strip()
        words = len(text(body).split())
        split = lambda k: [t.strip() for t in meta.get(k, "").split(",") if t.strip()]
        posts.append(dict(slug=f.stem, body=body, read=max(1, round(words / 200)),
                          date=datetime.date.fromisoformat(meta["date"]), title=meta["title"],
                          summary=meta["summary"], image=meta.get("image"), tags=split("tags"),
                          related=split("related")))
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def post_card(p):
    url = f"/insights/{p['slug']}/"
    tags = "".join(f"<li>{attr(t)}</li>" for t in p["tags"])
    return (f'<article><a href="{url}" tabindex="-1" aria-hidden="true"><img src="/assets/img/{p["image"]}-sm.webp" '
            f'alt="" width="720" height="450" loading="lazy"></a><div class="bd">'
            f'<div class="meta2">{nice_date(p["date"])} · {p["read"]} min read</div>'
            f'<h3><a href="{url}">{attr(p["title"])}</a></h3><p>{attr(p["summary"])}</p>'
            f'<ul class="tags">{tags}</ul><a class="more arrow" href="{url}">Read </a></div></article>')


def posts_section(posts, heading, intro, sid="", extra="", cls="sec"):
    cards = "".join(post_card(p) for p in posts)
    sid_attr = f' id="{sid}"' if sid else ""
    return (f'  <section{sid_attr} class="{cls}">\n    <div class="wrap">\n      <div class="sec-head">\n'
            f'        <div class="tick"></div>\n        <h2>{heading}</h2>\n        <p>{intro}</p>\n      </div>\n'
            f'      <div class="posts">{cards}</div>\n{extra}    </div>\n  </section>\n')


def post_page(p, others):
    url = f"/insights/{p['slug']}/"
    related = ", ".join(f'<a href="{URL[r]}">{attr(LABEL[r])}</a>' for r in p["related"] if r in URL)
    related_html = f'<p class="meta2" style="margin-top:12px">Related: {related}</p>' if related else ""
    main = banner(p["slug"], p["image"]) + f"""  <article class="post">
    <div class="wrap">
      <header class="hd">
        <span class="kicker">Insights · {attr(" · ".join(p["tags"]))}</span>
        <h1 class="pg">{attr(p["title"])}</h1>
        <p class="lede">{attr(p["summary"])}</p>
        <div class="meta2"><span>{nice_date(p["date"])}</span><span>{p["read"]} min read</span><span>By the MindYards team</span></div>
      </header>
      <div class="body">
{p["body"]}
      </div>
      <div class="share"><a data-share="linkedin" href="#" target="_blank" rel="noopener">Share on LinkedIn</a><a data-share="whatsapp" href="#" target="_blank" rel="noopener">WhatsApp</a><a data-share="x" href="#" target="_blank" rel="noopener">X</a><button type="button" data-share="copy">Copy link</button></div>
      <div class="box">
        <div><h3>Want to talk this through for your organisation?</h3><p>A 30-minute call with a senior consultant. No deck, no obligation.</p>{related_html}</div>
        <a class="btn btn-fire book" href="/contact/">Book a discovery call</a>
      </div>
    </div>
  </article>
"""
    if others:
        main += ('  <section class="related">\n    <div class="wrap">\n      <h2>More insights</h2>\n      <div class="posts">'
                 + "".join(post_card(o) for o in others[:3]) + "</div>\n    </div>\n  </section>\n")
    data = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"],
            "description": p["summary"], "datePublished": p["date"].isoformat(),
            "dateModified": p["date"].isoformat(), "image": og(p["image"]),
            "author": {"@type": "Organization", "name": BRAND, "url": SITE},
            "publisher": {"@type": "Organization", "name": BRAND, "logo": {"@type": "ImageObject", "url": f"{SITE}/assets/logo.png"}},
            "mainEntityOfPage": SITE + url}
    jsonld = ('<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>\n"
              + breadcrumb([("Home", "/"), ("Insights", "/insights/"), (p["title"], url)]))
    return main, jsonld


def knowledge(posts):
    """Plain-text digest of the site for the assistant worker's system prompt (worker/knowledge.md)."""
    def plain(markup):
        markup = re.sub(r"<!--.*?-->", "", markup, flags=re.S)
        markup = re.sub(r"<(script|style|svg)\b.*?</\1>", "", markup, flags=re.S)
        markup = re.sub(r"</(h1|h2|h3|h4|p|li|dt|dd|tr|summary|blockquote|figcaption)>", "\n", markup)
        markup = re.sub(r"<(h2|h3)[^>]*>", "\n## ", markup)
        t = htmlmod.unescape(re.sub(r"<[^>]+>", "", markup))
        t = re.sub(r"[ \t]+", " ", t)
        return re.sub(r"\n\s*\n+", "\n", t).strip()
    out = [f"# {BRAND} site digest (generated by build.py, do not edit)\n",
           f"Home: {SITE}/\n" + plain(read("partials/hero.html") + read("partials/strip.html") + section("platforms"))]
    for g in GROUPS:
        out.append(f"\n# {g['label']} overview: {SITE}/{g['slug']}/\n" + plain(section(g["slug"])))
        for sid, label in g["items"]:
            out.append(f"\n# {label}: {SITE}{URL[sid]}\n" + plain(section(sid)))
    out.append(f"\n# About: {SITE}/about/\n" + plain(section("about") + section("approach") + section("faq")))
    out.append(f"\n# Contact: {SITE}/contact/\n" + plain(section("contact")))
    out.append(f"\n# Estimator: {SITE}/estimate/ (interactive savings estimate and readiness check)")
    out.append(f"\n# Checklist: {SITE}/resources/ai-readiness-checklist/ (25-point AI readiness checklist)")
    for p in posts:
        out.append(f"\n# Insight: {p['title']} ({SITE}/insights/{p['slug']}/, {nice_date(p['date'])})\n{p['summary']}")
    (ROOT / "worker").mkdir(exist_ok=True)
    (ROOT / "worker/knowledge.md").write_text("\n".join(out) + "\n", encoding="utf-8")


def analytics():
    out = ""
    if CONFIG["ga"]:
        gid = attr(CONFIG["ga"])
        out += (f'<script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>\n'
                f'<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}'
                f'gtag("js",new Date());gtag("config","{gid}",{{anonymize_ip:true}});</script>\n')
    if CONFIG["plausible"]:
        out += f'<script defer data-domain="{attr(CONFIG["plausible"])}" src="https://plausible.io/js/script.js"></script>\n'
    return out


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


CONFIG_JS = ('<script>document.documentElement.classList.add("js");window.MY_CONFIG='
             + json.dumps({k: v for k, v in CONFIG.items() if v}, separators=(",", ":")) + "</script>\n")
ANALYTICS = analytics()


def write_page(path, *, title, description, main, subnav_html="", jsonld="", body_class="",
               inline_js="", priority=0.7, image=None):
    out = (LAYOUT.replace("{{title}}", attr(title))
           .replace("{{description}}", attr(description))
           .replace("{{canonical}}", SITE + path)
           .replace("{{cssv}}", CSSV).replace("{{jsv}}", JSV)
           .replace("{{jsonld}}", jsonld)
           .replace("{{og}}", og(image))
           .replace("{{config}}", CONFIG_JS).replace("{{analytics}}", ANALYTICS)
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

    posts = load_posts()

    # Home
    latest = posts_section(posts[:3], "Latest insights",
                           "Short, practical notes from our engagements. One or two a month.", cls="sec blush",
                           extra='      <p style="margin-top:28px"><a class="btn btn-line arrow" href="/insights/">All insights </a></p>\n')
    home = "".join([read("partials/hero.html"), read("partials/strip.html"), read("partials/ticker.html"),
                    section("services"), read("partials/estcta.html"), section("platforms"), latest,
                    section("approach"), CTABAND])
    write_page("/", title=f"{BRAND} — AI Consulting: Strategy, Build, Govern, Run",
               description=("MindYards is an AI consulting firm in Chennai serving India and the Middle East. "
                            "Six service lines: implementation and build, agentic AI, managed AI operations, "
                            "strategy and advisory, governance and compliance, data and enablement."),
               main=relink(home), jsonld=read("partials/jsonld-home.html"), inline_js=legacy_js, priority=1.0,
               image="hero")

    # Group hubs and detail pages
    for g in GROUPS:
        hub = section(g["slug"])
        write_page(f"/{g['slug']}/", title=f"{g['title']} — {BRAND}", description=describe(hub),
                   main=banner(g["slug"]) + relink(promote_h1(hub)) + CTABAND, subnav_html=subnav(g, None),
                   jsonld=breadcrumb([("Home", "/"), (g["label"], f"/{g['slug']}/")]), priority=0.8, image=g["slug"])
        for i, (sid, label) in enumerate(g["items"]):
            sec = section(sid)
            main = banner(sid) + relink(promote_h1(sec), contact_topic=sid) + pager(g, i) + CTABAND
            write_page(URL[sid], title=f"{label} — {g['label']} — {BRAND}", description=describe(sec),
                       main=main, subnav_html=subnav(g, sid), image=sid,
                       jsonld=breadcrumb([("Home", "/"), (g["label"], f"/{g['slug']}/"), (label, URL[sid])]))

    # About (with approach and FAQ) and contact
    about = promote_h1(section("about")) + section("approach") + section("faq") + CTABAND
    write_page("/about/", title=f"About {BRAND} — built by practitioners",
               description=("MindYards was founded by Selvakumar Dhanasekaran and is based in Chennai, working "
                            "with clients across India and the Middle East on short, well-defined AI engagements."),
               main=relink(about), jsonld=breadcrumb([("Home", "/"), ("About", "/about/")]), priority=0.6,
               image="about")
    write_page("/contact/", title=f"Contact {BRAND} — book a discovery call",
               description=("Tell us what you are trying to do. We reply within two working days with a call "
                            "slot and then a written proposal with scope, timeline and fixed price."),
               main=relink(promote_h1(section("contact"))), inline_js=topics_js,
               jsonld=breadcrumb([("Home", "/"), ("Contact", "/contact/")]), priority=0.6, image="engagement")

    # Insights
    hub = posts_section(posts, "Insights", "Short, practical notes from our engagements: what works, what does not, "
                        "and what we would do first. One or two a month.", sid="insights")
    write_page("/insights/", title=f"Insights — practical notes on AI delivery — {BRAND}",
               description=("Short, practical articles from MindYards on building, evaluating, governing and running "
                            "AI systems: agents, evaluation suites, cost, compliance and operations."),
               main=relink(promote_h1(hub)) + CTABAND, jsonld=breadcrumb([("Home", "/"), ("Insights", "/insights/")]),
               priority=0.8, image=posts[0]["image"] if posts else None)
    for p in posts:
        main, jsonld = post_page(p, [o for o in posts if o is not p])
        write_page(f"/insights/{p['slug']}/", title=f"{p['title']} — {BRAND} Insights", description=p["summary"],
                   main=relink(main), jsonld=jsonld, body_class="is-post", image=p["image"])

    # Estimator and checklist
    write_page("/estimate/", title=f"AI value and readiness estimator — {BRAND}",
               description=("Estimate the hours and money AI could free in one of your processes, then check your "
                            "readiness in eight questions. Rough, interactive, and free. Not a quote."),
               main=banner("estimate", "cost-optimisation") + relink(promote_h1(section("estimate"))) + CTABAND,
               jsonld=breadcrumb([("Home", "/"), ("Engagement", "/engagement/"), ("Estimator", "/estimate/")]),
               priority=0.8, image="cost-optimisation")
    write_page("/resources/ai-readiness-checklist/", title=f"AI readiness checklist: 25 things to check — {BRAND}",
               description=("The 25-point AI readiness checklist MindYards uses in the first week of an assessment: "
                            "strategy, data, people, technology and governance. Tick, print and share."),
               main=banner("checklist", "assessment") + relink(promote_h1(section("checklist"))) + CTABAND,
               jsonld=breadcrumb([("Home", "/"), ("Resources", "/resources/ai-readiness-checklist/"),
                                  ("AI readiness checklist", "/resources/ai-readiness-checklist/")]),
               priority=0.7, image="assessment")
    knowledge(posts)

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
    print(f"built {len(PAGES)} pages + 404.html, sitemap.xml, assets/site.css, assets/site.js, worker/knowledge.md")


if __name__ == "__main__":
    build()
