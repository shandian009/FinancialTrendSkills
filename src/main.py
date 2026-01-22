import os
import json
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import anthropic
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# 1. 绘图函数
def create_chart(symbol, name):
    df = yf.Ticker(symbol).history(period="1y")
    plt.figure(figsize=(6, 3), facecolor='#F5F5F5')
    plt.plot(df.index, df['Close'], color='#1A237E', linewidth=1.5)
    plt.fill_between(df.index, df['Close'], color='#1A237E', alpha=0.1)
    plt.axis('off')
    img_path = f"data/{symbol.replace('=', '').replace('^', '')}_chart.png"
    plt.savefig(img_path, bbox_inches='tight', dpi=100, facecolor='#F5F5F5')
    plt.close()
    return img_path

# 2. 获取数据
def get_advanced_data():
    targets = {
        "QQQ": "科技股", "GC=F": "黄金", "SI=F": "白银", 
        "HG=F": "高级铜", "XLU": "电网",
        "DX-Y.NYB": "美元指数", "^TNX": "10年美债收益率"
    }
    results = {}
    print("📊 正在调取全球宏观数据...")
    for symbol, name in targets.items():
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1y")
            if not df.empty:
                chart_path = create_chart(symbol, name)
                results[symbol] = {
                    "name": name,
                    "price": round(df['Close'].iloc[-1], 2),
                    "chart": chart_path,
                    "news": [n.get('title') for n in ticker.news[:2]]
                }
        except: pass
    return results

# 3. AI 分析
def ask_claude_pro(current_data, last_memory):
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key: return "错误：未检测到 CLAUDE_API_KEY。请检查 GitHub Secrets 设置。"
    
    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""
    你是一名顶级大类资产策略师。
    当前数据: {json.dumps(current_data, ensure_ascii=False)}
    上期预测记录: {json.dumps(last_memory, ensure_ascii=False)}

    任务：
    1. 【对账与反思】：对比价格。如果预测不符，请结合美元和美债的变化解释。
    2. 【大趋势分析】：分析科技股、金银铜、电网未来3个月至2年的趋势。
    3. 【小白建议】：用极简、高端的配色语言给小白写总结。
    """
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

# 4. 生成 PDF
def generate_pro_report(ai_text, market_data):
    os.makedirs('data', exist_ok=True)
    doc = SimpleDocTemplate("data/report.pdf", pagesize=A4)
    font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
    font_name = "Helvetica"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('wqy-microhei', font_path))
        font_name = 'wqy-microhei'
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='T', fontName=font_name, fontSize=20, textColor='#1A237E', spaceAfter=20)
    body_style = ParagraphStyle(name='B', fontName=font_name, fontSize=10, leading=14)
    
    elements = [Paragraph("AI 金融大趋势进化分析报告", title_style)]
    for line in ai_text.split('\n'):
        if line.strip(): elements.append(Paragraph(line, body_style))
    
    elements.append(Spacer(1, 20))
    for symbol, info in market_data.items():
        data = [[Paragraph(f"<b>{info['name']}</b><br/>${info['price']}", body_style), Image(info['chart'], width=200, height=80)]]
        elements.append(Table(data, colWidths=[100, 250]))
    doc.build(elements)

if __name__ == "__main__":
    current_market = get_advanced_data()
    memory_file = "data/memory.json"
    last_mem = {}
    if os.path.exists(memory_file):
        with open(memory_file, 'r', encoding='utf-8') as f: last_mem = json.load(f)
    
    report_text = ask_claude_pro(current_market, last_mem)
    generate_pro_report(report_text, current_market)
    
    with open(memory_file, 'w', encoding='utf-8') as f:
        json.dump({"prices": {s: d['price'] for s, d in current_market.items()}}, f)
