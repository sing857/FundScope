import streamlit as st
import pandas as pd

from data_fetcher import fetch_fund_nav
from analyzer import calculate_metrics


st.set_page_config(
    page_title="FundScope 基金分析器",
    page_icon="📊",
    layout="wide",
)

st.title("FundScope 基金分析器")
st.caption("个人基金收益与风险分析工具")

fund_code = st.text_input(
    "请输入六位公募基金代码",
    value="005827",
    max_chars=6,
)

if st.button("开始分析"):
    if len(fund_code) != 6 or not fund_code.isdigit():
        st.error("请输入有效的六位基金代码。")
    else:
        try:
            with st.spinner("正在获取基金历史净值……"):
                df = fetch_fund_nav(fund_code)
                df = df.set_index("date")
                metrics = calculate_metrics(df["nav"])

            st.subheader(f"基金代码：{fund_code}")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "区间收益率",
                f"{metrics['区间收益率']:.2%}",
            )
            col2.metric(
                "年化收益率",
                f"{metrics['年化收益率']:.2%}",
            )
            col3.metric(
                "最大回撤",
                f"{metrics['最大回撤']:.2%}",
            )

            col4, col5 = st.columns(2)

            col4.metric(
                "年化波动率",
                f"{metrics['年化波动率']:.2%}",
            )
            col5.metric(
                "夏普比率",
                f"{metrics['夏普比率']:.3f}",
            )

            st.subheader("历史单位净值走势")
            st.line_chart(df[["nav"]].rename(columns={"nav": "单位净值"}))

            st.subheader("历史净值数据")
            st.write(
                f"数据范围：{df.index.min().date()} 至 "
                f"{df.index.max().date()}"
            )
            st.write(f"有效记录数：{len(df)} 条")

            st.dataframe(
                df.sort_index(ascending=False),
                use_container_width=True,
            )

            st.info(
                "本工具仅用于历史数据分析，不构成投资建议。"
                "历史表现不代表未来收益。"
            )

        except Exception as exc:
            st.error(f"分析失败：{exc}")
            st.warning("请检查基金代码、网络连接或数据接口状态。")
