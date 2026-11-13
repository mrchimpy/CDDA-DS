"""Host checks for body-details; substitutes are not the actual CDDA renderer."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import apply_activity_status as activity
import apply_body_status as body
import apply_core_status as core
import apply_environment_status as environment
import apply_equipment_status as equipment
import apply_body_details as details

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "body-details/host-fixtures"
WIDGET_FILES = {
    "body_temp": "aafafe1251e39fed3fa9fac93b3a10f92626e5ed",
    "oxygen": "a3e03f6f65be327ca60408ed7003f2f9633a118b",
    "bodypart_armor": "d9e78614890e12ddb564376138f51c5f22b149b2",
}
# Generated files from accepted build 10, not fresh expected values derived by this test.
PARENT_OUTPUTS = {
    "src/ds_hud.h": "e42857aa5c8778f585c63477392dcf034299a61e8b3a121153ba5715582a0a3c",
    "src/ds_hud.cpp": "c645570da3a92e66d1b4928a29d84cc3fa29bf08918b9582b689811c2e55cd40",
    activity.JAVA_DIR + "DualScreenHud.java": "903372b74671da5c7bf5fd37d8dd8782f352dd0c0cbefc670f24923845d735d8",
    activity.JAVA_DIR + "CoreHudSnapshot.java": "d95a69c314a4419b2baa915ec3d10724135414a5c086001079aa5816954c7070",
    activity.JAVA_DIR + "ActivityHudSnapshot.java": "0b9c3553bb2b5e4c5c43d4848afc0eb0b7c4d744e94b0a5e5d4a139716116c83",
}


def run(command: list[str]) -> subprocess.CompletedProcess:
    result = subprocess.run(command, capture_output=True, text=True, timeout=45)
    if result.returncode:
        raise AssertionError(f"{command[0]} failed:\n{result.stdout}\n{result.stderr}")
    return result


class BodyDetailsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.sources = {
            "src/game.cpp": body.INCLUDE + body.PANEL + "    (void)force_draw;\n}\n",
            "src/main.cpp": body.INCLUDE + "void loop() {\n" + body.SESSION + "}\n",
            body.JAVA: "class CataclysmDDA {\n    private NativeUI nativeUI = null;\n"
                + body.RESUME + "    }\n" + body.FOCUS + "}\n}\n",
        }
        for path, text in self.sources.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        self.guard = patch.dict(details.EXPECTED_BLOBS, {
            p: body.blob_sha(t.encode()) for p, t in self.sources.items()
        }, clear=True)
        self.guard.start()
        self.addCleanup(self.guard.stop)

    def originals(self):
        for p, t in self.sources.items():
            self.assertEqual((self.root / p).read_text(), t)
        self.assertFalse((self.root / "src/ds_hud.h").exists())

    def generated(self):
        directory = self.root / "generated"
        directory.mkdir(exist_ok=True)
        for path, text in details.render_templates().items():
            (directory / Path(path).name).write_text(text)
        return directory

    def widgets(self):
        definitions = {}
        for name, expected in WIDGET_FILES.items():
            raw = (HERE.parent.parent / f"data/json/ui/{name}.json").read_bytes()
            self.assertEqual(body.blob_sha(raw), expected)
            definitions.update({w['id']: w for w in json.loads(raw)})
        return definitions

    def test_pinned_widgets_and_append_order(self):
        definitions = self.widgets()
        self.assertEqual(details.WIDGET_IDS[:17], equipment.WIDGET_IDS)
        self.assertEqual(len(set(details.WIDGET_IDS)), 26)
        for wid, _ in details.BODY_WIDGETS:
            self.assertIn(wid, definitions)
        self.assertEqual(details.OXYGEN_INDEX, 19)

    def test_comfort_and_trend_reuse_native_clauses(self):
        w = self.widgets()
        self.assertEqual(w['body_temp_desc_label']['copy-from'], 'body_temp_template')
        self.assertEqual(w['body_temp_delta_desc_label']['copy-from'], 'body_temp_delta_template')
        self.assertEqual(w['body_temp_delta_template']['default_clause']['text'], '')
        self.assertIn('Comfortable', [c['text'] for c in w['body_temp_template']['clauses']])

    def test_armor_is_native_grouped_outer_layer_summary(self):
        w = self.widgets()
        ids = [wid for wid, _ in details.BODY_WIDGETS[3:]]
        self.assertEqual(w['bodypart_armor_outer_layout']['widgets'], ids)
        self.assertEqual([w[wid]['bodypart'] for wid in ids],
                         ['head', 'torso', 'arm_r', 'hand_r', 'leg_r', 'foot_r'])
        self.assertEqual(w['bodypart_armor_outer_text']['var'], 'bp_armor_outer_text')
        self.assertTrue(all(w[wid]['copy-from'] == 'bodypart_armor_outer_text' for wid in ids))

    def test_oxygen_definition_and_native_condition(self):
        w = self.widgets()
        graph = w['oxygen_graph_classic']
        self.assertEqual((graph['style'], graph['width'], graph['symbols']), ('graph', 5, '.\\|'))
        gate = w[details.OXYGEN_LAYOUT]
        self.assertEqual(gate['clauses'][0]['condition']['math'], ['u_oxygen_max() != u_oxygen()'])
        self.assertEqual(gate['clauses'][0]['widgets'], 'oxygen_graph_classic')
        self.assertIn('W_DISABLED_WHEN_EMPTY', gate['flags'])

    def test_parent_rendering_matches_build_10(self):
        for path, text in equipment.render_templates().items():
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), PARENT_OUTPUTS[path])

    def test_original_templates_and_scripts_not_changed(self):
        files = list(environment.TEMPLATE_BLOBS) + [
            'apply_body_status.py', 'apply_core_status.py', 'apply_activity_status.py',
            'apply_environment_status.py', 'apply_equipment_status.py']
        before = {p: (HERE / p).read_bytes() for p in files}
        before_ids = equipment.WIDGET_IDS
        details.apply(self.root, self.root / 'dist')
        self.assertEqual(equipment.WIDGET_IDS, before_ids)
        for p, raw in before.items():
            self.assertEqual((HERE / p).read_bytes(), raw)

    def test_transport_counts_and_native_logic_preserved(self):
        output, parent = details.render_templates(), equipment.render_templates()
        self.assertEqual(output[activity.JAVA_DIR + 'CoreHudSnapshot.java'],
                         parent[activity.JAVA_DIR + 'CoreHudSnapshot.java'])
        self.assertEqual(output['src/ds_hud.cpp'], parent['src/ds_hud.cpp'].replace(
            'Object[] { long[41], byte[18][] }', 'Object[] { long[50], byte[27][] }'))
        self.assertIn('activity_field_count = 26;', output['src/ds_hud.h'])
        self.assertIn('STATUS_COUNT = 26;', output[activity.JAVA_DIR + 'ActivityHudSnapshot.java'])

    def test_layout_only_changes_title_and_oxygen_typeface(self):
        key = activity.JAVA_DIR + 'DualScreenHud.java'
        java, parent = details.render_templates()[key], equipment.render_templates()[key]
        restored = java.replace('CDDA-DS / BODY DETAILS', 'CDDA-DS / EQUIPMENT STATUS').replace(
            '                if (i == ActivityHudSnapshot.OXYGEN) {\n'
            '                    activityValues[i].setTypeface(Typeface.MONOSPACE);\n'
            '                }\n', '')
        self.assertEqual(restored, parent)
        self.assertIn('for (TextView field : activityValues) field.setText("")', java)
        self.assertIn('activityValues[i] = text("", 16)', java)

    def test_lifecycle_and_input_hooks_unchanged(self):
        for p in ('src/main.cpp', body.JAVA):
            self.assertEqual(details.patch_text(p, self.sources[p]), equipment.patch_text(p, self.sources[p]))
        java = details.render_templates()[activity.JAVA_DIR + 'DualScreenHud.java']
        self.assertIn('FLAG_NOT_FOCUSABLE', java)
        self.assertIn('FOCUS_BLOCK_DESCENDANTS', java)
        self.assertIn('handler.postDelayed(this, 250)', java)

    def test_capture_is_read_only_and_uses_conditional_child_selection(self):
        capture = details.patch_text('src/game.cpp', self.sources['src/game.cpp'])
        for wid in details.WIDGET_IDS:
            self.assertEqual(capture.count('"' + wid + '"'), 1)
        self.assertIn('gate.widgets( true )', capture)
        self.assertIn('children.front() != id', capture)
        self.assertIn('remove_color_tags( view.show( u, 80 ) )', capture)
        self.assertIn('if( ds_hud::read().active )', capture)
        self.assertEqual(capture.count('ds_hud::publish('), 1)
        for forbidden in ('.layout(', 'get_oxygen(', 'get_oxygen_max(', 'u_oxygen(',
                          'calendar::turn', 'invalidate_main_ui', 'u.moves', 'wear_item(', 'takeoff('):
            self.assertNotIn(forbidden, capture)

    def test_overlay_all_eight_targets_and_provenance(self):
        report = details.apply(self.root, self.root / 'dist')
        self.assertEqual(report['experiment'], 'body_details')
        self.assertEqual(len(report['paths']), 8)
        self.assertFalse(report['game_actions'])
        self.assertTrue(report['original_sidebar_retained'])
        self.assertEqual(report['conditional_widget_layouts'], {'oxygen_graph_classic': 'oxygen_classic_layout'})
        for p, expected in report['paths'].items():
            self.assertEqual(hashlib.sha256((self.root / p).read_bytes()).hexdigest(), expected)
        self.assertEqual(json.loads((self.root / 'dist/BODY-DETAILS.json').read_text()), report)
        self.assertIn('oxygen_classic_layout', (self.root / 'dist/BODY-DETAILS.patch').read_text())

    def test_original_source_guards_unchanged(self):
        self.assertEqual(body.EXPECTED_BLOBS, equipment.EXPECTED_BLOBS)
        self.assertEqual(body.EXPECTED_BLOBS['src/game.cpp'], '9c5ac1c44ab7079852eebdad1bb92b77c5c3d5c5')

    def test_bad_hash_fails_before_writes(self):
        (self.root / 'src/main.cpp').write_text('changed')
        with self.assertRaises(ValueError): details.apply(self.root, self.root / 'dist')
        self.assertEqual((self.root / 'src/game.cpp').read_text(), self.sources['src/game.cpp'])
        self.assertFalse((self.root / 'src/ds_hud.h').exists())

    def test_existing_destination_fails_before_writes(self):
        (self.root / 'src/ds_hud.cpp').write_text('existing')
        with self.assertRaises(ValueError): details.apply(self.root, self.root / 'dist')
        self.originals()

    def test_source_symlink_refused(self):
        p = self.root / 'src/game.cpp'
        p.rename(self.root / 'original')
        p.symlink_to(self.root / 'original')
        with self.assertRaises(ValueError): details.apply(self.root, self.root / 'dist')
        self.originals()

    def test_destination_symlink_refused(self):
        (self.root / 'src/ds_hud.cpp').symlink_to(self.root / 'missing')
        with self.assertRaises(ValueError): details.apply(self.root, self.root / 'dist')
        self.originals()

    def test_parent_path_escape_refused(self):
        (self.root / 'escape').symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaises(ValueError): core.safe_target(self.root, 'escape/file')

    def test_missing_template_fails_before_writes(self):
        empty = self.root / 'empty'
        empty.mkdir()
        with self.assertRaises(FileNotFoundError): details.apply(self.root, self.root / 'dist', empty)
        self.originals()

    def test_changed_template_fails_before_writes(self):
        folder = self.root / 'templates'
        for name in environment.TEMPLATE_BLOBS:
            path = folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((HERE / name).read_bytes())
        (folder / 'activity-status/ds_hud.h').write_text('changed')
        with self.assertRaises(ValueError): details.apply(self.root, self.root / 'dist', folder)
        self.originals()

    def test_duplicate_anchor_refused(self):
        with self.assertRaises(ValueError):
            details.patch_text('src/game.cpp', self.sources['src/game.cpp'] + body.PANEL)

    def test_repeat_application_refused(self):
        details.apply(self.root, self.root / 'dist')
        with self.assertRaises(ValueError): details.apply(self.root, self.root / 'dist')

    def test_native_snapshot_coherence_copy_and_session_clearing(self):
        d = self.generated()
        compiler = shutil.which('g++') or shutil.which('clang++')
        self.assertIsNotNone(compiler)
        exe = self.root / 'native'
        run([compiler, '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pthread', '-I', str(d),
             str(d / 'ds_hud.cpp'), str(FIXTURES / 'test_native.cpp'), '-o', str(exe)])
        run([str(exe)])

    def test_real_jni_transport_and_decoder(self):
        d = self.generated()
        compiler = shutil.which('g++') or shutil.which('clang++')
        javac, java = shutil.which('javac'), shutil.which('java')
        self.assertIsNotNone(compiler)
        self.assertIsNotNone(javac)
        self.assertIsNotNone(java)
        inc = Path(javac).resolve().parent.parent / 'include'
        lib = self.root / 'libbodydetails.so'
        run([compiler, '-std=c++17', '-shared', '-fPIC', '-pthread', '-D__ANDROID__',
             '-Wall', '-Wextra', '-Werror', '-I', str(inc), '-I', str(inc / 'linux'), '-I', str(d),
             str(d / 'ds_hud.cpp'), str(FIXTURES / 'test_native.cpp'), '-o', str(lib)])
        classes = self.root / 'classes'
        classes.mkdir()
        run([javac, '--release', '8', '-Xlint:all,-options', '-Werror', '-d', str(classes),
             str(d / 'CoreHudSnapshot.java'), str(d / 'ActivityHudSnapshot.java'),
             str(FIXTURES / 'DualScreenHud.java'), str(FIXTURES / 'BodyDetailsSnapshotTest.java')])
        result = run([java, '-Xcheck:jni', '-cp', str(classes),
                      'com.cleverraven.cataclysmdda.BodyDetailsSnapshotTest', str(lib)])
        self.assertIn('body details real JNI round-trip passed', result.stdout)
        self.assertNotIn('WARNING', result.stdout + result.stderr)

    def test_compiled_capture_fixture_full_reduced_missing_and_changed(self):
        d = self.generated()
        compiler = shutil.which('g++') or shutil.which('clang++')
        self.assertIsNotNone(compiler)
        (d / 'game.h').write_text(r'''#pragma once
#include <string>
struct bodypart_id { explicit bodypart_id(const char *) {} };
struct mode { std::string name() const { return "walk"; } char panel_letter() const { return 'W'; } };
struct avatar {
    mode movement;
    int get_part_hp_cur(const bodypart_id &) const { return 20; }
    int get_part_hp_max(const bodypart_id &) const { return 80; }
    int get_stamina() const { return 25; } int get_stamina_max() const { return 100; }
    int get_str() const { return 5; } int get_dex() const { return 3; }
    int get_int() const { return 4; } int get_per() const { return 2; }
    int get_speed() const { return 75; } int get_focus() const { return 137; }
    const mode *current_movement_mode() const { return &movement; }
};
struct game { avatar u; void draw_panels(bool force_draw); };
''')
        (d / 'move_mode.h').write_text('#include "game.h"\n')
        (d / 'widget.h').write_text(r'''#pragma once
#include "game.h"
#include <cassert>
#include <map>
#include <vector>
struct widget;
struct widget_id {
    std::string id;
    explicit widget_id(const char *p): id(p) {}
    bool is_valid() const;
    const widget &obj() const;
    bool operator!=(const widget_id &other) const { return id != other.id; }
};
inline int total_calls = 0;
inline int gate_calls = 0;
struct widget {
    std::string value;
    int calls = 0;
    std::vector<widget_id> children;
    std::string show(const avatar &, int width) {
        assert(width == 80); ++calls; ++total_calls; return value;
    }
    std::vector<widget_id> widgets(bool conditions) {
        assert(conditions); ++calls; ++gate_calls; return children;
    }
};
inline std::map<std::string, widget> definitions;
inline bool widget_id::is_valid() const { return definitions.count(id) != 0; }
inline const widget &widget_id::obj() const { return definitions.at(id); }
inline std::string remove_color_tags(const std::string &s) { return s; }
''')
        (d / 'capture.cpp').write_text(details.patch_text('src/game.cpp', self.sources['src/game.cpp']))
        ids = ', '.join(json.dumps(i) for i in details.WIDGET_IDS)
        caller = (FIXTURES / 'test_capture.cpp').read_text().replace('/* WIDGET_IDS */', ids)
        (d / 'caller.cpp').write_text(caller)
        # The generated game hook uses __ANDROID__, but the mailbox is a host object.
        run([compiler, '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pthread', '-I', str(d),
             '-c', str(d / 'ds_hud.cpp'), '-o', str(d / 'mailbox.o')])
        exe = self.root / 'capture'
        run([compiler, '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pthread', '-D__ANDROID__',
             '-I', str(d), str(d / 'capture.cpp'), str(d / 'caller.cpp'), str(d / 'mailbox.o'),
             '-o', str(exe)])
        run([str(exe)])
