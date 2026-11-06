import unittest
import pandas as pd

from company_analyzer import convert_cumulative_to_quarterly


class TestQuarterlyConversion(unittest.TestCase):

    def make_data(self):
        return pd.DataFrame({
            "REPORT_DATE": pd.to_datetime([
                "2025-03-31",
                "2025-06-30",
                "2025-09-30",
                "2025-12-31",
                "2026-03-31",
                "2026-06-30",
                "2026-09-30",
            ]),
            "OPERATE_INCOME": [
                100, 250, 400, 600,
                120, 280, 450,
            ],
        })

    def test_quarterly_conversion(self):
        df = self.make_data()

        result = convert_cumulative_to_quarterly(
            df,
            ["OPERATE_INCOME"],
        )

        values = result.set_index("REPORT_DATE")[
            "OPERATE_INCOME_QUARTER"
        ]

        expected = {
            "2025-03-31": 100,
            "2025-06-30": 150,
            "2025-09-30": 150,
            "2025-12-31": 200,
            "2026-03-31": 120,
            "2026-06-30": 160,
            "2026-09-30": 170,
        }

        for date, value in expected.items():
            self.assertAlmostEqual(
                values.loc[pd.Timestamp(date)],
                value,
            )

    def test_original_data_unchanged(self):
        df = self.make_data()
        original = df.copy()

        result = convert_cumulative_to_quarterly(
            df,
            ["OPERATE_INCOME"],
        )

        pd.testing.assert_frame_equal(df, original)

        self.assertIn(
            "OPERATE_INCOME",
            result.columns,
        )

    def test_missing_previous_period(self):
        df = pd.DataFrame({
            "REPORT_DATE": pd.to_datetime([
                "2026-03-31",
                "2026-09-30",
            ]),
            "OPERATE_INCOME": [100, 300],
        })

        result = convert_cumulative_to_quarterly(
            df,
            ["OPERATE_INCOME"],
        )

        values = result.set_index("REPORT_DATE")[
            "OPERATE_INCOME_QUARTER"
        ]

        self.assertEqual(
            values.loc[pd.Timestamp("2026-03-31")],
            100,
        )

        self.assertTrue(
            pd.isna(
                values.loc[pd.Timestamp("2026-09-30")]
            )
        )

    def test_missing_value(self):
        df = pd.DataFrame({
            "REPORT_DATE": pd.to_datetime([
                "2026-03-31",
                "2026-06-30",
            ]),
            "OPERATE_INCOME": [100, None],
        })

        result = convert_cumulative_to_quarterly(
            df,
            ["OPERATE_INCOME"],
        )

        values = result.set_index("REPORT_DATE")[
            "OPERATE_INCOME_QUARTER"
        ]

        self.assertTrue(
            pd.isna(
                values.loc[pd.Timestamp("2026-06-30")]
            )
        )

    def test_duplicate_dates(self):
        df = pd.DataFrame({
            "REPORT_DATE": pd.to_datetime([
                "2026-03-31",
                "2026-03-31",
            ]),
            "OPERATE_INCOME": [100, 120],
        })

        with self.assertRaises(ValueError):
            convert_cumulative_to_quarterly(
                df,
                ["OPERATE_INCOME"],
            )

    def test_missing_columns(self):
        df = pd.DataFrame({
            "REPORT_DATE": pd.to_datetime([
                "2026-03-31",
            ]),
        })

        with self.assertRaises(ValueError):
            convert_cumulative_to_quarterly(
                df,
                ["OPERATE_INCOME"],
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)