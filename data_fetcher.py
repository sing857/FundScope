import akshare as ak
import pandas as pd


def fetch_fund_name(fund_code: str) -> str:
    """根据基金代码获取基金简称。"""

    fund_code = str(fund_code).strip()

    if len(fund_code) != 6 or not fund_code.isdigit():
        raise ValueError("请输入有效的6位基金代码，例如005827。")

    fund_list = ak.fund_name_em()

    matched = fund_list.loc[
        fund_list["基金代码"].astype(str).str.zfill(6) == fund_code,
        "基金简称",
    ]

    if matched.empty:
        raise ValueError(f"没有找到基金代码 {fund_code} 对应的名称。")

    return str(matched.iloc[0])


def fetch_fund_nav(fund_code: str) -> pd.DataFrame:
    """获取指定基金的历史净值。"""

    fund_code = str(fund_code).strip()

    if len(fund_code) != 6 or not fund_code.isdigit():
        raise ValueError("请输入有效的6位基金代码，例如005827。")

    df = ak.fund_open_fund_info_em(
        symbol=fund_code,
        indicator="单位净值走势",
    )

    if df is None or df.empty:
        raise ValueError("没有获取到基金净值数据，请检查基金代码或数据接口。")

    df = df.rename(
        columns={
            "净值日期": "date",
            "单位净值": "nav",
        }
    )

    required_columns = {"date", "nav"}

    if not required_columns.issubset(df.columns):
        raise ValueError(
            f"数据缺少必要字段，当前字段为：{list(df.columns)}"
        )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")

    df = df.dropna(subset=["date", "nav"])
    df = df[df["nav"] > 0]
    df = df.drop_duplicates(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    if len(df) < 2:
        raise ValueError("有效历史净值数据不足，无法进行分析。")

    return df
