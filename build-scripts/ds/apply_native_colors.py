#!/usr/bin/env python3
"""Native color fidelity and one comfort pair, applied after the unchanged hud_polish stage."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
JAVA = 'android/app/src/main/java/com/cleverraven/cataclysmdda/'
UI = JAVA + 'DualScreenHud.java'
PARENT_SHA256 = {'src/ds_hud.h': '8c47d4b841ca6ebe8ce27855b600ac56f6a200d6d8868197e87a8b0a02d75b56', 'src/ds_hud.cpp': 'f1413b8d07c549fbe57fe9da81c7bb0d44f40f6f84c8c2ecc39d128803697f5d', 'android/app/src/main/java/com/cleverraven/cataclysmdda/CoreHudSnapshot.java': 'd95a69c314a4419b2baa915ec3d10724135414a5c086001079aa5816954c7070', 'android/app/src/main/java/com/cleverraven/cataclysmdda/ActivityHudSnapshot.java': '560cb0c6edfa2c946b7e74e3a705af844b55a4ddaa686882df648032c395edf1', 'android/app/src/main/java/com/cleverraven/cataclysmdda/HudTypeface.java': '093fb83d6b3377b2bae49ca46e68bb9147c8896039c2ef0efcb323dcfcfd2642', 'android/app/src/main/java/com/cleverraven/cataclysmdda/DualScreenHud.java': 'f7a0c3d02432e058b2aa1afc728dda14f2e2f62e031850eb66f6c1d21c7bacea', 'src/game.cpp': '1fb77fb8a136ce24fb5e024adc63670396e62fffe9a30b125d630f64cb155221', 'src/main.cpp': 'edd842646586a3ec55c41ced17ccbff0b8564aed874c1183b12a8de2e7cdc99e', 'android/app/src/main/java/com/cleverraven/cataclysmdda/CataclysmDDA.java': 'bd0c0a6b61c411723487904777871f3efb53c161180e9b1cc36087b73124cc91'}
DEPENDENCY_BLOBS = {'data/raw/colors.json': 'db6e7abe05494c36f1c5096b9332ef04f9c1a779', 'data/json/move_modes.json': '3d192121f0f26c7c8ab3efee9e3c8367ddbbfe98', 'data/json/ui/morale.json': '99ba0e965a8f2501fe142f51bb5249a9d6892f49', 'data/json/ui/sleepiness.json': 'c1a8c2f018d4e26937a77f7c199f8bd71fcb8b49', 'data/json/ui/body_temp.json': 'aafafe1251e39fed3fa9fac93b3a10f92626e5ed', 'data/json/ui/power.json': 'ec009ad36ee11b5b646fb4ca220b88df5ab770f9', 'data/json/ui/stamina.json': '59119a8a83f0f46a5cb8e9806fdfc5da9a7dc18e', 'data/json/ui/pain.json': '8cfa52b17b98821682fba545c11cd9592f5988fe', 'data/json/ui/activity.json': '19c8755996ea166eaeb9fd1f3175f53511863a2c', 'data/json/ui/movement.json': 'd0e99fae9a778178a7289e5cf319bb7b5849fb3c', 'data/json/ui/stats.json': '050fef77d03e3ce1866950f92b6a2b54ffbe6fc8', 'data/json/ui/weariness.json': 'a18c11eefad568bc9acfd423c4768e2f15f49c70', 'data/json/ui/hunger.json': '0ff6803cd0199ce99bde23efd4f79566ec204efb', 'data/json/ui/thirst.json': 'de6038aef54385d037082567e59c493f808fa395', 'data/json/ui/bodypart_color_text.json': '181300748650175ab5778e149d2eee2c32672a87', 'data/json/ui/focus.json': 'f6bf9884ede33264077bfa6dee5233db5e7c56c0', 'data/json/ui/sound.json': '8bb06f1d93bf33dac8b4ecb4ca968004f0ef5130', 'data/json/ui/speed.json': '91de7495affb01ded05d5305663ebf6f44d2c787', 'data/json/ui/hp.json': '574c1aa72b77eb6019bede01b6716e35f5f0ce5f', 'data/json/ui/oxygen.json': 'a3e03f6f65be327ca60408ed7003f2f9633a118b', 'data/json/ui/bodypart_armor.json': 'd9e78614890e12ddb564376138f51c5f22b149b2', 'src/widget.cpp': '9694e79611e175d7edf5385b3cf55aab798a9c10', 'src/widget.h': '96e076d98c6cde984151a292b71c9fa39461a0fe', 'src/cursesport.cpp': '4d91755302a83b476070e9ffcace517c04ef5540', 'src/color.cpp': '3dcfad21879c061b588adecc8dea13da8679a919', 'src/color.h': '75f3e522b966ae5cfbcd752bf46faf53e9a79c33', 'src/sdltiles.h': '75245b36ca441221a6fd9afceba88f4c74ac65ef', 'src/color_loader.h': 'dc5b9ea45a9ad06c707df0096590feaf3ffd6806'}
TEMPLATE_BLOBS = {'ds_hud_colors.h': '450faa7e8a640fc090bd1f483e09fbc9a886b4ae', 'ds_hud_color_capture.h': 'a611dfe963ccd7a2cf8785f75a10752a745f3915', 'NativeHudColors.java': '5389cfc5902aa1a199e592f044dadb69c6601f93'}
TEMPLATES = {
    'ds_hud_colors.h': 'src/ds_hud_colors.h',
    'ds_hud_color_capture.h': 'src/ds_hud_color_capture.h',
    'NativeHudColors.java': JAVA + 'NativeHudColors.java',
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def replace(text: str, before: str, after: str) -> str:
    if text.count(before) != 1:
        raise ValueError('Expected one native-color patch anchor: ' + before[:100])
    return text.replace(before, after, 1)


def safe_target(root: Path, relative: str) -> Path:
    parts = PurePosixPath(relative)
    if parts.is_absolute() or not parts.parts or any(p in ('..', '.') for p in parts.parts):
        raise ValueError('Unsafe relative path: ' + relative)
    current = root
    for part in parts.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('Symlinks are not supported: ' + relative)
    return current


def patch_game(text: str) -> str:
    text = replace(text, '#include "ds_hud.h"\n', '#include "ds_hud.h"\n#include "ds_hud_color_capture.h"\n')
    text = replace(text, '    ds_hud::activity_status activity;\n',
                   '    ds_hud::activity_status activity;\n    ds_hud::color_status colors;\n')
    text = replace(text, '    if( ds_hud::read().active ) {\n',
                   '    if( ds_hud::read().active ) {\n        colors = ds_hud::capture_native_colors( u );\n')
    text = replace(text, '                activity.text[i] = remove_color_tags( view.show( u, 80 ) );\n',
        '                const std::string marked = view.show( u, 80 );\n'
        '                activity.text[i] = remove_color_tags( marked );\n'
        '                const auto styled = ds_hud::native_styled_text( marked, colors.neutral );\n'
        '                if( styled.valid && styled.text == activity.text[i] ) {\n'
        '                    colors.runs[i] = styled.runs;\n'
        '                } else {\n'
        '                    // Keep the accepted plain reading; never expose parser artifacts.\n'
        '                    colors.complete = false;\n'
        '                }\n')
    return replace(text,
        '    ds_hud::publish( u.get_stamina(), u.get_stamina_max(), health, core, activity );\n',
        '    ds_hud::publish( u.get_stamina(), u.get_stamina_max(), health, core, activity, colors );\n')


def patch_header(text: str) -> str:
    text = replace(text, '#include <string>\n', '#include <string>\n#include "ds_hud_colors.h"\n')
    text = replace(text, '    activity_status activity;\n', '    activity_status activity;\n    color_status colors;\n')
    text = replace(text, 'const activity_status &activity = {} );',
                   'const activity_status &activity = {},\n              const color_status &colors = {} );')
    return replace(text, 'constexpr std::size_t activity_field_count = 29;',
        'constexpr std::size_t activity_field_count = 29;\n'
        'static_assert( activity_field_count == color_widget_count, "Native color field mapping" );')


def patch_native(text: str) -> str:
    text = replace(text, '              const activity_status &activity )\n',
                   '              const activity_status &activity, const color_status &colors )\n')
    text = replace(text, '    mailbox.activity = mailbox.ready ? activity : activity_status{};\n',
                   '    mailbox.activity = mailbox.ready ? activity : activity_status{};\n'
                   '    mailbox.colors = mailbox.ready ? colors : color_status{};\n')
    text = replace(text, '// Object[] { long[53], byte[30][] }, all from one locked mailbox copy.',
                   '// Object[] { long[53], byte[30][], long[] DSC1 colors }, ONE locked copy.')
    text = replace(text, 'env->NewObjectArray( 2, object_class, nullptr )',
                   'env->NewObjectArray( 3, object_class, nullptr )')
    return replace(text, '        return result;\n    } catch( ... )',
        '        const auto packed_colors = ds_hud::pack_colors( state.colors, state.sequence );\n'
        '        if( packed_colors.size() > static_cast<std::size_t>( std::numeric_limits<jsize>::max() ) ) {\n'
        '            return nullptr;\n'
        '        }\n'
        '        std::vector<jlong> color_values( packed_colors.begin(), packed_colors.end() );\n'
        '        const jsize color_count = static_cast<jsize>( color_values.size() );\n'
        '        jlongArray appearance = env->NewLongArray( color_count );\n'
        '        if( appearance == nullptr ) {\n'
        '            return nullptr;\n'
        '        }\n'
        '        env->SetLongArrayRegion( appearance, 0, color_count, color_values.data() );\n'
        '        if( env->ExceptionCheck() ) {\n'
        '            return nullptr;\n'
        '        }\n'
        '        env->SetObjectArrayElement( result, 2, appearance );\n'
        '        env->DeleteLocalRef( appearance );\n'
        '        if( env->ExceptionCheck() ) {\n'
        '            return nullptr;\n'
        '        }\n'
        '        return result;\n    } catch( ... )')


def patch_ui(text: str) -> str:
    text = replace(text, '// One coherent copy: Object[] { long[53], byte[30][] UTF-8 movement/status text }.',
                   '// One coherent copy: original values/text plus long[] DSC1 native colors.')
    text = replace(text, '"CDDA-DS / HUD POLISH"', '"CDDA-DS / NATIVE COLORS"')
    text = replace(text, '        private final ProgressBar[] healthBars = new ProgressBar[6];',
                   '        private final ProgressBar[] healthBars = new ProgressBar[6];\n'
                   '        private final TextView[] bodyLabels = new TextView[6];')
    text = replace(text, '            TextView[] bodyLabels = new TextView[labels.length];\n', '')
    text = replace(text,
        '            full(details, widget(17)); // Body comfort, NOT environmental Temperature.\n'
        '            full(details, widget(18)); // Comfort trend.\n',
        '            pair(details, widget(17), widget(18), padding,\n'
        '                "Body comfort: Comfortable", "Comfort trend: (Falling!!)");\n')
    text = replace(text, '            bar.setProgress(0);\n',
                   '            bar.setProgress(0);\n'
                   '            NativeHudColors.reset(bodyLabels, healthBars, bar, value);\n')
    text = replace(text, 'ActivityHudSnapshot.decode(raw);', 'ActivityHudSnapshot.decode(NativeHudColors.values(raw));')
    text = replace(text, '            body.setVisibility(View.VISIBLE);\n',
                   '            NativeHudColors colors = NativeHudColors.decode(raw, activity);\n'
                   '            body.setVisibility(View.VISIBLE);\n')
    text = replace(text, '                if (activityValues[i] != null) activityValues[i].setText(activity.label(i));',
                   '                if (activityValues[i] != null) colors.widget(activityValues[i], activity, i);')
    text = replace(text,
        '                    ? (int) Math.max(0, Math.min(1000, 1000.0 * current / maximum)) : 0);\n',
        '                    ? (int) Math.max(0, Math.min(1000, 1000.0 * current / maximum)) : 0);\n'
        '                colors.bar(healthBars[i], i + 1, maximum > 0 && current == 0);\n'
        '                colors.bodyLabel(bodyLabels[i], i);\n')
    text = replace(text, '                coreValues[i].setText(state.coreLabel(i));',
                   '                String label = state.coreLabel(i);\n'
                   '                colors.scalar(coreValues[i], label, label.indexOf(": ") + 2, 13 + i);')
    text = replace(text, '            movement.setText("Movement mode: " + state.movementMode);',
                   '            colors.scalar(movement, "Movement mode: " + state.movementMode, 15, 19);')
    text = replace(text, '            value.setText(String.format(Locale.ROOT, "Stamina: %.1f%%", percent));',
                   '            colors.scalar(value, String.format(Locale.ROOT, "Stamina: %.1f%%", percent), 9, 0);')
    text = replace(text, '            bar.setProgress((int) Math.max(0, Math.min(1000, percent * 10)));',
                   '            bar.setProgress((int) Math.max(0, Math.min(1000, percent * 10)));\n'
                   '            colors.bar(bar, 0, state.current == 0);')
    return replace(text, 'state.sequence, state.ageMs / 1000.0) + "\\nFont: " + hudFont.description);',
                   'state.sequence, state.ageMs / 1000.0) + "\\nFont: " + hudFont.description\n'
                   '                + colors.diagnostic());')


PATCHERS = {'src/game.cpp': patch_game, 'src/ds_hud.h': patch_header,
            'src/ds_hud.cpp': patch_native, UI: patch_ui}


def apply(root: Path, output: Path) -> dict:
    root = root.resolve()
    before = {}
    for path, expected in PARENT_SHA256.items():
        data = safe_target(root, path).read_bytes()
        if sha(data) != expected:
            raise ValueError('Native colors requires exact build-16 input: ' + path)
        before[path] = data.decode('utf-8')
    for path, expected in DEPENDENCY_BLOBS.items():
        if blob(safe_target(root, path).read_bytes()) != expected:
            raise ValueError('Native color definition changed: ' + path)
    pending = {p: (before[p], function(before[p])) for p, function in PATCHERS.items()}
    for name, destination in TEMPLATES.items():
        target = safe_target(root, destination)
        if target.exists():
            raise ValueError('Native color destination already exists: ' + destination)
        data = safe_target(HERE / 'native-colors', name).read_bytes()
        if blob(data) != TEMPLATE_BLOBS[name]:
            raise ValueError('Native color template changed: ' + name)
        pending[destination] = ('', data.decode('utf-8'))
    # Everything is validated and rendered before the first production-source write.
    diff = ''.join(''.join(difflib.unified_diff(
        a.splitlines(keepends=True), b.splitlines(keepends=True),
        fromfile='a/' + p if a else '/dev/null', tofile='b/' + p))
        for p, (a, b) in pending.items())
    report = {
        'experiment': 'native_colors', 'base_experiment': 'hud_polish',
        'game_actions': False, 'original_sidebar_retained': True,
        'color_source': 'native widgets, native tag parser, live colorpairs/windowsPalette',
        'comfort_pair': ['Body comfort', 'Comfort trend'],
        'wire_extension': 'Object[2] long[] DSC1/v1; original long[53]/byte[30][] unchanged',
        'color_scalar_count': 20, 'color_widget_slots': 29, 'displayed_widget_count': 20,
        'zero_bar_policy': 'At exact zero only, tint empty track with native graph color; no fake fill.',
        'blank_policy': 'Accepted dash/Unavailable text stays neutral; no invented severity.',
        'deferred': ['body-label spacing', 'Oxygen final placement', 'diagnostic cleanup', 'variable anatomy'],
        'overlay_order': ['BODY-DETAILS.patch', 'HUD-PRESENTATION.patch', 'NEEDS-STATUS.patch',
                          'HUD-LAYOUT.patch', 'HUD-REFINEMENT.patch', 'HUD-POLISH.patch', 'NATIVE-COLORS.patch'],
        'input_sha256': PARENT_SHA256, 'definition_git_blobs': DEPENDENCY_BLOBS,
        'template_git_blobs': TEMPLATE_BLOBS,
        'patch_file': 'NATIVE-COLORS.patch',
        'paths': {p: sha(b.encode('utf-8')) for p, (_, b) in pending.items()},
    }
    for p, (_, text) in pending.items():
        destination = root / p; destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding='utf-8')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'NATIVE-COLORS.patch').write_text(diff, encoding='utf-8')
    (output / 'NATIVE-COLORS.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(apply(args.root, args.output), indent=2))


if __name__ == '__main__':
    main()
