import os
import json
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from datetime import datetime
import anthropic
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# 1. 绘图函数：生成简约的高端图表
def create_chart(symbol, name):
    df = yf.Ticker(symbol).history(period="1y")
    plt.figure(figsize=(6, 3), facecolor='#F5F5F5')
    plt.plot(df.index, df['Close'], color='#1A237E', linewidth=1.5)
    plt.fill_between(df.index, df['Close'], color='#1A237E', alpha=0.1)
    plt.title(f"{name} ({symbol}) 1-Year Trend", fontsize=10, color='#333333')
    plt.axis('off') # 极简风格，去掉坐标轴
    img_path = f"data/{symbol}_chart.png"
    plt.savefig(img_path, bbox_inches='tight', dpi=100, facecolor='#F5F5F5')
    plt.close()
    return img_path

# 2. 获取数据逻辑（同前，增加绘图触发）
def get_full_data():
    targets = {"QQQ": "科技股", "GC=F": "黄金", "SI=F": "白银", "HG=F": "高级铜", "XLU": "电网"}
    results = {}
    for symbol, name in targets.items():
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")
        chart_path = create_chart(symbol, name)
        results[symbol] = {
            "name": name,
            "price": round(df['Close'].iloc[-1], 2),
            "chart": chart_path
        }
    return results

# 3. 生成 PDF 报告（视觉重构）
def generate_pro_report(ai_text, market_data):
    os.makedirs('data', exist_ok=True)
    doc = SimpleDocTemplate("data/report.pdf", pagesize=A4, leftMargin=40, rightMargin=40)
    
    # 注册中文字体
    font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
    font_name = "Helvetica"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('wqy-microhei', font_path))
        font_name = 'wqy-microhei'

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='Title', fontName=font_name, fontSize=24, textColor='#1A237E', alignment=0, spaceAfter=20)
    sub_style = ParagraphStyle(name='Sub', fontName=font_name, fontSize=10, textColor='#666666', spaceAfter=30)
    body_style = ParagraphStyle(name='Body', fontName=font_name, fontSize=11, leading=16, textColor='#333333')
    section_style = ParagraphStyle(name='Section', fontName=font_name, fontSize=14, textColor='#1A237E', spaceBefore=15, spaceAfter=10, borderPadding=5)

    elements = []
    # 标题栏
    elements.append(Paragraph("Global Market Trend Intelligence", title_style))
    elements.append(Paragraph(f"报告编号: {datetime.now().strftime('%Y%m%d')} | 自动生成自 AI 金融分析系统", sub_style))

    # AI 深度分析部分 (第一页)
    elements.append(Paragraph("AI 深度复盘与未来趋势预测", section_style))
    for para in ai_text.split('\n'):
        if para.strip():
            elements.append(Paragraph(para, body_style))
            elements.append(Spacer(1, 8))

    elements.append(Spacer(1, 20))
    
    # 可视化数据部分
    elements.append(Paragraph("资产走势可视化 (Asset Visuals)", section_style))
    for symbol, info in market_data.items():
        # 创建一个表格来并排显示文字和图表
        data = [[Paragraph(f"<b>{info['name']}</b><br/>Current: ${info['price']}", body_style), Image(info['chart'], width=250, height=120)]]
        t = Table(data, colWidths=[150, 300])
        t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        elements.append(t)
        elements.append(Spacer(1, 10))

    doc.build(elements)

# 主程序逻辑
if __name__ == "__main__":
    # 1. 获取数据并生成图表
    data = get_full_data()
    # 2. 调用 Claude（逻辑同前）
    # ai_content = ask_claude_pro(...) 
    # 此处假设 ai_content 为 Claude 生成的文本
    ai_content = "这里是 Claude 生成的带反省、总结和预测的长篇中文文本..."
    # 3. 渲染高端 PDF
    generate_pro_report(ai_content, data)
