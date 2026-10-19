"""Turn files dropped into Inbox/ into vault notes. Never calls an LLM.

    python .claude/scripts/ingest.py                  # process Inbox/, print manifest
    python .claude/scripts/ingest.py --max-pages 20   # smaller batch (default 60)
    python .claude/scripts/ingest.py --finish x.pdf   # after the transcript is written
    python .claude/scripts/ingest.py --figure x.pdf 12 "Endsley Model"  # page -> image
    python .claude/scripts/ingest.py --selftest       # temp vault, asserts, prints ok

Two paths, chosen per file:
- Typed pdf/pptx/docx/epub: markitdown extracts the text and the script writes the
  source note itself, then moves the raw file to Sources/.
- Handwritten pdf (GoodNotes producer, or a text layer too thin to be real): pages
  are rendered to PNG and listed in the JSON manifest on stdout. The /ingest skill
  transcribes them, writes the note, then calls --finish to move the raw file. The
  raw file only leaves Inbox/ once its note exists, so a crash loses nothing.

--figure saves one page of a raw PDF (in Inbox/ or Sources/) as a PNG in
System/Attachments/, so a Concept note can embed the diagram. Whole page, not a crop.

Re-ingest matches by filename: same `source_hash:` -> skip, changed -> rewrite the
whole note (no per-page hashing yet). Failures go to Inbox/_failed/ with a .log.
"""

import hashlib
import json
import shutil
import sys
import tempfile
import traceback
from datetime import date
from pathlib import Path

import pymupdf
from markitdown import MarkItDown

# ponytail: pre-flatten target. Phase 2 of the v2 spec changes this one line to "Notes".
NOTES_DIR = "Notes"
ATTACHMENTS_DIR = "System/Attachments"  # = attachmentFolderPath in .obsidian/app.json
TYPED = {".pdf", ".pptx", ".docx", ".epub"}
WORK = Path(tempfile.gettempdir()) / "vault-ingest"
# A real typed page carries hundreds of characters; GoodNotes' stray OCR layer a handful.
MIN_CHARS_PER_PAGE = 20
MIN_LETTER_RATIO = 0.5
# GoodNotes exported via the iPad share sheet says "iOS Version ... Quartz PDFContext",
# not "GoodNotes", and carries a junk OCR layer that passes the text checks below.
# ponytail: any iPad export counts as handwritten; a typed one just costs a transcription.
IPAD_PRODUCER = "ios version"
FIGURE_DPI = 150
# Illegal in a Windows filename, or breaks the ![[...]] embed that points at it.
BAD_TITLE_CHARS = set('\\/:*?"<>|[]#^')


class RawFile:
    """One file in Inbox/: what it is, how big, and its content fingerprint."""

    def __init__(self, path):
        self.path = path
        self.hash = hashlib.sha256(path.read_bytes()).hexdigest()
        self.note_name = "%s (Source).md" % path.stem

    @property
    def is_pdf(self):
        return self.path.suffix.lower() == ".pdf"

    def pages(self):
        if not self.is_pdf:
            return 1  # pptx/docx/epub have no cheap page count; budget them as one
        with pymupdf.open(self.path) as doc:
            return doc.page_count

    def is_handwritten(self):
        if not self.is_pdf:
            return False
        with pymupdf.open(self.path) as doc:
            producer = (doc.metadata.get("producer") or "").lower()
            if "goodnotes" in producer or producer.startswith(IPAD_PRODUCER):
                return True
            text = "".join(page.get_text() for page in doc).strip()
            letters = sum(c.isalnum() or c.isspace() for c in text)
            return (len(text) < MIN_CHARS_PER_PAGE * doc.page_count
                    or letters / len(text) < MIN_LETTER_RATIO)

    def render_pages(self):
        """PNG per page for Claude to read. 150 dpi keeps handwriting legible."""
        out = WORK / self.path.stem
        shutil.rmtree(out, ignore_errors=True)
        out.mkdir(parents=True)
        pngs = []
        with pymupdf.open(self.path) as doc:
            for number, page in enumerate(doc, start=1):
                png = out / ("page-%03d.png" % number)
                page.get_pixmap(dpi=150).save(png)
                pngs.append(str(png))
        return pngs


class SourceNote:
    """The vault note that stands for one raw file: reads its hash, writes it fresh."""

    def __init__(self, path):
        self.path = path

    def frontmatter(self, key):
        if not self.path.exists():
            return None
        for line in self.path.read_text(encoding="utf-8").split("\n---", 1)[0].splitlines():
            if line.startswith(key + ":"):
                return line.split(":", 1)[1].strip().strip("'\"")
        return None

    def is_current(self, raw):
        return self.frontmatter("source_hash") == raw.hash

    def is_owners(self):
        """A note that lost `source: claude` belongs to the owner; never overwrite it."""
        return self.path.exists() and self.frontmatter("source") != "claude"

    def write(self, raw, body):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            "---\nnote_type: Source\ncreated: %s\nsource: claude\n"
            'source_file: "[[%s]]"\nsource_hash: %s\nproject:\ntags: []\n---\n\n%s\n'
            % (date.today().isoformat(), raw.path.name, raw.hash, _escape_templater(body)),
            encoding="utf-8")


class Ingest:
    """One pass over Inbox/: route each file, respect the page budget, report."""

    def __init__(self, vault, max_pages=60):
        self.inbox = vault / "Inbox"
        self.failed = self.inbox / "_failed"
        self.sources = vault / "Sources"
        self.notes = vault / NOTES_DIR
        self.attachments = vault / ATTACHMENTS_DIR
        self.budget = max_pages
        self.report = {"written": [], "skipped": [], "transcribe": [],
                       "deferred": [], "failed": []}

    def run(self):
        self.inbox.mkdir(exist_ok=True)
        for path in sorted(p for p in self.inbox.iterdir() if p.is_file()):
            try:
                self._process(RawFile(path))
            except Exception:
                self._fail(path, traceback.format_exc())
        return self.report

    def finish(self, name):
        """Move a transcribed file out of Inbox/, but only once its note is current."""
        raw = RawFile(self.inbox / name)
        if not SourceNote(self.notes / raw.note_name).is_current(raw):
            raise SystemExit("No note with source_hash %s for %s yet." % (raw.hash[:8], name))
        self._archive(raw)

    def figure(self, name, page, title):
        """Save one page of a raw PDF as `<title>.png` for a Concept note to embed."""
        if BAD_TITLE_CHARS & set(title):
            raise SystemExit("Title %r may not contain any of %s."
                             % (title, "".join(sorted(BAD_TITLE_CHARS))))
        raw = next((d / name for d in (self.inbox, self.sources) if (d / name).is_file()), None)
        if raw is None or raw.suffix.lower() != ".pdf":
            raise SystemExit("%s is not a PDF in Inbox/ or Sources/." % name)
        target = self.attachments / (title + ".png")
        if target.exists():
            raise SystemExit("%s already exists; pick another title." % target.name)
        with pymupdf.open(raw) as doc:
            if not 1 <= page <= doc.page_count:
                raise SystemExit("%s has pages 1-%d, not %d." % (name, doc.page_count, page))
            self.attachments.mkdir(parents=True, exist_ok=True)
            doc[page - 1].get_pixmap(dpi=FIGURE_DPI).save(target)
        return target

    def _process(self, raw):
        if raw.path.suffix.lower() not in TYPED:
            return self._fail(raw.path, "Unsupported format %r. Handled: %s."
                              % (raw.path.suffix, ", ".join(sorted(TYPED))))
        note = SourceNote(self.notes / raw.note_name)
        if note.is_owners():
            return self._fail(raw.path, "%s exists without `source: claude`; it is the "
                                        "owner's note and is never overwritten." % note.path.name)
        if note.is_current(raw):
            self._archive(raw)
            return self.report["skipped"].append(raw.path.name)
        pages = raw.pages()
        # A file bigger than the whole budget still runs alone, or it would never run.
        if pages > self.budget and self._spent_anything():
            return self.report["deferred"].append(raw.path.name)
        self.budget -= pages
        if raw.is_handwritten():
            self.report["transcribe"].append({
                "file": raw.path.name, "note": str(note.path), "source_hash": raw.hash,
                "update": note.path.exists(), "pages": raw.render_pages()})
        else:
            note.write(raw, MarkItDown().convert(str(raw.path)).text_content.strip())
            self._archive(raw)
            self.report["written"].append(str(note.path))

    def _spent_anything(self):
        return bool(self.report["written"] or self.report["transcribe"])

    def _archive(self, raw):
        """Raw files in Sources/ are never deleted: a changed re-drop keeps the old one."""
        self.sources.mkdir(exist_ok=True)
        target = self.sources / raw.path.name
        if target.exists() and RawFile(target).hash != raw.hash:
            old = RawFile(target).hash[:8]
            target.rename(target.with_name("%s.%s%s" % (target.stem, old, target.suffix)))
        shutil.move(str(raw.path), str(target))

    def _fail(self, path, reason):
        self.failed.mkdir(exist_ok=True)
        shutil.move(str(path), str(self.failed / path.name))
        (self.failed / (path.name + ".log")).write_text(reason, encoding="utf-8")
        self.report["failed"].append(path.name)


def _escape_templater(text):
    """Extracted text may quote `<%`; Templater would execute it on file creation."""
    return text.replace("<%", "<\\%")


def _selftest():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        inbox = vault / "Inbox"
        inbox.mkdir()
        _make_pdf(inbox / "Typed.pdf", text="Retrieval practice beats rereading. <% x %>")
        _make_pdf(inbox / "Notizen.pdf", producer="GoodNotes 6")
        _make_pdf(inbox / "iPad.pdf", text="Wies ein Mensch auch ein Sprachmodel sind Impul",
                  producer="iOS Version 18.6.2 (Build 22G100) Quartz PDFContext")
        (inbox / "junk.xyz").write_text("?")

        report = Ingest(vault).run()
        note = vault / NOTES_DIR / "Typed (Source).md"
        text = note.read_text(encoding="utf-8")
        assert report["written"] == [str(note)], report
        assert text.startswith("---\nnote_type: Source\n"), text
        assert 'source_file: "[[Typed.pdf]]"' in text and "Retrieval practice" in text, text
        assert "<\\% x %>" in text, text
        assert (vault / "Sources/Typed.pdf").exists() and not (inbox / "Typed.pdf").exists()
        assert (inbox / "_failed/junk.xyz.log").exists(), report

        ipad, job = report["transcribe"]
        assert ipad["file"] == "iPad.pdf", "iPad export with OCR text is still handwritten"
        assert job["file"] == "Notizen.pdf" and len(job["pages"]) == 1, job
        assert Path(job["pages"][0]).exists() and (inbox / "Notizen.pdf").exists()
        transcript = Path(job["note"])
        transcript.write_text("---\nnote_type: Transcript\nsource: claude\nsource_hash: %s\n"
                              "---\n## Page 1\n" % job["source_hash"], encoding="utf-8")
        Ingest(vault).finish("Notizen.pdf")
        assert (vault / "Sources/Notizen.pdf").exists() and not (inbox / "Notizen.pdf").exists()

        shutil.copy(vault / "Sources/Typed.pdf", inbox / "Typed.pdf")
        again = Ingest(vault).run()
        assert again["skipped"] == ["Typed.pdf"] and not again["written"], again
        assert not (inbox / "Typed.pdf").exists()

        image = Ingest(vault).figure("Notizen.pdf", 1, "Notizen Sketch")
        assert image == vault / ATTACHMENTS_DIR / "Notizen Sketch.png" and image.exists()
        for args in [("Notizen.pdf", 1, "Notizen Sketch"), ("Notizen.pdf", 2, "Other"),
                     ("Notizen.pdf", 0, "Other"), ("Notizen.pdf", 1, "A/B"), ("None.pdf", 1, "X")]:
            try:
                Ingest(vault).figure(*args)
            except SystemExit:
                continue
            raise AssertionError("figure%r should refuse" % (args,))

        _make_pdf(inbox / "Typed.pdf", text="Changed: spacing beats cramming, every time.")
        changed = Ingest(vault).run()
        assert changed["written"] == [str(note)], changed
        assert "spacing beats cramming" in note.read_text(encoding="utf-8")
        assert len(list((vault / "Sources").glob("Typed*.pdf"))) == 2, "old raw file kept"
    print("ok")


def _make_pdf(path, text="", producer=""):
    with pymupdf.open() as doc:
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), text)
        else:
            page.draw_line((72, 72), (300, 200))
        doc.set_metadata({"producer": producer})
        doc.save(path)


def _arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


if __name__ == "__main__":
    from tidy import VAULT

    if "--selftest" in sys.argv:
        _selftest()
    elif "--finish" in sys.argv:
        Ingest(VAULT).finish(_arg("--finish"))
        print("moved %s to Sources/" % _arg("--finish"))
    elif "--figure" in sys.argv:
        name, page, title = sys.argv[sys.argv.index("--figure") + 1:][:3]
        print(Ingest(VAULT).figure(name, int(page), title))
    else:
        result = Ingest(VAULT, int(_arg("--max-pages", 60))).run()
        print(json.dumps(result, indent=2, ensure_ascii=False))
