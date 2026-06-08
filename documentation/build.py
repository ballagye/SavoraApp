# -*- coding: utf-8 -*-
"""Génère les PDF de documentation Savora (pandoc + Chrome headless)."""
import subprocess, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "src")
ROOT = os.path.dirname(HERE)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

CSS = r"""
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Calibri, Arial, sans-serif; color: #1f2937;
       font-size: 11pt; line-height: 1.5; margin: 0; }
h1 { color: #18181B; font-size: 19pt; border-bottom: 3px solid #C9963A;
     padding-bottom: 6px; margin: 26px 0 14px; page-break-after: avoid; }
h2 { color: #8a6a28; font-size: 14pt; margin: 20px 0 10px; page-break-after: avoid; }
h3 { color: #374151; font-size: 12pt; margin: 16px 0 8px; page-break-after: avoid; }
p { margin: 8px 0; }
code { background: #f3f4f6; padding: 1px 5px; border-radius: 4px;
       font-family: 'Consolas', monospace; font-size: 9.5pt; color: #b45309; }
pre { background: #1a1a1f; color: #e5e7eb; padding: 14px 16px; border-radius: 8px;
      font-family: 'Consolas', monospace; font-size: 8.5pt; line-height: 1.35;
      overflow-x: auto; page-break-inside: avoid; }
pre code { background: none; color: inherit; padding: 0; }
pre.mermaid { background: #ffffff; color: #1f2937; text-align: center; border: none; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 10pt;
        page-break-inside: avoid; }
th { background: #C9963A; color: #18181B; text-align: left; padding: 7px 10px;
     font-weight: 700; }
td { border: 1px solid #e5e7eb; padding: 6px 10px; vertical-align: top; }
tr:nth-child(even) td { background: #faf8f3; }
hr { border: none; border-top: 1px solid #d1d5db; margin: 16px 0; }
strong { color: #18181B; }
blockquote { border-left: 4px solid #C9963A; background: #faf8f3; margin: 12px 0;
             padding: 8px 16px; color: #4b5563; }
ul, ol { margin: 8px 0; padding-left: 24px; }
li { margin: 3px 0; }
.cover { text-align: center; padding: 60px 20px 40px; page-break-after: always; }
.cover h1 { font-size: 32pt; border: none; color: #18181B; margin-bottom: 6px; }
.cover h2 { font-size: 18pt; color: #8a6a28; }
.cover hr { width: 40%; margin: 24px auto; border-top: 2px solid #C9963A; }
.cover p { color: #4b5563; line-height: 1.8; }
.pagebreak { page-break-before: always; }
.titlebox { border-left: 5px solid #C9963A; background: #faf8f3; padding: 10px 18px;
            margin-bottom: 18px; }
.titlebox h1 { border: none; font-size: 20pt; margin: 4px 0; }
.titlebox p { color: #4b5563; margin: 2px 0; font-size: 10pt; }
"""

WRAP = """<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<style>{css}</style>
<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
mermaid.initialize({{ startOnLoad: true, theme: 'neutral',
  themeVariables: {{ primaryColor:'#faf8f3', primaryBorderColor:'#C9963A',
                     lineColor:'#8a6a28', fontFamily:'Segoe UI' }} }});
window.addEventListener('load', () => {{ setTimeout(() => {{ document.title='ready'; }}, 100); }});
</script></head><body>{body}</body></html>"""


def md_to_html(md_path):
    out = subprocess.run(
        ["pandoc", md_path, "-f", "markdown+fenced_divs+pipe_tables", "-t", "html"],
        capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        print("PANDOC ERROR:", out.stderr); sys.exit(1)
    return out.stdout


def build(body_html, out_pdf, has_mermaid):
    html_path = out_pdf.replace(".pdf", ".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(WRAP.format(css=CSS, body=body_html))
    budget = 12000 if has_mermaid else 3000
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", f"--virtual-time-budget={budget}",
                    f"--print-to-pdf={out_pdf}", html_path],
                   capture_output=True)
    size = os.path.getsize(out_pdf) if os.path.exists(out_pdf) else 0
    print(f"  -> {os.path.basename(out_pdf)}  ({size//1024} Ko)")


def build_full(src_html, out_pdf):
    """Imprime un fichier HTML autonome (avec ses propres règles @page)."""
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", "--virtual-time-budget=4000",
                    f"--print-to-pdf={out_pdf}", src_html], capture_output=True)
    size = os.path.getsize(out_pdf) if os.path.exists(out_pdf) else 0
    print(f"  -> {os.path.basename(out_pdf)}  ({size//1024} Ko)")


JOBS = [
    ("md",   os.path.join(SRC, "cahier_des_charges.md"),  "Cahier_des_charges_Savora.pdf",   False),
    ("full", os.path.join(SRC, "doc_technique_pro.html"), "Documentation_technique_SavoraApp.pdf", False),
    ("full", os.path.join(SRC, "doc_technique_web.html"), "Documentation_technique_SavoraWeb.pdf", False),
    ("md",   os.path.join(SRC, "guide_utilisateur.md"),   "Guide_utilisateur_ClientLourd_Savora.pdf", False),
    ("body", os.path.join(SRC, "diagrammes_uml.htmlbody"), "Diagrammes_UML_Savora.pdf",       True),
    ("body", os.path.join(SRC, "maquette.htmlbody"),       "Maquette_Savora.pdf",             True),
]

if __name__ == "__main__":
    for kind, src, name, mermaid in JOBS:
        print(f"Building {name} ...")
        if kind == "full":
            build_full(src, os.path.join(HERE, name))
        else:
            body = md_to_html(src) if kind == "md" else open(src, encoding="utf-8").read()
            build(body, os.path.join(HERE, name), mermaid)
    print("\nTerminé. PDF dans :", HERE)
