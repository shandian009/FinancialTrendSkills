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
from reportlab.lib.colors import HexColor

# 1. 绘图 Skill 修正：增加网格、价格标注和专业配色
def create_chart(symbol, name):
    try:
        df = yf.Ticker(symbol).history(period="1y")
        if df.empty: return None
        
        plt.figure(figsize=(7, 3), facecolor='#FFFFFF')
        # 增加轻微网格
        plt.grid(True, linestyle='--', alpha=0.3, color='#CCCCCC')
        # 价格曲线
        plt.plot(df.index, df['Close'], color='#001F3F', linewidth=1.8)
        # 趋势辅助线
        df['MA50'] = df['Close'].rolling(window=50).mean()
        plt.plot(df.index, df['MA50'], color='#D4AF37', linestyle='--', linewidth=1, alpha=0.6)
        
        # 标注最新价格
        last_price = df['Close'].iloc[-1]
        plt.annotate(f'${last_price:.2f}', xy=(df.index[-1], last_price), xytext=(5,0), 
                     textcoords='offset points', fontsize=9, color='#001F3F', fontweight='bold')
        
        plt.fill_between(df.index, df['Close'], color='#001F3F', alpha=0.04)
        plt.axis('off')
        
        os.makedirs('data', exist_ok=True)
        img_path = f"data/{symbol.replace('=', '').replace('^', '')}_chart.png"
        plt.savefig(img_path, bbox_inches='tight', dpi=120)
        plt.close()
        return img_path
    except: return None

# 2. 提示词 (Prompt) 修正：强制结构化输出，避免排版混乱
def ask_deepseek_analysis(current_data, last_memory):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    prompt = f"""
    你是一名全球顶级宏观策略分析师。请根据以下数据提交一份精简且极具专业度的报告。
    当前数据: {json.dumps(current_data, ensure_ascii=False)}
    历史记忆: {json.dumps(last_memory, ensure_ascii=False)}

    要求必须严格按照以下格式输出（不要有开场白，直接开始）：

    ## 1. 误差溯源与复盘
    (对比上期价格，分析偏差原因，重点提及美元指数和美债收益率的挤压效应)

    ## 2. 跨资产联动分析
    (分析美债收益率与科技股、大宗商品的逻辑关系)

    ## 3. 跨时空趋势预判
    - **未来3个月（情绪视角）**: 预判波动区间。
    - **未来1年（周期视角）**: 预判政策转向后的路径。
    - **未来2年（结构视角）**: 宏观新平衡下的终极建议。

    ## 4. 首席操作建议
    (为投资者写一段直击本质的操作逻辑，强调“现金流”与“择质”)
    """

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "system", "content": "你是一个严谨、犀利的金融研报专家，善于结构化写作。"},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# 3. PDF 排版 Skill 修正：增加标题识别和层次感
def generate_report(ai_text, market_data):
    doc = SimpleDocTemplate("data/report.pdf", pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40)
    
    font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
    font_name = "Helvetica"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('wqy-microhei', font_path))
        font_name = 'wqy-microhei'
    
    styles = getSampleStyleSheet()
    # 样式微调
    title_style = ParagraphStyle(name='T', fontName=font_name, fontSize=24, textColor='#001F3F', spaceAfter=20, alignment=1)
    h2_style = ParagraphStyle(name='H2', fontName=font_name, fontSize=14, textColor='#001F3F', spaceBefore=15, spaceAfter=10, bold=True)
    body_style = ParagraphStyle(name='B', fontName=font_name, fontSize=10.5, leading=16, textColor='#333333')
    
    elements = [Paragraph("DeepSeek 宏观策略深度分析报告", title_style)]
    elements.append(Paragraph(f"报告日期: {datetime.now().strftime('%Y-%m-%d')}", body_style))
    elements.append(Spacer(1, 20))

    # 智能识别 AI 的 Markdown 标题进行美化
    for line in ai_text.split('\n'):
        line = line.strip()
        if not line: continue
        if line.startswith('##'):
            elements.append(Paragraph(line.replace('#', '').strip(), h2_style))
        elif line.startswith('-') or line.startswith('*'):
            elements.append(Paragraph(f"• {line[1:].strip()}", body_style))
        else:
            elements.append(Paragraph(line, body_style))
    
    elements.append(Spacer(1, 20))
    # 资产卡片
    for symbol, info in market_data.items():
        if info['chart']:
            card_data = [[Paragraph(f"<b>{info['name']}</b><br/>${info['price']}", body_style), Image(info['chart'], width=240, height=90)]]
            t = Table(card_data, colWidths=[120, 260])
            t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'), ('BOTTOMPADDING', (0,0), (-1,-1), 10)]))
            elements.append(t)
            
    doc.build(elements)

if __name__ == "__main__":
    targets = {"QQQ": "科技股(Nasdaq)", "GC=F": "黄金期货", "SI=F": "白银期货", "DX-Y.NYB": "美元指数", "^TNX": "10年美债收益率"}
    market_results = {}
    for s, n in targets.items():
        c = create_chart(s, n)
        if c: market_results[s] = {"name": n, "price": round(yf.Ticker(s).history(period="1y")['Close'].iloc[-1], 2), "chart": c}
    
    mem_file = "data/memory.json"
    last_mem = {}
    if os.path.exists(mem_file):
        with open(mem_file, 'r', encoding='utf-8') as f: last_mem = json.load(f)
        
    analysis = ask_deepseek_analysis(market_results, last_mem)
    generate_report(analysis, market_results)
    
    with open(mem_file, 'w', encoding='utf-8') as f:
        json.dump({"prices": {s: d['price'] for s, d in market_results.items()}}, f)
