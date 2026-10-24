import unittest
import numpy as np
import pandas as pd

from analyzer import calculate_metrics


class TestFundMetrics(unittest.TestCase):

    def test_total_return(self):
        nav = pd.Series(
            [1.0, 1.1, 1.2],
            index=pd.to_datetime(
                ["2026-01-01", "2026-01-02", "2026-01-03"]
            ),
        )
        result = calculate_metrics(nav)
        self.assertAlmostEqual(result["区间收益率"], 0.2)

    def test_max_drawdown(self):
        nav = pd.Series(
            [1.0, 1.2, 0.9, 1.1],
            index=pd.to_datetime(
                ["2026-01-01", "2026-01-02",
                 "2026-01-03", "2026-01-04"]
            ),
        )
        result = calculate_metrics(nav)
        self.assertAlmostEqual(result["最大回撤"], -0.25)

    def test_invalid_nav(self):
        nav = pd.Series(
            [1.0, 0.0],
            index=pd.to_datetime(["2026-01-01", "2026-01-02"]),
        )
        with self.assertRaises(ValueError):
            calculate_metrics(nav)

    def test_missing_data(self):
        nav = pd.Series([1.0, np.nan])
        with self.assertRaises(ValueError):
            calculate_metrics(nav)

    def test_annualized_return(self):
        dates = pd.to_datetime(["2025-01-01", "2026-01-01"])
        nav = pd.Series([1.0, 1.1], index=dates)
        result = calculate_metrics(nav)
        expected = 1.1 ** (365 / 365.25) - 1
        self.assertAlmostEqual(
            result["年化收益率"],
            expected,
            places=3,
        )

    def test_duplicate_dates(self):
        dates = pd.to_datetime(["2026-01-01", "2026-01-01"])
        nav = pd.Series([1.0, 1.1], index=dates)
        with self.assertRaises(ValueError):
            calculate_metrics(nav)

    def test_zero_volatility(self):
        dates = pd.date_range("2026-01-01", periods=4, freq="D")
        nav = pd.Series([1.0, 1.0, 1.0, 1.0], index=dates)
        result = calculate_metrics(nav)
        self.assertAlmostEqual(result["区间收益率"], 0.0)
        self.assertTrue(np.isnan(result["夏普比率"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)