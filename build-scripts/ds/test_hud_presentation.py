"""Presentation-only tests. Host Android substitutes do not prove device rendering."""
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
from zipfile import ZipFile

import apply_hud_presentation as presentation

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FIXTURE = HERE / "hud-presentation"


def run(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True, timeout=45)
    if result.returncode:
        raise AssertionError(f"Command failed: {command[0]}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def parent_sources() -> dict[str, str]:
    # Local validation can use the exact generated sources in the reviewed build-11
    # artifact. CI (without this variable) uses the real body_details generator.
    fixture = os.environ.get("DS_PRESENTATION_PARENT_FIXTURE")
    if fixture:
        root = Path(fixture)
        result = {str(p.relative_to(root)): p.read_text(encoding="utf-8")
                  for p in root.rglob("*") if p.is_file()}
    else:
        import apply_body_details
        result = apply_body_details.render_templates()
    digest = hashlib.sha256(result[presentation.JAVA].encode("utf-8")).hexdigest()
    if digest != presentation.PARENT_UI_SHA256:
        raise AssertionError("Parent fixture/generator does not match accepted build-11 UI")
    return result


class HudPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = parent_sources()
        cls.host_tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.host_tmp.cleanup)
        cls.host_root = Path(cls.host_tmp.name)
        specification = importlib.util.spec_from_file_location("android_fixture", FIXTURE / "android_fixture.py")
        fixture = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(fixture)
        sources = fixture.write_stubs(cls.host_root / "src")
        package = cls.host_root / "src/com/cleverraven/cataclysmdda"
        package.mkdir(parents=True)
        for name in ("DualScreenHud.java", "CoreHudSnapshot.java", "ActivityHudSnapshot.java"):
            text = cls.parent[presentation.JAVA_DIR + name]
            if name == "DualScreenHud.java":
                text = presentation.patch_ui(text)
            path = package / name
            path.write_text(text, encoding="utf-8")
            sources.append(path)
        for name in ("HudTypeface.java", "PresentationHostTest.java"):
            path = package / name
            shutil.copyfile(FIXTURE / name, path)
            sources.append(path)
        cls.classes = cls.host_root / "classes"
        cls.classes.mkdir()
        compiler = shutil.which("javac")
        if not compiler or not shutil.which("java"):
            raise AssertionError("Java is required for the presentation host tests")
        run([compiler, "--release", "8", "-encoding", "UTF-8", "-Xlint:all,-options", "-Werror",
             "-d", str(cls.classes), *map(str, sources)])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name, text in self.parent.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        for name in presentation.FONT_BLOBS:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, path)

    def unchanged(self):
        self.assertEqual((self.root / presentation.JAVA).read_text(), self.parent[presentation.JAVA])
        self.assertFalse((self.root / presentation.HELPER).exists())

    def apply(self):
        return presentation.apply(self.root, self.root / "dist")

    def test_overlay_two_paths_and_provenance(self):
        report = self.apply()
        self.assertEqual(report["experiment"], "hud_presentation")
        self.assertTrue(report["presentation_only"])
        self.assertFalse(report["game_actions"])
        self.assertTrue(report["original_sidebar_retained"])
        self.assertEqual(set(report["paths"]), {presentation.JAVA, presentation.HELPER})
        self.assertEqual(report["background"], "#000000")
        for path, digest in report["paths"].items():
            self.assertEqual(hashlib.sha256((self.root/path).read_bytes()).hexdigest(), digest)
        self.assertEqual(json.loads((self.root/"dist/HUD-PRESENTATION.json").read_text()), report)

    def test_native_data_decoders_and_parent_unchanged(self):
        before = dict(self.parent)
        self.apply()
        for path, text in before.items():
            if path != presentation.JAVA:
                self.assertEqual((self.root/path).read_text(), text)
        self.assertEqual(parent_sources(), before)

    def test_asset_bytes_and_font_defaults_unchanged(self):
        self.apply()
        for name, expected in presentation.FONT_BLOBS.items():
            self.assertEqual(presentation.blob_sha((self.root/name).read_bytes()), expected)
        config = json.loads((self.root/"data/fontdata.json").read_text())
        self.assertEqual(config["typeface"][0]["path"], "data/font/Terminus.ttf")
        self.assertEqual(config["typeface"][1], "data/font/unifont.ttf")

    def test_bad_ui_hash_before_writes(self):
        path = self.root/presentation.JAVA
        path.write_text("unexpected")
        with self.assertRaises(ValueError): self.apply()
        self.assertEqual(path.read_text(), "unexpected")
        self.assertFalse((self.root/presentation.HELPER).exists())

    def test_missing_font_before_writes(self):
        (self.root/"data/font/Terminus.ttf").unlink()
        with self.assertRaises(FileNotFoundError): self.apply()
        self.unchanged()

    def test_changed_font_before_writes(self):
        (self.root/"data/font/unifont.ttf").write_bytes(b"changed")
        with self.assertRaises(ValueError): self.apply()
        self.unchanged()

    def test_changed_font_config_before_writes(self):
        (self.root/"data/fontdata.json").write_text("{}")
        with self.assertRaises(ValueError): self.apply()
        self.unchanged()

    def test_existing_helper_before_writes(self):
        (self.root/presentation.HELPER).write_text("keep")
        with self.assertRaises(ValueError): self.apply()
        self.assertEqual((self.root/presentation.HELPER).read_text(), "keep")
        self.assertEqual((self.root/presentation.JAVA).read_text(), self.parent[presentation.JAVA])

    def test_helper_template_hash_guard(self):
        template = self.root/"bad-helper.java"; template.write_text("changed")
        with self.assertRaises(ValueError):
            presentation.apply(self.root,self.root/"dist",template)
        self.unchanged()

    def test_missing_helper_template(self):
        with self.assertRaises(FileNotFoundError):
            presentation.apply(self.root,self.root/"dist",self.root/"missing.java")
        self.unchanged()

    def test_source_symlink_rejected(self):
        path=self.root/presentation.JAVA
        original=self.root/"original.java"; path.rename(original); path.symlink_to(original)
        with self.assertRaises(ValueError): self.apply()
        self.unchanged()

    def test_destination_symlink_rejected(self):
        (self.root/presentation.HELPER).symlink_to(self.root/"missing.java")
        with self.assertRaises(ValueError): self.apply()
        self.unchanged()

    def test_parent_path_escape_rejected(self):
        (self.root/"escape").symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaises(ValueError): presentation.safe_target(self.root,"escape/file")
        self.unchanged()

    def test_font_symlink_rejected(self):
        path=self.root/"data/font/Terminus.ttf"
        original=self.root/"original-font"; path.rename(original); path.symlink_to(original)
        with self.assertRaises(ValueError): self.apply()
        self.unchanged()

    def test_duplicate_anchor_rejected(self):
        text=self.parent[presentation.JAVA]+"\n        private TextView value;\n"
        with self.assertRaises(ValueError): presentation.patch_ui(text)
        self.unchanged()

    def test_repeated_overlay_rejected(self):
        self.apply()
        prior=(self.root/presentation.JAVA).read_bytes()
        with self.assertRaises(ValueError): self.apply()
        self.assertEqual((self.root/presentation.JAVA).read_bytes(),prior)

    def test_only_shared_typeface_assignment_remains(self):
        text=presentation.patch_ui(self.parent[presentation.JAVA])
        self.assertEqual(text.count("setTypeface("),1)
        self.assertIn("view.setTypeface(hudFont.typeface)",text)
        self.assertNotIn("Typeface.MONOSPACE",text)
        self.assertEqual(text.count("HudTypeface.load("),1)

    def test_no_input_or_polling_changes(self):
        old=self.parent[presentation.JAVA]; new=presentation.patch_ui(old)
        marker="    private static final class HudPresentation"
        self.assertEqual(old.split(marker)[0].replace("import android.graphics.Typeface;",
            "import android.graphics.drawable.ColorDrawable;"),new.split(marker)[0])
        self.assertIn("handler.postDelayed(this, 250)",new)
        self.assertNotIn("dispatchKeyEvent",new)
        self.assertNotIn("TabLayout",new)

    def test_size_color_spacing_and_bars_not_redesigned(self):
        old=self.parent[presentation.JAVA]; new=presentation.patch_ui(old)
        for token in ("setTextSize(size)","setPadding(0, 8, 0, 8)","Color.WHITE",
                      "new ProgressBar(","bar.setMax(1000)","healthBars[i].setMax(1000)"):
            self.assertEqual(old.count(token),new.count(token),token)
        self.assertNotIn("setMaxLines",new)
        self.assertNotIn("setEllipsize",new)
        self.assertEqual(new.count("Color.BLACK"),3)

    def apk(self, omit: str | None = None, corrupt: str | None = None) -> Path:
        path=self.root/"test.apk"
        with ZipFile(path,"w") as z:
            for name in presentation.FONT_BLOBS:
                if name!=omit:
                    z.writestr("assets/"+name,b"changed" if name==corrupt else (self.root/name).read_bytes())
        return path

    def test_apk_asset_identity_check(self):
        output=self.root/"font-assets.json"
        report=presentation.verify_apk(self.apk(),output)
        self.assertEqual(report["asset_git_blobs"],presentation.FONT_BLOBS)
        self.assertEqual(json.loads(output.read_text()),report)

    def test_apk_missing_font_rejected(self):
        output=self.root/"font-assets.json"
        with self.assertRaises(KeyError):
            presentation.verify_apk(self.apk(omit="data/font/Terminus.ttf"),output)
        self.assertFalse(output.exists())

    def test_apk_changed_font_rejected(self):
        output=self.root/"font-assets.json"
        with self.assertRaises(ValueError):
            presentation.verify_apk(self.apk(corrupt="data/font/unifont.ttf"),output)
        self.assertFalse(output.exists())

    def host(self, mode: str):
        result=run([shutil.which("java"),"-cp",str(self.classes),
            "com.cleverraven.cataclysmdda.PresentationHostTest",mode])
        self.assertIn("presentation host substitute passed: "+mode,result)

    def test_host_normal_font_and_all_ui_states(self): self.host("normal")
    def test_host_missing_unifont_keeps_terminus(self): self.host("missing-fallback")
    def test_host_primary_failure_uses_visible_monospace_fallback(self): self.host("primary-failure")
    def test_host_modern_failure_retries_legacy(self): self.host("modern-failure")
    def test_host_builder_failure_retries_legacy(self): self.host("builder-failure")
    def test_host_legacy_api_gated(self): self.host("legacy")
    def test_host_legacy_load_failure_keeps_hud(self): self.host("legacy-failure")


if __name__=="__main__":
    unittest.main()
