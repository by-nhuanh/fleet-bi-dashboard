"""Streamlit runtime smoke tests for all three Fleet BI pages.

These tests exercise the real bundled DDS databases and catch query/runtime
exceptions which compilation alone will not detect.
"""
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]

class DashboardPageSmokeTests(unittest.TestCase):
    def check_page(self,path):
        test=AppTest.from_file(str(ROOT/path),default_timeout=120).run()
        errors=[str(e.message) for e in test.exception]
        self.assertFalse(errors, f"{path}: {errors}")
        self.assertGreater(len(test.markdown)+len(test.metric)+len(test.title),0)

    def test_overview_loads(self):
        self.check_page(Path("app.py"))

    def test_routes_load(self):
        self.check_page(Path("pages/2_Route_GIS.py"))

    def test_fuel_load(self):
        self.check_page(Path("pages/3_Fuel_Analytics.py"))

if __name__=="__main__":
    unittest.main()
