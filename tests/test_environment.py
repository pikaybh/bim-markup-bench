"""Real offline environment/IFC smoke tests."""
import unittest

from tools.doctor import check_environment

class EnvironmentTests(unittest.TestCase):
    def test_environment_and_synthetic_ifc4_roundtrip(self):
        report = check_environment()
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(report["ifc4_smoke"]["status"], "PASS")
        self.assertEqual(report["paid_api_calls"], 0)

if __name__ == "__main__":
    unittest.main()
