import os
import json
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai
from datetime import datetime
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# 1. 绘图函数：高端黑金配色 + 趋势参考线
def create_chart(symbol, name):
    df = yf.Ticker(symbol).history(period="1y")
    plt.figure(figsize=(7, 3), facecolor='#FDFDFD')
    
    # 主价格线：海军蓝
    plt.plot(df.index, df['Close'], color='#001F3F', linewidth=1.8, label='Price')
    # 20日均线：金色虚线
    df['MA20'] = df['Close'].rolling(window=20).mean()
    plt.plot(df.index, df['MA20'], color='#D4AF37', linestyle='--', linewidth=1, alpha=0.6)
    
    plt.fill_between(df.index, df['Close'], color='#001F3F', alpha=0.04)
    plt.axis('off')
    
    img_path = f"data/{symbol.replace('=', '').replace('^', '')}_chart.png"
    plt.savefig(img_path, bbox_inches='tight', dpi=120, facecolor='#FDFDFD')
    plt.close()
    return img_path

# 2. 获取数据 (宏观指标 + 行业标的)
def get_market_data():
    targets = {
        "QQQ": "科技股(Nasdaq)", "GC=F": "避险黄金", "SI=F": "工业白银", 
        "HG=F": "基建高级铜", "XLU": "公用电网",
        "DX-Y.NYB": "美元指数(DXY)", "^TNX": "10年美债收益率"
    }
    results = {}
    print("📊 正在通过 yfinance 获取 2026 全球市场实时流...")
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
        except Exception as e:
            print(f"跳过 {symbol}: {e}")
    return results

# 3. Gemini 3.0 Flash 深度分析 (带误差溯源提示词)
def ask_gemini_3_flash(current_data, last_memory):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: return "错误：未配置 GEMINI_API_KEY。"
    
    genai.configure(api_key=api_key)
    # 调用 2026 年最新 Gemini 3 Flash 模型
    model = genai.GenerativeModel('gemini-3-flash') 
    
    prompt = f"""
    你现在是基于 Gemini 3.0 引擎的顶级策略分析师。请针对以下数据进行深度进化分析。

    【当前数据】: {json.dumps(current_data, ensure_ascii=False)}
    【上期记忆】: {json.dumps(last_memory, ensure_ascii=False)}

    任务指令：
    1. 【误差溯源】：对比上期价格。如果之前看涨但本期下跌，请深度反省。分析是否因为忽略了“美元指数”走强或“美债收益率”对估值的挤压。
    2. 【多资产联动】：解释当前宏观环境下，科技股与大宗商品（金银铜）的背离或共振逻辑。
    3. 【进化预测】：给出 3个月（情绪视角）、1年（周期视角）、2年（结构视角）的资产配置建议。
    4. 【风险/机会】：识别 RSI 极端或地缘突发对电网/基建板块的潜在冲击。
    5. 【小白寄语】：用一段极简、高端且具有温度的话，为小白投资者总结操作逻辑。

    要求：输出必须专业、冷静，逻辑链条严密。
    """
    
    response = model.generate_content(prompt)
    return response.text

# 4. 生成专业 PDF (视觉升级版)
def generate_pro_report(ai_text, market_data):
    os.makedirs('data', exist_ok=True)
    doc = SimpleDocTemplate("data/report.pdf", pagesize=A4, rightMargin=40, leftMargin=40)
    
    font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
    font_name = "Helvetica"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('wqy-microhei', font_path))
        font_name = 'wqy-microhei'
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='T', fontName=font_name, fontSize=22, textColor='#001F3F', spaceAfter=20, alignment=0)
    body_style = ParagraphStyle(name='B', fontName=font_name, fontSize=10, leading=16, textColor='#333333')
    sub_title = ParagraphStyle(name='ST', fontName=font_name, fontSize=12, textColor='#001F3F', spaceBefore=10, spaceAfter=10, borderPadding=5)

    elements = [Paragraph("Gemini 3.0 全球趋势进化报告", title_style)]
    elements.append(Paragraph(f"发布时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 模型驱动: Gemini-3-Flash", body_style))
    elements.append(Spacer(1, 15))
    
    # 插入 AI 分析内容
    for line in ai_text.split('\n'):
        if line.strip():
            elements.append(Paragraph(line, body_style))
    
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("资产走势可视化对比", sub_title))
    
    # 资产卡片
    for symbol, info in market_data.items():
        data = [[
            Paragraph(f"<b>{info['name']}</b><br/>现价: ${info['price']}", body_style), 
            Image(info['chart'], width=240, height=90)
        ]]
        t = Table(data, colWidths=[130, 260])
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'), ('BOTTOMPADDING', (0,0), (-1,-1), 10)]))
        elements.append(t)
    
    doc.build(elements)

if __name__ == "__main__":
    # 执行主流程
    market_info = get_market_data()
    
    # 记忆持久化逻辑
    mem_file = "data/memory.json"
    last_mem = {}
    if os.path.exists(mem_file):
        try:
            with open(mem_file, 'r', encoding='utf-8') as f: last_mem = json.load(f)
        except: pass

    # AI 生成研报
    report_content = ask_gemini_3_flash(market_info, last_mem)
    
    # 渲染 PDF
    generate_pro_report(report_content, market_info)
    
    # 更新记忆文件供下次对账
    with open(mem_file, 'w', encoding='utf-8') as f:
        new_mem = {
            "last_date": datetime.now().strftime('%Y-%m-%d'),
            "prices": {s: d['price'] for s, d in market_info.items()},
            "summary": report_content[:300] # 保存部分概要
        }
        json.dump(new_mem, f, ensure_ascii=False, indent=2)
