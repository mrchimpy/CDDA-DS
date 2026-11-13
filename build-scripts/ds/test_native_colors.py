"""Native colors: guarded overlay, actual JNI, native evaluator and host UI tests.

Fixtures are not a full game, Android renderer, font engine or Thor acceptance.
"""
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
from unittest.mock import patch

import apply_native_colors as overlay

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SUPPORT = HERE / 'native-colors'
FIXTURE = os.environ.get('DS_NATIVE_COLOR_PARENT_FIXTURE')


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    result = subprocess.run(args, capture_output=True, text=True, timeout=90, **kwargs)
    if result.returncode:
        raise AssertionError(f'{args}\n{result.stdout}\n{result.stderr}')
    return result


def parent_sources() -> dict[str,str]:
    if FIXTURE:
        # Local reviewed artifact reconstruction; production apply() has NO bypass.
        base = Path(FIXTURE)
        return {p: (base/p).read_text() if (base/p).is_file() else '// unchanged test-only placeholder\n'
                for p in overlay.PARENT_SHA256}
    import apply_body_details as body
    import apply_hud_presentation as presentation
    import apply_needs_status as needs
    import apply_hud_layout as layout
    import apply_hud_refinement as refinement
    import apply_hud_polish as polish
    result = body.render_templates()
    for p in ['src/game.cpp','src/main.cpp',overlay.JAVA+'CataclysmDDA.java']:
        result[p] = body.patch_text(p,(ROOT/p).read_text())
    result[overlay.UI] = presentation.patch_ui(result[overlay.UI])
    result[overlay.JAVA+'HudTypeface.java'] = presentation.TEMPLATE.read_text()
    for p in list(result):
        if p in needs.PARENT_SHA256: result[p] = needs.patch_text(p,result[p])
    for module in [layout,refinement,polish]:
        result[overlay.UI] = module.patch_ui(result[overlay.UI])
    return {p:result[p] for p in overlay.PARENT_SHA256}


class NativeColorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = parent_sources()
        # In CI all nine exact production inputs are checked. The local artifact
        # fixture has six full generated sources plus a focused game-hook fragment.
        local_fragments = {'src/game.cpp','src/main.cpp',overlay.JAVA+'CataclysmDDA.java'}
        for p,expected in overlay.PARENT_SHA256.items():
            if not (FIXTURE and p in local_fragments):
                if overlay.sha(cls.parent[p].encode()) != expected:
                    raise AssertionError('Build-16 parent changed: '+p)
        cls.generated = dict(cls.parent)
        for p,fn in overlay.PATCHERS.items(): cls.generated[p] = fn(cls.parent[p])
        for name,p in overlay.TEMPLATES.items():
            data=(SUPPORT/name).read_bytes()
            if overlay.blob(data) != overlay.TEMPLATE_BLOBS[name]:
                raise AssertionError('Production template identity mismatch: '+name)
            cls.generated[p]=data.decode()
        cls.tmp = tempfile.TemporaryDirectory(); cls.addClassCleanup(cls.tmp.cleanup)
        cls.work = Path(cls.tmp.name)
        for p,text in cls.generated.items():
            target=cls.work/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
        stubs=load('native_color_android_fixture',SUPPORT/'android_fixture.py').write_stubs(cls.work/'stubs')
        cls.classes=cls.work/'classes'
        cls.javac=shutil.which('javac')
        if not cls.javac: raise AssertionError('JDK required')
        java_files=[cls.work/p for p in cls.generated if p.endswith('.java') and not p.endswith('/CataclysmDDA.java')]
        run([cls.javac,'--release','8','-Xlint:all,-options','-Werror','-d',str(cls.classes)]
            +list(map(str,stubs+java_files+[SUPPORT/'NativeColorHostTest.java'])))
        native=load('native_color_game_fixture',SUPPORT/'native_fixture.py')
        fixtures=native.write(cls.work/'native-stubs',ROOT)
        cls.cxx=['g++','-std=c++17','-Wall','-Wextra','-Werror','-Wno-unused-function','-pthread',
                 '-I',str(cls.work/'src'),'-I',str(cls.work/'native-stubs'),
                 str(cls.work/'src/ds_hud.cpp'),str(SUPPORT/'NativeColorTest.cpp')]+list(map(str,fixtures))
        cls.executable=cls.work/'native-test';run(cls.cxx+['-o',str(cls.executable)])
        java_home=Path(cls.javac).resolve().parents[1]
        cls.library=cls.work/'libnativecolors.so'
        run(cls.cxx+['-D__ANDROID__','-shared','-fPIC','-I',str(java_home/'include'),
                    '-I',str(java_home/'include/linux'),'-o',str(cls.library)])

    def setUp(self):
        self.tmpdir=tempfile.TemporaryDirectory();self.addCleanup(self.tmpdir.cleanup)
        self.root=Path(self.tmpdir.name)/'root';self.root.mkdir()
        self.report=Path(self.tmpdir.name)/'report'
        self.parents={p:overlay.sha(text.encode()) for p,text in self.parent.items()}
        self.deps={}
        for p,text in self.parent.items():
            target=self.root/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
        for p in overlay.DEPENDENCY_BLOBS:
            # Mock identities belong only to this synthetic apply() unit fixture.
            # Actual JSON bytes and native evaluator are tested separately.
            data=(ROOT/p).read_bytes() if (ROOT/p).is_file() else b'fixture-only dependency\n'
            target=self.root/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
            self.deps[p]=overlay.blob(data)

    def apply(self):
        with patch.dict(overlay.PARENT_SHA256,self.parents,clear=True),patch.dict(overlay.DEPENDENCY_BLOBS,self.deps,clear=True):
            return overlay.apply(self.root,self.report)

    def tree(self):
        return {p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def reject(self):
        before=self.tree()
        with self.assertRaises((ValueError,FileNotFoundError)): self.apply()
        self.assertEqual(before,self.tree());self.assertFalse(self.report.exists())

    def test_parent_generated_identities(self):
        for p in ['src/ds_hud.h','src/ds_hud.cpp',overlay.UI,
                  overlay.JAVA+'CoreHudSnapshot.java',overlay.JAVA+'ActivityHudSnapshot.java',overlay.JAVA+'HudTypeface.java']:
            self.assertEqual(overlay.sha(self.parent[p].encode()),overlay.PARENT_SHA256[p])

    def test_only_seven_integration_targets(self):
        before=self.tree();report=self.apply();after=self.tree()
        changed={p for p in after if before.get(p)!=after[p]}
        self.assertEqual(changed,set(overlay.PATCHERS)|set(overlay.TEMPLATES.values()))
        self.assertEqual(len(changed),7)
        for p,digest in report['paths'].items():self.assertEqual(overlay.sha(after[p]),digest)
        self.assertFalse(report['game_actions']);self.assertEqual(report['comfort_pair'],['Body comfort','Comfort trend'])

    def test_json_definition_identities(self):
        for p,h in overlay.DEPENDENCY_BLOBS.items():
            if p.endswith('.json'):self.assertEqual(overlay.blob((ROOT/p).read_bytes()),h)

    def test_decoders_and_font_loader_unchanged(self):
        for p in ['CoreHudSnapshot.java','ActivityHudSnapshot.java','HudTypeface.java']:
            self.assertEqual(self.parent[overlay.JAVA+p],self.generated[overlay.JAVA+p])

    def test_outer_input_focus_and_polling_unchanged(self):
        split='    private static final class HudPresentation'
        old=self.parent[overlay.UI].split(split)[0]
        new=self.generated[overlay.UI].split(split)[0]
        old=old.replace('// One coherent copy: Object[] { long[53], byte[30][] UTF-8 movement/status text }.',
                        '// One coherent copy: original values/text plus long[] DSC1 native colors.')
        self.assertEqual(old,new)
        for p in ['src/main.cpp',overlay.JAVA+'CataclysmDDA.java']:
            self.assertEqual(self.parent[p],self.generated[p])

    def test_native_rules_not_reimplemented_in_java(self):
        java=self.generated[overlay.JAVA+'NativeHudColors.java']
        self.assertNotIn('get_stamina',java);self.assertNotIn('37.5',java);self.assertNotIn('get_perceived_pain',java)
        capture=self.generated['src/ds_hud_color_capture.h']
        self.assertIn('view.value_color( view.get_var_value( u ) )',capture)
        self.assertIn('get_color_from_tag( candidate, report_color_error::no )',capture)
        self.assertIn('color.is_blink() ? 8 : 0',capture)

    def test_capture_keeps_plain_text_and_single_publish(self):
        text=self.generated['src/game.cpp']
        self.assertEqual(text.count('const std::string marked = view.show( u, 80 );'),1)
        self.assertIn('activity.text[i] = remove_color_tags( marked );',text)
        self.assertIn('styled.text == activity.text[i]',text)
        self.assertEqual(text.count('ds_hud::publish('),1)
        self.assertIn('activity, colors );',text)
        self.assertIn('children.empty()',text) # Full oxygen suppression remains.

    def test_one_mailbox_copy_for_jni_extension(self):
        text=self.generated['src/ds_hud.cpp']
        self.assertEqual(text.count('const ds_hud::snapshot state = ds_hud::read();'),1)
        self.assertIn('pack_colors( state.colors, state.sequence )',text)
        self.assertIn('mailbox.colors = mailbox.ready ? colors : color_status{};',text)

    def test_geometry_and_percentage_math_unchanged(self):
        text=self.generated[overlay.UI]
        for line in ['int barGap = Math.round(4 * getContext().getResources().getDisplayMetrics().density);',
                     'int minimumBar = Math.round(64 * getContext().getResources().getDisplayMetrics().density);',
                     'double percent = 100.0 * state.current / state.maximum;',
                     'bar.setProgress((int) Math.max(0, Math.min(1000, percent * 10)));']:
            self.assertIn(line,text);self.assertIn(line,self.parent[overlay.UI])
        self.assertNotIn('setGravity(Gravity.RIGHT',text)
        self.assertIn('"Body comfort: Comfortable", "Comfort trend: (Falling!!)"',text)

    def test_changed_inputs_refused_before_write(self):
        for p in self.parents:
            with self.subTest(path=p):
                target=self.root/p;data=target.read_bytes();target.write_text('changed');self.reject();target.write_bytes(data)

    def test_changed_native_definitions_refused(self):
        for p in self.deps:
            with self.subTest(path=p):
                target=self.root/p;data=target.read_bytes();target.write_text('changed');self.reject();target.write_bytes(data)

    def test_missing_inputs_refused(self):
        for p in [overlay.UI,'src/game.cpp','data/json/ui/hp.json']:
            target=self.root/p;data=target.read_bytes();target.unlink();self.reject();target.write_bytes(data)

    def test_source_symlinks_refused(self):
        for p in [overlay.UI,'src/game.cpp','data/json/ui/body_temp.json']:
            target=self.root/p;data=target.read_bytes();outside=Path(self.tmpdir.name)/'outside';outside.write_bytes(data)
            target.unlink();target.symlink_to(outside);self.reject();target.unlink();target.write_bytes(data)

    def test_parent_directory_symlink_refused(self):
        target=self.root/'android';outside=Path(self.tmpdir.name)/'android';target.rename(outside);target.symlink_to(outside,target_is_directory=True);self.reject()

    def test_existing_new_destination_refused(self):
        for destination in overlay.TEMPLATES.values():
            target=self.root/destination;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('existing');self.reject();target.unlink()

    def test_repeat_application_refused(self):
        self.apply();before=self.tree()
        with self.assertRaises(ValueError):self.apply()
        self.assertEqual(before,self.tree())

    def test_duplicate_or_missing_anchors_refused(self):
        for anchor in ['#include "ds_hud.h"\n','    ds_hud::activity_status activity;\n']:
            source=self.parent['src/game.cpp']
            for bad in [source.replace(anchor,''),source+anchor]:
                with self.assertRaises(ValueError):overlay.patch_game(bad)

    def test_path_traversal_refused(self):
        for name in ['../x','/tmp/x','a/../x','']:
            with self.assertRaises(ValueError):overlay.safe_target(self.root,name)

    def test_patch_forward_reverse_roundtrip(self):
        before=self.tree();self.apply();after=self.tree()
        run(['patch','--batch','-R','-p1','-i',str(self.report/'NATIVE-COLORS.patch')],cwd=self.root)
        self.assertEqual(before,self.tree())
        run(['patch','--batch','-p1','-i',str(self.report/'NATIVE-COLORS.patch')],cwd=self.root)
        self.assertEqual(after,self.tree())

    def native(self,mode):
        self.assertIn('native color test passed: '+mode,run([str(self.executable),mode]).stdout)
    def host(self,mode):
        result=run(['java','-cp',str(self.classes),'com.cleverraven.cataclysmdda.NativeColorHostTest',str(self.library),mode])
        self.assertIn('native color host passed: '+mode,result.stdout)

    def test_native_markup_nested_unicode_and_limits(self):self.native('parser')
    def test_native_threshold_boundaries_from_real_evaluator(self):self.native('thresholds')
    def test_native_palette_background_bold_and_missing_widgets(self):self.native('palette')
    def test_native_mailbox_copy_coherence_and_clearing(self):self.native('mailbox')
    def test_jni_ui_mapping_order_and_native_colors(self):self.host('normal')
    def test_jni_ui_multicolor_and_utf8_to_utf16(self):self.host('unicode')
    def test_jni_ui_malformed_color_fallback(self):self.host('malformed')
    def test_jni_ui_blank_clears_styling(self):self.host('blank')
    def test_jni_ui_missing_reading(self):self.host('missing')
    def test_jni_ui_menu_and_waiting_clear_backgrounds(self):self.host('lifecycle')
    def test_jni_ui_zero_bars_and_recovery(self):self.host('zero')
    def test_jni_ui_recovery_clears_status_colors(self):self.host('recovery')
    def test_jni_ui_color_uses_unrounded_native_values(self):self.host('rounding')
    def test_jni_ui_custom_resolved_rgb(self):self.host('palette')
    def test_jni_ui_copy_isolation(self):self.host('copy')
    def test_jni_ui_comfort_width_boundaries(self):self.host('width')
    def test_jni_ui_large_modeled_font(self):self.host('large-font')
    def test_jni_ui_partial_color_diagnostic(self):self.host('partial')
    def test_jni_ui_font_fallback_preserved(self):self.host('font-fallback')


if __name__ == '__main__':
    unittest.main()
