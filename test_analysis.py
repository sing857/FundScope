import unittest
import numpy as np
import pandas as pd

from analyzer import calculate_metrics


class TestFundMetrics(unittest.TestCase):

    def make_nav(self, values, start="2026-01-01"):
        dates = pd.date_range(start, periods=len(values), freq="D")
        return pd.Series(values, index=dates, dtype=float)

    def test_total_return(self):
        nav = self.make_nav([1.0, 1.1, 1.2])
        result = calculate_metrics(nav)
        self.assertAlmostEqual(result["区间收益率"], 0.2)

    def test_max_drawdown(self):
        nav = self.make_nav([1.0, 1.2, 0.9, 1.1])
        result = calculate_metrics(nav)
        self.assertAlmostEqual(result["最大回撤"], -0.25)

    def test_invalid_nav(self):
        nav = self.make_nav([1.0, 0.0])
        with self.assertRaises(ValueError):
            calculate_metrics(nav)

    def test_missing_data(self):
        nav = pd.Series(
            [1.0, np.nan],
            index=pd.to_datetime(["2026-01-01", "2026-01-02"]),
        )
        with self.assertRaises(ValueError):
            calculate_metrics(nav)

    def test_annualized_return(self):
        dates = pd.to_datetime(["2025-01-01", "2026-01-01"])
        nav = pd.Series([1.0, 1.1], index=dates)
        result = calculate_metrics(nav)
        expected = 1.1 ** (365.25 / 365) - 1
        self.assertAlmostEqual(
            result["年化收益率"], expected, places=6
        )

    def test_duplicate_dates(self):
        dates = pd.to_datetime(["2026-01-01", "2026-01-01"])
        nav = pd.Series([1.0, 1.1], index=dates)
        with self.assertRaises(ValueError):
            calculate_metrics(nav)

    def test_zero_volatility(self):
        nav = self.make_nav([1.0, 1.0, 1.0, 1.0])
        result = calculate_metrics(nav)
        self.assertAlmostEqual(result["区间收益率"], 0.0)
        self.assertTrue(np.isnan(result["夏普比率"]))

    def test_downside_volatility(self):
        nav = self.make_nav([1.0, 1.1, 1.0, 1.1])
        result = calculate_metrics(nav)

        returns = nav.pct_change().dropna().to_numpy()
        daily_rf = (1.02 ** (1 / 252)) - 1
        downside = np.minimum(returns - daily_rf, 0)
        expected = np.sqrt(np.mean(downside ** 2)) * np.sqrt(252)

        self.assertAlmostEqual(
            result["下行波动率"], expected, places=8
        )

    def test_calmar_ratio(self):
        nav = self.make_nav([1.0, 1.2, 0.9, 1.1])
        result = calculate_metrics(nav)

        expected = result["年化收益率"] / abs(result["最大回撤"])
        self.assertAlmostEqual(
            result["卡玛比率"], expected, places=8
        )

    def test_drawdown_recovery(self):
        nav = self.make_nav([1.0, 1.2, 0.9, 1.0, 1.2])
        result = calculate_metrics(nav)

        self.assertTrue(result["回撤是否恢复"])
        self.assertEqual(result["回撤峰值日期"], "2026-01-02")
        self.assertEqual(result["回撤谷底日期"], "2026-01-03")
        self.assertEqual(result["回撤恢复日期"], "2026-01-05")
        self.assertEqual(result["峰值至恢复天数"], 3)

    def test_drawdown_not_recovered(self):
        nav = self.make_nav([1.0, 1.2, 0.9, 1.0])
        result = calculate_metrics(nav)

        self.assertFalse(result["回撤是否恢复"])
        self.assertIsNone(result["回撤恢复日期"])
        self.assertIsNone(result["峰值至恢复天数"])

    def test_data_quality_counts(self):
        dates = pd.date_range("2026-01-01", periods=4, freq="D")
        nav = pd.Series([1.0, np.nan, 1.1, 1.2], index=dates)

        result = calculate_metrics(nav)

        self.assertEqual(result["原始记录数"], 4)
        self.assertEqual(result["有效净值记录数"], 3)
        self.assertEqual(result["无效记录数"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)