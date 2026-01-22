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
from reportlab.lib import colors

# 1. 深度图表 Skill：MA + Bollinger + MACD
def create_expert_chart(symbol, name):
    try:
        df = yf.Ticker(symbol).history(period="1y")
        if df.empty: return None
        
        # 计算布林带
        df['MA20'] = df['Close'].rolling(20).mean()
        df['STD'] = df['Close'].rolling(20).std()
        df['Upper'] = df['MA20'] + (df['STD'] * 2)
        df['Lower'] = df['MA20'] - (df['STD'] * 2)
        # 计算 MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 5), gridspec_kw={'height_ratios': [3, 1]}, facecolor='#FFFFFF')
        
        # 主图：布林带 + 价格
        ax1.plot(df.index, df['Close'], color='#001F3F', linewidth=1.5, label='Price')
        ax1.plot(df.index, df['Upper'], color='#D4AF37', linestyle='--', linewidth=0.6, alpha=0.5)
        ax1.plot(df.index, df['Lower'], color='#D4AF37', linestyle='--', linewidth=0.6, alpha=0.5)
        ax1.fill_between(df.index, df['Upper'], df['Lower'], color='#D4AF37', alpha=0.03)
        ax1.set_title(f"{name} (Trend & Momentum)", fontsize=10, loc='left', fontweight='bold')
        ax1.grid(True, linestyle=':', alpha=0.3)
        ax1.axis('off')

        # 副图：MACD 柱状图
        colors_macd = ['#FF4136' if (x < 0) else '#2ECC40' for x in (df['MACD'] - df['Signal'])]
        ax2.bar(df.index, df['MACD'] - df['Signal'], color=colors_macd, alpha=0.7)
        ax2.plot(df.index, df['MACD'], color='#001F3F', linewidth=0.8)
        ax2.axis('off')
        
        plt.tight_layout()
        os.makedirs('data', exist_ok=True)
        img_path = f"data/{symbol.replace('=', '').replace('^', '')}_pro.png"
        plt.savefig(img_path, bbox_inches='tight', dpi=120)
        plt.close()
        return img_path
    except: return None

# 2. 增强型提示词指令
def ask_expert_deepseek(current_data, last_memory):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    prompt = f"""
    作为顶级策略师，请基于以下数据撰写深度报告。
    数据: {json.dumps(current_data, ensure_ascii=False)}
    记忆: {json.dumps(last_memory, ensure_ascii=False)}

    格式要求：
    ## 1. 深度宏观复盘 (重点分析 DXY 和 TNX 对大宗商品/科技股的压制)
    ## 2. 跨时空趋势预判 (分段描述 3月、1年、2年 路径)
    ## 3. 板块操作矩阵 (必须以表格形式给出每个板块的评级：加仓/减仓/观望，并说明理由)
    ## 4. 首席结语 (直击核心逻辑)
    """

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "system", "content": "你是一位专注于跨资产联动的首席经济学家。"},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# 3. PDF 高级排版渲染
def generate_pro_pdf(ai_text, market_data):
    doc = SimpleDocTemplate("data/report.pdf", pagesize=A4, topMargin=30)
    font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
    font_name = "Helvetica"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('wqy-microhei', font_path))
        font_name = 'wqy-microhei'
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='T', fontName=font_name, fontSize=24, textColor='#001F3F', alignment=1, spaceAfter=20)
    h2_style = ParagraphStyle(name='H2', fontName=font_name, fontSize=15, textColor='#001F3F', spaceBefore=15, spaceAfter=10, borderLeftIndent=5, borderLeftColor='#D4AF37')
    body_style = ParagraphStyle(name='B', fontName=font_name, fontSize=10, leading=16)

    elements = [Paragraph("机构级宏观资产配置进化研报", title_style)]
    
    for line in ai_text.split('\n'):
        line = line.strip()
        if line.startswith('##'):
            elements.append(Paragraph(line.replace('#','').strip(), h2_style))
        elif line:
            elements.append(Paragraph(line, body_style))
    
    elements.append(Spacer(1, 20))
    # 专家图表卡片
    for symbol, info in market_data.items():
        if info['chart']:
            elements.append(Paragraph(f"<b>图表分析：{info['name']}</b>", body_style))
            elements.append(Image(info['chart'], width=450, height=220))
            elements.append(Spacer(1, 15))
            
    doc.build(elements)

if __name__ == "__main__":
    # 配置监测目标
    targets = {"QQQ": "纳指100(科技股)", "GC=F": "黄金(避险资产)", "DX-Y.NYB": "美元指数", "^TNX": "10年美债收益率"}
    market_results = {}
    for s, n in targets.items():
        img = create_expert_chart(s, n)
        if img:
            market_results[s] = {"name": n, "price": round(yf.Ticker(s).history(period="1y")['Close'].iloc[-1], 2), "chart": img}
    
    mem_file, last_mem = "data/memory.json", {}
    if os.path.exists(mem_file):
        with open(mem_file, 'r', encoding='utf-8') as f: last_mem = json.load(f)
        
    analysis_text = ask_expert_deepseek(market_results, last_mem)
    generate_pro_pdf(analysis_text, market_results)
    
    with open(mem_file, 'w', encoding='utf-8') as f:
        json.dump({"prices": {s: d['price'] for s, d in market_results.items()}}, f)
