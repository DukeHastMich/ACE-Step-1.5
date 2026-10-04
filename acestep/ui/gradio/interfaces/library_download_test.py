"""Verify direct downloads stay in the library and preserve formats and menu actions."""

from html.parser import HTMLParser
from pathlib import Path
import tempfile
import unittest
from urllib.parse import unquote

from .library_download import download_link
from .library_rows import render_song_rows


class LinkParser(HTMLParser):
    """Collect the download link's decoded attributes."""
    def handle_starttag(self, tag, attrs):
        """Capture anchors for assertions."""
        if tag == "a":
            self.link = dict(attrs)


class DownloadTests(unittest.TestCase):
    """Use temporary audio; no desktop downloads are triggered by these tests."""
    def test_menu_link_and_safe_title(self):
        """Download uses original bytes, a safe title, and the existing Gradio route."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "mix #1 & take.mp3"
            path.write_bytes(b"original audio")
            song = dict(path=path.name, title='Night / Sky <live>', style="folk",
                        created="Today", duration="4:00", format="MP3")
            html = render_song_rows([song], root)
            parser = LinkParser()
            parser.feed(html)
            self.assertEqual(unquote(parser.link["href"]), "gradio_api/file=" + path.as_posix())
            self.assertEqual(parser.link["download"], "Night _ Sky _live_.mp3")
            for label in ("Download", "Get stems", "Open folder", "Move to trash"):
                self.assertIn(label, html)
            self.assertEqual(path.read_bytes(), b"original audio")

    def test_rejects_external_and_missing_files(self):
        """No download links may target files outside the library or stale entries."""
        with tempfile.TemporaryDirectory() as temporary:
            for path in ("../outside.wav", "missing.wav"):
                with self.assertRaises(ValueError):
                    download_link(Path(temporary), {"path": path, "title": "Track"})


if __name__ == "__main__":
    unittest.main()
