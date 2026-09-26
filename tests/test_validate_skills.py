import tempfile
import unittest
from pathlib import Path


from scripts.validate_skills import validate


class SkillFormatTests(unittest.TestCase):
    def test_official_compatibility_field_is_accepted(self):
        with tempfile.TemporaryDirectory(prefix="bioagent-skill-format-") as temp_root:
            folder = Path(temp_root) / "example-skill"
            folder.mkdir()
            skill = folder / "SKILL.md"
            skill.write_text(
                "---\nname: example-skill\ndescription: Example capability. Use for test requests.\n"
                "license: MIT\ncompatibility: Requires a terminal.\n---\n\nDo the task.\n",
                encoding="utf-8",
            )
            validate(skill)

    def test_oversized_compatibility_field_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="bioagent-skill-format-") as temp_root:
            folder = Path(temp_root) / "example-skill"
            folder.mkdir()
            skill = folder / "SKILL.md"
            skill.write_text(
                "---\nname: example-skill\ndescription: Example capability. Use for test requests.\n"
                "license: MIT\ncompatibility: " + "x" * 501 + "\n---\n\nDo the task.\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                validate(skill)


if __name__ == "__main__":
    unittest.main()
