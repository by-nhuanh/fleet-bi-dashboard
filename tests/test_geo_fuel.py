"""Acceptance tests for Task 11–12 analysis database sourced from DDS."""
from pathlib import Path
import unittest
import duckdb

DB=Path(__file__).resolve().parents[1]/"database"/"fleet_analysis.duckdb"

class GeoFuelAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DB.is_file():
            raise FileNotFoundError(f"Missing required GPS database: {DB}")
        cls.con=duckdb.connect(str(DB),read_only=True)
    @classmethod
    def tearDownClass(cls):
        cls.con.close()

    def test_gps_counts(self):
        count,trips=self.con.execute("""
            SELECT COUNT(*),COUNT(DISTINCT trip_id) FROM dds.Fact_GPS_Points
        """).fetchone()
        self.assertEqual((count,trips),(1435571,746))

    def test_route_dimension_exists(self):
        n=self.con.execute("SELECT COUNT(*) FROM dds.Dim_Route").fetchone()[0]
        self.assertEqual(n,59)

    def test_gps_required_fields(self):
        fields={row[1] for row in self.con.execute(
            "PRAGMA table_info('dds.Fact_GPS_Points')"
        ).fetchall()}
        required={"trip_id","date_key","time_key","latitude","longitude",
                  "speed_kmh","fuel_level_pct","fuel_liters_remaining",
                  "engine_status","anomaly_type"}
        self.assertTrue(required.issubset(fields),required-fields)

    def test_recorded_gps_anomaly_counts(self):
        recorded=dict(self.con.execute("""
            SELECT anomaly_type,COUNT(*)
            FROM dds.Fact_GPS_Points
            GROUP BY anomaly_type
        """).fetchall())
        expected={
            "NORMAL": 1435491,
            "FUEL_THEFT": 15,
            "IDLE_EXTENDED": 36,
            "GPS_JUMP_RECOVERY": 16,
            "FUEL_RECEIPT_MISMATCH": 13,
        }
        self.assertEqual(recorded,expected)

    def test_linked_trip_keys(self):
        n=self.con.execute("""
            SELECT COUNT(*) FROM dds.Fact_GPS_Points g
            LEFT JOIN dds.Fact_Trips t ON g.trip_id=t.trip_id
            WHERE t.trip_id IS NULL
        """).fetchone()[0]
        self.assertEqual(n,0)

    def test_time_dimension_link(self):
        n=self.con.execute("""
            SELECT COUNT(*) FROM dds.Fact_GPS_Points g
            LEFT JOIN dds.Dim_Time d ON g.time_key=d.time_key
            WHERE d.time_key IS NULL
        """).fetchone()[0]
        self.assertEqual(n,0)

if __name__=="__main__":
    unittest.main()
