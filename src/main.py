import os
import json
from datetime import datetime

print("🚀 金融趋势分析启动")
print(f"⏰ 时间: {datetime.now().isoformat()}")

# 检查API Key
api_key = os.getenv('CLAUDE_API_KEY')
if not api_key:
    print("❌ 错误: CLAUDE_API_KEY未设置")
    exit(1)

print("✅ API Key已读取")

# 创建简单的报告
report = {
    'timestamp': datetime.now().isoformat(),
    'status': 'success',
    'message': '金融分析系统已启动'
}

# 保存报告
os.makedirs('data', exist_ok=True)
with open('data/latest_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print("✅ 分析完成！报告已保存")
print(json.dumps(report, ensure_ascii=False, indent=2))
```

4. **Commit changes**

---

### **Step 2：创建requirements.txt**

1. 点击 **Add file → Create new file**
2. 文件名：`requirements.txt`
3. 复制内容：
```
anthropic==0.39.0
yfinance==0.2.39
requests==2.31.0
feedparser==6.0.10
beautifulsoup4==4.12.2
pyyaml==6.0
pandas==2.1.4
