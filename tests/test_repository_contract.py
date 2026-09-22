"""Local-only checks for the public signed-update artifact repository."""

import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    def test_manifest_declares_delivery_without_an_application_component(self):
        manifest = json.loads(
            (ROOT / ".fellow/automation-components.json").read_text()
        )
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["repository"], "Fellow-legal/fellow-time-updates")
        self.assertEqual(manifest["components"], [])
        self.assertEqual(
            manifest["delivery_tracking"],
            {
                "enabled": True,
                "source": "github_pull_requests",
                "start_date": "2026-10-01",
            },
        )

    def test_pull_request_template_contains_one_delivery_record(self):
        template = (ROOT / ".github/pull_request_template.md").read_text()
        self.assertEqual(template.count("## Fellow delivery"), 1)
        match = re.search(r"## Fellow delivery\s+```json\s+(.*?)\s+```", template, re.S)
        self.assertIsNotNone(match)
        records = json.loads(match.group(1))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["component_keys"], [])

    def test_impact_map_covers_every_owned_contract_path(self):
        impact_map = json.loads((ROOT / "impact-map.json").read_text())
        self.assertEqual(impact_map["version"], 2)
        self.assertEqual(impact_map["service"], "fellow-time-updates")
        paths = set(impact_map["rules"][0]["paths"])
        self.assertTrue(
            {
                ".fellow/automation-components.json",
                ".github/pull_request_template.md",
                ".gitignore",
                "appcast.xml",
                "impact-map.json",
                "scenario-contract.json",
                "test-env.json",
                "tests/test_repository_contract.py",
            }.issubset(paths)
        )

    def test_appcast_is_valid_xml_with_signed_release_enclosures(self):
        root = ET.parse(ROOT / "appcast.xml").getroot()
        items = root.findall("./channel/item")
        self.assertTrue(items)
        signature_key = "{http://www.andymatuschak.org/xml-namespaces/sparkle}edSignature"
        for item in items:
            enclosure = item.find("enclosure")
            self.assertIsNotNone(enclosure)
            self.assertTrue(enclosure.get("url", "").startswith("https://"))
            self.assertTrue(enclosure.get(signature_key))


if __name__ == "__main__":
    unittest.main()
