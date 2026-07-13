#!/usr/bin/env python3
"""
TSQA website static site generator (Rev 2 SEO restructure).

Assembles the multi-page site from shared head / nav / footer templates plus
per-page content and structured data. Run from the repo root:

    python3 build/build.py

Output HTML is written to the repo root (and sub-directories) and committed so
GitHub Pages serves plain static files. No server-side code is required.
"""
import json
import os
import re
import shutil
import html as htmllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
BASE = "https://tsqa.co.nz"

EMAIL = "contact@tsqa.co.nz"
ASSET_VERSION = "20260713b"  # bump to bust Cloudflare/browser cache on CSS/JS changes
PHONE_DISPLAY = "021 125 8705"
PHONE_TEL = "+64211258705"
PHONE_SCHEMA = "+64 21 125 8705"
SLOGAN = "Protecting People, Perfecting Process"

AREA_SERVED = [
    {"@type": "AdministrativeArea", "name": "Bay of Plenty"},
    {"@type": "AdministrativeArea", "name": "Waikato"},
    {"@type": "AdministrativeArea", "name": "Auckland"},
    {"@type": "AdministrativeArea", "name": "Taranaki"},
    {"@type": "Country", "name": "New Zealand"},
]

# ── Load verbatim service descriptions ─────────────────────────────────────
with open(os.path.join(BUILD, "services.json"), encoding="utf-8") as fh:
    SERVICES = json.load(fh)

# Fix em dash in verbatim copy (word-preserving punctuation swap only).
for k, v in list(SERVICES.items()):
    SERVICES[k] = v.replace(" — ", ", ").replace("—", ",")

# Pre-approved new service copy (Task 2).
SERVICES["ISO 45001 System Setup"] = (
    "ISO 45001 is the international standard for occupational health and safety "
    "management systems. We build and implement your safety management system to "
    "the ISO 45001 framework, establishing the processes, documentation, and "
    "controls the standard requires. Whether you are working towards certification "
    "through an accredited body or simply want your system built to the "
    "internationally recognised benchmark, we set up the foundations so your "
    "system is structured, practical, and ready to perform."
)

# Approved reword of the SHE Pre-Qual description to lead with the fact that it
# now runs on the Totika-accredited framework (replaces the earlier verbatim copy).
SERVICES["SHE Pre-Qual"] = (
    "SHE Pre-Qual is a health and safety pre-qualification pathway widely used "
    "across the building and construction sector, and it now operates on the "
    "Totika-accredited framework, using Totika categories and pricing. Many "
    "councils require contractors to hold a valid SHE assessment before "
    "undertaking high-risk or long-term work. TSQA helps you build and evidence "
    "an active safety management system that meets SHE Pre-Qual standards, not "
    "just on paper, but demonstrably in practice."
)


def plain(text):
    """HTML string -> plain text for JSON-LD (decode entities, strip tags)."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)
    text = htmllib.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def jsonld(obj):
    body = json.dumps(obj, ensure_ascii=False, indent=2)
    return '<script type="application/ld+json">\n' + body + "\n</script>"


# ── Structured data builders ───────────────────────────────────────────────
def professional_service_ld():
    return {
        "@context": "https://schema.org",
        "@type": "ProfessionalService",
        "name": "TSQA",
        "url": BASE + "/",
        "logo": BASE + "/images/logo.jpg",
        "image": BASE + "/images/tsqa-logo-og.jpg",
        "telephone": PHONE_SCHEMA,
        "email": EMAIL,
        "slogan": SLOGAN,
        "description": (
            "TSQA is a New Zealand health, safety, and quality assurance "
            "consultancy helping SMEs and contractors with risk management, "
            "safety systems, pre-qualification, auditing, and quality control."
        ),
        "areaServed": AREA_SERVED,
        "address": {"@type": "PostalAddress", "addressCountry": "NZ"},
        "knowsAbout": [
            "Health and safety management",
            "ISO 45001", "ISO 9001",
            "Contractor pre-qualification",
            "IMPAC PREQUAL", "SiteWise", "SHE Pre-Qual", "Totika",
            "Quality assurance", "Quality control", "Auditing",
        ],
    }


def service_ld(service_type, description, service_names):
    return {
        "@context": "https://schema.org",
        "@type": "Service",
        "serviceType": service_type,
        "name": service_type,
        "description": plain(description),
        "provider": {"@type": "ProfessionalService", "name": "TSQA", "url": BASE + "/"},
        "areaServed": AREA_SERVED,
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": service_type,
            "itemListElement": [
                {"@type": "Offer",
                 "itemOffered": {"@type": "Service", "name": plain(n)}}
                for n in service_names
            ],
        },
    }


def breadcrumb_ld(trail):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "name": name, "item": BASE + path}
            for i, (name, path) in enumerate(trail)
        ],
    }


def faqpage_ld(faqs):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": plain(q),
             "acceptedAnswer": {"@type": "Answer",
                                "text": plain(" ".join(paras))}}
            for (q, paras, _verify) in faqs
        ],
    }


# ── Visible-HTML builders ──────────────────────────────────────────────────
def breadcrumb_html(trail):
    items = []
    last = len(trail) - 1
    for i, (name, path) in enumerate(trail):
        if i == last:
            items.append(f'<li aria-current="page">{name}</li>')
        else:
            items.append(f'<li><a href="{path}">{name}</a></li>')
    return ('<nav class="breadcrumb" aria-label="Breadcrumb">\n  <ol>\n    '
            + "\n    ".join(items) + "\n  </ol>\n</nav>")


def faq_items_html(faqs):
    out = []
    for (q, paras, verify) in faqs:
        ans = ""
        if verify:
            ans += "\n      <!-- VERIFY -->"
        for p in paras:
            ans += f"\n      <p>{p}</p>"
        out.append(
            '    <details class="faq-item">\n'
            f'      <summary>{q}</summary>\n'
            f'      <div class="faq-answer">{ans}\n      </div>\n'
            '    </details>'
        )
    return "\n".join(out)


def faq_section_html(faqs, heading="Frequently Asked Questions", hid="faqs"):
    return (
        f'<section class="faq-section" aria-labelledby="{hid}">\n'
        f'  <h2 id="{hid}">{heading}</h2>\n'
        f'{faq_items_html(faqs)}\n'
        '</section>'
    )


def service_cards_html(names, heading_level="h3"):
    cards = []
    for n in names:
        desc = SERVICES[n]
        cards.append(
            '        <div class="service-card">\n'
            f'          <{heading_level} class="service-name">{n}</{heading_level}>\n'
            f'          <p class="service-desc">{desc}</p>\n'
            '        </div>'
        )
    return "\n".join(cards)


def pillar_section_html(icon, title, names):
    return (
        '    <div class="pillar-section reveal">\n'
        '      <div class="pillar-header">\n'
        f'        <div class="pillar-icon-lg" aria-hidden="true">{icon}</div>\n'
        f'        <h2 class="pillar-title">{title}</h2>\n'
        '      </div>\n'
        '      <div class="services-grid">\n'
        f'{service_cards_html(names)}\n'
        '      </div>\n'
        '    </div>'
    )


def related_links_html(links, heading="Related services"):
    anchors = "\n    ".join(f'<a href="{path}">{name}</a>' for name, path in links)
    return (
        '<section class="related-links reveal">\n'
        f'  <h2>{heading}</h2>\n'
        '  <div class="related-grid">\n    '
        f'{anchors}\n'
        '  </div>\n'
        '</section>'
    )


def cta_bar_html(heading, text):
    return (
        '<div class="services-cta-bar reveal">\n'
        f'  <h2>{heading}</h2>\n'
        f'  <p>{text}</p>\n'
        '  <a href="/contact/" class="btn-primary">Talk to TSQA</a>\n'
        '</div>'
    )


print("build.py library loaded")


# ── Shared chrome ──────────────────────────────────────────────────────────
NAV_HTML = """<header>
<nav id="navbar" aria-label="Main navigation">
  <a class="nav-logo" href="/" aria-label="TSQA home">
    <img src="/images/logo.jpg" alt="TSQA logo" width="44" height="44">
  </a>
  <ul class="nav-links" id="navLinks">
    <li class="has-dropdown">
      <a href="/health-safety/">Health &amp; Safety <span class="caret" aria-hidden="true">&#9662;</span></a>
      <ul class="dropdown">
        <li><a href="/health-safety/">Health &amp; Safety Overview</a></li>
        <li><a href="/health-safety/risk-management/">Risk &amp; Safety Management</a></li>
        <li><a href="/health-safety/safety-systems/">Safety Systems &amp; Preparedness</a></li>
        <li><a href="/health-safety/incident-culture/">Incident &amp; Culture Improvement</a></li>
        <li><a href="/health-safety/auditing/">Auditing &amp; Compliance</a></li>
      </ul>
    </li>
    <li><a href="/pre-qualification/">Pre-Qualification</a></li>
    <li class="has-dropdown">
      <a href="/quality/">Quality <span class="caret" aria-hidden="true">&#9662;</span></a>
      <ul class="dropdown">
        <li><a href="/quality/">Quality Overview</a></li>
        <li><a href="/quality/quality-assurance/">Quality Assurance</a></li>
        <li><a href="/quality/quality-control/">Quality Control</a></li>
      </ul>
    </li>
    <li><a href="/documents/">Documents</a></li>
    <li><a href="/contact/" class="nav-cta">Get in Touch</a></li>
  </ul>
  <button class="hamburger" id="hamburger" onclick="toggleMenu()" aria-label="Toggle navigation menu" aria-expanded="false" aria-controls="navLinks">
    <span></span><span></span><span></span>
  </button>
</nav>
</header>"""

FOOTER_HTML = """<footer>
  <img src="/images/logo.jpg" alt="TSQA logo" class="footer-logo" width="64" height="64" loading="lazy">
  <div class="footer-tagline">Protecting People, Perfecting Process</div>
  <nav class="footer-links" aria-label="Footer">
    <a href="/">Home</a>
    <a href="/health-safety/">Health &amp; Safety</a>
    <a href="/pre-qualification/">Pre-Qualification</a>
    <a href="/quality/">Quality</a>
    <a href="/documents/">Documents</a>
    <a href="/contact/">Contact</a>
    <a href="/terms/">Terms &amp; Conditions</a>
    <a href="/privacy/">Privacy Policy</a>
    <a href="/disclaimer/">Disclaimer</a>
  </nav>
  <div class="footer-copy">&copy; 2026 TSQA. All rights reserved. New Zealand.</div>
</footer>"""

# Simple three-step pricing process block (no figures, builds trust).
PROCESS_SECTION = """  <section class="process-flow reveal" aria-labelledby="process-heading">
    <div class="process-inner">
      <h2 class="process-title" id="process-heading">
        <span class="process-step">Free Consultation</span>
        <span class="process-arrow" aria-hidden="true">&rarr;</span>
        <span class="process-step">Fixed-Price Proposal</span>
        <span class="process-arrow" aria-hidden="true">&rarr;</span>
        <span class="process-step">We Do the Work</span>
      </h2>
      <p class="process-sub">No obligation, no hidden hourly rates. You will know the full cost before we start.</p>
    </div>
  </section>"""


def render_page(out_path, title, description, canonical, body, ld_blocks,
                gsc=False):
    """Assemble a full HTML document and write it to out_path."""
    assert len(title) <= 60, f"title too long ({len(title)}): {title}"
    assert len(description) <= 155, f"desc too long ({len(description)}): {description}"
    ld = "\n".join(jsonld(b) for b in ld_blocks)
    gsc_line = "\n<!-- GSC verification tag goes here -->" if gsc else ""
    doc = f"""<!DOCTYPE html>
<html lang="en-NZ">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow">{gsc_line}
<meta property="og:type" content="website">
<meta property="og:site_name" content="TSQA">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{BASE}/images/tsqa-logo-og.jpg">
<meta name="twitter:card" content="summary">
<link rel="icon" type="image/png" href="/images/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&family=Open+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css?v={ASSET_VERSION}">
<script src="/site.js?v={ASSET_VERSION}" defer></script>
{ld}
</head>
<body>

{NAV_HTML}

{body}

{FOOTER_HTML}

</body>
</html>
"""
    full = os.path.join(ROOT, out_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(doc)
    assert "—" not in doc, f"em dash found in {out_path}"
    print("wrote", out_path, f"({len(doc)} bytes)")


def scheme_faq_html(heading, faqs, hid):
    return (
        f'<section class="faq-section faq-scheme" aria-labelledby="{hid}">\n'
        f'  <h3 id="{hid}">{heading}</h3>\n'
        f'{faq_items_html(faqs)}\n'
        '</section>'
    )


def hub_card(icon, name, path, blurb):
    return (
        f'    <a class="hub-card reveal" href="{path}">\n'
        f'      <div class="hub-card-icon" aria-hidden="true">{icon}</div>\n'
        f'      <h2>{name}</h2>\n'
        f'      <p>{blurb}</p>\n'
        '      <span class="hub-card-link">Learn more &rarr;</span>\n'
        '    </a>'
    )


def leads_html(paras):
    return ('<div class="page-lead reveal">\n  '
            + "\n  ".join(f"<p>{p}</p>" for p in paras)
            + "\n</div>")


def service_subpage(out, title, desc, path, trail, h1, hero_sub, lead_paras,
                    pillar_icon, pillar_title, service_names, faqs, related,
                    cta_h, cta_t, svc_type, svc_desc):
    body = f"""<main>

  <div class="services-hero">
    <h1>{h1}</h1>
    <p>{hero_sub}</p>
  </div>

  {breadcrumb_html(trail)}

  {leads_html(lead_paras)}

  <div class="services-body">
{pillar_section_html(pillar_icon, pillar_title, service_names)}
  </div>

  {faq_section_html(faqs)}

  {related_links_html(related)}

  {cta_bar_html(cta_h, cta_t)}

</main>"""
    ld = [professional_service_ld(),
          service_ld(svc_type, svc_desc, service_names),
          breadcrumb_ld(trail),
          faqpage_ld(faqs)]
    render_page(out, title, desc, BASE + path, body, ld)


def hub_page(out, title, desc, path, trail, h1, hero_sub, lead_paras, cards,
             faqs, svc_type, svc_desc, all_names, cta_h, cta_t):
    cards_html = "\n".join(hub_card(*c) for c in cards)
    body = f"""<main>

  <div class="services-hero">
    <h1>{h1}</h1>
    <p>{hero_sub}</p>
  </div>

  {breadcrumb_html(trail)}

  {leads_html(lead_paras)}

  <section class="hub-section">
    <div class="hub-grid">
{cards_html}
    </div>
  </section>

  {faq_section_html(faqs)}

  {cta_bar_html(cta_h, cta_t)}

</main>"""
    ld = [professional_service_ld(),
          service_ld(svc_type, svc_desc, all_names),
          breadcrumb_ld(trail),
          faqpage_ld(faqs)]
    render_page(out, title, desc, BASE + path, body, ld)


# ══════════════════════════════ FAQ CONTENT ════════════════════════════════
# Each FAQ: (question, [answer paragraphs], verify_flag)
# verify_flag=True emits an HTML <!-- VERIFY --> comment for facts to confirm.

FAQ_HS_HUB = [
    ("What health and safety services does TSQA provide?",
     ["TSQA provides end-to-end health and safety support for New Zealand businesses, covering risk and safety management, safety systems and preparedness, incident and culture improvement, and auditing and compliance.",
      "We work with SMEs and contractors to build practical systems, plans, and documentation that protect people and help you meet your obligations under the Health and Safety at Work Act 2015."],
     False),
    ("Do small businesses need a health and safety system?",
     ["Yes. Under the Health and Safety at Work Act 2015, every PCBU (person conducting a business or undertaking) has a duty to manage risks to the health and safety of workers and others, regardless of size.",
      "A health and safety system does not have to be complicated, but it does need to be genuine and used in practice. TSQA builds systems that are proportionate to the size and risk of your business."],
     False),
    ("Does hiring a consultant remove my health and safety responsibilities?",
     ["No. Under the Health and Safety at Work Act 2015, a PCBU cannot contract out of its duties.",
      "A consultant like TSQA provides advice, systems, and support to help you meet your obligations, but the legal responsibility for health and safety in your business stays with you."],
     False),
]

FAQ_RISK = [
    ("What does a workplace safety inspection involve?",
     ["A workplace safety inspection is a structured walk-through of your site by an experienced assessor to identify hazards, unsafe practices, and compliance gaps.",
      "The findings are set out in a clear, actionable report so issues can be prioritised and resolved. It is a practical way to catch problems that familiarity can cause your own team to overlook."],
     False),
    ("What is a risk assessment and why do I need one?",
     ["A risk assessment is a documented process that identifies the hazards in your workplace, evaluates the level of risk, and sets out the controls needed to manage it.",
      "It is a core part of meeting your duties under the Health and Safety at Work Act 2015 and gives you a clear picture of where your business is exposed. TSQA produces assessments that are practical and specific to your operations."],
     False),
    ("What is a site safety plan?",
     ["A site safety plan sets out how health and safety risks will be managed on a particular project or site before work begins.",
      "It typically covers the hazards involved, the controls in place, roles and responsibilities, and how the site will coordinate contractors and visitors, so everyone on site understands how safety will be managed from day one."],
     False),
    ("How often should risk assessments be reviewed?",
     ["Risk assessments should be reviewed whenever something changes that could affect the risk, such as new equipment, new tasks, a change in site conditions, or after an incident.",
      "It is also good practice to review them periodically even when nothing obvious has changed. Keeping them current is part of showing that your health and safety system is active rather than static."],
     False),
]

FAQ_SAFETY_SYS = [
    ("What is a safety management system?",
     ["A safety management system is the set of policies, processes, and records a business uses to manage health and safety in a consistent, structured way.",
      "It brings together how you identify risk, train people, respond to incidents, and improve over time. A good system is practical enough for your team to actually use, not just a folder of documents."],
     False),
    ("What is ISO 45001?",
     ["ISO 45001 is the international standard for occupational health and safety management systems.",
      "It sets out a framework of processes, documentation, and controls for managing health and safety risk. Building your system to ISO 45001 means it is structured to an internationally recognised benchmark, whether or not you go on to seek certification."],
     False),
    ("Does TSQA certify my business to ISO 45001?",
     ["No. TSQA builds and implements your safety management system to the ISO 45001 framework, but certification decisions are made by accredited certification bodies, not by TSQA.",
      "We set up the foundations so your system is structured, practical, and ready to perform, whether you are working towards certification through an accredited body or simply want your system built to the recognised benchmark."],
     False),
    ("Why do I need emergency response plans and drills?",
     ["Emergency response plans set out what your team should do when something goes wrong, and drills test whether those plans actually work.",
      "Together they help your people respond quickly and confidently in a real emergency. TSQA develops site-specific plans and facilitates drills that identify weaknesses before they matter."],
     False),
]

FAQ_INCIDENT = [
    ("Why should workplace incidents be investigated?",
     ["Investigating incidents helps you understand why something went wrong so you can stop it happening again.",
      "A good investigation looks beyond the immediate cause to the underlying factors, then turns those findings into practical improvements. It also supports your obligations to manage risk and, where required, to record and notify certain events."],
     False),
    ("What is the difference between safety culture assessment and improvement?",
     ["A safety culture assessment gives you an honest picture of how safety is actually lived and led across your organisation, while safety culture improvement is the work of shifting that culture over time.",
      "The assessment tells you where you stand and what is holding you back. The improvement work uses practical engagement and measurable goals to move you forward. The two work best together."],
     False),
    ("What is a root cause in an incident investigation?",
     ["A root cause is the underlying reason an incident happened, as opposed to the immediate or surface cause.",
      "For example, the surface cause might be a slip, while the root cause could be a process that allowed a spill to go uncleared. Identifying root causes is what makes an investigation useful, because it points to changes that genuinely reduce the chance of a repeat."],
     False),
]

FAQ_AUDITING = [
    ("What is the difference between an internal audit and an external audit?",
     ["An internal audit is carried out within your own systems to check that your processes, procedures, and records are working as intended.",
      "An external or supplier audit assesses another party, such as a supplier or subcontractor, against your health and safety requirements. Both help you find and fix gaps before they cause problems."],
     False),
    ("Who is responsible for hazardous substances registers?",
     ["The business that manages a workplace where hazardous substances are present is responsible for keeping an accurate register of those substances.",
      "Under New Zealand's hazardous substances rules you need to know what is on site, where it is, and how it must be handled. TSQA develops and maintains registers so you have full visibility and can meet your obligations."],
     False),
    ("What is SDS management?",
     ["SDS management is the ongoing task of keeping your Safety Data Sheets current, accessible, and organised so the people who handle hazardous substances have the right information.",
      "Safety Data Sheets describe the hazards of a substance and how to handle it safely. TSQA keeps your SDS library up to date so the correct information is always at hand."],
     False),
    ("How often should internal audits be carried out?",
     ["Internal audits are usually carried out on a planned schedule through the year, with the frequency set to match the size and risk of your operations.",
      "Higher-risk activities generally warrant more frequent checks. Regular internal audits keep your system honest and surface issues before an external party finds them."],
     False),
]

# ── Pre-qualification FAQs ──
FAQ_PREQUAL_GENERAL = [
    ("What is contractor pre-qualification?",
     ["Contractor pre-qualification is a check that confirms a business has the health and safety systems, documentation, and processes in place to work safely before it is awarded work.",
      "Many principal organisations, councils, and main contractors in New Zealand require suppliers to hold a current pre-qualification before they can go on site. It gives the client confidence that the contractors they engage manage risk to a recognised standard."],
     False),
    ("Which pre-qualification scheme do I need?",
     ["The scheme you need usually depends on who you want to work for, because different clients and sectors specify different schemes.",
      "Some principals ask for SiteWise or Totika, while certain councils and organisations require IMPAC PREQUAL or SHE Pre-Qual. The simplest approach is to ask the client or main contractor which scheme they recognise, then build your evidence to suit. TSQA can help you focus on the right scheme."],
     False),
    ("Can one health and safety system cover more than one scheme?",
     ["Yes, a single well-built health and safety management system can support submissions to several pre-qualification schemes.",
      "The schemes assess similar things, such as your policies, risk management, training records, incident processes, and evidence that your system works in practice. Building one solid system means you can reuse much of the same evidence across IMPAC PREQUAL, SiteWise, SHE Pre-Qual, and Totika rather than starting again each time."],
     False),
]

FAQ_IMPAC = [
    ("What is IMPAC PREQUAL?",
     ["IMPAC PREQUAL is a health and safety pre-qualification service used by councils, government agencies, and large organisations to verify that a contractor has the right health and safety systems in place before work is awarded.",
      "It focuses on how your systems perform in practice, not just what is written in your documents. TSQA assesses your documentation, identifies gaps, builds your evidence base, and prepares your submission."],
     False),
    ("What documents do I need for IMPAC PREQUAL?",
     ["You generally need evidence of your health and safety management system, including your policies, risk assessments, training and induction records, incident reporting and investigation processes, and proof that these are used day to day.",
      "The exact requirements depend on your industry and the risk level of the work you do. TSQA reviews your existing documentation, identifies gaps, and helps you build the evidence base your submission needs."],
     False),
    ("How long does IMPAC PREQUAL take?",
     ["PREQUAL aims to deliver your assessment report within 20 working days of submitting your material, which includes the 14 days allowed for resubmitting evidence.",
      "You generally have 6 months from registration and payment to complete your submission, or 2 months if a client formally initiated the process. How ready your existing health and safety system is will affect how quickly you can submit, and TSQA helps you prepare a complete submission to avoid avoidable delays."],
     False),
    ("Does IMPAC PREQUAL need to be renewed?",
     ["Yes, PREQUAL is maintained on an ongoing basis and is typically renewed annually, with updated evidence required at each renewal.",
      "Some higher-scoring contractors may move to a longer cycle, and your renewal cycle is confirmed by PREQUAL based on your assessment. TSQA can help you keep your system and evidence current so renewal is straightforward."],
     False),
]

FAQ_SITEWISE = [
    ("What is SiteWise and do I need it?",
     ["SiteWise is a health and safety pre-qualification scheme administered by Site Safe New Zealand that grades a contractor's health and safety capability.",
      "You are likely to need it if the main contractors or principals you want to work for use SiteWise grades to decide who they engage. A strong grade is visible to those clients and can directly influence whether you are selected for work."],
     False),
    ("How is a SiteWise grade calculated?",
     ["A SiteWise grade reflects an assessment of your health and safety management system against a set of questions covering your policies, processes, and evidence, scored as a percentage.",
      "Site Safe sets the grade bands: Red is 0 to 49 percent, Amber is 50 to 74 percent, Green is 75 to 89 percent, and Gold is 90 percent or above on your annual assessment. TSQA works with you to strengthen the areas that carry weight so you can achieve a strong grade."],
     False),
    ("How long does a SiteWise assessment last?",
     ["A SiteWise grade runs on an annual cycle, so it is valid until your next yearly assessment.",
      "Site Safe aims to turn around online assessments in 5 to 10 working days, and first-year registrations include three assessment attempts. Keeping your health and safety evidence up to date through the year makes renewal much easier."],
     False),
    ("Can TSQA guarantee a particular SiteWise grade?",
     ["No. TSQA helps you build and evidence a strong health and safety system and prepares your submission, but the grade is determined by Site Safe as the scheme operator.",
      "We focus on giving you the best possible foundation and evidence, while the assessment outcome rests with the scheme."],
     False),
]

FAQ_SHE = [
    ("What is SHE Pre-Qual?",
     ["SHE Pre-Qual is a health and safety pre-qualification assessment widely used across the building and construction sector.",
      "Many councils and principal organisations require contractors to hold a valid SHE assessment before undertaking high-risk or long-term work. It checks that you have an active safety management system that works in practice, not just on paper. SHE Pre-Qual now operates as a Totika-accredited pathway, using Totika categories and pricing."],
     False),
    ("Who requires SHE Pre-Qual?",
     ["SHE Pre-Qual is commonly required by councils and larger organisations in the construction and infrastructure sector, particularly for higher-risk or ongoing work.",
      "Whether you need it depends on the clients you want to work for, so it is worth confirming with the principal or main contractor which pre-qualification they accept before you apply."],
     False),
    ("What does a SHE Pre-Qual assessment cover?",
     ["A SHE Pre-Qual assessment reviews your health and safety documentation and evidence, including your policies, risk management processes, training and competency records, and incident management.",
      "It looks for proof that your system is actively used rather than simply written down. TSQA helps you build and evidence a system that meets these expectations."],
     False),
    ("How long does SHE Pre-Qual take to complete?",
     ["Turnaround depends on your business category and how complete your evidence is when you submit, and SHE Pre-Qual does not publish a single standard timeframe.",
      "Because SHE Pre-Qual now runs on the Totika-accredited framework, it is best to contact SHE Pre-Qual for current timeframes. TSQA helps you prepare a complete submission so avoidable delays are minimised."],
     False),
]

FAQ_TOTIKA = [
    ("What is Totika?",
     ["Totika is New Zealand's national health and safety pre-qualification scheme, developed by CHASNZ to create one consistent standard across the construction and contracting sector.",
      "It is designed so you can complete it once and have it recognised across multiple clients and industries, rather than repeating separate pre-qualifications for each principal."],
     False),
    ("How long does Totika certification take?",
     ["Assessment timeframes depend on which accredited provider you assess through, and express options are available, including a two working day turnaround through PREQUAL's Totika service.",
      "Certification validity is set by category: Sole Trader and Category 1 assessments are valid for 2 years, while Category 2 and 3 assessments are valid for 1 year. TSQA guides you through the process from start to finish to keep it moving."],
     False),
    ("How is Totika different from SiteWise or IMPAC?",
     ["Totika is not a separate assessment that competes with schemes like SiteWise or IMPAC PREQUAL. It sits above them as a national register that recognises approved pre-qualification schemes under one consistent standard.",
      "In practice this means an approved assessment can feed into your Totika status, reducing duplication across clients that accept it."],
     False),
    ("Is Totika recognised nationally?",
     ["Yes, Totika is designed as a national scheme so that a single recognised assessment can be accepted by multiple clients across the construction and contracting sector.",
      "This is intended to reduce the need to complete a different pre-qualification for every principal. Recognition still depends on the individual client accepting Totika, so it is worth confirming with your target clients."],
     False),
]

FAQ_QUALITY_HUB = [
    ("What quality services does TSQA provide?",
     ["TSQA provides quality assurance and quality control services for New Zealand businesses.",
      "Quality assurance covers building and maintaining systems such as ISO 9001 quality management, internal auditing, inspection and test plans, and manufacturing data reports. Quality control covers hands-on checks such as visual weld inspection, welding procedure verification, welder qualifications, material traceability, and inspection and test records."],
     False),
    ("What is the difference between quality assurance and quality control?",
     ["Quality assurance is about the systems and processes that prevent defects and build quality in, while quality control is about checking and verifying that the actual work meets the required standard.",
      "In simple terms, assurance is proactive and system-focused, while control is about inspection and verification. Most businesses need both, and TSQA supports each."],
     False),
    ("Do I need ISO 9001 to work in quality-driven industries?",
     ["Not always, but many clients and contracts either require or strongly favour a recognised quality management system such as ISO 9001.",
      "Even without formal certification, having structured quality processes helps you win and keep work, reduce errors, and demonstrate consistency. TSQA can help you build quality systems whether or not you pursue certification."],
     False),
]

FAQ_QA = [
    ("Do I need ISO 9001 certification to win contracts?",
     ["Not in every case, but a growing number of clients and tenders ask for ISO 9001 or an equivalent quality management system.",
      "Even where certification is not mandatory, having a system built to the standard can strengthen your bids and improve consistency. TSQA implements ISO 9001:2015 systems, though certification itself is decided by an accredited certification body."],
     False),
    ("What is an Inspection and Test Plan (ITP)?",
     ["An Inspection and Test Plan, or ITP, defines exactly what gets inspected, when, by whom, and to what standard on a project.",
      "It gives your team a clear quality framework and gives clients confidence that work is being checked at every critical stage. TSQA develops project-specific ITPs tailored to the work you are delivering."],
     False),
    ("What is a Manufacturing Data Report (MDR)?",
     ["A Manufacturing Data Report, or MDR, brings together all the quality documentation for a project or product into one complete, organised record.",
      "It provides a reliable audit trail from start to finish and satisfies client and contract requirements for traceability. TSQA compiles accurate MDRs so your handover documentation is complete."],
     False),
    ("What does ISO 9001:2015 implementation involve?",
     ["Implementing ISO 9001:2015 means establishing the processes, documentation, and controls the standard requires, built around how your business actually works.",
      "The aim is to improve consistency, reduce errors, and demonstrate quality to your clients. TSQA guides you through implementation from the ground up so the system is practical and usable."],
     False),
]

FAQ_QC = [
    ("What does a visual weld inspection check for?",
     ["A visual weld inspection checks welds for surface defects, poor workmanship, and non-conformances against the applicable standards and project specifications.",
      "It is one of the most common and cost-effective forms of weld quality control. TSQA's inspectors identify issues so they can be corrected before they affect the finished work."],
     False),
    ("What is a Welding Procedure Specification (WPS)?",
     ["A Welding Procedure Specification, or WPS, is a document that defines how a weld must be carried out to achieve the required result, including the variables that must be controlled.",
      "Verifying that your WPS is fit for purpose and correctly aligned to the relevant codes helps ensure welds are done to standard. TSQA verifies WPS documentation against the applicable codes and standards."],
     False),
    ("Why do welder qualifications matter?",
     ["Using qualified welders is often a contractual and regulatory requirement, not just good practice, because it provides evidence that the person doing the work has the competency to meet the required standard.",
      "TSQA assesses and verifies welder qualifications so you can demonstrate that your team is competent for the work."],
     False),
    ("What is material traceability?",
     ["Material traceability is the ability to show where a material came from and that it meets the specification that was ordered.",
      "It relies on reviewing material certifications and documentation so that what was supplied matches what was specified. TSQA reviews material certification and traceability records so quality can be relied on through the project."],
     False),
]

FAQ_DOCS = [
    ("What kinds of documents can TSQA create?",
     ["TSQA creates clear, fit-for-purpose documents tailored to your business and industry, including policies, procedures, forms, registers, and plans.",
      "The focus is on documentation your team can actually use, written in plain language, structured logically, and aligned to the relevant standards and legislation. Document creation supports both the health and safety and quality sides of your business."],
     False),
    ("Can you review and update our existing documents?",
     ["Yes. Documents can become outdated, inconsistent, or no longer fit for purpose as a business evolves.",
      "TSQA reviews your current documentation against applicable standards, legal requirements, and best practice, identifies gaps and inconsistencies, and updates it to reflect how your business actually operates."],
     False),
    ("Do these documents cover both health and safety and quality?",
     ["Yes. TSQA's document creation and review services serve both pillars of the business, from health and safety policies, registers, and plans through to quality procedures and records.",
      "Whichever side you need support with, the aim is documentation that is practical, current, and aligned to the relevant standards."],
     False),
]

print("FAQ content loaded")


# ══════════════════════════════ PAGE ASSEMBLY ══════════════════════════════
PAGEMAP = {
    "home": "/", "services": "/health-safety/", "contact": "/contact/",
    "terms": "/terms/", "privacy": "/privacy/", "disclaimer": "/disclaimer/",
}


def transform_legacy(s):
    s = s.replace("mailto:contact@tsqa.co.nz", "mailto:" + EMAIL)
    s = s.replace("contact@tsqa.co.nz", EMAIL)
    s = re.sub(r'href="#"\s+onclick="showPage\(\'([^\']+)\'\)"',
               lambda m: 'href="' + PAGEMAP.get(m.group(1), "/") + '"', s)
    s = s.replace(" — ", ", ").replace("—", ",")
    return s


def read_src(name):
    with open(os.path.join(BUILD, "src_" + name + ".html"), encoding="utf-8") as fh:
        return transform_legacy(fh.read())


def build_home():
    body = f"""<main>

  <section class="hero">
    <div class="hero-bg-pattern" aria-hidden="true"></div>
    <div class="hero-grid parallax-hero" id="heroGrid" aria-hidden="true"></div>
    <div class="hero-content">
      <div class="hero-eyebrow">Bay of Plenty, Waikato, Auckland &amp; Taranaki</div>
      <h1 class="hero-title">
        Health &amp; Safety.<br>
        Quality Assurance.<br>
        <span>One Partner.</span>
      </h1>
      <p class="hero-sub">
        TSQA delivers end-to-end risk management, safety systems, and quality assurance services across Bay of Plenty, Waikato, Auckland and Taranaki giving your business the protection and compliance it needs to operate with confidence.
      </p>
      <div class="hero-actions">
        <a href="/contact/" class="btn-primary">Get a Free Consultation</a>
        <a href="/health-safety/" class="btn-secondary">Explore Services</a>
      </div>
    </div>
  </section>

  <section class="about-strip">
    <div class="about-inner">
      <div class="reveal">
        <div class="about-label">Who We Are</div>
        <h2 class="about-title">Built for businesses that can't afford to get it wrong</h2>
        <p class="about-text">
          TSQA is a New Zealand-based health, safety, and quality consultancy. We work alongside SMEs and contractors to build the systems, plans, and documentation that protect your people, satisfy your clients, and keep your business compliant.
        </p>
        <p class="about-text">
          What sets us apart is our end-to-end capability. From a first risk assessment through to pre-qualification, auditing, quality control, and document management. We cover both pillars of a well-run business under one roof.
        </p>
        <a href="/contact/" class="btn-primary" style="margin-top:8px;">Work With Us</a>
      </div>
      <div class="about-pillars reveal reveal-delay-2">
        <a class="pillar-card" href="/health-safety/">
          <div class="pillar-icon" aria-hidden="true">&#128737;&#65039;</div>
          <div class="pillar-name">Health &amp; Safety</div>
        </a>
        <a class="pillar-card" href="/quality/quality-assurance/">
          <div class="pillar-icon" aria-hidden="true">&#9989;</div>
          <div class="pillar-name">Quality Assurance</div>
        </a>
        <a class="pillar-card" href="/pre-qualification/">
          <div class="pillar-icon" aria-hidden="true">&#128203;</div>
          <div class="pillar-name">Pre-Qualification</div>
        </a>
        <a class="pillar-card" href="/health-safety/auditing/">
          <div class="pillar-icon" aria-hidden="true">&#128269;</div>
          <div class="pillar-name">Auditing &amp; Compliance</div>
        </a>
      </div>
    </div>
  </section>

  <div class="nz-banner reveal">
    <div class="nz-content">
      <div class="nz-flag" aria-hidden="true">&#127475;&#127487;</div>
      <h2 class="nz-title">Serving businesses across Bay of Plenty, Waikato, Auckland and Taranaki</h2>
      <p class="nz-text">Whether you're a contractor in Tauranga, an SME in Hamilton, or a project team anywhere in between, TSQA works with you on-site or remotely to get the job done.</p>
    </div>
  </div>

  <section class="diff-section">
    <div class="section-header reveal">
      <div class="section-label">Why TSQA</div>
      <h2 class="section-title">The complete picture, not half the solution</h2>
      <p class="section-sub">Most consultants do safety or quality. We do both and we build them together so nothing falls through the gaps.</p>
    </div>
    <div class="diff-grid">
      <div class="diff-card reveal reveal-delay-1">
        <div class="diff-num">01</div>
        <div class="diff-title">End-to-End Service</div>
        <p class="diff-text">Risk assessments, safety systems, pre-qualification, auditing, and quality control all under one roof, all working together.</p>
      </div>
      <div class="diff-card reveal reveal-delay-2">
        <div class="diff-num">02</div>
        <div class="diff-title">Plain-Language Practical</div>
        <p class="diff-text">We write and build things your team can actually use. No jargon, no filler just clear systems that work in the real world.</p>
      </div>
      <div class="diff-card reveal reveal-delay-3">
        <div class="diff-num">03</div>
        <div class="diff-title">Compliance That Holds Up</div>
        <p class="diff-text">Our documentation and systems are built to meet legal obligations, pass audits, and satisfy pre-qualification schemes including <a href="/pre-qualification/#impac">IMPAC</a>, <a href="/pre-qualification/#sitewise">SiteWise</a>, <a href="/pre-qualification/#she">SHE</a>, and <a href="/pre-qualification/#totika">T&#333;tika</a>.</p>
      </div>
    </div>
  </section>

{PROCESS_SECTION}

  <section class="home-cta reveal">
    <h2>Ready to protect your business?</h2>
    <p>Talk to the team at TSQA about your health, safety, or quality needs. We'll tell you exactly what you need and how we can help.</p>
    <a href="/contact/" class="btn-primary">Get in Touch Today</a>
  </section>

</main>"""
    render_page(
        "index.html",
        "Health, Safety & Quality Consultants NZ | TSQA",
        "NZ health, safety, pre-qualification, and quality consultants for SMEs and contractors across Bay of Plenty, Waikato, Auckland and Taranaki.",
        BASE + "/", body,
        [professional_service_ld()], gsc=True)


def build_prequal():
    trail = [("Home", "/"), ("Pre-Qualification", "/pre-qualification/")]
    all_faqs = (FAQ_PREQUAL_GENERAL + FAQ_IMPAC + FAQ_SITEWISE + FAQ_SHE + FAQ_TOTIKA)
    schemes = [
        ("impac", "IMPAC PREQUAL", "IMPAC PREQUAL", FAQ_IMPAC),
        ("sitewise", "SiteWise", "SiteWise", FAQ_SITEWISE),
        ("she", "SHE Pre-Qual", "SHE Pre-Qual", FAQ_SHE),
        ("totika", "T&#333;tika", "Tōtika", FAQ_TOTIKA),
    ]
    scheme_html = []
    for anchor, heading, key, faqs in schemes:
        scheme_html.append(
            f'  <div class="scheme-section" id="{anchor}">\n'
            f'    <h2>{heading}</h2>\n'
            f'    <p class="scheme-desc">{SERVICES[key]}</p>\n'
            f'{scheme_faq_html(heading + " FAQs", faqs, anchor + "-faqs")}\n'
            '  </div>'
        )
    body = f"""<main>

  <div class="services-hero">
    <h1>Contractor Pre-Qualification Support</h1>
    <p>Get pre-qualified and stay work-ready. TSQA helps New Zealand contractors and suppliers meet IMPAC PREQUAL, SiteWise, SHE Pre-Qual, and T&#333;tika.</p>
  </div>

  {breadcrumb_html(trail)}

  {leads_html([
      "Pre-qualification is how principals, councils, and main contractors check that a contractor manages health and safety to a recognised standard before awarding work. TSQA helps you build the systems and evidence these schemes look for, then prepares your submission.",
      "Below you will find a section on each major New Zealand scheme with its own answers to common questions. If you are not sure which one you need, start with the general questions and get in touch."])}

  <section class="section-intro reveal">
    <h2>Contractor &amp; Supplier Safety Management</h2>
    <p>{SERVICES['Contractor &amp; Supplier Safety Management']}</p>
  </section>

  {faq_section_html(FAQ_PREQUAL_GENERAL, "Pre-Qualification FAQs", "prequal-faqs")}

{chr(10).join(scheme_html)}

  {cta_bar_html("Ready to get pre-qualified?", "Tell us which clients or schemes you are working towards and we'll map out what you need.")}

</main>"""
    ld = [professional_service_ld(),
          service_ld("Contractor Pre-Qualification Support",
                     "TSQA supports New Zealand contractors and suppliers through pre-qualification schemes including IMPAC PREQUAL, SiteWise, SHE Pre-Qual, and Totika.",
                     ["Contractor &amp; Supplier Safety Management", "IMPAC PREQUAL",
                      "SiteWise", "SHE Pre-Qual", "Tōtika"]),
          breadcrumb_ld(trail),
          faqpage_ld(all_faqs)]
    render_page("pre-qualification/index.html",
                "Contractor Pre-Qualification Support NZ | TSQA",
                "IMPAC PREQUAL, SiteWise, SHE Pre-Qual and Totika support for NZ contractors. TSQA builds your safety evidence and prepares your submission.",
                BASE + "/pre-qualification/", body, ld)


def build_contact():
    trail = [("Home", "/"), ("Contact", "/contact/")]
    src = read_src("contact")
    # Process band sits directly under the hero (dark on dark), then the
    # breadcrumb leads into the white contact body.
    src = src.replace('<div class="contact-body">',
                      PROCESS_SECTION + '\n\n' + breadcrumb_html(trail)
                      + '\n\n  <div class="contact-body">', 1)
    body = "<main>\n\n  " + src + "\n\n</main>"
    ld = [professional_service_ld(), breadcrumb_ld(trail)]
    render_page("contact/index.html",
                "Contact TSQA | Health, Safety & Quality NZ",
                "Get in touch with TSQA for health, safety, pre-qualification, and quality support across Bay of Plenty, Waikato, Auckland and Taranaki.",
                BASE + "/contact/", body, ld)


def build_legal(name, out, title, desc, path):
    trail = [("Home", "/"), (title.split(" |")[0], path)]
    src = read_src(name)
    src = src.replace('<div class="legal-body">',
                      breadcrumb_html(trail) + '\n\n  <div class="legal-body">', 1)
    body = "<main>\n\n  " + src + "\n\n</main>"
    ld = [professional_service_ld(), breadcrumb_ld(trail)]
    render_page(out, title, desc, BASE + path, body, ld)


def build_404():
    body = """<main>
  <section class="notfound">
    <h1>404</h1>
    <p>Sorry, we couldn't find that page. It may have moved or no longer exists.</p>
    <div class="hero-actions" style="justify-content:center;">
      <a href="/" class="btn-primary">Back to Home</a>
      <a href="/contact/" class="btn-secondary">Contact TSQA</a>
    </div>
  </section>
</main>"""
    render_page("404.html", "Page Not Found | TSQA",
                "The page you were looking for could not be found. Return to the TSQA home page or get in touch with our team.",
                BASE + "/404.html", body, [professional_service_ld()])


HSE_ALL = ["Risk Assessments", "Workplace Safety Inspections",
           "Site Safety Plans &amp; Risk Assessments",
           "Safety Management Systems Development", "ISO 45001 System Setup",
           "Emergency Preparedness &amp; Response Plans", "Emergency Drills",
           "Incident &amp; Accident Investigation", "Safety Culture Assessment",
           "Safety Culture Improvement", "Internal Audits",
           "Supplier &amp; External Audits", "Hazardous Substances Registers",
           "SDS Management"]

QUALITY_ALL = ["ISO 9001:2015 QMS Implementation", "Internal Auditing",
               "Inspection &amp; Test Plan (ITP) Development",
               "Manufacturing Data Report (MDR) Compilation",
               "Visual Weld Inspection",
               "Welding Procedure Specification (WPS) Verification",
               "Welder Qualifications",
               "Material Traceability &amp; Certification Review",
               "Inspection &amp; Test Record (ITR) Management"]


def build_hubs_and_subpages():
    # ── Health & Safety hub ──
    hub_page(
        "health-safety/index.html",
        "Health & Safety Consultants NZ | TSQA",
        "TSQA's health and safety services for NZ businesses: risk management, safety systems, ISO 45001, incident investigation, safety culture, and auditing.",
        "/health-safety/",
        [("Home", "/"), ("Health & Safety", "/health-safety/")],
        "Health & Safety Services",
        "Practical health and safety support for New Zealand SMEs and contractors, from risk assessments to safety systems, incident investigation, and auditing.",
        ["TSQA helps you build health and safety systems that protect your people and stand up to scrutiny. We cover the full picture, from identifying risk on the ground to building the management systems, response plans, and audits that keep your business compliant.",
         "Explore the four areas below, or get in touch and we will point you to the right starting place for your business."],
        [("&#128737;&#65039;", "Risk & Safety Management", "/health-safety/risk-management/",
          "Risk assessments, workplace safety inspections, and site safety plans that give you a clear picture of your hazards and how to manage them."),
         ("&#9881;&#65039;", "Safety Systems & Preparedness", "/health-safety/safety-systems/",
          "Safety management systems, ISO 45001 setup, and emergency preparedness plans and drills built to be used in the real world."),
         ("&#128300;", "Incident & Culture Improvement", "/health-safety/incident-culture/",
          "Incident and accident investigation plus safety culture assessment and improvement that drive genuine change."),
         ("&#128202;", "Auditing & Compliance", "/health-safety/auditing/",
          "Internal and supplier audits, hazardous substances registers, and SDS management to keep your systems honest and compliant.")],
        FAQ_HS_HUB,
        "Health and Safety Services",
        "End-to-end health and safety consultancy for New Zealand SMEs and contractors.",
        HSE_ALL,
        "Not sure where to start?",
        "Get in touch and we'll help you work out which health and safety support your business needs first.")

    # ── HSE subpages ──
    service_subpage(
        "health-safety/risk-management/index.html",
        "Risk Assessments & Safety Inspections NZ | TSQA",
        "Site-specific risk assessments, workplace safety inspections, and site safety plans for NZ businesses under the Health and Safety at Work Act 2015.",
        "/health-safety/risk-management/",
        [("Home", "/"), ("Health & Safety", "/health-safety/"), ("Risk & Safety Management", "/health-safety/risk-management/")],
        "Risk & Safety Management",
        "Understand where your business is exposed and how to manage it, with practical, site-specific risk assessments, inspections, and plans.",
        ["Managing risk is the foundation of health and safety. TSQA identifies the hazards specific to your operations, evaluates them, and sets out clear, workable controls, so you know exactly where you stand and what to do next."],
        "&#128737;&#65039;", "Risk & Safety Management Services",
        ["Risk Assessments", "Workplace Safety Inspections", "Site Safety Plans &amp; Risk Assessments"],
        FAQ_RISK,
        [("Health & Safety overview", "/health-safety/"),
         ("Safety Systems & Preparedness", "/health-safety/safety-systems/"),
         ("Auditing & Compliance", "/health-safety/auditing/")],
        "Need a risk assessment or site safety plan?",
        "Tell us about your site or project and we'll scope exactly what you need.",
        "Risk & Safety Management",
        "Risk assessments, workplace safety inspections, and site safety plans built to meet obligations under the Health and Safety at Work Act 2015.")

    service_subpage(
        "health-safety/safety-systems/index.html",
        "Safety Management Systems & ISO 45001 Setup NZ | TSQA",
        "TSQA builds safety management systems and sets up your system to the ISO 45001 framework, plus emergency response plans and drills for NZ businesses.",
        "/health-safety/safety-systems/",
        [("Home", "/"), ("Health & Safety", "/health-safety/"), ("Safety Systems & Preparedness", "/health-safety/safety-systems/")],
        "Safety Systems & Preparedness",
        "The systems and plans that hold everything together, from your safety management system and ISO 45001 setup to emergency response plans and drills.",
        ["A safety management system is the backbone of a compliant business. TSQA designs systems that your team can actually use and, where you want an internationally recognised benchmark, we set your system up to the ISO 45001 framework. We also make sure you are ready for the unexpected with clear emergency plans and tested drills."],
        "&#9881;&#65039;", "Safety Systems & Preparedness Services",
        ["Safety Management Systems Development", "ISO 45001 System Setup",
         "Emergency Preparedness &amp; Response Plans", "Emergency Drills"],
        FAQ_SAFETY_SYS,
        [("Health & Safety overview", "/health-safety/"),
         ("Contractor Pre-Qualification", "/pre-qualification/"),
         ("Risk & Safety Management", "/health-safety/risk-management/")],
        "Ready to build your safety system?",
        "Whether you are starting from scratch or working towards ISO 45001, we'll set the right foundations.",
        "Safety Systems & Preparedness",
        "Safety management system development, ISO 45001 system setup, and emergency preparedness planning and drills.")

    service_subpage(
        "health-safety/incident-culture/index.html",
        "Incident Investigation & Safety Culture NZ | TSQA",
        "Impartial incident and accident investigation plus safety culture assessment and improvement to help NZ businesses learn and get better.",
        "/health-safety/incident-culture/",
        [("Home", "/"), ("Health & Safety", "/health-safety/"), ("Incident & Culture Improvement", "/health-safety/incident-culture/")],
        "Incident & Culture Improvement",
        "Learn from what goes wrong and build a workplace where safety is genuinely valued, through investigation, assessment, and practical improvement.",
        ["When something goes wrong, the response matters. TSQA runs thorough, impartial investigations that find root causes rather than surface blame, then helps you shift your safety culture so improvements actually stick."],
        "&#128300;", "Incident & Culture Improvement Services",
        ["Incident &amp; Accident Investigation", "Safety Culture Assessment", "Safety Culture Improvement"],
        FAQ_INCIDENT,
        [("Health & Safety overview", "/health-safety/"),
         ("Risk & Safety Management", "/health-safety/risk-management/"),
         ("Auditing & Compliance", "/health-safety/auditing/")],
        "Had an incident, or want to improve your culture?",
        "Get in touch to talk through an investigation or a culture assessment for your team.",
        "Incident & Culture Improvement",
        "Incident and accident investigation, safety culture assessment, and safety culture improvement.")

    service_subpage(
        "health-safety/auditing/index.html",
        "Health & Safety Auditing & Compliance NZ | TSQA",
        "Internal and supplier audits, hazardous substances registers, and SDS management to keep your NZ health and safety systems compliant and audit-ready.",
        "/health-safety/auditing/",
        [("Home", "/"), ("Health & Safety", "/health-safety/"), ("Auditing & Compliance", "/health-safety/auditing/")],
        "Auditing & Compliance",
        "Keep your systems honest and your compliance in order, with internal and supplier audits, hazardous substances registers, and SDS management.",
        ["Good systems need checking. TSQA audits your processes and your suppliers against your health and safety requirements, and keeps your hazardous substances registers and Safety Data Sheets accurate and accessible, so you can meet your obligations with confidence."],
        "&#128202;", "Auditing & Compliance Services",
        ["Internal Audits", "Supplier &amp; External Audits", "Hazardous Substances Registers", "SDS Management"],
        FAQ_AUDITING,
        [("Health & Safety overview", "/health-safety/"),
         ("Contractor Pre-Qualification", "/pre-qualification/"),
         ("Safety Systems & Preparedness", "/health-safety/safety-systems/")],
        "Need an audit or a compliant register?",
        "Get in touch and we'll help you close the gaps before an external party finds them.",
        "Auditing & Compliance",
        "Internal audits, supplier and external audits, hazardous substances registers, and SDS management.")

    # ── Quality hub ──
    hub_page(
        "quality/index.html",
        "Quality Assurance & Control Consultants NZ | TSQA",
        "TSQA's quality services for NZ businesses: ISO 9001 systems, ITPs, MDRs, weld inspection, WPS verification, welder qualifications, and traceability.",
        "/quality/",
        [("Home", "/"), ("Quality", "/quality/")],
        "Quality Services",
        "Quality assurance and quality control for New Zealand businesses, from ISO 9001 systems to hands-on weld inspection and material traceability.",
        ["TSQA helps you build quality in and prove it. On the assurance side we develop the systems, plans, and records that keep quality consistent. On the control side we carry out the inspections and verifications that confirm the work meets standard.",
         "Explore quality assurance and quality control below, or get in touch to talk through what your project or contract requires."],
        [("&#127941;", "Quality Assurance", "/quality/quality-assurance/",
          "ISO 9001:2015 implementation, internal auditing, inspection and test plans, and manufacturing data reports that build quality into your systems."),
         ("&#128295;", "Quality Control", "/quality/quality-control/",
          "Visual weld inspection, WPS verification, welder qualifications, material traceability, and inspection and test records that verify the work.")],
        FAQ_QUALITY_HUB,
        "Quality Assurance and Control",
        "Quality assurance and quality control services for New Zealand businesses.",
        QUALITY_ALL,
        "Not sure what your contract needs?",
        "Get in touch and we'll help you work out the quality support your project requires.")

    service_subpage(
        "quality/quality-assurance/index.html",
        "ISO 9001 QMS Implementation NZ | TSQA",
        "ISO 9001:2015 quality management system implementation, internal auditing, ITP development, and MDR compilation for New Zealand businesses.",
        "/quality/quality-assurance/",
        [("Home", "/"), ("Quality", "/quality/"), ("Quality Assurance", "/quality/quality-assurance/")],
        "Quality Assurance",
        "Build quality into how you work, with ISO 9001 systems, internal auditing, inspection and test plans, and manufacturing data reports.",
        ["Quality assurance is about the systems that prevent problems before they happen. TSQA implements ISO 9001:2015 quality management systems from the ground up and builds the plans and records, from ITPs to MDRs, that give your clients confidence and your team a clear framework."],
        "&#127941;", "Quality Assurance Services",
        ["ISO 9001:2015 QMS Implementation", "Internal Auditing",
         "Inspection &amp; Test Plan (ITP) Development",
         "Manufacturing Data Report (MDR) Compilation"],
        FAQ_QA,
        [("Quality overview", "/quality/"),
         ("Quality Control", "/quality/quality-control/"),
         ("Document Creation & Review", "/documents/")],
        "Building a quality management system?",
        "Talk to us about ISO 9001 implementation or the quality records your contract requires.",
        "Quality Assurance",
        "ISO 9001:2015 QMS implementation, internal auditing, inspection and test plan development, and manufacturing data report compilation.")

    service_subpage(
        "quality/quality-control/index.html",
        "Weld Inspection & Quality Control NZ | TSQA",
        "Visual weld inspection, WPS verification, welder qualifications, material traceability, and ITR management for New Zealand fabrication and construction.",
        "/quality/quality-control/",
        [("Home", "/"), ("Quality", "/quality/"), ("Quality Control", "/quality/quality-control/")],
        "Quality Control",
        "Verify the work meets standard, with visual weld inspection, WPS verification, welder qualifications, material traceability, and ITR management.",
        ["Quality control is where standards are checked and proven. TSQA's inspectors carry out visual weld inspections, verify welding procedures and welder qualifications, review material traceability, and manage inspection and test records, so you can demonstrate that the work meets specification."],
        "&#128295;", "Quality Control Services",
        ["Visual Weld Inspection", "Welding Procedure Specification (WPS) Verification",
         "Welder Qualifications", "Material Traceability &amp; Certification Review",
         "Inspection &amp; Test Record (ITR) Management"],
        FAQ_QC,
        [("Quality overview", "/quality/"),
         ("Quality Assurance", "/quality/quality-assurance/")],
        "Need weld inspection or quality control?",
        "Get in touch and we'll scope the inspection and verification your project needs.",
        "Quality Control",
        "Visual weld inspection, WPS verification, welder qualification checks, material traceability and certification review, and ITR management.")

    # ── Documents (serves both pillars) ──
    service_subpage(
        "documents/index.html",
        "Document Creation & Review NZ | TSQA",
        "TSQA creates and reviews health, safety, and quality documents for NZ businesses: policies, procedures, forms, registers, and plans in plain language.",
        "/documents/",
        [("Home", "/"), ("Documents", "/documents/")],
        "Document Creation & Review",
        "Clear, fit-for-purpose documentation for both sides of your business, from health and safety policies and registers to quality procedures and records.",
        ["Good documentation is practical, current, and actually used. TSQA creates documents tailored to your business and industry, and reviews your existing ones against applicable standards and legislation. Our document services support both the health and safety and the quality pillars of your business."],
        "&#128196;", "Our Document Services",
        ["Document Creation", "Document Review"],
        FAQ_DOCS,
        [("Health & Safety", "/health-safety/"),
         ("Quality", "/quality/"),
         ("Contact TSQA", "/contact/")],
        "Need documents created or reviewed?",
        "Tell us what you need and we'll build documentation your team can actually use.",
        "Document Creation & Review",
        "Creation and review of health, safety, and quality documentation including policies, procedures, forms, registers, and plans.")


# ── Crawlability + assets ──────────────────────────────────────────────────
SITEMAP_PAGES = [
    ("/", "1.0"),
    ("/health-safety/", "0.9"),
    ("/health-safety/risk-management/", "0.8"),
    ("/health-safety/safety-systems/", "0.8"),
    ("/health-safety/incident-culture/", "0.8"),
    ("/health-safety/auditing/", "0.8"),
    ("/pre-qualification/", "0.9"),
    ("/quality/", "0.9"),
    ("/quality/quality-assurance/", "0.8"),
    ("/quality/quality-control/", "0.8"),
    ("/documents/", "0.7"),
    ("/contact/", "0.7"),
    ("/terms/", "0.3"),
    ("/privacy/", "0.3"),
    ("/disclaimer/", "0.3"),
]
LASTMOD = "2026-07-12"

ROBOTS = """User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

Sitemap: https://tsqa.co.nz/sitemap.xml
"""

SITE_JS = """// TSQA shared site behaviour (Rev 2 multi-page).
function toggleMenu() {
  var links = document.getElementById('navLinks');
  var btn = document.getElementById('hamburger');
  var open = links.classList.toggle('open');
  if (btn) { btn.setAttribute('aria-expanded', open ? 'true' : 'false'); }
}

window.addEventListener('scroll', function () {
  var nav = document.getElementById('navbar');
  if (nav) {
    if (window.scrollY > 40) { nav.classList.add('scrolled'); }
    else { nav.classList.remove('scrolled'); }
  }
  var grid = document.getElementById('heroGrid');
  if (grid) { grid.style.transform = 'translateY(' + (window.scrollY * 0.25) + 'px)'; }
});

function observeReveal() {
  var reveals = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) {
    reveals.forEach(function (el) { el.classList.add('visible'); });
    return;
  }
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  reveals.forEach(function (el) { observer.observe(el); });
}

async function submitForm() {
  var required = ['f-first', 'f-email', 'f-service'];
  var valid = true;
  required.forEach(function (id) {
    var el = document.getElementById(id);
    if (!el.value.trim()) {
      el.style.borderColor = '#e05252';
      valid = false;
      setTimeout(function () { el.style.borderColor = ''; }, 2000);
    }
  });
  if (!valid) return;

  var btn = document.querySelector('.form-submit');
  btn.textContent = 'Sending...';
  btn.disabled = true;

  var data = {
    firstName: document.getElementById('f-first').value,
    lastName: document.getElementById('f-last').value,
    company: document.getElementById('f-company').value,
    email: document.getElementById('f-email').value,
    phone: document.getElementById('f-phone').value,
    service: document.getElementById('f-service').value,
    message: document.getElementById('f-message').value
  };

  try {
    var response = await fetch('https://formspree.io/f/xvznypvy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(data)
    });
    if (response.ok) {
      document.getElementById('contactFormWrap').style.display = 'none';
      document.getElementById('formSuccess').style.display = 'block';
    } else {
      btn.textContent = 'Something went wrong. Try again.';
      btn.disabled = false;
    }
  } catch (err) {
    btn.textContent = 'Something went wrong. Try again.';
    btn.disabled = false;
  }
}

document.addEventListener('DOMContentLoaded', observeReveal);
"""


def write_assets():
    # Shared stylesheet
    with open(os.path.join(BUILD, "_base.css"), encoding="utf-8") as fh:
        css = fh.read()
    with open(os.path.join(ROOT, "styles.css"), "w", encoding="utf-8") as fh:
        fh.write(css)
    print("wrote styles.css")

    with open(os.path.join(ROOT, "site.js"), "w", encoding="utf-8") as fh:
        fh.write(SITE_JS)
    print("wrote site.js")

    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as fh:
        fh.write(ROBOTS)
    print("wrote robots.txt")

    urls = "\n".join(
        f'  <url>\n    <loc>{BASE}{p}</loc>\n    <lastmod>{LASTMOD}</lastmod>\n'
        f'    <priority>{pr}</priority>\n  </url>'
        for p, pr in SITEMAP_PAGES)
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + urls + "\n</urlset>\n")
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write(sitemap)
    print("wrote sitemap.xml")


def build_all():
    build_home()
    build_hubs_and_subpages()
    build_prequal()
    build_contact()
    build_legal("terms", "terms/index.html", "Terms & Conditions | TSQA",
                "The terms and conditions governing use of the TSQA website.",
                "/terms/")
    build_legal("privacy", "privacy/index.html", "Privacy Policy | TSQA",
                "How TSQA collects, uses, and protects your personal information under the Privacy Act 2020.",
                "/privacy/")
    build_legal("disclaimer", "disclaimer/index.html", "Disclaimer | TSQA",
                "Important information about the general nature of content on the TSQA website and your health and safety duties.",
                "/disclaimer/")
    build_404()
    write_assets()
    print("\nBuild complete.")


if __name__ == "__main__":
    build_all()
