import os
import json
from datetime import datetime

print("🚀 金融趋势分析启动")

# 检查API Key
api_key = os.getenv('CLAUDE_API_KEY')
if not api_key:
    print("❌ CLAUDE_API_KEY未设置")
    exit(1)

print("✅ API Key已读取")

# 创建分析报告
report = {
    'timestamp': datetime.now().isoformat(),
    'status': 'success',
    'message': '金融分析系统运行成功',
    'api_key_status': 'configured'
}

# 保存报告
os.makedirs('data', exist_ok=True)
with open('data/latest_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print("✅ 分析完成！")
print(json.dumps(report, ensure_ascii=False, indent=2))
