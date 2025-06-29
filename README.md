# 🤖 Telegram AI Bot

一个功能丰富的Telegram AI聊天机器人，支持智能对话、语音处理、图片分析等多种功能。

## ✨ 主要功能

- 🤖 **智能对话** - GPT驱动的自然语言对话
- 🗣️ **语音处理** - 语音转文字并智能回复
- 🖼️ **图片分析** - 图像内容识别和描述
- 🌐 **多语翻译** - 支持多种语言互译
- 🧮 **数学计算** - 基础数学运算
- 📊 **用户统计** - 个人使用数据分析
- ⚙️ **个性设置** - 自定义聊天偏好

## 🚀 快速开始

### 1. 环境要求

- Python 3.9+
- Telegram Bot Token
- OpenAI API Key

### 2. 安装部署

```bash
# 克隆项目
git clone <your-repo-url>
cd telegram_ai_bot

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥

# 运行机器人
python main.py