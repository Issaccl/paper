import json
import sys
from pathlib import Path

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QPlainTextEdit, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)

from doc_formatter import DocFormatter
from llm_client import DEFAULT_BASE_URL, call_llm
from prompts import SYSTEM_PROMPT

CONFIG_PATH = Path(__file__).parent / "config.json"

TEMPLATES = [
    ("自定义", ""),
    ("毕业论文 - 全套", "一级标题黑体小三号加粗居中，二级标题黑体四号加粗左对齐，正文宋体小四号首行缩进2字符1.5倍行距"),
    ("毕业论文 - 一级标题", "把一级标题改成黑体小三号，加粗，居中"),
    ("毕业论文 - 二级标题", "把二级标题改成黑体四号，加粗，左对齐"),
    ("毕业论文 - 正文", "把正文改成宋体小四号，首行缩进2字符，1.5倍行距"),
    ("公文格式", "正文仿宋三号，首行缩进2字符，行距28磅"),
    ("英文论文", "正文Times New Roman 12pt, double spacing, left aligned, first line indent 0.5 inch"),
]

# ── 样式表 ────────────────────────────────────────────────────────────

STYLE = """
QMainWindow {
    background-color: #f5f5f7;
}
QLabel {
    color: #1d1d1f;
    font-size: 13px;
}
QLabel#titleLabel {
    font-size: 22px;
    font-weight: bold;
    color: #1d1d1f;
}
QLabel#subtitleLabel {
    font-size: 12px;
    color: #86868b;
}
QLineEdit, QComboBox, QPlainTextEdit {
    background-color: white;
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    color: #1d1d1f;
    selection-background-color: #0071e3;
}
QLineEdit:focus, QComboBox:on, QPlainTextEdit:focus {
    border: 2px solid #0071e3;
}
QComboBox::drop-down {
    border: none;
    width: 30px;
}
QComboBox QAbstractItemView {
    background-color: white;
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    selection-background-color: #e8f0fe;
    selection-color: #1d1d1f;
    padding: 4px;
}
QPushButton#pickBtn {
    background-color: white;
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 13px;
    color: #1d1d1f;
    font-weight: bold;
}
QPushButton#pickBtn:hover {
    background-color: #f0f0f2;
    border-color: #0071e3;
}
QPushButton#runBtn {
    background-color: #0071e3;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 12px;
    font-size: 15px;
    font-weight: bold;
}
QPushButton#runBtn:hover {
    background-color: #0077ed;
}
QPushButton#runBtn:pressed {
    background-color: #006edb;
}
QPushButton#runBtn:disabled {
    background-color: #d2d2d7;
    color: #86868b;
}
QPlainTextEdit#logBox {
    background-color: #1d1d1f;
    color: #e0e0e0;
    border: none;
    border-radius: 8px;
    padding: 12px;
    font-family: "Consolas", "Microsoft YaHei", monospace;
    font-size: 12px;
}
QFrame#card {
    background-color: white;
    border: 1px solid #d2d2d7;
    border-radius: 12px;
    padding: 16px;
}
"""


def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def save_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2),
                           encoding="utf-8")


class WorkThread(QThread):
    log = pyqtSignal(str)
    done = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, api_key, base_url, model, docx_path, instruction):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.docx_path = docx_path
        self.instruction = instruction

    def run(self):
        try:
            self.log.emit(">> 提取文档内容...")
            formatter = DocFormatter(self.docx_path)
            paragraphs = formatter.extract_paragraphs()
            self.log.emit(f">> 共 {len(paragraphs)} 个段落，发送给 AI 分析...")

            result = call_llm(
                api_key=self.api_key,
                user_instruction=self.instruction,
                system_prompt=SYSTEM_PROMPT,
                paragraphs=paragraphs,
                base_url=self.base_url,
                model=self.model,
            )
            self.log.emit(f">> AI 返回 {len(result)} 条排版指令")
            for item in result[:15]:
                self.log.emit(f"   {item}")
            if len(result) > 15:
                self.log.emit(f"   ... 还有 {len(result) - 15} 条")

            self.log.emit(">> 执行排版...")
            formatter.execute(result)

            out_path = str(
                Path(self.docx_path).with_stem(
                    Path(self.docx_path).stem + "_排版"
                )
            )
            formatter.save_as(out_path)
            self.done.emit(out_path)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 排版助手")
        self.setMinimumSize(680, 640)
        icon_path = Path(__file__).parent / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.docx_path = None
        self._init_ui()
        self._load_config()

    def _init_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # ── 标题 ──
        title = QLabel("AI 排版助手")
        title.setObjectName("titleLabel")
        subtitle = QLabel("用自然语言指令，一键排版 Word 文档")
        subtitle.setObjectName("subtitleLabel")
        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)
        main_layout.addSpacing(4)

        # ── API 设置卡片 ──
        api_card = self._make_card()
        api_layout = QVBoxLayout(api_card)
        api_layout.setSpacing(10)

        api_label = QLabel("API 设置")
        api_label.setStyleSheet("font-weight:bold; font-size:14px;")
        api_layout.addWidget(api_label)

        row1 = QHBoxLayout()
        row1.setSpacing(8)
        row1.addWidget(QLabel("地址"))
        self.url_combo = QComboBox()
        self.url_combo.setEditable(True)
        self.url_combo.addItems([
            DEFAULT_BASE_URL,
            "https://api.deepseek.com/v1",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ])
        self.url_combo.setMinimumWidth(360)
        row1.addWidget(self.url_combo, 1)
        api_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        row2.addWidget(QLabel("密钥"))
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.Password)
        self.key_input.setPlaceholderText("粘贴你的 API Key")
        row2.addWidget(self.key_input, 1)
        api_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.setSpacing(8)
        row3.addWidget(QLabel("模型"))
        self.model_input = QLineEdit()
        self.model_input.setText("mimo-v2.5")
        row3.addWidget(self.model_input, 1)
        api_layout.addLayout(row3)

        main_layout.addWidget(api_card)

        # ── 文档选择卡片 ──
        doc_card = self._make_card()
        doc_layout = QVBoxLayout(doc_card)
        doc_layout.setSpacing(10)

        doc_label = QLabel("文档")
        doc_label.setStyleSheet("font-weight:bold; font-size:14px;")
        doc_layout.addWidget(doc_label)

        file_row = QHBoxLayout()
        file_row.setSpacing(8)
        self.doc_btn = QPushButton("选择文件")
        self.doc_btn.setObjectName("pickBtn")
        self.doc_btn.clicked.connect(self._pick_file)
        self.doc_label = QLabel("拖放或点击选择 .docx 文件")
        self.doc_label.setStyleSheet("color: #86868b;")
        file_row.addWidget(self.doc_btn)
        file_row.addWidget(self.doc_label, 1)
        doc_layout.addLayout(file_row)

        main_layout.addWidget(doc_card)

        # ── 指令卡片 ──
        instr_card = self._make_card()
        instr_layout = QVBoxLayout(instr_card)
        instr_layout.setSpacing(10)

        instr_header = QHBoxLayout()
        instr_label = QLabel("排版指令")
        instr_label.setStyleSheet("font-weight:bold; font-size:14px;")
        self.tpl_combo = QComboBox()
        self.tpl_combo.setMinimumWidth(180)
        for name, _ in TEMPLATES:
            self.tpl_combo.addItem(name)
        self.tpl_combo.currentIndexChanged.connect(self._apply_template)
        instr_header.addWidget(instr_label)
        instr_header.addStretch()
        instr_header.addWidget(QLabel("模板:"))
        instr_header.addWidget(self.tpl_combo)
        instr_layout.addLayout(instr_header)

        self.instr_input = QPlainTextEdit()
        self.instr_input.setPlaceholderText(
            "输入自然语言排版指令，例如：\n"
            "一级标题黑体小三号加粗居中，正文宋体小四号首行缩进2字符1.5倍行距"
        )
        self.instr_input.setMaximumHeight(100)
        instr_layout.addWidget(self.instr_input)

        main_layout.addWidget(instr_card)

        # ── 开始按钮 ──
        self.run_btn = QPushButton("开始排版")
        self.run_btn.setObjectName("runBtn")
        self.run_btn.clicked.connect(self._run)
        main_layout.addWidget(self.run_btn)

        # ── 日志 ──
        log_card = self._make_card()
        log_layout = QVBoxLayout(log_card)
        log_layout.setSpacing(6)
        log_label = QLabel("日志")
        log_label.setStyleSheet("font-weight:bold; font-size:14px;")
        log_layout.addWidget(log_label)
        self.log_box = QPlainTextEdit()
        self.log_box.setObjectName("logBox")
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(120)
        log_layout.addWidget(self.log_box)
        main_layout.addWidget(log_card)

    def _make_card(self):
        frame = QWidget()
        frame.setObjectName("card")
        frame.setStyleSheet(
            "QWidget#card{background:white; border:1px solid #d2d2d7; border-radius:12px;}"
        )
        return frame

    # ── actions ──────────────────────────────────────────────────────

    def _pick_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 Word 文档", "",
            "Word 文档 (*.docx);;所有文件 (*)"
        )
        if path:
            self.docx_path = path
            name = Path(path).name
            self.doc_label.setText(name)
            self.doc_label.setStyleSheet("color: #1d1d1f; font-weight:bold;")
            self._log(f"已选择: {name}")

    def _apply_template(self, idx):
        if 0 < idx < len(TEMPLATES):
            self.instr_input.setPlainText(TEMPLATES[idx][1])

    def _run(self):
        if not self.docx_path:
            self._log("[错误] 请先选择文档")
            return
        api_key = self.key_input.text().strip()
        if not api_key:
            self._log("[错误] 请填写 API 密钥")
            return
        instruction = self.instr_input.toPlainText().strip()
        if not instruction:
            self._log("[错误] 请输入排版指令")
            return

        base_url = self.url_combo.currentText().strip()
        model = self.model_input.text().strip()
        self._save_config(base_url, api_key, model)

        self.run_btn.setEnabled(False)
        self.run_btn.setText("排版中...")
        self._log(f"\n{'='*40}")
        self._log(f"开始排版: {Path(self.docx_path).name}")
        self._log(f"指令: {instruction[:60]}...")

        self.worker = WorkThread(api_key, base_url, model,
                                 self.docx_path, instruction)
        self.worker.log.connect(self._log)
        self.worker.done.connect(self._on_done)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_done(self, path):
        self.run_btn.setEnabled(True)
        self.run_btn.setText("开始排版")
        self._log(f"\n[完成] 已保存到: {Path(path).name}")

    def _on_error(self, msg):
        self.run_btn.setEnabled(True)
        self.run_btn.setText("开始排版")
        self._log(f"[错误] {msg}")

    def _log(self, text):
        self.log_box.appendPlainText(text)

    # ── config ───────────────────────────────────────────────────────

    def _save_config(self, url, key, model):
        cfg = load_config()
        cfg["base_url"] = url
        cfg["api_key"] = key
        cfg["model"] = model
        save_config(cfg)

    def _load_config(self):
        cfg = load_config()
        if "base_url" in cfg:
            self.url_combo.setEditText(cfg["base_url"])
        if "api_key" in cfg:
            self.key_input.setText(cfg["api_key"])
        if "model" in cfg:
            self.model_input.setText(cfg["model"])


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    app.setStyleSheet(STYLE)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
