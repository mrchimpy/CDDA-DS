"""Presentation-only checks; host substitutes do not establish Android/Thor appearance."""
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

import apply_hud_polish as polish

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIXTURE = os.environ.get('DS_POLISH_PARENT_FIXTURE')
SUPPORT_BLOBS = {
    'hud-presentation/android_fixture.py': 'd233a438dddfb46fe8026b65cfc1dc6cc22293cb',
    'hud-layout/android_fixture.py': '3ae2fd540c9ab0b7d94ca571863745fdd1bab12b',
}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def parent_sources() -> dict[str, str]:
    keys = [polish.UI, *polish.UNCHANGED_SHA256]
    if FIXTURE:
        # Explicit local fixture selection, never a production identity/hash override.
        return {p: (Path(FIXTURE) / p).read_text(encoding='utf-8') for p in keys}
    import apply_body_details as body
    import apply_hud_presentation as presentation
    import apply_needs_status as needs
    import apply_hud_layout as layout
    import apply_hud_refinement as refinement
    result = body.render_templates()
    result[polish.UI] = presentation.patch_ui(result[polish.UI])
    result[polish.JAVA_DIR + 'HudTypeface.java'] = presentation.TEMPLATE.read_text(encoding='utf-8')
    for p in keys:
        if p in needs.PARENT_SHA256:
            result[p] = needs.patch_text(p, result[p])
    result[polish.UI] = refinement.patch_ui(layout.patch_ui(result[polish.UI]))
    return {p: result[p] for p in keys}


def run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    result = subprocess.run(args, capture_output=True, text=True, timeout=60, **kwargs)
    if result.returncode:
        raise AssertionError(f'Command failed: {args}\n{result.stdout}\n{result.stderr}')
    return result


class HudPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = parent_sources()
        for p, expected in {polish.UI: polish.PARENT_UI_SHA256, **polish.UNCHANGED_SHA256}.items():
            if sha(cls.parent[p]) != expected:
                raise AssertionError(f'Parent does not match build 15: {p}')
        for p, expected in SUPPORT_BLOBS.items():
            if polish.blob_sha((HERE / p).read_bytes()) != expected:
                raise AssertionError(f'Accepted Android substitute changed: {p}')
        cls.generated = dict(cls.parent)
        cls.generated[polish.UI] = polish.patch_ui(cls.parent[polish.UI])
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.work = Path(cls.temporary.name)
        for p, text in cls.generated.items():
            target = cls.work / p
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding='utf-8')
        spec = importlib.util.spec_from_file_location('polish_android_substitutes', HERE / 'hud-layout/android_fixture.py')
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        stubs = module.write_stubs(cls.work / 'stubs', HERE / 'hud-presentation/android_fixture.py')
        # Observe alignment assignments without modifying the accepted fixture sources.
        tv = cls.work / 'stubs/android/widget/TextView.java'
        tv.write_text(polish.replace_once(tv.read_text(), 'public class TextView extends View {',
            'public class TextView extends View {\n public int gravityCalls; '
            'public void setGravity(int g){gravityCalls++;}'), encoding='utf-8')
        cls.classes = cls.work / 'classes'
        javac = shutil.which('javac')
        if not javac:
            raise AssertionError('JDK required for polish host tests')
        sources = [cls.work / p for p in cls.generated if p.endswith('.java')]
        run([javac, '--release', '8', '-Xlint:all,-options', '-Werror', '-d', str(cls.classes)]
            + [str(p) for p in stubs + sources + [HERE / 'hud-polish/PolishHostTest.java']])
        modes = json.loads((ROOT / 'data/json/move_modes.json').read_text())
        cls.mode_labels = [m['name'] + ' (' + m['panel_char'] + ')' for m in modes] + ['']

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'root'
        self.root.mkdir()
        self.out = Path(self.temp.name) / 'report'
        for p, text in self.parent.items():
            target = self.root / p
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding='utf-8')
        for p in polish.WIDGET_BLOBS:
            target = self.root / p
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / p).read_bytes())

    def tree(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def reject(self):
        before = self.tree()
        with self.assertRaises((ValueError, FileNotFoundError)):
            polish.apply(self.root, self.out)
        self.assertEqual(before, self.tree())
        self.assertFalse(self.out.exists())

    def test_exact_parent_inputs(self):
        for p, expected in {polish.UI: polish.PARENT_UI_SHA256, **polish.UNCHANGED_SHA256}.items():
            self.assertEqual(sha(self.parent[p]), expected)

    def test_only_four_approved_changes_and_title(self):
        text = self.generated[polish.UI]
        text = polish.replace_once(text, '"CDDA-DS / HUD POLISH"', '"CDDA-DS / HUD REFINEMENT"')
        anchor = '                bodyLabels[i] = text(labels[i], 16);\n'
        text = polish.replace_once(text, anchor, anchor + polish.LABEL_ALIGNMENT)
        text = polish.replace_once(text, polish.NEW_MOVEMENT, polish.OLD_MOVEMENT)
        text = polish.replace_once(text, polish.OXYGEN_ROW, '')
        text = polish.replace_once(text, polish.NEW_STAMINA, polish.OLD_STAMINA)
        self.assertEqual(text, self.parent[polish.UI])
        for p in polish.UNCHANGED_SHA256:
            self.assertEqual(self.generated[p], self.parent[p])

    def test_no_literal_label_padding_or_shortening(self):
        labels = 'String[] labels = {"Head", "Torso", "Left arm", "Right arm", "Left leg", "Right leg"};'
        self.assertIn(labels, self.generated[polish.UI])
        self.assertNotIn('Gravity.RIGHT', self.generated[polish.UI])
        self.assertIn('labelWidth, LinearLayout.LayoutParams.WRAP_CONTENT', self.generated[polish.UI])

    def test_stamina_calculation_and_bar_unchanged(self):
        for text in ['double percent = 100.0 * state.current / state.maximum;',
                     'bar.setProgress((int) Math.max(0, Math.min(1000, percent * 10)));']:
            self.assertIn(text, self.parent[polish.UI])
            self.assertIn(text, self.generated[polish.UI])
        self.assertNotIn('(%d / %d)', self.generated[polish.UI])

    def test_all_pinned_movement_names_fit_probe(self):
        self.assertEqual(max(len('Movement mode: ' + m) for m in self.mode_labels),
                         len('Movement mode: crouch (C)'))
        self.assertLess(len('Movement mode: Unknown'), len('Movement mode: crouch (C)'))
        for p, expected in polish.WIDGET_BLOBS.items():
            self.assertEqual(polish.blob_sha((ROOT / p).read_bytes()), expected)

    def test_existing_helpers_font_refresh_and_lifecycle_unchanged(self):
        start = '        private TextView widget(int field) {'
        end = '        void render(Object[] raw) {'
        a, b = self.parent[polish.UI], self.generated[polish.UI]
        self.assertEqual(a[a.index(start):a.index(end)], b[b.index(start):b.index(end)])
        header = '            TextView title = text('
        self.assertEqual(a[:a.index(header)], b[:b.index(header)])
        for p, expected in SUPPORT_BLOBS.items():
            self.assertEqual(polish.blob_sha((HERE / p).read_bytes()), expected)

    def test_single_ui_target_and_provenance(self):
        before = self.tree()
        report = polish.apply(self.root, self.out)
        self.assertEqual([p for p in before if before[p] != self.tree()[p]], [polish.UI])
        self.assertEqual(report['paths'], {polish.UI: sha(self.generated[polish.UI])})
        self.assertEqual(report['movement_pair'], ['Movement mode', 'Sound'])
        self.assertEqual(report['needs_pair'], ['Thirst', 'Hunger'])
        self.assertEqual(report['displayed_widget_count'], 20)
        self.assertTrue(report['presentation_only'])
        self.assertFalse(report['game_actions'])
        self.assertIn('revisit', report['health_spacing_deferred'].lower())
        self.assertEqual(report['overlay_order'][-2:], ['HUD-REFINEMENT.patch', 'HUD-POLISH.patch'])
        self.assertEqual(json.loads((self.out / 'HUD-POLISH.json').read_text()), report)

    def test_patch_round_trip(self):
        polish.apply(self.root, self.out)
        patch = (self.out / 'HUD-POLISH.patch').read_text()
        run(['patch', '-p1', '--batch', '--reverse'], cwd=self.root, input=patch)
        self.assertEqual((self.root / polish.UI).read_text(), self.parent[polish.UI])
        run(['patch', '-p1', '--batch', '--forward'], cwd=self.root, input=patch)
        self.assertEqual((self.root / polish.UI).read_text(), self.generated[polish.UI])

    def test_bad_ui_hash(self):
        (self.root / polish.UI).write_text('changed')
        self.reject()

    def test_changed_dependencies(self):
        for p in polish.UNCHANGED_SHA256:
            with self.subTest(path=p):
                target = self.root / p
                raw = target.read_bytes()
                target.write_text('changed')
                self.reject()
                target.write_bytes(raw)

    def test_changed_movement_definitions(self):
        (self.root / 'data/json/move_modes.json').write_text('[]')
        self.reject()

    def test_missing_inputs(self):
        for p in [polish.UI, *polish.UNCHANGED_SHA256, *polish.WIDGET_BLOBS]:
            with self.subTest(path=p):
                target = self.root / p
                raw = target.read_bytes()
                target.unlink()
                self.reject()
                target.write_bytes(raw)

    def test_missing_and_duplicate_anchors(self):
        for anchor in ['"CDDA-DS / HUD REFINEMENT"', polish.LABEL_ALIGNMENT,
                       polish.OLD_MOVEMENT, polish.OXYGEN_ANCHOR, polish.OLD_STAMINA]:
            for text in [self.parent[polish.UI].replace(anchor, ''), self.parent[polish.UI] + anchor]:
                with self.assertRaises(ValueError):
                    polish.patch_ui(text)

    def test_repeat_application_refused(self):
        polish.apply(self.root, self.out)
        before = self.tree()
        with self.assertRaises(ValueError):
            polish.apply(self.root, self.out)
        self.assertEqual(before, self.tree())

    def test_source_dependency_and_definition_symlinks_refused(self):
        for p in [polish.UI, *polish.UNCHANGED_SHA256, *polish.WIDGET_BLOBS]:
            with self.subTest(path=p):
                target = self.root / p
                raw = target.read_bytes()
                outside = Path(self.temp.name) / 'outside'
                outside.write_bytes(raw)
                target.unlink()
                target.symlink_to(outside)
                self.reject()
                target.unlink()
                target.write_bytes(raw)

    def test_parent_directory_symlink_refused(self):
        target = self.root / 'android'
        outside = Path(self.temp.name) / 'android'
        target.rename(outside)
        target.symlink_to(outside, target_is_directory=True)
        self.reject()

    def test_unsafe_paths_refused(self):
        for p in ['/tmp/escape', '../escape']:
            with self.assertRaises(ValueError):
                polish.safe_target(self.root, p)

    def host(self, mode):
        result = run(['java', '-cp', str(self.classes), 'com.cleverraven.cataclysmdda.PolishHostTest',
                      mode, *self.mode_labels])
        self.assertIn('polish host substitute passed: ' + mode, result.stdout)

    def test_host_order_alignment_mapping_width_and_modes(self): self.host('normal')
    def test_host_blank_transitions(self): self.host('blank')
    def test_host_missing_readings(self): self.host('missing')
    def test_host_long_text_preserved(self): self.host('long')
    def test_host_changing_values_keep_positions(self): self.host('changing')
    def test_host_larger_modeled_text(self): self.host('large-font')
    def test_host_font_fallback(self): self.host('fallback')
    def test_host_stamina_precision_math_and_raw_values(self): self.host('stamina')


if __name__ == '__main__':
    unittest.main()
