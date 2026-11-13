"""Needs/dedup tests; host substitutes do not establish Android/device behavior."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import apply_needs_status as needs

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SUPPORT = HERE / "needs-status"
FIXTURE = os.environ.get("DS_NEEDS_PARENT_FIXTURE")


def sha(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def parent_sources() -> dict[str, str]:
    keys = list(needs.PARENT_SHA256) + list(needs.UNCHANGED_SHA256)
    if FIXTURE:
        # Explicit local fixture only: generated files verified against build 12;
        # game.cpp contains only the exact added hook, not the whole engine file.
        return {key: (Path(FIXTURE) / key).read_text(encoding="utf-8") for key in keys}
    import apply_body_details as base
    import apply_hud_presentation as presentation
    files = base.render_templates()
    files[needs.UI] = presentation.patch_ui(files[needs.UI])
    files[needs.JAVA_DIR + "HudTypeface.java"] = presentation.TEMPLATE.read_text(encoding="utf-8")
    files["src/game.cpp"] = base.patch_text("src/game.cpp", (ROOT / "src/game.cpp").read_text(encoding="utf-8"))
    return {key: files[key] for key in keys}


def run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    result = subprocess.run(args, capture_output=True, text=True, timeout=60, **kwargs)
    if result.returncode:
        raise AssertionError(f"Command failed: {args}\n{result.stdout}\n{result.stderr}")
    return result


class NeedsStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = parent_sources()
        cls.generated = {p: needs.patch_text(p, text) if p in needs.PARENT_SHA256 else text
                         for p, text in cls.parent.items()}
        cls.suite_temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.suite_temp.cleanup)
        cls.work = Path(cls.suite_temp.name)
        for rel, text in cls.generated.items():
            p = cls.work / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("needs_android_substitutes", HERE / "hud-presentation/android_fixture.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        stubs = module.write_stubs(cls.work / "stubs")
        javac = shutil.which("javac")
        if not javac: raise AssertionError("Java JDK is required for needs tests")
        java_home = Path(javac).resolve().parents[1]
        cls.classes = cls.work / "classes"
        java_sources = [cls.work / p for p in cls.generated if p.endswith(".java")]
        run([javac, "--release", "8", "-Xlint:all,-options", "-Werror", "-d", str(cls.classes)]
            + [str(p) for p in stubs + java_sources + [SUPPORT / "NeedsHostTest.java"]])
        cls.lib = cls.work / "libneeds_host.so"
        run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC", "-pthread",
             "-D__ANDROID__", "-DNEEDS_JNI_TEST", "-I" + str(java_home / "include"),
             "-I" + str(java_home / "include/linux"), "-I" + str(cls.work / "src"),
             str(cls.work / "src/ds_hud.cpp"), str(SUPPORT / "native_host.cpp"), "-o", str(cls.lib)])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "root"; self.root.mkdir()
        self.out = Path(self.temp.name) / "report"
        for rel, text in self.parent.items():
            p = self.root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding="utf-8")
        for rel in needs.WIDGET_BLOBS:
            p = self.root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes((ROOT / rel).read_bytes())
        # Fixture application may use a hook-only game.cpp locally. CI derives the
        # full game file and these values must match production constants below.
        self.expected = {p: sha(self.parent[p]) for p in needs.PARENT_SHA256}

    def apply(self):
        with patch.dict(needs.PARENT_SHA256, self.expected, clear=True):
            return needs.apply(self.root, self.out)

    def tree_bytes(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes()
                for p in self.root.rglob("*") if p.is_file()}

    def assert_rejected_unchanged(self):
        before = self.tree_bytes()
        with self.assertRaises((ValueError, FileNotFoundError)): self.apply()
        self.assertEqual(before, self.tree_bytes()); self.assertFalse(self.out.exists())

    def test_parent_inputs_match_build_12(self):
        for p, expected in {**needs.PARENT_SHA256, **needs.UNCHANGED_SHA256}.items():
            if FIXTURE and p == "src/game.cpp":
                self.assertIn('void game::draw_panels( bool force_draw )', self.parent[p])
            else: self.assertEqual(sha(self.parent[p]), expected, p)
        self.assertEqual(needs.PARENT_SHA256['src/game.cpp'],
                         'f7c41242f48f0787afdb0f6c4cb7c61a8ec2738914f6121ca2ea10ebf07036b4')

    def test_pinned_needs_definitions(self):
        for rel, expected in needs.WIDGET_BLOBS.items():
            self.assertEqual(needs.blob_sha((ROOT / rel).read_bytes()), expected)
        for filename, (wid, _) in zip(('hunger', 'thirst', 'sleepiness'), needs.NEEDS_WIDGETS):
            definitions = json.loads((ROOT / f'data/json/ui/{filename}.json').read_text())
            self.assertTrue(any(obj['id'] == wid for obj in definitions))

    def test_blank_states_are_native_not_invented(self):
        hunger = json.loads((ROOT / 'data/json/ui/hunger.json').read_text())[0]
        thirst = json.loads((ROOT / 'data/json/ui/thirst.json').read_text())[0]
        sleep = json.loads((ROOT / 'data/json/ui/sleepiness.json').read_text())[0]
        self.assertTrue(any(c['id'] == 'blank' and c['text'] == '' for c in hunger['clauses']))
        self.assertTrue(any(c['id'] == 'neutral' and c['text'] == '' for c in thirst['clauses']))
        self.assertEqual([c['text'] for c in sleep['clauses']], ['Tired', 'Dead Tired', 'Exhausted'])

    def test_capture_only_appends_native_widget_ids(self):
        pattern = r'const char \*const widget_ids\[\] = \{ (.*?) \};'
        old = re.search(pattern, self.parent['src/game.cpp']).group(1)
        new = re.search(pattern, self.generated['src/game.cpp']).group(1)
        self.assertEqual(json.loads('[' + new + ']'),
                         json.loads('[' + old + ']') + [w for w, _ in needs.NEEDS_WIDGETS])
        self.assertEqual(self.generated['src/game.cpp'].replace(new, old), self.parent['src/game.cpp'])

    def test_native_logic_and_core_font_helpers_unchanged(self):
        self.assertEqual(self.generated['src/ds_hud.cpp'].replace('long[53], byte[30][]', 'long[50], byte[27][]'),
                         self.parent['src/ds_hud.cpp'])
        for p in needs.UNCHANGED_SHA256: self.assertEqual(self.parent[p], self.generated[p])

    def test_font_lifecycle_focus_polling_and_sizes_unchanged(self):
        old, new = self.parent[needs.UI], self.generated[needs.UI]
        self.assertEqual(old.split('private static final class HudPresentation')[0].replace(
            'long[29], byte[6][]', 'long[53], byte[30][]'), new.split('private static final class HudPresentation')[0])
        for section in ('private TextView text(', 'HudPresentation(Context context, Display display)'):
            self.assertEqual(old.split(section)[1].split('\n        }')[0], new.split(section)[1].split('\n        }')[0])
        self.assertIn('for (int i = 14; i < activityValues.length; i++)', new)

    def test_overlay_five_paths_and_sequential_provenance(self):
        report = self.apply()
        self.assertEqual(set(report['paths']), set(needs.PARENT_SHA256))
        self.assertEqual(report['wire_shape'], {'numeric': 53, 'text': 30})
        self.assertEqual(report['removed_lower_labels'], list(needs.HIDDEN_LABELS))
        self.assertFalse(report['removed_from_capture'])
        self.assertEqual(report['displayed_widget_count'], 20)
        self.assertEqual(report['overlay_order'][-1], 'NEEDS-STATUS.patch')
        for p, digest in report['paths'].items(): self.assertEqual(sha((self.root / p).read_text()), digest)

    def test_bad_source_hash_fails_before_writes(self):
        (self.root / needs.UI).write_text('wrong source'); self.assert_rejected_unchanged()

    def test_bad_unchanged_helper_fails_before_writes(self):
        (self.root / (needs.JAVA_DIR + 'HudTypeface.java')).write_text('changed helper'); self.assert_rejected_unchanged()

    def test_changed_widget_fails_before_writes(self):
        (self.root / 'data/json/ui/hunger.json').write_text('[]'); self.assert_rejected_unchanged()

    def test_missing_widget_fails_before_writes(self):
        (self.root / 'data/json/ui/thirst.json').unlink(); self.assert_rejected_unchanged()

    def test_duplicate_anchor_fails(self):
        text = self.parent['src/game.cpp'] + '\n"bp_armor_outer_feet_text" };'
        with self.assertRaises(ValueError): needs.patch_text('src/game.cpp', text)

    def test_missing_anchor_fails(self):
        with self.assertRaises(ValueError): needs.patch_text(needs.UI, self.parent[needs.UI].replace('int i = 5;', 'int i = 6;'))

    def test_unknown_target_refused(self):
        with self.assertRaises(ValueError): needs.patch_text('src/unrelated.cpp', '')

    def test_repeat_application_refused(self):
        self.apply(); before = self.tree_bytes()
        with self.assertRaises(ValueError): self.apply()
        self.assertEqual(before, self.tree_bytes())

    def test_source_symlink_refused(self):
        p = self.root / needs.UI; outside = Path(self.temp.name) / 'copy.java'
        outside.write_bytes(p.read_bytes()); p.unlink(); p.symlink_to(outside)
        self.assert_rejected_unchanged()

    def test_parent_directory_symlink_refused(self):
        p = self.root / 'src'; outside = Path(self.temp.name) / 'source'; p.rename(outside); p.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError): self.apply()
        self.assertFalse(self.out.exists())

    def test_path_traversal_and_absolute_refused(self):
        for rel in ('../escape', '/tmp/escape'):
            with self.assertRaises(ValueError): needs.safe_target(self.root, rel)

    def test_widget_symlink_refused(self):
        p = self.root / 'data/json/ui/hunger.json'; outside = Path(self.temp.name) / 'hunger.json'
        outside.write_bytes(p.read_bytes()); p.unlink(); p.symlink_to(outside)
        self.assert_rejected_unchanged()

    def test_compiled_capture_coherence_and_clearing(self):
        text = self.generated['src/game.cpp'].split('void game::draw_panels( bool force_draw )\n{\n', 1)[1]
        hook = text.split('#if defined(__ANDROID__)\n', 1)[1].split('#endif', 1)[0]
        source = (SUPPORT / 'native_host.cpp').read_text().replace('// NEEDS_CAPTURE_HOOK', hook)
        p = Path(self.temp.name) / 'capture.cpp'; p.write_text(source)
        binary = Path(self.temp.name) / 'capture'
        run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pthread', '-I' + str(self.work / 'src'),
             str(p), str(self.work / 'src/ds_hud.cpp'), '-o', str(binary)])
        run([str(binary)])

    def host(self, mode):
        result = run(['java', '-Xcheck:jni', '-cp', str(self.classes),
                      'com.cleverraven.cataclysmdda.NeedsHostTest', str(self.lib), mode])
        self.assertIn('passed: ' + mode, result.stdout)
        self.assertNotIn('WARNING', result.stderr + result.stdout)

    def test_jni_ui_normal(self): self.host('normal')
    def test_jni_ui_changed(self): self.host('changed')
    def test_jni_ui_blank(self): self.host('blank')
    def test_jni_ui_whitespace(self): self.host('whitespace')
    def test_jni_ui_missing_and_recovery(self): self.host('missing')
    def test_jni_ui_unicode_long_and_nul(self): self.host('unicode')
    def test_jni_ui_copy_isolation(self): self.host('copy')
    def test_jni_ui_malformed(self): self.host('malformed')
    def test_jni_ui_font_fallback_retained(self): self.host('fallback')


if __name__ == '__main__':
    unittest.main()
