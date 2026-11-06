import akshare as ak
import pandas as pd


def _validate_fund_code(fund_code):
    fund_code = str(fund_code).strip()
    if len(fund_code) != 6 or not fund_code.isdigit():
        raise ValueError("基金代码必须是6位数字，例如005827。")
    return fund_code


def fetch_fund_name(fund_code):
    fund_code = _validate_fund_code(fund_code)
    df = ak.fund_name_em()
    matched = df.loc[
        df["基金代码"].astype(str).str.zfill(6) == fund_code,
        "基金简称",
    ]
    if matched.empty:
        raise ValueError(f"未找到基金：{fund_code}")
    return str(matched.iloc[0])


def fetch_fund_nav(fund_code):
    fund_code = _validate_fund_code(fund_code)
    df = ak.fund_open_fund_info_em(
        symbol=fund_code,
        indicator="单位净值走势",
    )
    if df is None or df.empty:
        raise ValueError("没有获取到基金净值数据。")

    df = df.rename(columns={"净值日期": "date", "单位净值": "nav"})
    if not {"date", "nav"}.issubset(df.columns):
        raise ValueError(f"净值数据字段不完整：{list(df.columns)}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df = df.dropna(subset=["date", "nav"])
    df = df[df["nav"] > 0]
    df = df.drop_duplicates(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    if len(df) < 2:
        raise ValueError("有效净值数据不足。")
    return df


def fetch_fund_holdings(fund_code, year):
    fund_code = _validate_fund_code(fund_code)
    year = str(year).strip()
    if len(year) != 4 or not year.isdigit():
        raise ValueError("年份格式错误，例如2026。")

    df = ak.fund_portfolio_hold_em(symbol=fund_code, date=year)
    if df is None or df.empty:
        raise ValueError(f"没有获取到基金 {fund_code} 在 {year} 年的持仓。")

    cols = ["股票代码", "股票名称", "占净值比例", "季度"]
    missing = [col for col in cols if col not in df.columns]
    if missing:
        raise ValueError(f"持仓数据缺少字段：{missing}")

    df = df[cols].copy()
    df["股票代码"] = df["股票代码"].astype("string").str.strip()
    df["股票名称"] = df["股票名称"].astype("string").str.strip()
    df["占净值比例"] = pd.to_numeric(df["占净值比例"], errors="coerce")
    df["季度"] = df["季度"].astype("string").str.strip()
    df = df.dropna(subset=cols)
    df = df[
        df["股票代码"].str.len().gt(0)
        & df["股票名称"].str.len().gt(0)
        & df["季度"].str.len().gt(0)
        & df["占净值比例"].between(0, 100)
    ].reset_index(drop=True)

    if df.empty:
        raise ValueError("清洗后没有可用的持仓数据。")
    return df


def fetch_latest_fund_holdings(fund_code, year):
    df = fetch_fund_holdings(fund_code, year)
    quarter = pd.to_numeric(
        df["季度"].str.extract(r"(\d+)季度")[0],
        errors="coerce",
    )
    df = df.assign(_quarter=quarter).dropna(subset=["_quarter"])
    if df.empty:
        raise ValueError("无法识别持仓报告期。")

    latest = df[df["_quarter"] == df["_quarter"].max()]
    return latest.drop(columns="_quarter").reset_index(drop=True)


def _fetch_stock_report(symbol, report_type):
    symbol = str(symbol).strip().upper()
    if len(symbol) != 6 or not symbol.isdigit():
        raise ValueError("股票代码必须是6位数字，例如600519。")

    stock_symbol = ("SH" if symbol.startswith("6") else "SZ") + symbol
    functions = {
        "income": ak.stock_profit_sheet_by_report_em,
        "balance": ak.stock_balance_sheet_by_report_em,
        "cashflow": ak.stock_cash_flow_sheet_by_report_em,
    }
    if report_type not in functions:
        raise ValueError("报表类型必须是 income、balance 或 cashflow。")

    df = functions[report_type](symbol=stock_symbol)
    if df is None or df.empty:
        raise ValueError(f"未获取到股票 {symbol} 的 {report_type} 报表。")

    if "REPORT_DATE" not in df.columns:
        raise ValueError("财报数据缺少报告日期字段。")

    df = df.copy()
    df["REPORT_DATE"] = pd.to_datetime(df["REPORT_DATE"], errors="coerce")
    df = df.dropna(subset=["REPORT_DATE"])
    return df.sort_values("REPORT_DATE", ascending=False).reset_index(drop=True)


def fetch_stock_income_statement(symbol):
    """获取上市公司利润表，原始字段保持数据源命名。"""
    return _fetch_stock_report(symbol, "income")


def fetch_stock_balance_sheet(symbol):
    """获取上市公司资产负债表，原始字段保持数据源命名。"""
    return _fetch_stock_report(symbol, "balance")


def fetch_stock_cash_flow_statement(symbol):
    """获取上市公司现金流量表，原始字段保持数据源命名。"""
    return _fetch_stock_report(symbol, "cashflow")