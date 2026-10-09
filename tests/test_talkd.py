"""Real TCP lifecycle tests against a fake SDK; no camera/audio hardware used."""
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]

class TalkdTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = tempfile.TemporaryDirectory()
        cls.binary = str(Path(cls.build.name) / "talkd")
        subprocess.run([os.environ.get("CC", "cc"), "-std=gnu99", "-Wall", "-Wextra", "-Werror",
                        "-I" + str(ROOT / "tests/fake_sdk"), str(ROOT / "camera_talkd/anyka_talkd.c"),
                        str(ROOT / "tests/fake_sdk/sdk.c"), "-o", cls.binary], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.build.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.output = Path(self.tmp.name) / "audio"
        self.log_path = Path(self.tmp.name) / "log"
        self.log = self.log_path.open("wb")
        self.process = None

    def tearDown(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try: self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
                self.fail("daemon did not stop on SIGTERM")
        self.log.close()
        self.tmp.cleanup()

    def logs(self):
        return self.log_path.read_text()

    def wait_for(self, predicate, timeout=5):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if predicate(): return
            time.sleep(.02)
        self.fail("timed out: " + self.logs())

    def start(self, mode="", allowed="127.0.0.1"):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            self.port = s.getsockname()[1]
        env = dict(os.environ, FAKE_MODE=mode, FAKE_OUTPUT=str(self.output))
        self.process = subprocess.Popen([self.binary, "--port", str(self.port), "--allow", allowed],
                                        stdout=self.log, stderr=self.log, env=env)
        self.wait_for(lambda: "listening on" in self.logs())

    def connect(self):
        return socket.create_connection(("127.0.0.1", self.port), timeout=5)

    def test_allowlist_required_and_arguments_validated(self):
        for args in ([], ["--allow", "bad"], ["--port", "0"], ["--volume", "7"]):
            result = subprocess.run([self.binary] + args, capture_output=True, timeout=2)
            self.assertNotEqual(result.returncode, 0)

    def test_sigterm_while_accepting(self):
        self.start()
        self.process.terminate()
        self.assertEqual(self.process.wait(timeout=2), 0)

    def test_idle_probe_does_not_open_speaker_and_expires(self):
        self.start()
        with self.connect() as s:
            self.assertEqual(s.recv(1), b"")
        self.assertNotIn("fake: ao_open", self.logs())

    def test_partial_writes_and_repeated_sessions(self):
        self.start()
        payload = bytes(range(256)) * 4
        for i in range(5):
            with self.connect() as s:
                s.sendall(payload)
                s.shutdown(socket.SHUT_WR)
                self.assertEqual(s.recv(1), b"")
            self.wait_for(lambda: self.logs().count("talk session stopped") == i + 1)
        self.assertEqual(self.output.read_bytes(), payload * 5)
        self.assertEqual(self.logs().count("fake: ak_ao_close"), 5)

    def test_busy_client_rejected(self):
        self.start()
        with self.connect() as first:
            first.sendall(b"\xd5" * 160)
            self.wait_for(lambda: "fake: stream_open" in self.logs())
            with self.connect() as second:
                self.assertEqual(second.recv(1), b"")
            first.sendall(b"\xd5" * 160)
        self.wait_for(lambda: "talk session stopped" in self.logs())
        self.assertEqual(self.output.read_bytes(), b"\xd5" * 320)

    def test_disallowed_client_never_opens_audio(self):
        self.start(allowed="192.0.2.1")
        with self.connect() as s:
            self.assertEqual(s.recv(1), b"")
        self.assertNotIn("fake: ao_open", self.logs())

    def test_decoder_stall_is_bounded(self):
        self.start(mode="stall")
        with self.connect() as s:
            s.sendall(b"\xd5" * 160)
            self.assertEqual(s.recv(1), b"")
        self.assertIn("decoder stalled", self.logs())
        self.assertIn("fake: ak_ao_close", self.logs())

    def test_initialization_failure_releases_output(self):
        self.start(mode="stream_fail")
        with self.connect() as s:
            s.sendall(b"\xd5" * 160)
            self.assertEqual(s.recv(1), b"")
        self.assertIn("fake: ak_adec_close", self.logs())
        self.assertIn("fake: ak_ao_close", self.logs())

    def test_sigterm_during_audio(self):
        self.start()
        with self.connect() as s:
            s.sendall(b"\xd5" * 160)
            self.wait_for(lambda: "fake: stream_open" in self.logs())
            self.process.terminate()
            self.assertEqual(self.process.wait(timeout=2), 0)
        self.assertIn("fake: ak_adec_cancel_stream", self.logs())
        self.assertIn("fake: ak_ao_close", self.logs())

if __name__ == "__main__":
    unittest.main()
