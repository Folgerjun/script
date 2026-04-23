import efinance as ef
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os

# 设置 Matplotlib 支持中文
plt.rcParams['font.sans-serif'] = ['文泉驿正黑', 'WenQuanYi Zen Hei', 'SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False    # 解决保存图像是负号'-'显示为方块的问题

def get_stock_data(stock_code, start_date, end_date):
    """
    获取股票的历史K线数据和实时基本面数据
    """
    try:
        # 1. 获取历史数据
        # efinance 的日期格式为 YYYYMMDD
        history_data = ef.stock.get_quote_history(
            stock_code, 
            beg=start_date.strftime('%Y%m%d'), 
            end=end_date.strftime('%Y%m%d')
        )
        if history_data.empty:
            print(f"未找到 {stock_code} ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}) 的历史数据。")
            return None, None
        
        # 转换日期格式
        history_data['日期'] = pd.to_datetime(history_data['日期'])
        history_data.set_index('日期', inplace=True)
        
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

def plot_stock_prices(stock_data_list, start_date, end_date, output_filename="stock_comparison.png"):
    """
    绘制多股票股价走势图
    """
    if not stock_data_list:
        print("没有可用的股票数据进行绘图。")
        return

    fig, ax = plt.subplots(figsize=(14, 8))
    
    # 标题和基本信息
    title_lines = [f"股票走势对比 ({start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')})"]
    
    for _, info in stock_data_list:
        if info:
            market_cap_billion = info.get('总市值', 0) / 100000000 if info.get('总市值') else 'N/A'
            pe_ratio = info.get('动态市盈率', 'N/A')
            latest_price = info.get('最新价', 'N/A')
            change_percent = info.get('涨跌幅', 'N/A')
            
            info_line = (
                f"{info['名称']}({info['代码']}): "
                f"最新价 {latest_price} ({change_percent}%), "
                f"总市值 {market_cap_billion:.2f} 亿, "
                f"PE(TTM) {pe_ratio}"
            )
            title_lines.append(info_line)

    plt.title('\n'.join(title_lines), loc='left', fontsize=12, pad=20)
    
    # 绘制走势图
    for history_data, info in stock_data_list:
        if history_data is not None and info:
            stock_name = info['名称']
            # 归一化处理：以起始日收盘价为基准
            base_price = history_data['收盘'].iloc[0]
            normalized_price = history_data['收盘'] / base_price * 100
            
            ax.plot(normalized_price.index, normalized_price, label=f"{stock_name} (基准化)")

    # 格式化日期轴
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate() # 自动旋转日期标签
    
    # 设置图表样式
    ax.set_xlabel("日期")
    ax.set_ylabel("相对价格指数 (起始日=100)")
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='upper right')
    
    # 保存图片
    plt.tight_layout()
    plt.savefig(output_filename)
    print(f"\n走势图已保存至: {output_filename}")
    plt.close(fig)

def main():
    print("=== 股票走势对比工具 ===")
    print("支持输入股票代码（如 600519, AAPL）或股票名称（如 贵州茅台, 苹果）")
    
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
    
    # --- 数据获取与处理 ---
    all_stock_data = []
    for code in stock_codes:
        history, info = get_stock_data(code, start_date, end_date)
        if history is not None and info is not None:
            all_stock_data.append((history, info))
            
    # --- 绘图 ---
    if all_stock_data:
        output_file = "stock_comparison.png"
        plot_stock_prices(all_stock_data, start_date, end_date, output_file)
        print(f"\n任务完成！走势图已保存为: {os.path.abspath(output_file)}")
    else:
        print("无法获取任何股票数据，请检查输入是否正确。")

if __name__ == "__main__":
    main()
