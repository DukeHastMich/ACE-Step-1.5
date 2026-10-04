"""Test track menus, safe Demucs execution, caching, and failure cleanup."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from .library_rows import render_song_rows, ROW_SCRIPT
from .library_stem_controls import requested_song
from .library_stems import separate_song, stem_command, STEM_PROFILES
from .library_store import scan_songs

MODULE = "acestep.ui.gradio.interfaces.library_stems"


class StemTests(unittest.TestCase):
    """Use temporary audio and a mock CLI; no model or GPU is needed."""

    def setUp(self):
        """Create a library with a filename containing spaces and shell metacharacters."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "song & a mix.wav"
        self.source.write_bytes(b"original-audio")

    def fake_run(self, command, **kwargs):
        """Emulate a successful CLI without touching the input file."""
        output = Path(command[command.index("-o") + 1]) / command[command.index("-n") + 1]
        output.mkdir()
        count = 2 if "--two-stems=vocals" in command else (6 if "htdemucs_6s" in command else 4)
        for stem in STEM_PROFILES[count][1]:
            name = stem + ".wav"
            (output / name).write_bytes(b"RIFF" + b"0" * 100)
        return SimpleNamespace(returncode=0)

    def test_success_cache_and_library_exclusion(self):
        """Reuse complete pairs, leave source unchanged, and hide stem artifacts from songs."""
        with patch(MODULE + ".subprocess.run", side_effect=self.fake_run) as run:
            first = separate_song(self.root, self.source.name)
            self.assertEqual(first, separate_song(self.root, self.source.name))
            self.assertEqual(run.call_count, 1)
            self.assertTrue(all(Path(path).is_file() for path in first))
        self.assertEqual(self.source.read_bytes(), b"original-audio")
        self.assertEqual(len(scan_songs(self.root)), 1)

    def test_all_profiles_have_independent_complete_caches(self):
        """Four/six stems use the right model, with no two-stem switch or cache collision."""
        with patch(MODULE + ".subprocess.run", side_effect=self.fake_run) as run:
            outputs = [separate_song(self.root, self.source.name, count) for count in (2, 4, 6)]
            self.assertEqual([len(paths) for paths in outputs], [2, 4, 6])
            self.assertEqual(len({Path(paths[0]).parent for paths in outputs}), 3)
            for count, paths in zip((2, 4, 6), outputs):
                self.assertEqual(paths, separate_song(self.root, self.source.name, count))
            self.assertEqual(run.call_count, 3)
            self.assertNotIn("--two-stems=vocals", run.call_args_list[1].args[0])
            self.assertIn("htdemucs_6s", run.call_args_list[2].args[0])

    def test_reject_unknown_profile_before_launch(self):
        """Untrusted menu values cannot select arbitrary models or commands."""
        with patch(MODULE + ".subprocess.run") as run:
            with self.assertRaises(ValueError):
                separate_song(self.root, self.source.name, 8)
            run.assert_not_called()

    def test_trash_restores_every_profile(self):
        """All stem sets move with the source and are restored together."""
        from .library_trash import move_to_trash, restore_from_trash
        with patch(MODULE + ".subprocess.run", side_effect=self.fake_run):
            paths = [p for count in (2, 4, 6)
                     for p in separate_song(self.root, self.source.name, count)]
        token = move_to_trash(self.root, self.source.name, "Test")
        self.assertTrue(all(not Path(path).exists() for path in paths))
        restore_from_trash(self.root, token)
        self.assertTrue(all(Path(path).exists() for path in paths))

    def test_changed_source_gets_new_stems(self):
        """A replacement source cannot reuse an old cached separation."""
        with patch(MODULE + ".subprocess.run", side_effect=self.fake_run):
            first = separate_song(self.root, self.source.name)
            self.source.write_bytes(b"new-longer-audio")
            self.assertNotEqual(first, separate_song(self.root, self.source.name))

    def test_failed_or_incomplete_job_not_cached(self):
        """A zero-exit CLI with missing files still fails and cleans temporary output."""
        with patch(MODULE + ".subprocess.run", return_value=SimpleNamespace(returncode=0)):
            with self.assertRaises(RuntimeError):
                separate_song(self.root, self.source.name)
        self.assertEqual(list((self.root / ".stems").iterdir()), [])

    def test_timeout_and_traversal(self):
        """Kill timed-out subprocesses through subprocess.run and reject external inputs."""
        with patch(MODULE + ".subprocess.run", side_effect=subprocess.TimeoutExpired("demucs", 1)):
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                separate_song(self.root, self.source.name)
        with patch(MODULE + ".subprocess.run") as run:
            with self.assertRaises(ValueError):
                separate_song(self.root, "../outside.wav")
            run.assert_not_called()

    def test_command_uses_argument_array(self):
        """Paths remain one argument; the reference two-stem flag is preserved."""
        command = stem_command(self.source, self.root)
        self.assertIn("--two-stems=vocals", command)
        self.assertEqual(command[-1], str(self.source))

    def test_menu_escaping_and_stable_identity(self):
        """Untrusted titles are escaped, while filtered rows use stable song identities."""
        song = scan_songs(self.root)[0]
        song["title"] = '<script>alert("bad")</script>'
        html = render_song_rows([song])
        self.assertNotIn("<script>", html)
        self.assertIn("Get stems", html)
        self.assertIn("song &amp; a mix.wav", html)
        self.assertIs(requested_song([song], song["path"]), song)
        with self.assertRaises(ValueError):
            requested_song([song], "stale-track.wav")

    def test_menu_event_avoids_reserved_file_payload_field(self):
        """Gradio must not treat a library identity as an uploaded file descriptor."""
        self.assertIn("{song_id: stems.dataset.stems, stems: Number(stems.dataset.stemCount || 2)}", ROW_SCRIPT)
        self.assertNotIn("{path:", ROW_SCRIPT)


if __name__ == "__main__":
    unittest.main()
