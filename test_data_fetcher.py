import pandas as pd
import pytest

import data_fetcher


def test_fetch_stock_info_success(monkeypatch):
    """正常获取并整理企业基本信息。"""

    fake_data = pd.DataFrame({
        "item": [
            "股票代码",
            "股票简称",
            "行业",
            "最新",
            "总股本",
            "流通股",
            "总市值",
            "流通市值",
            "上市时间",
        ],
        "value": [
            "600519",
            "贵州茅台",
            "白酒Ⅱ",
            1453.0,
            1250081601.0,
            1250081601.0,
            1816368566253.0,
            1816368566253.0,
            "20010827",
        ],
    })

    monkeypatch.setattr(
        data_fetcher.ak,
        "stock_individual_info_em",
        lambda symbol: fake_data,
    )

    result = data_fetcher.fetch_stock_info("600519")

    assert result["symbol"] == "600519"
    assert result["name"] == "贵州茅台"
    assert result["industry"] == "白酒Ⅱ"
    assert result["latest_price"] == 1453.0
    assert result["market_cap"] == 1816368566253.0
    assert result["listing_date"] == "2001-08-27"


def test_fetch_stock_info_invalid_symbol():
    """非法股票代码应被拒绝。"""

    with pytest.raises(ValueError):
        data_fetcher.fetch_stock_info("123")


def test_fetch_stock_info_empty_data(monkeypatch):
    """数据源返回空数据时应明确报错。"""

    monkeypatch.setattr(
        data_fetcher.ak,
        "stock_individual_info_em",
        lambda symbol: pd.DataFrame(),
    )

    with pytest.raises(ValueError, match="未获取到股票"):
        data_fetcher.fetch_stock_info("600519")


def test_fetch_stock_info_missing_columns(monkeypatch):
    """数据源缺少必要字段时应明确报错。"""

    fake_data = pd.DataFrame({
        "名称": ["贵州茅台"],
        "数值": ["600519"],
    })

    monkeypatch.setattr(
        data_fetcher.ak,
        "stock_individual_info_em",
        lambda symbol: fake_data,
    )

    with pytest.raises(ValueError, match="缺少必要字段"):
        data_fetcher.fetch_stock_info("600519")