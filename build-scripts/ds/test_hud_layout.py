"""Layout-only checks. Host substitutes do not establish real Android rendering."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import apply_hud_layout as layout

HERE = Path(__file__).resolve().parent
SUPPORT = HERE / 'hud-layout'
FIXTURE = os.environ.get('DS_LAYOUT_PARENT_FIXTURE')


def sha(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def parent_sources() -> dict[str, str]:
    keys = [layout.UI, *layout.UNCHANGED_SHA256]
    if FIXTURE:
        # All six files must still match the production hashes; no fixture hash bypass.
        return {p: (Path(FIXTURE) / p).read_text(encoding='utf-8') for p in keys}
    import apply_body_details as body
    import apply_hud_presentation as presentation
    import apply_needs_status as needs
    result = body.render_templates()
    result[layout.UI] = presentation.patch_ui(result[layout.UI])
    result[layout.JAVA_DIR + 'HudTypeface.java'] = presentation.TEMPLATE.read_text(encoding='utf-8')
    for path in keys:
        if path in needs.PARENT_SHA256:
            result[path] = needs.patch_text(path, result[path])
    return {p: result[p] for p in keys}


def run(args: list[str]) -> subprocess.CompletedProcess:
    p = subprocess.run(args, capture_output=True, text=True, timeout=60)
    if p.returncode:
        raise AssertionError(f'Command failed: {args}\n{p.stdout}\n{p.stderr}')
    return p


class HudLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = parent_sources()
        for p, digest in {layout.UI: layout.PARENT_UI_SHA256, **layout.UNCHANGED_SHA256}.items():
            if sha(cls.parent[p]) != digest:
                raise AssertionError(f'Parent fixture/generator differs from build 13: {p}')
        cls.generated = dict(cls.parent)
        cls.generated[layout.UI] = layout.patch_ui(cls.parent[layout.UI])
        cls.suite_temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.suite_temp.cleanup)
        cls.work = Path(cls.suite_temp.name)
        for rel, text in cls.generated.items():
            p = cls.work / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding='utf-8')
        spec = importlib.util.spec_from_file_location('layout_android_substitutes', SUPPORT / 'android_fixture.py')
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.stubs = module.write_stubs(cls.work / 'stubs', HERE / 'hud-presentation/android_fixture.py')
        cls.classes = cls.work / 'classes'
        javac = shutil.which('javac')
        if not javac:
            raise AssertionError('JDK required for layout host tests')
        sources = [cls.work / p for p in cls.generated if p.endswith('.java')]
        run([javac, '--release', '8', '-Xlint:all,-options', '-Werror', '-d', str(cls.classes)]
            + [str(p) for p in cls.stubs + sources + [SUPPORT / 'LayoutHostTest.java']])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'root'
        self.root.mkdir()
        self.out = Path(self.temp.name) / 'report'
        for relative, text in self.parent.items():
            p = self.root / relative
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding='utf-8')

    def bytes(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def rejected(self):
        before = self.bytes()
        with self.assertRaises((ValueError, FileNotFoundError)):
            layout.apply(self.root, self.out)
        self.assertEqual(before, self.bytes())
        self.assertFalse(self.out.exists())

    def test_parent_sources_match_accepted_build_13(self):
        self.assertEqual(sha(self.parent[layout.UI]), layout.PARENT_UI_SHA256)
        for p, digest in layout.UNCHANGED_SHA256.items():
            self.assertEqual(sha(self.parent[p]), digest)

    def test_only_ui_changes_and_staged_provenance(self):
        before = self.bytes()
        report = layout.apply(self.root, self.out)
        after = self.bytes()
        self.assertEqual([p for p in before if before[p] != after[p]], [layout.UI])
        self.assertEqual(set(before), set(after))
        self.assertEqual(report['paths'], {layout.UI: sha(self.generated[layout.UI])})
        self.assertEqual(report['overlay_order'][-1], 'HUD-LAYOUT.patch')
        self.assertEqual(report['displayed_widget_count'], 20)
        self.assertEqual(report['health_pairs'], [['Head', 'Torso'], ['Left arm', 'Right arm'], ['Left leg', 'Right leg']])
        self.assertTrue(report['presentation_only'])
        self.assertFalse(report['game_actions'])
        self.assertEqual(json.loads((self.out / 'HUD-LAYOUT.json').read_text()), report)
        patch = (self.out / 'HUD-LAYOUT.patch').read_text()
        self.assertEqual(patch.count('--- a/'), 1)

    def test_capture_transport_decoders_and_font_helper_unchanged(self):
        for p in layout.UNCHANGED_SHA256:
            self.assertEqual(self.generated[p], self.parent[p])

    def test_outer_polling_lifecycle_display_routing_unchanged(self):
        split = 'private static final class HudPresentation'
        self.assertEqual(self.generated[layout.UI].split(split)[0], self.parent[layout.UI].split(split)[0])

    def test_typeface_sizes_colors_text_factory_unchanged(self):
        key = '        private TextView text(String content, int size) {\n'
        self.assertEqual(self.generated[layout.UI].split(key)[1].split('\n        }')[0],
                         self.parent[layout.UI].split(key)[1].split('\n        }')[0])

    def test_full_stamina_setup_unchanged_except_title(self):
        start = '        @Override protected void onCreate(Bundle state) {'
        end = '            body = new LinearLayout(getContext());'
        old = self.parent[layout.UI].split(start)[1].split(end)[0]
        new = self.generated[layout.UI].split(start)[1].split(end)[0]
        self.assertEqual(old.replace('CDDA-DS / NEEDS STATUS', 'CDDA-DS / HUD LAYOUT'), new)

    def test_readings_rendering_unchanged_except_container_visibility(self):
        start = '        void render(Object[] raw) {'
        old = self.parent[layout.UI].split(start)[1]
        new = self.generated[layout.UI].split(start)[1]
        old = old.replace('core.setVisibility(View.VISIBLE);\n            activityStatus.setVisibility(View.VISIBLE);',
                          'details.setVisibility(View.VISIBLE);')
        self.assertEqual(old, new)

    def test_session_clearing_unchanged_except_container_visibility(self):
        start, end = '        void setMessage(String message) {', '        void render('
        old = self.parent[layout.UI].split(start)[1].split(end)[0]
        new = self.generated[layout.UI].split(start)[1].split(end)[0]
        old = old.replace('core.setVisibility(View.GONE);\n            activityStatus.setVisibility(View.GONE);',
                          'details.setVisibility(View.GONE);')
        self.assertEqual(old, new)

    def test_no_truncation_shrinking_or_game_actions(self):
        for forbidden in ('setSingleLine', 'setMaxLines', 'setEllipsize', 'setAutoSize', 'requestFocus',
                          'dispatchKeyEvent', 'sendKeyEvent', 'setTextScaleX'):
            self.assertNotIn(forbidden, self.generated[layout.UI])
        self.assertEqual(self.generated[layout.UI].count('setTextSize('), 1)
        self.assertIn('getPaint().measureText(probe)', self.generated[layout.UI])

    def test_bad_ui_hash_fails_before_writes(self):
        (self.root / layout.UI).write_text('changed')
        self.rejected()

    def test_all_changed_dependencies_fail_before_write(self):
        for p in layout.UNCHANGED_SHA256:
            with self.subTest(path=p):
                original = (self.root / p).read_bytes()
                (self.root / p).write_bytes(b'changed')
                self.rejected()
                (self.root / p).write_bytes(original)

    def test_missing_dependency_fails_before_write(self):
        (self.root / (layout.JAVA_DIR + 'ActivityHudSnapshot.java')).unlink()
        self.rejected()

    def test_missing_ui_fails_before_write(self):
        (self.root / layout.UI).unlink()
        self.rejected()

    def test_source_symlink_refused(self):
        p = self.root / layout.UI
        target = Path(self.temp.name) / 'copy.java'
        p.rename(target)
        p.symlink_to(target)
        self.rejected()

    def test_dependency_symlink_refused(self):
        p = self.root / 'src/ds_hud.h'
        target = Path(self.temp.name) / 'copy.h'
        p.rename(target)
        p.symlink_to(target)
        self.rejected()

    def test_parent_symlink_refused(self):
        p = self.root / 'android'
        target = Path(self.temp.name) / 'android-copy'
        p.rename(target)
        p.symlink_to(target, target_is_directory=True)
        with self.assertRaises(ValueError):
            layout.apply(self.root, self.out)
        self.assertFalse(self.out.exists())

    def test_unsafe_relative_paths_refused(self):
        for p in ('../escape', '/tmp/escape', 'src/../../escape'):
            with self.assertRaises(ValueError):
                layout.safe_target(self.root, p)

    def test_duplicate_anchor_refused(self):
        with self.assertRaises(ValueError):
            layout.patch_ui(self.parent[layout.UI] + '\n            layout.addView(status);\n')

    def test_missing_anchor_refused(self):
        with self.assertRaises(ValueError):
            layout.patch_ui(self.parent[layout.UI].replace('body = new LinearLayout(getContext());', 'body = null;'))

    def test_repeat_application_refused(self):
        layout.apply(self.root, self.out)
        before = self.bytes()
        with self.assertRaises(ValueError):
            layout.apply(self.root, self.out)
        self.assertEqual(before, self.bytes())

    def test_original_android_fixture_unmodified(self):
        data = (HERE / 'hud-presentation/android_fixture.py').read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()
        self.assertEqual(blob, 'd233a438dddfb46fe8026b65cfc1dc6cc22293cb')

    def host(self, mode):
        result = run(['java', '-cp', str(self.classes), 'com.cleverraven.cataclysmdda.LayoutHostTest', mode])
        self.assertIn('passed: ' + mode, result.stdout)
        self.assertNotIn('WARNING', result.stderr + result.stdout)

    def test_host_mapping_order_health_and_width_boundaries(self): self.host('normal')
    def test_host_blank_needs_and_clearing(self): self.host('blank')
    def test_host_missing_readings_and_clearing(self): self.host('missing')
    def test_host_long_descriptions_remain_full_width(self): self.host('long')
    def test_host_value_changes_do_not_rearrange(self): self.host('changing')
    def test_host_larger_modeled_font_width(self): self.host('large-font')
    def test_host_emergency_font_fallback(self): self.host('fallback')


if __name__ == '__main__':
    unittest.main()
