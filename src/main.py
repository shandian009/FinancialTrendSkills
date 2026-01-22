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

# 1. 绘图函数：高端黑金配色 + 趋势辅助线
def create_chart(symbol, name):
    try:
        df = yf.Ticker(symbol).history(period="1y")
        if df.empty: return None
        
        plt.figure(figsize=(7, 3), facecolor='#FFFFFF')
        # 价格主线：深海军蓝
        plt.plot(df.index, df['Close'], color='#001F3F', linewidth=1.8, label='Price')
        # 50日均线：金色虚线 (大趋势参考)
        df['MA50'] = df['Close'].rolling(window=50).mean()
        plt.plot(df.index, df['MA50'], color='#D4AF37', linestyle='--', linewidth=1, alpha=0.6)
        
        plt.fill_between(df.index, df['Close'], color='#001F3F', alpha=0.04)
        plt.axis('off')
        
        os.makedirs('data', exist_ok=True)
        img_path = f"data/{symbol.replace('=', '').replace('^', '')}_chart.png"
        plt.savefig(img_path, bbox_inches='tight', dpi=120)
        plt.close()
        return img_path
    except Exception as e:
        print(f"绘图失败 {symbol}: {e}")
        return None

# 2. 获取全球宏观数据
def get_market_data():
    targets = {
        "QQQ": "科技股指数", 
        "GC=F": "黄金期货", 
        "SI=F": "白银期货", 
        "HG=F": "高级铜(基建)", 
        "XLU": "公用事业电网",
        "DX-Y.NYB": "美元指数(DXY)", 
        "^TNX": "10年美债收益率"
    }
    results = {}
    print("📊 正在调取全球宏观数据流...")
    for symbol, name in targets.items():
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1y")
            if not df.empty:
                chart_path = create_chart(symbol, name)
                results[symbol] = {
                    "name": name,
                    "price": round(df['Close'].iloc[-1], 2),
                    "chart": chart_path
                }
        except Exception as e:
            print(f"数据获取失败 {symbol}: {e}")
    return results

# 3. DeepSeek 深度逻辑分析
def ask_deepseek_analysis(current_data, last_memory):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key: return "错误：未检测到 DEEPSEEK_API_KEY。"
    
    # DeepSeek 官方 API 接入配置
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    prompt = f"""
    你是一名全球顶尖的宏观策略分析师。请针对以下数据进行深度进化分析。

    【当前市场数据】: {json.dumps(current_data, ensure_ascii=False)}
    【上期历史记忆】: {json.dumps(last_memory, ensure_ascii=False)}

    任务指令：
    1. 【误差溯源】：对比上期价格。如果预测与走势不符，请分析是否受美元指数走强或美债收益率波动的压制。
    2. 【联动推演】：解释科技股与大宗商品在当前利率环境下的共振或背离逻辑。
    3. 【跨时空预测】：给出 3个月（情绪驱动）、1年（周期驱动）、2年（结构驱动）的判断。
    4. 【操作建议】：为小白投资者写一段极简、高端且直击本质的总结。
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat", # 使用 DeepSeek-V3
            messages=[
                {"role": "system", "content": "你是一个严谨、犀利且具备长线思维的金融研报专家"},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"DeepSeek 接口返回错误: {str(e)}"

# 4. 生成专业 PDF 研报
def generate_report(ai_text, market_data):
    doc = SimpleDocTemplate("data/report.pdf", pagesize=A4, rightMargin=40, leftMargin=40)
    
    # 字体处理
    font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
    font_name = "Helvetica"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('wqy-microhei', font_path))
        font_name = 'wqy-microhei'
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='T', fontName=font_name, fontSize=24, textColor='#001F3F', spaceAfter=20)
    body_style = ParagraphStyle(name='B', fontName=font_name, fontSize=11, leading=16, textColor='#333333')
    
    elements = [Paragraph("DeepSeek 宏观趋势进化研报", title_style)]
    elements.append(Paragraph(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style))
    elements.append(Spacer(1, 20))
    
    # 写入 AI 分析内容
    for line in ai_text.split('\n'):
        if line.strip():
            elements.append(Paragraph(line, body_style))
    
    elements.append(Spacer(1, 25))
    
    # 插入资产数据卡片
    for symbol, info in market_data.items():
        if info['chart']:
            data = [[
                Paragraph(f"<b>{info['name']}</b><br/>现价: ${info['price']}", body_style), 
                Image(info['chart'], width=240, height=90)
            ]]
            t = Table(data, colWidths=[120, 260])
            t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'), ('BOTTOMPADDING', (0,0), (-1,-1), 12)]))
            elements.append(t)
            
    doc.build(elements)

if __name__ == "__main__":
    # 执行主流程
    current_market = get_market_data()
    
    # 记忆逻辑
    mem_file = "data/memory.json"
    last_mem = {}
    if os.path.exists(mem_file):
        try:
            with open(mem_file, 'r', encoding='utf-8') as f: last_mem = json.load(f)
        except: pass

    # AI 生成内容
    print("🤖 正在请求 DeepSeek 进行深度逻辑推演...")
    analysis_text = ask_deepseek_analysis(current_market, last_mem)
    
    # 生成 PDF
    print("📄 正在渲染 PDF 专业报告...")
    generate_report(analysis_text, current_market)
    
    # 更新记忆
    with open(mem_file, 'w', encoding='utf-8') as f:
        json.dump({"prices": {s: d['price'] for s, d in current_market.items()}, "date": datetime.now().strftime('%Y-%m-%d')}, f)
    
    print("✅ 任务完成！")
