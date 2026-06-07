[README.md](https://github.com/user-attachments/files/28676835/README.md)
# AI 排版助手

用自然语言指令一键排版 Word 文档。输入如"一级标题黑体三号加粗居中，正文宋体小四首行缩进2字符"，AI 自动识别标题和正文并完成排版。

## 功能

- AI 阅读理解文档内容，自动区分章标题、节标题、正文
- 支持字体、字号、加粗、对齐、缩进、行距等排版操作
- 内置毕业论文、公文、英文论文等常用模板
- 桌面版 (PyQt5) + 网页版 (Streamlit)

## 快速开始

### 桌面版

```bash
pip install -r requirements.txt
python main.py
```

### 网页版

```bash
pip install streamlit
streamlit run app.py
```

浏览器自动打开 `localhost:8501`。

## 获取 API Key

本工具使用 [小米 MiMo](https://mimo.xiaomi.com) 大模型 API，注册后免费获取 Key：

1. 访问小米 MiMo 开放平台
2. 注册账号，创建 API Key
3. 填入工具的「API 密钥」输入框

也兼容其他 OpenAI 格式 API（DeepSeek、通义千问等），只需修改 API 地址。

## 打包为 exe

```bash
pip install pyinstaller pillow
python create_icon.py
pyinstaller --onefile --windowed --icon=icon.ico --name="AI排版助手" main.py
```

生成的 `dist/AI排版助手.exe` 可直接发给别人使用，无需安装 Python。

## 部署到网站（免费）

1. 将代码推送到 GitHub
2. 访问 [Streamlit Cloud](https://share.streamlit.io)
3. 用 GitHub 账号登录，选择本仓库
4. 入口文件填 `app.py`，点击 Deploy
5. 获得免费网址 `xxx.streamlit.app`

## 项目结构

```
├── main.py            # 桌面版 (PyQt5)
├── app.py             # 网页版 (Streamlit)
├── llm_client.py      # API 调用
├── doc_formatter.py   # 排版引擎 (python-docx)
├── prompts.py         # AI 提示词
├── create_icon.py     # 图标生成
├── requirements.txt   # 依赖
└── build.bat          # 一键打包脚本
```

## 使用示例

输入指令：

```
一级标题黑体小三号加粗居中，二级标题黑体四号加粗左对齐，正文宋体小四号首行缩进2字符1.5倍行距
```

AI 会自动识别文档中的标题和正文，分别应用对应格式。

## 技术栈

- **GUI**: PyQt5 (桌面版) / Streamlit (网页版)
- **排版引擎**: python-docx
- **AI**: 小米 MiMo v2.5 (兼容 OpenAI API 格式)
