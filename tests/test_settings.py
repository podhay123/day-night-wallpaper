"""Tests for the settings of day-night-wallpaper. Run: python3 -m unittest discover -s tests -v"""
import contextlib
import importlib.machinery
import importlib.util
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parent.parent / "day-night-wallpaper"


def load_module():
    loader = importlib.machinery.SourceFileLoader("dnw", str(SCRIPT))
    spec = importlib.util.spec_from_loader("dnw", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        env = {"HOME": self.tmp.name, "XDG_CONFIG_HOME": os.path.join(self.tmp.name, "cfg")}
        self.env = mock.patch.dict(os.environ, env)
        self.env.start()
        self.m = load_module()
        self.m.available_schemes = lambda: ["BreezeClassic", "BreezeDark", "BreezeLight"]
        self.conf = Path(env["XDG_CONFIG_HOME"]) / "day-night-wallpaper.conf"

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def norm(self, name, value):
        return self.m.SETTINGS[name].normalize(value)


class TestNormalize(Base):
    def test_bool(self):
        for v in ("on", "ON", "true", "yes", "1"):
            self.assertEqual(self.norm("theme", v), "on")
        for v in ("off", "false", "no", "0"):
            self.assertEqual(self.norm("lockscreen", v), "off")
        with self.assertRaises(ValueError):
            self.norm("theme", "maybe")

    def test_location(self):
        self.assertEqual(self.norm("location", "50.06 19.94"), "50.06 19.94")
        self.assertEqual(self.norm("location", "50.06,19.94"), "50.06 19.94")
        self.assertEqual(self.norm("location", "40.71 -74.01"), "40.71 -74.01")
        for bad in ("91 0", "0 181", "abc", "50", "1 2 3"):
            with self.assertRaises(ValueError):
                self.norm("location", bad)

    def test_fade(self):
        self.assertEqual(self.norm("fade", "30"), "30")
        self.assertEqual(self.norm("fade", "2.5"), "2.5")
        self.assertEqual(self.norm("fade", "off"), "off")
        self.assertEqual(self.norm("fade", "0"), "off")
        for bad in ("-5", "301", "x"):
            with self.assertRaises(ValueError):
                self.norm("fade", bad)

    def test_accent(self):
        self.assertEqual(self.norm("day-accent", "#ABCDEF"), "#abcdef")
        self.assertEqual(self.norm("night-accent", "abcdef"), "#abcdef")
        for bad in ("#xyz", "#12345", "red"):
            with self.assertRaises(ValueError):
                self.norm("day-accent", bad)

    def test_scheme(self):
        self.assertEqual(self.norm("night-scheme", "breezedark"), "BreezeDark")
        with self.assertRaises(ValueError):
            self.norm("day-scheme", "NoSuchScheme")

    def test_screen_and_numbers(self):
        self.assertEqual(self.norm("screen", "2560X1440"), "2560x1440")
        for bad in ("abc", "0x100", "1920"):
            with self.assertRaises(ValueError):
                self.norm("screen", bad)
        self.assertEqual(self.norm("neon-x", "auto"), "auto")
        self.assertEqual(self.norm("neon-x", "900"), "900")
        self.assertEqual(self.norm("neon-y", "250"), "250")
        self.assertEqual(self.norm("neon-size", "200"), "200")
        self.assertEqual(self.norm("panel-left", "0"), "0")
        for name, bad in (("neon-x", "-1"), ("neon-size", "0"), ("panel-left", "-3"), ("neon-y", "x")):
            with self.assertRaises(ValueError):
                self.norm(name, bad)


class TestFile(Base):
    def test_defaults_without_file(self):
        values = self.m.load_settings()
        self.assertEqual(values["theme"], "on")
        self.assertEqual(values["location"], "52.23 21.01")
        self.assertEqual(set(values), set(self.m.SETTINGS))

    def test_round_trip_stores_only_changes(self):
        values = self.m.load_settings()
        values["theme"] = "off"
        self.m.save_settings(values)
        text = self.conf.read_text()
        self.assertIn("theme = off", text)
        self.assertNotIn("lockscreen", text)
        self.assertEqual(self.m.load_settings()["theme"], "off")

    def test_bad_value_in_file_falls_back(self):
        self.conf.parent.mkdir(parents=True)
        self.conf.write_text("[settings]\ntheme = maybe\nbogus = 1\nfade = 30\n")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            values = self.m.load_settings()
        self.assertEqual(values["theme"], "on")
        self.assertEqual(values["fade"], "30")
        self.assertIn("theme", err.getvalue())
        self.assertIn("bogus", err.getvalue())


class TestApply(Base):
    def apply(self, **changes):
        values = self.m.load_settings()
        values.update({k.replace("_", "-"): v for k, v in changes.items()})
        self.m.apply_settings(values)

    def test_derived_constants(self):
        self.apply(panel_left="100", screen="2560x1440", location="50.06 19.94")
        self.assertEqual((self.m.SCREEN_W, self.m.SCREEN_H, self.m.PANEL_LEFT), (2560, 1440, 100))
        self.assertEqual(self.m.NEON_X, 1330)
        self.assertEqual((self.m.LATITUDE, self.m.LONGITUDE), (50.06, 19.94))

    def test_fade(self):
        self.apply(fade="off")
        self.assertEqual(self.m.TRANSITION_FRAMES, 1)
        self.apply(fade="32")
        self.assertEqual(self.m.TRANSITION_FRAMES, 16)
        self.assertAlmostEqual(self.m.TRANSITION_STEP_S, 2.0)

    def test_switches_and_style(self):
        self.apply(theme="off", lockscreen="off", night_scheme="BreezeClassic", day_accent="#112233")
        self.assertFalse(self.m.SWITCH_THEME)
        self.assertFalse(self.m.SWITCH_LOCKSCREEN)
        self.assertEqual(self.m.STYLE["night"]["scheme"], "BreezeClassic")
        self.assertEqual(self.m.STYLE["day"]["accent"], "#112233")

    def test_render_key_ignores_colours_but_not_crop(self):
        self.m.SOURCES = {k: SCRIPT for k in ("day", "night")}   # any existing file
        self.apply()
        base = self.m._render_key()
        self.apply(day_accent="#000000", night_scheme="BreezeClassic", theme="off")
        self.assertEqual(self.m._render_key(), base)
        self.apply(neon_size="200")
        self.assertNotEqual(self.m._render_key(), base)


class TestCli(Base):
    def setUp(self):
        super().setUp()
        self.triggered = []
        self.m.trigger_apply = lambda: self.triggered.append(True) or 0

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(self.m.sys, "argv", ["wallpaper", *argv]), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.m.main()
        return code, out.getvalue(), err.getvalue()

    def test_set_writes_and_applies(self):
        code, out, _ = self.run_cli("set", "theme", "off")
        self.assertEqual(code, 0)
        self.assertIn("theme = off", self.conf.read_text())
        self.assertIn("theme", out)
        self.assertEqual(self.triggered, [True])

    def test_set_location_two_args(self):
        self.assertEqual(self.run_cli("set", "location", "50.06", "19.94")[0], 0)
        self.assertEqual(self.m.load_settings()["location"], "50.06 19.94")
        self.assertEqual(self.run_cli("set", "location", "40.71", "-74.01")[0], 0)
        self.assertEqual(self.m.load_settings()["location"], "40.71 -74.01")

    def test_set_rejects_bad_input(self):
        for argv in (("set", "nope", "1"), ("set", "theme", "maybe"), ("set", "theme"), ("set",)):
            code, _, err = self.run_cli(*argv)
            self.assertEqual(code, 2, argv)
            self.assertTrue(err, argv)
        self.assertFalse(self.conf.exists())
        self.assertEqual(self.triggered, [])

    def test_reset(self):
        self.run_cli("set", "theme", "off")
        self.run_cli("set", "fade", "30")
        self.run_cli("reset", "theme")
        values = self.m.load_settings()
        self.assertEqual((values["theme"], values["fade"]), ("on", "30"))
        self.run_cli("reset", "all")
        self.assertNotIn("fade", self.conf.read_text())
        self.assertEqual(self.run_cli("reset", "nope")[0], 2)

    def test_settings_lists_everything_and_marks_changes(self):
        self.run_cli("set", "fade", "30")
        code, out, _ = self.run_cli("settings")
        self.assertEqual(code, 0)
        for name in self.m.SETTINGS:
            self.assertIn(name, out)
        fade_line = next(l for l in out.splitlines() if l.lstrip("* ").startswith("fade"))
        self.assertTrue(fade_line.startswith("*"))
        self.assertIn("30", fade_line)
        self.assertIn("19", fade_line)   # default shown

    def test_settings_survives_bad_file(self):
        self.conf.parent.mkdir(parents=True)
        self.conf.write_text("[settings]\ntheme = maybe\n")
        code, out, _ = self.run_cli("settings")
        self.assertEqual(code, 0)
        self.assertIn("theme", out)

    def test_complete(self):
        c = self.m.complete
        for cmd in ("day", "night", "auto", "toggle", "status", "settings", "set", "reset", "help"):
            self.assertIn(cmd, c([]))
        self.assertEqual(set(c(["set"])), set(self.m.SETTINGS))
        self.assertEqual(set(c(["reset"])), set(self.m.SETTINGS) | {"all"})
        self.assertEqual(c(["set", "theme"]), ["on", "off"])
        self.assertIn("off", c(["set", "fade"]))
        self.assertIn("BreezeDark", c(["set", "night-scheme"]))
        self.assertEqual(c(["status"]), [])


if __name__ == "__main__":
    unittest.main()
