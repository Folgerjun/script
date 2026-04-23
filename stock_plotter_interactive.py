import efinance as ef
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os

def get_stock_data(stock_code, start_date, end_date):
    """
    获取股票的历史K线数据和实时基本面数据
    """
    try:
        # 1. 获取历史数据
        history_data = ef.stock.get_quote_history(
            stock_code, 
            beg=start_date.strftime('%Y%m%d'), 
            end=end_date.strftime('%Y%m%d')
        )
        if history_data.empty:
            print(f"未找到 {stock_code} 的历史数据。")
            return None, None
        
        # 转换日期格式
        history_data['日期'] = pd.to_datetime(history_data['日期'])
        
        # 2. 获取实时基本面数据
        realtime_data = ef.stock.get_latest_quote(stock_code)
        
        # 提取所需的基本面数据
        if not realtime_data.empty:
            info = {
                '名称': realtime_data['名称'].iloc[0],
                '代码': realtime_data['代码'].iloc[0],
                '总市值': realtime_data['总市值'].iloc[0],
                '动态市盈率': realtime_data['动态市盈率'].iloc[0],
                '最新价': realtime_data['最新价'].iloc[0],
                '涨跌幅': realtime_data['涨跌幅'].iloc[0]
            }
        else:
            info = {'名称': stock_code, '代码': stock_code}
            
        return history_data, info
    
    except Exception as e:
        print(f"获取 {stock_code} 数据时发生错误: {e}")
        return None, None

def plot_interactive(stock_data_list, start_date, end_date):
    """
    使用 Plotly 绘制交互式走势图
    """
    fig = go.Figure()
    
    # 构建标题信息
    header_info = []
    for _, info in stock_data_list:
        market_cap = info.get('总市值', 0) / 1e8 if info.get('总市值') else 0
        pe = info.get('动态市盈率', 'N/A')
        header_info.append(
            f"<b>{info['名称']}</b>: 现价 {info.get('最新价','N/A')} | 市值 {market_cap:.2f}亿 | PE {pe}"
        )
    
    title_text = f"股票走势对比 ({start_date} 至 {end_date})<br><span style='font-size:12px;'>" + " | ".join(header_info) + "</span>"

    for history_data, info in stock_data_list:
        # 归一化处理：以起始日收盘价为基准 (100)
        base_price = history_data['收盘'].iloc[0]
        normalized_series = (history_data['收盘'] / base_price) * 100
        
        fig.add_trace(go.Scatter(
            x=history_data['日期'],
            y=normalized_series,
            mode='lines',
            name=f"{info['名称']} ({info['代码']})",
            hovertemplate='日期: %{x}<br>相对指数: %{y:.2f}<br>实际收盘: ' + history_data['收盘'].astype(str)
        ))

    fig.update_layout(
        title=title_text,
        xaxis_title="日期",
        yaxis_title="相对价格指数 (起始日=100)",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=100)
    )

    # 自动在浏览器中弹出
    print("\n正在生成交互式图表并尝试在浏览器中打开...")
    fig.show()

def main():
    print("=== 交互式股票走势对比工具 ===")
    
    # 1. 输入股票
    codes_input = input("请输入股票代码或名称（多个请用逗号分隔，留空默认: 600519,AAPL）: ").strip()
    if not codes_input:
        stock_codes = ['600519', 'AAPL']
    else:
        stock_codes = [c.strip() for c in codes_input.replace('，', ',').split(',')]
    
    # 2. 输入时间范围
    days_input = input("请输入查看的天数（如 365，留空默认 365）: ").strip()
    days = int(days_input) if days_input else 365
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    # --- 数据获取 ---
    all_stock_data = []
    for code in stock_codes:
        print(f"正在获取 {code} 的数据...")
        history, info = get_stock_data(code, start_date, end_date)
        if history is not None:
            all_stock_data.append((history, info))
            
    # --- 绘图 ---
    if all_stock_data:
        plot_interactive(all_stock_data, start_date, end_date)
    else:
        print("无法获取任何股票数据，请检查输入。")

if __name__ == "__main__":
    main()
