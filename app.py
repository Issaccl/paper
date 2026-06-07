"""AI 排版助手 - 网页版 (Streamlit)"""
import json
import tempfile
from pathlib import Path

import streamlit as st

from doc_formatter import DocFormatter
from llm_client import DEFAULT_BASE_URL, call_llm
from prompts import SYSTEM_PROMPT

st.set_page_config(page_title="AI 排版助手", page_icon="📄", layout="centered")

st.title("AI 排版助手")
st.caption("上传 Word 文档，用自然语言指令一键排版")

# ── 侧边栏配置 ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("API 设置")
    api_key = st.text_input("API Key", type="password", placeholder="粘贴你的 Key")
    api_url = st.text_input("API 地址", value=DEFAULT_BASE_URL)
    model = st.text_input("模型", value="mimo-v2.5")

    st.divider()
    st.markdown("""
**使用说明**
1. 填入 API 密钥
2. 上传 .docx 文件
3. 输入排版指令
4. 点击「开始排版」
5. 下载排版后的文件
""")

# ── 主界面 ────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    uploaded = st.file_uploader("上传 Word 文档", type=["docx"])
with col2:
    st.selectbox("常用模板", [
        "自定义",
        "毕业论文 - 全套",
        "毕业论文 - 一级标题",
        "毕业论文 - 二级标题",
        "毕业论文 - 正文",
        "公文格式",
        "英文论文",
    ], key="tpl")

TEMPLATES = {
    "毕业论文 - 全套": "一级标题黑体小三号加粗居中，二级标题黑体四号加粗左对齐，正文宋体小四号首行缩进2字符1.5倍行距",
    "毕业论文 - 一级标题": "把一级标题改成黑体小三号，加粗，居中",
    "毕业论文 - 二级标题": "把二级标题改成黑体四号，加粗，左对齐",
    "毕业论文 - 正文": "把正文改成宋体小四号，首行缩进2字符，1.5倍行距",
    "公文格式": "正文仿宋三号，首行缩进2字符，行距28磅",
    "英文论文": "正文Times New Roman 12pt, double spacing, left aligned, first line indent 0.5 inch",
}

default_instruction = TEMPLATES.get(st.session_state.get("tpl", ""), "")
instruction = st.text_area(
    "排版指令",
    value=default_instruction,
    placeholder="例如：一级标题黑体小三号加粗居中，正文宋体小四号首行缩进2字符1.5倍行距",
    height=100,
)

# ── 执行 ──────────────────────────────────────────────────────────────
if st.button("开始排版", type="primary", use_container_width=True):
    if not api_key:
        st.error("请在左侧填入 API 密钥")
    elif not uploaded:
        st.error("请上传 Word 文档")
    elif not instruction.strip():
        st.error("请输入排版指令")
    else:
        with st.spinner("AI 正在分析文档并排版..."):
            try:
                # 保存上传文件到临时目录
                tmp_dir = tempfile.mkdtemp()
                in_path = Path(tmp_dir) / uploaded.name
                in_path.write_bytes(uploaded.read())

                # 提取文档结构
                formatter = DocFormatter(str(in_path))
                paragraphs = formatter.extract_paragraphs()
                st.info(f"文档共 {len(paragraphs)} 个段落，正在调用 AI...")

                # 调用 AI
                result = call_llm(
                    api_key=api_key,
                    user_instruction=instruction.strip(),
                    system_prompt=SYSTEM_PROMPT,
                    paragraphs=paragraphs,
                    base_url=api_url,
                    model=model,
                )

                # 执行排版
                formatter.execute(result)
                out_name = Path(uploaded.name).stem + "_排版.docx"
                out_path = Path(tmp_dir) / out_name
                formatter.save_as(str(out_path))

                # 提供下载
                st.success(f"排版完成！共修改 {len(result)} 个段落")
                st.download_button(
                    label="下载排版后的文件",
                    data=out_path.read_bytes(),
                    file_name=out_name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary",
                    use_container_width=True,
                )

                # 显示 AI 返回的指令详情
                with st.expander("查看排版详情"):
                    for item in result:
                        st.json(item)

            except Exception as e:
                st.error(f"排版失败: {e}")
