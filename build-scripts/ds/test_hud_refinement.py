"""Two bounded UI refinements. Host tests are not an Android renderer or Thor test."""
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

import apply_hud_refinement as refinement

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIXTURE = os.environ.get('DS_REFINEMENT_PARENT_FIXTURE')
SUPPORT_BLOBS = {
    'hud-presentation/android_fixture.py': 'd233a438dddfb46fe8026b65cfc1dc6cc22293cb',
    'hud-layout/android_fixture.py': '3ae2fd540c9ab0b7d94ca571863745fdd1bab12b',
    'hud-layout/LayoutHostTest.java': 'c02f96489484e2331a295446c343051b1e636f69',
}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def parent_sources() -> dict[str, str]:
    keys = [refinement.UI, *refinement.UNCHANGED_SHA256]
    if FIXTURE:
        # Explicit local fixture; every input must still match its production hash.
        return {p: (Path(FIXTURE) / p).read_text(encoding='utf-8') for p in keys}
    import apply_body_details as body
    import apply_hud_presentation as presentation
    import apply_needs_status as needs
    import apply_hud_layout as layout
    result = body.render_templates()
    result[refinement.UI] = presentation.patch_ui(result[refinement.UI])
    result[refinement.JAVA_DIR + 'HudTypeface.java'] = presentation.TEMPLATE.read_text(encoding='utf-8')
    for p in keys:
        if p in needs.PARENT_SHA256:
            result[p] = needs.patch_text(p, result[p])
    result[refinement.UI] = layout.patch_ui(result[refinement.UI])
    return {p: result[p] for p in keys}


def descriptions(name: str) -> list[str]:
    definition = json.loads((ROOT / f'data/json/ui/{name}.json').read_text())[0]
    return [c['text']['str'] if isinstance(c['text'], dict) else c['text']
            for c in definition['clauses']]


def run(args: list[str]) -> subprocess.CompletedProcess:
    result = subprocess.run(args, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise AssertionError(f'Command failed: {args}\n{result.stdout}\n{result.stderr}')
    return result


def host_source() -> str:
    """Extend a private copy of the earlier harness, never the earlier test files."""
    text = (HERE / 'hud-layout/LayoutHostTest.java').read_text()
    replace = refinement.replace_once
    text = replace(text, 'public final class LayoutHostTest', 'public final class RefinementHostTest')
    text = replace(text, 'DISPLAY_ORDER = {4,19,15,26,27,', 'DISPLAY_ORDER = {4,19,15,27,26,')
    text = replace(text, 'check(pairs(p.content).size()==10,"three health and seven metric pairs");',
                   'check(pairs(p.content).size()==11,"three health and eight metric pairs");\n'
                   '        needsPairChecks(p);')
    text = replace(text,
        'for(int i:new int[]{4,14,17,18,20,21,22,23,24,25,26,27}){\n'
        '            check(w[i].parent==field(p,"details"),',
        'for(int i:new int[]{4,14,17,18,20,21,22,23,24,25}){\n'
        '            check(w[i].parent==field(p,"details"),')
    text = replace(text, '            check(label.text.equals(PARTS[i]),"named left/right mapping");',
        '            check(label.text.equals(PARTS[i]),"named left/right mapping");\n'
        '            check(label.gravity==(android.view.Gravity.RIGHT|android.view.Gravity.CENTER_VERTICAL),"right health labels");\n'
        '            check(((LinearLayout.LayoutParams)hp[i].params).leftMargin==4,"unchanged fixed bar gap");')
    text = replace(text, '        TextView[] widgets=(TextView[])field(p,"activityValues");',
        '        int aligned=0;\n'
        '        for(TextView t:ts){\n'
        '            if(Arrays.asList(PARTS).contains(t.text)){check(t.gravity==21,"health-only alignment");aligned++;}\n'
        '            else check(t.gravity==0,"non-health text alignment unchanged");\n'
        '        }\n'
        '        check(aligned==6,"exactly six health labels");\n'
        '        TextView[] widgets=(TextView[])field(p,"activityValues");')
    text = replace(text, 'System.out.println("layout host substitute passed: "+mode);',
                   'System.out.println("refinement host substitute passed: "+mode);')
    arrays = '        String[] hunger=' + json.dumps(descriptions('hunger') + ['Unavailable']).replace('[','{').replace(']','}') + ';\n'
    arrays += '        String[] thirst=' + json.dumps(descriptions('thirst') + ['Unavailable']).replace('[','{').replace(']','}') + ';\n'
    extra = '''    static void needsPairChecks(Presentation p) throws Exception {
        TextView[] w=(TextView[])field(p,"activityValues");
        check(w[27].parent==w[26].parent,"one shared needs row");
        LinearLayout row=(LinearLayout)w[27].parent;
        check(row.children.get(0)==w[27]&&row.children.get(1)==w[26],"Thirst left then Hunger right");
        int minimum=(Integer)field(row,"pairWidth");
        int gap=(Integer)field(row,"gap");
        int expected=2*(2+(int)Math.ceil(w[26].getPaint().measureText("Hunger: Near starving")))+gap;
        check(minimum==expected,"fixed longest-description width budget");
        measure(row,minimum,View.MeasureSpec.EXACTLY);
''' + arrays + '''        for(String h:hunger)for(String t:thirst){
            Object[] raw=snapshot();
            ((byte[][])raw[1])[27]=h.getBytes(StandardCharsets.UTF_8);
            ((byte[][])raw[1])[28]=t.getBytes(StandardCharsets.UTF_8);
            int before=row.children.get(0).setParamsCalls;
            call(p,"render",Object[].class,raw);
            check(row.children.get(0)==w[27]&&row.children.get(1)==w[26],"fixed ordering through transitions");
            check(row.getOrientation()==LinearLayout.HORIZONTAL,"no value-driven stacking");
            check(before==row.children.get(0).setParamsCalls,"no value-driven layout mutation");
            check(w[27].text.startsWith("Thirst: ")&&w[26].text.startsWith("Hunger: "),"correct labels");
            for(int i:new int[]{27,26})check(w[i].getPaint().measureText(w[i].text)+2<=(minimum-gap)/2,"all pinned descriptions fit modeled budget");
        }
        measure(row,minimum-1,View.MeasureSpec.EXACTLY);
        check(row.getOrientation()==LinearLayout.VERTICAL,"needs narrow fallback");
        check(row.children.get(0)==w[27]&&row.children.get(1)==w[26],"stacked Thirst then Hunger");
        measure(row,minimum,View.MeasureSpec.EXACTLY);
        check(row.getOrientation()==LinearLayout.HORIZONTAL,"needs width recovery");
        call(p,"render",Object[].class,snapshot());
    }

'''
    return replace(text, '    static void clearState(', extra + '    static void clearState(')


class HudRefinementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = parent_sources()
        for p, expected in {refinement.UI: refinement.PARENT_UI_SHA256, **refinement.UNCHANGED_SHA256}.items():
            if sha(cls.parent[p]) != expected:
                raise AssertionError(f'Parent does not match build 14: {p}')
        for p, expected in SUPPORT_BLOBS.items():
            if refinement.blob_sha((HERE / p).read_bytes()) != expected:
                raise AssertionError(f'Accepted test support changed: {p}')
        cls.generated = dict(cls.parent)
        cls.generated[refinement.UI] = refinement.patch_ui(cls.parent[refinement.UI])
        cls.temporary = tempfile.TemporaryDirectory(); cls.addClassCleanup(cls.temporary.cleanup)
        cls.work = Path(cls.temporary.name)
        for p, text in cls.generated.items():
            target = cls.work / p; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(text)
        spec = importlib.util.spec_from_file_location('refinement_android_substitutes', HERE / 'hud-layout/android_fixture.py')
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        stubs = module.write_stubs(cls.work / 'stubs', HERE / 'hud-presentation/android_fixture.py')
        # Extend only emitted temporary substitutes; earlier fixture sources stay byte-identical.
        gravity = cls.work / 'stubs/android/view/Gravity.java'
        gravity.write_text(refinement.replace_once(gravity.read_text(), 'CENTER_VERTICAL=16;', 'CENTER_VERTICAL=16, RIGHT=5;'))
        tv = cls.work / 'stubs/android/widget/TextView.java'
        tv.write_text(refinement.replace_once(tv.read_text(), 'public class TextView extends View {',
            'public class TextView extends View {\n public int gravity; public void setGravity(int g){gravity=g;}'))
        harness = cls.work / 'RefinementHostTest.java'; harness.write_text(host_source())
        cls.classes = cls.work / 'classes'
        javac = shutil.which('javac')
        if not javac: raise AssertionError('JDK required for refinement host tests')
        sources = [cls.work / p for p in cls.generated if p.endswith('.java')]
        run([javac, '--release', '8', '-Xlint:all,-options', '-Werror', '-d', str(cls.classes)]
            + [str(p) for p in stubs + sources + [harness]])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'root'; self.root.mkdir()
        self.out = Path(self.temp.name) / 'report'
        for p, text in self.parent.items():
            target = self.root / p; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(text)
        for p in refinement.WIDGET_BLOBS:
            target = self.root / p; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes((ROOT / p).read_bytes())

    def tree(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def reject(self):
        before = self.tree()
        with self.assertRaises((ValueError, FileNotFoundError)): refinement.apply(self.root, self.out)
        self.assertEqual(before, self.tree()); self.assertFalse(self.out.exists())

    def test_exact_parent_inputs(self):
        for p, expected in {refinement.UI: refinement.PARENT_UI_SHA256, **refinement.UNCHANGED_SHA256}.items():
            self.assertEqual(sha(self.parent[p]), expected)

    def test_only_approved_ui_changes(self):
        result = self.generated[refinement.UI].replace('"CDDA-DS / HUD REFINEMENT"', '"CDDA-DS / HUD LAYOUT"')
        result = result.replace(refinement.LABEL_ALIGNMENT, '').replace(refinement.NEW_NEEDS, refinement.OLD_NEEDS)
        self.assertEqual(result, self.parent[refinement.UI])
        self.assertEqual(self.generated[refinement.UI].count(refinement.LABEL_ALIGNMENT), 1)
        for p in refinement.UNCHANGED_SHA256: self.assertEqual(self.generated[p], self.parent[p])

    def test_all_native_descriptions_within_fixed_probes(self):
        for name, probe in [('thirst', 'Thirst: Very thirsty'), ('hunger', 'Hunger: Near starving')]:
            texts = descriptions(name) + ['Unavailable', '\u2014']
            self.assertEqual(max(len(name.title() + ': ' + v) for v in texts), len(probe))
        for p, blob in refinement.WIDGET_BLOBS.items(): self.assertEqual(refinement.blob_sha((ROOT / p).read_bytes()), blob)

    def test_unchanged_previous_test_support(self):
        for p, blob in SUPPORT_BLOBS.items(): self.assertEqual(refinement.blob_sha((HERE / p).read_bytes()), blob)

    def test_single_ui_target_and_provenance(self):
        before = self.tree(); report = refinement.apply(self.root, self.out)
        self.assertEqual([p for p in before if before[p] != self.tree()[p]], [refinement.UI])
        self.assertEqual(report['paths'], {refinement.UI: sha(self.generated[refinement.UI])})
        self.assertEqual(report['needs_pair'], ['Thirst', 'Hunger'])
        self.assertEqual(report['displayed_widget_count'], 20)
        self.assertFalse(report['game_actions']); self.assertTrue(report['presentation_only'])
        self.assertEqual(report['overlay_order'][-2:], ['HUD-LAYOUT.patch', 'HUD-REFINEMENT.patch'])

    def test_bad_ui_hash(self):
        (self.root / refinement.UI).write_text('changed'); self.reject()

    def test_all_changed_dependencies(self):
        for p in refinement.UNCHANGED_SHA256:
            with self.subTest(path=p):
                target = self.root / p; raw = target.read_bytes(); target.write_text('changed')
                self.reject(); target.write_bytes(raw)

    def test_changed_definitions(self):
        for p in refinement.WIDGET_BLOBS:
            with self.subTest(path=p):
                target = self.root / p; raw = target.read_bytes(); target.write_text('[]')
                self.reject(); target.write_bytes(raw)

    def test_missing_inputs(self):
        for p in [refinement.UI, *refinement.UNCHANGED_SHA256, *refinement.WIDGET_BLOBS]:
            with self.subTest(path=p):
                target = self.root / p; raw = target.read_bytes(); target.unlink(); self.reject(); target.write_bytes(raw)

    def test_missing_and_duplicate_anchors(self):
        for anchor in [refinement.LABEL_ANCHOR, refinement.OLD_NEEDS, '"CDDA-DS / HUD LAYOUT"']:
            for text in [self.parent[refinement.UI].replace(anchor,''), self.parent[refinement.UI]+anchor]:
                with self.assertRaises(ValueError): refinement.patch_ui(text)

    def test_repeat_application_refused(self):
        refinement.apply(self.root, self.out); before = self.tree()
        with self.assertRaises(ValueError): refinement.apply(self.root, self.out)
        self.assertEqual(before, self.tree())

    def test_source_dependency_and_widget_symlinks_refused(self):
        for p in [refinement.UI, *refinement.UNCHANGED_SHA256, *refinement.WIDGET_BLOBS]:
            with self.subTest(path=p):
                target = self.root / p; raw = target.read_bytes()
                outside = Path(self.temp.name) / 'outside'; outside.write_bytes(raw)
                target.unlink(); target.symlink_to(outside); self.reject(); target.unlink(); target.write_bytes(raw)

    def test_parent_directory_symlink_refused(self):
        target = self.root / 'android'; outside = Path(self.temp.name) / 'android'
        target.rename(outside); target.symlink_to(outside, target_is_directory=True); self.reject()

    def test_unsafe_paths_refused(self):
        for p in ['/tmp/escape', '../escape']:
            with self.assertRaises(ValueError): refinement.safe_target(self.root, p)

    def host(self, mode):
        result = run(['java', '-cp', str(self.classes), 'com.cleverraven.cataclysmdda.RefinementHostTest', mode])
        self.assertIn('refinement host substitute passed: ' + mode, result.stdout)

    def test_host_mapping_alignment_order_and_all_needs_states(self): self.host('normal')
    def test_host_blank_states(self): self.host('blank')
    def test_host_missing_states(self): self.host('missing')
    def test_host_long_strings_preserved(self): self.host('long')
    def test_host_value_changes_do_not_rearrange(self): self.host('changing')
    def test_host_larger_modeled_text(self): self.host('large-font')
    def test_host_font_fallback_retained(self): self.host('fallback')


if __name__ == '__main__':
    unittest.main()
