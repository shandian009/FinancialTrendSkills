import os
import json
import yfinance as yf
from datetime import datetime
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def get_market_data():
    # 获取标普500 (SPY) 的数据
    ticker = yf.Ticker("SPY")
    hist = ticker.history(period="1d")
    current_price = round(hist['Close'].iloc[-1], 2)
    change = round(hist['Close'].iloc[-1] - hist['Open'].iloc[-1], 2)
    return {"price": current_price, "change": change}

def create_pdf_report(market_info):
    os.makedirs('data', exist_ok=True)
    report_path = "data/report.pdf"
    doc = SimpleDocTemplate(report_path, pagesize=A4)
    
    # 加载系统自带中文字体 (GitHub Actions 的 Linux 环境自带)
    font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
    font_name = "Helvetica"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('wqy-microhei', font_path))
        font_name = 'wqy-microhei'

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='Title', fontName=font_name, fontSize=20, alignment=1, spaceAfter=20)
    text_style = ParagraphStyle(name='Text', fontName=font_name, fontSize=12, leading=16)

    content = []
    content.append(Paragraph("AI 金融市场分析简报", title_style))
    content.append(Paragraph(f"生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", text_style))
    content.append(Spacer(1, 20))
    
    content.append(Paragraph(f"<b>标普500 (SPY) 表现:</b>", text_style))
    content.append(Paragraph(f"当前价格: ${market_info['price']}", text_style))
    content.append(Paragraph(f"今日涨跌: ${market_info['change']}", text_style))
    
    content.append(Spacer(1, 20))
    content.append(Paragraph("<b>AI 简评:</b>", text_style))
    status = "表现稳健" if market_info['change'] >= 0 else "出现回调"
    ai_comment = f"根据今日行情，标普500指数{status}。当前价格维持在 ${market_info['price']} 附近。建议投资者保持关注，留意市场波动。"
    content.append(Paragraph(ai_comment, text_style))
    
    doc.build(content)

# 主运行逻辑
print("🚀 正在获取实时金融数据...")
data = get_market_data()
print("📄 正在生成中文 PDF 报告...")
create_pdf_report(data)

# 保存 JSON 备份
with open('data/latest_analysis.json', 'w', encoding='utf-8') as f:
    json.dump({"market_data": data, "timestamp": datetime.now().isoformat()}, f, ensure_ascii=False)
print("✅ 报告生成成功！")
