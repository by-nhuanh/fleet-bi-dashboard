"""Automated acceptance checks for Fleet BI Overview (real DDS data only)."""
from pathlib import Path
import unittest
import duckdb

DB = Path(__file__).resolve().parents[1] / "database" / "fleet_dw.duckdb"


class OverviewAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DB.is_file():
            raise FileNotFoundError(f"Missing deployment database: {DB}")
        cls.con = duckdb.connect(str(DB), read_only=True)

    @classmethod
    def tearDownClass(cls):
        cls.con.close()

    def test_reference_kpis(self):
        totals = self.con.execute("""
            SELECT COUNT(*),
                   COUNT(*) FILTER (WHERE is_kpi_eligible = 1),
                   COUNT(*) FILTER (WHERE is_kpi_eligible = 1 AND delay_minutes > 0)
            FROM dds.Fact_Trips
        """).fetchone()
        self.assertEqual(totals, (85410, 77959, 51970))
        fuel = self.con.execute(
            "SELECT SUM(total_cost_usd) FROM dds.Fact_Fuel_Purchases"
        ).fetchone()[0]
        self.assertAlmostEqual(float(fuel), 95592992.04, places=2)

    def test_trip_grain_is_unique(self):
        n, distinct_n = self.con.execute("""
            SELECT COUNT(*), COUNT(DISTINCT trip_id)
            FROM dds.Fact_Trips
        """).fetchone()
        self.assertEqual(n, distinct_n)

    def test_fact_dimension_relationships(self):
        checks = {
            "start_date_key": ("Dim_Date", "date_key"),
            "vehicle_key": ("Dim_Vehicle", "vehicle_key"),
            "origin_location_key": ("Dim_Location", "location_key"),
            "dest_location_key": ("Dim_Location", "location_key"),
        }
        for fact_key, (dim, dim_key) in checks.items():
            with self.subTest(foreign_key=fact_key):
                missing = self.con.execute(f"""
                    SELECT COUNT(*)
                    FROM dds.Fact_Trips t
                    LEFT JOIN dds.{dim} d ON t.{fact_key} = d.{dim_key}
                    WHERE d.{dim_key} IS NULL
                """).fetchone()[0]
                self.assertEqual(missing, 0)

    def test_dimension_keys_are_unique(self):
        for dim, key in [
            ("Dim_Date", "date_key"),
            ("Dim_Vehicle", "vehicle_key"),
            ("Dim_Location", "location_key"),
        ]:
            with self.subTest(dimension=dim):
                total, distinct_n = self.con.execute(f"""
                    SELECT COUNT(*), COUNT(DISTINCT {key}) FROM dds.{dim}
                """).fetchone()
                self.assertEqual(total, distinct_n)

    def test_fuel_links_to_trips(self):
        unlinked = self.con.execute("""
            SELECT COUNT(*)
            FROM dds.Fact_Fuel_Purchases f
            LEFT JOIN dds.Fact_Trips t ON f.trip_id = t.trip_id
            WHERE t.trip_id IS NULL
        """).fetchone()[0]
        self.assertEqual(unlinked, 0)

    def test_overview_query_full_date_window(self):
        r = self.con.execute("""
            WITH filtered_trips AS (
                SELECT t.trip_id, t.is_kpi_eligible, t.delay_minutes
                FROM dds.Fact_Trips t
                JOIN dds.Dim_Date d ON t.start_date_key = d.date_key
                JOIN dds.Dim_Vehicle v ON t.vehicle_key = v.vehicle_key
                JOIN dds.Dim_Location o ON t.origin_location_key = o.location_key
                WHERE d.full_date BETWEEN DATE '2022-01-01' AND DATE '2024-12-31'
            ), fuel_by_trip AS (
                SELECT f.trip_id, SUM(f.total_cost_usd) AS fuel_cost
                FROM dds.Fact_Fuel_Purchases f
                JOIN filtered_trips t ON f.trip_id = t.trip_id
                GROUP BY f.trip_id
            )
            SELECT
                (SELECT COUNT(*) FROM filtered_trips),
                (SELECT COUNT(*) FROM filtered_trips WHERE is_kpi_eligible=1),
                (SELECT COUNT(*) FROM filtered_trips
                 WHERE is_kpi_eligible=1 AND delay_minutes>0),
                (SELECT SUM(fuel_cost) FROM fuel_by_trip)
        """).fetchone()
        self.assertEqual(r[:3], (85410, 77959, 51970))
        self.assertAlmostEqual(float(r[3]), 95592992.04, places=2)

    def test_monthly_aggregation_reconciles(self):
        monthly = self.con.execute("""
            WITH trip_months AS (
                SELECT t.trip_id, d.year, d.month, t.is_kpi_eligible,
                       t.delay_minutes
                FROM dds.Fact_Trips t
                JOIN dds.Dim_Date d ON t.start_date_key=d.date_key
            ), fuel_by_trip AS (
                SELECT trip_id, SUM(total_cost_usd) AS fuel
                FROM dds.Fact_Fuel_Purchases GROUP BY trip_id
            ), monthly AS (
                SELECT t.year, t.month, COUNT(*) AS trips,
                    COUNT(*) FILTER (WHERE t.is_kpi_eligible=1) AS eligible,
                    COUNT(*) FILTER (WHERE t.is_kpi_eligible=1
                         AND t.delay_minutes>0) AS late,
                    SUM(COALESCE(f.fuel,0)) AS fuel
                FROM trip_months t
                LEFT JOIN fuel_by_trip f ON t.trip_id=f.trip_id
                GROUP BY t.year,t.month
            )
            SELECT COUNT(*), SUM(trips), SUM(eligible), SUM(late), SUM(fuel)
            FROM monthly
        """).fetchone()
        self.assertEqual(monthly[:4], (36, 85410, 77959, 51970))
        self.assertAlmostEqual(float(monthly[4]), 95592992.04, places=2)


if __name__ == "__main__":
    unittest.main()
