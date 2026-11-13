#!/usr/bin/env python3
"""Apply an explicitly selected, hash-locked stamina probe in the CI workspace."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path

JAVA = "android/app/src/main/java/com/cleverraven/cataclysmdda/CataclysmDDA.java"
EXPECTED_BLOBS = {
    "src/game.cpp": "9c5ac1c44ab7079852eebdad1bb92b77c5c3d5c5",
    "src/main.cpp": "a5f96b997377eaea9b8aee2aa07e98bf45e5988e",
    JAVA: "ce06c3d4438175eabfca4043742169c25e680220",
}
TEMPLATES = {
    "ds_hud.h": "src/ds_hud.h",
    "ds_hud.cpp": "src/ds_hud.cpp",
    "DualScreenHud.java": "android/app/src/main/java/com/cleverraven/cataclysmdda/DualScreenHud.java",
}
INCLUDE = '#include "game.h"\n'
DS_INCLUDE = INCLUDE + '#if defined(__ANDROID__)\n#include "ds_hud.h"\n#endif\n'
PANEL = 'void game::draw_panels( bool force_draw )\n{\n'
SESSION = '        shared_ptr_fast<ui_adaptor> ui = g->create_or_get_main_ui_adaptor();\n'
RESUME = '    protected void onResume() {\n        super.onResume();\n'
FOCUS = '    @Override\n    public void onWindowFocusChanged(boolean hasFocus) {'


def blob_sha(content: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()


def replace_once(text: str, before: str, after: str) -> str:
    if text.count(before) != 1:
        raise ValueError(f"Expected one integration anchor: {before!r}")
    return text.replace(before, after, 1)


def patch_text(path: str, text: str) -> str:
    if path == "src/game.cpp":
        text = replace_once(text, INCLUDE, DS_INCLUDE)
        return replace_once(text, PANEL, PANEL +
            '#if defined(__ANDROID__)\n'
            '    ds_hud::publish( u.get_stamina(), u.get_stamina_max() );\n'
            '#endif\n')
    if path == "src/main.cpp":
        text = replace_once(text, INCLUDE, DS_INCLUDE)
        return replace_once(text, SESSION,
            '#if defined(__ANDROID__)\n'
            '        const ds_hud::session_scope ds_hud_session;\n'
            '#endif\n' + SESSION)
    if path == JAVA:
        text = replace_once(text, '    private NativeUI nativeUI =',
                            '    private DualScreenHud dualScreenHud;\n\n    private NativeUI nativeUI =')
        text = replace_once(text, RESUME, RESUME +
            '        if (dualScreenHud == null) dualScreenHud = new DualScreenHud(this);\n'
            '        dualScreenHud.start();\n')
        return replace_once(text, FOCUS,
            '    @Override\n'
            '    protected void onPause() {\n'
            '        if (dualScreenHud != null) dualScreenHud.stop();\n'
            '        super.onPause();\n'
            '    }\n\n'
            '    @Override\n'
            '    protected void onDestroy() {\n'
            '        if (dualScreenHud != null) dualScreenHud.stop();\n'
            '        super.onDestroy();\n'
            '    }\n\n' + FOCUS)
    raise ValueError(f"Unexpected integration target: {path}")


def apply(root: Path, output: Path) -> dict:
    root = root.resolve()
    pending: dict[str, tuple[str, str]] = {}
    # Validate every target and destination before changing any file.
    for relative, expected in EXPECTED_BLOBS.items():
        path = root / relative
        if path.is_symlink():
            raise ValueError(f"Symlink source refused: {relative}")
        data = path.read_bytes()
        if blob_sha(data) != expected:
            raise ValueError(f"Probe expects the pinned original source: {relative}")
        before = data.decode("utf-8")
        pending[relative] = (before, patch_text(relative, before))
    templates = Path(__file__).resolve().parent / "stamina-probe"
    for template, relative in TEMPLATES.items():
        if (root / relative).exists() or (root / relative).is_symlink():
            raise ValueError(f"Probe destination already exists: {relative}")
        pending[relative] = ("", (templates / template).read_text(encoding="utf-8"))
    patch = "".join("".join(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile="a/" + relative if before else "/dev/null", tofile="b/" + relative))
        for relative, (before, after) in pending.items())
    report = {
        "experiment": "stamina_probe",
        "architecture": "same APK; native copied-state mailbox; Android Presentation",
        "game_actions": False,
        "original_sidebar_retained": True,
        "patch_file": "STAMINA-PROBE.patch",
        "paths": {path: hashlib.sha256(after.encode("utf-8")).hexdigest()
                  for path, (_, after) in pending.items()},
    }
    for relative, (_, after) in pending.items():
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(after, encoding="utf-8")
    output.mkdir(parents=True, exist_ok=True)
    (output / "STAMINA-PROBE.patch").write_text(patch, encoding="utf-8")
    (output / "STAMINA-PROBE.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(apply(args.root, args.output), indent=2))


if __name__ == "__main__":
    main()
