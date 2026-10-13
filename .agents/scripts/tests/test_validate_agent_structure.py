from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


SCRIPT = Path(__file__).resolve().parents[1] / "validate_agent_structure.py"
SPEC = importlib.util.spec_from_file_location("validate_agent_structure", SCRIPT)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class ProjectLifecycleTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profile_path = self.root / ".agents/config/project-profile.yml"
        self.profile_path.parent.mkdir(parents=True)
        self.profile = {
            "project": {"lifecycle": "pre-scaffold"},
            "android": {}, "modules": {}, "validation": {}, "sourceOfTruth": {},
        }

    def validate(self, mode="auto"):
        self.profile_path.write_text(yaml.safe_dump(self.profile), encoding="utf-8")
        errors = []
        validator.validate_profile(self.root, errors, mode)
        return errors

    def test_pre_scaffold_allows_empty_current_facts(self):
        self.assertEqual([], self.validate())

    def test_pre_scaffold_checks_existing_scope_without_planned_modules(self):
        (self.root / "AGENTS.md").touch()
        self.profile["sourceOfTruth"] = {"projectScope": "AGENTS.md"}
        self.profile["planned"] = {"moduleRoles": ["crash-library"], "libraryModule": "lib_crash"}
        self.assertEqual([], self.validate())

    def test_repository_registers_crash_workflow_and_rules(self):
        root = SCRIPT.parents[2]
        errors = []
        validator.validate_required_files(root, errors)
        self.assertEqual([], errors)
        self.assertIn("crash-testing.md", validator.REQUIRED["rules"])
        self.assertIn("test-crash.md", validator.REQUIRED["workflows"])
        self.assertNotIn("nas.md", validator.REQUIRED["rules"])

    def test_forced_project_rejects_empty_facts(self):
        self.assertTrue(self.validate("project"))

    def test_partial_gradle_project_cannot_hide_behind_pre_scaffold(self):
        (self.root / "build.gradle.kts").touch()
        self.assertTrue(any("pre-scaffold" in error for error in self.validate()))

    def test_config_mode_still_checks_declared_fact_paths(self):
        self.profile["sourceOfTruth"] = {"requirements": "missing.md"}
        self.assertTrue(any("missing.md" in error for error in self.validate("config")))

    def test_initialized_project_requires_existing_modules(self):
        self.profile["project"]["lifecycle"] = "initialized"
        self.profile["android"] = {"uiToolkit": "xml"}
        self.profile["validation"] = {"debugBuild": "gradlew.bat :app:assembleDebug"}
        self.profile["modules"] = {"app": "app"}
        self.profile["sourceOfTruth"] = {
            "dependencyVersions": "gradle/libs.versions.toml",
            "gradleWrapper": "gradle/wrapper/gradle-wrapper.properties",
            "moduleGraph": "settings.gradle",
            "moduleBuildFiles": "**/build.gradle",
        }
        for raw in list(self.profile["sourceOfTruth"].values())[:-1] + ["build.gradle"]:
            path = self.root / raw
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        self.assertTrue(any("modules.app" in error for error in self.validate()))
        (self.root / "app").mkdir()
        self.assertEqual([], self.validate())

    def test_unknown_lifecycle_is_rejected(self):
        self.profile["project"]["lifecycle"] = "ready"
        self.assertTrue(any("unknown project lifecycle" in error for error in self.validate()))


if __name__ == "__main__":
    unittest.main()
