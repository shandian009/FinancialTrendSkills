import os
import json
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI
from datetime import datetime
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# 1. 高端黑金配色绘图
def create_chart(symbol, name):
    df = yf.Ticker(symbol).history(period="1y")
    plt.figure(figsize=(7, 3), facecolor='#FFFFFF')
    # 价格主线 (深海军蓝)
    plt.plot(df.index, df['Close'], color='#001F3F', linewidth=1.8)
    # 趋势辅助线 (金色虚线)
    df['MA50'] = df['Close'].rolling(window=50).mean()
    plt.plot(df.index, df['MA50'], color='#D4AF37', linestyle='--', linewidth=1, alpha=0.6)
    
    plt.fill_between(df.index, df['Close'], color='#001F3F', alpha=0.04)
    plt.axis('off')
    
    img_path = f"data/{symbol.replace('=', '').replace('^', '')}_chart.png"
    plt.savefig(img_path, bbox_inches='tight', dpi=120)
    plt.close()
    return img_path

# 2. 调取数据
def get_market_data():
    targets = {
        "QQQ": "科技股(Nasdaq)", "GC=F": "黄金", "SI=F": "白银", 
        "HG=F": "铜(基建指标)", "XLU": "电网公用",
        "DX-Y.NYB": "美元指数", "^TNX": "10年美债收益率"
    }
    results = {}
    os.makedirs('data', exist_ok=True)
    for symbol, name in targets.items():
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1y")
            if not df.empty:
                chart_path = create_chart(symbol, name)
                results[symbol] = {"name": name, "price": round(df['Close'].iloc[-1], 2), "chart": chart_path}
        except: pass
    return results

# 3. 调用 DeepSeek API
def ask_deepseek(current_data, last_memory):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    prompt = f"当前数据: {json.dumps(current_data, ensure_ascii=False)}\n历史记忆: {json.dumps(last_memory, ensure_ascii=False)}\n请作为首席策略师，分析误差、多资产联动逻辑，并给出未来3个月至2年的趋势预测，最后为小白写一段总结。"

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "system", "content": "你是一个严谨且犀利的金融研报专家"}, {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# 4. 生成 PDF 报告
def generate_pdf(ai_text, market_data):
    doc = SimpleDocTemplate("data/report.pdf", pagesize=A4)
    font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
    font_name = "Helvetica"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('wqy-microhei', font_path))
        font_name = 'wqy-microhei'
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='T', fontName=font_name, fontSize=22, textColor='#001F3F', spaceAfter=20)
    body_style = ParagraphStyle(name='B', fontName=font_name, fontSize=10, leading=15)

    elements = [Paragraph("DeepSeek 金融大趋势进化研报", title_style)]
    elements.append(Paragraph(f"生成日期: {datetime.now().strftime('%Y-%m-%d')}", body_style))
    elements.append(Spacer(1, 20))
    
    for line in ai_text.split('\n'):
        if line.strip(): elements.append(Paragraph(line, body_style))
    
    elements.append(Spacer(1, 20))
    for symbol, info in market_data.items():
        data = [[Paragraph(f"<b>{info['name']}</b><br/>现价: ${info['price']}", body_style), Image(info['chart'], width=220, height=85)]]
        elements.append(Table(data, colWidths=[120, 260]))
    doc.build(elements)

if __name__ == "__main__":
    data = get_market_data()
    mem_file = "data/memory.json"
    last_mem = {}
    if os.path.exists(mem_file):
        with open(mem_file, 'r', encoding='utf-8') as f: last_mem = json.load(f)
    
    analysis = ask_deepseek(data, last_mem)
    generate_pdf(analysis, data)
    
    with open(mem_file, 'w', encoding='utf-8') as f:
        json.dump({"prices": {s: d['price'] for s, d in data.items()}}, f)
