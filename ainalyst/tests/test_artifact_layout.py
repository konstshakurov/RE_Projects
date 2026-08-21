"""
tests/test_artifact_layout.py — раскладка артефактов по проектам эпика RE_Projects (KON-12).

Покрывает:
  - безопасную нормализацию project_id (защита от path traversal);
  - резолвер пути data_path (projects/<project_id>/output/data/<filename>);
  - save_artifact с project_id (markdown в projects/<project_id>/output/reports/);
  - save_artifact без project_id (общий FALLBACK_REPORTS_DIR).
"""

import os
import importlib
import shutil
import tempfile
import unittest

import tests.conftest  # noqa: F401  — применяет моки sys.modules до импорта проекта
import skills.common as common


class TestNormalizeProjectId(unittest.TestCase):
    def test_basic_lower_and_spaces(self):
        self.assertEqual(common.normalize_project_id("  CRM Up "), "crm_up")

    def test_traversal_is_neutralized(self):
        for evil in ["../../etc", "..", "a/b\\c", "/abs/path", "..\\..\\x"]:
            out = common.normalize_project_id(evil)
            self.assertNotIn("/", out)
            self.assertNotIn("\\", out)
            self.assertNotIn("..", out)
            joined = os.path.realpath(common.data_dir_for(evil))
            base = os.path.realpath(common.PROJECTS_DIR)
            self.assertTrue(joined.startswith(base))

    def test_empty_becomes_unknown(self):
        self.assertEqual(common.normalize_project_id(""), "_unknown")
        self.assertEqual(common.normalize_project_id(".."), "_unknown")


class TestDataPath(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._cwd = os.getcwd()
        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_data_path_is_project_scoped(self):
        p = common.data_path("crm", "crm_traceability_repo.json")
        self.assertEqual(
            os.path.normpath(p),
            os.path.normpath("projects/crm/output/data/crm_traceability_repo.json"),
        )

    def test_specs_dir_is_project_scoped(self):
        d = common.specs_dir("Demo V2")
        self.assertEqual(
            os.path.normpath(d),
            os.path.normpath("projects/demo_v2/output/specs"),
        )

    def test_dir_helpers(self):
        self.assertEqual(
            os.path.normpath(common.data_dir_for("crm")),
            os.path.normpath("projects/crm/output/data"),
        )
        self.assertEqual(
            os.path.normpath(common.report_dir_for("crm")),
            os.path.normpath("projects/crm/output/reports"),
        )


class TestSaveArtifact(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._cwd = os.getcwd()
        os.chdir(self.tmp)
        # conftest замокал common.save_artifact — восстановим реальную через reload
        importlib.reload(common)

    def tearDown(self):
        os.chdir(self._cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)
        importlib.reload(common)  # вернуть состояние модуля (моки conftest)

    def test_with_project_id_nests_under_projects(self):
        common.save_artifact("# hi", "6_1_current_state_crm", project_id="crm")
        files = []
        for root, _dirs, fs in os.walk("projects/crm/output/reports"):
            for f in fs:
                files.append(os.path.join(root, f))
        self.assertEqual(len(files), 1)

    def test_without_project_id_uses_fallback_dir(self):
        common.save_artifact("# hi", "confluence_pull")
        flat = [f for f in os.listdir(common.FALLBACK_REPORTS_DIR) if f.endswith(".md")]
        self.assertEqual(len(flat), 1)
