from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QTextCursor, QColor, QTextCharFormat, QTextBlockFormat
from openai import OpenAI
from qfluentwidgets import PushButton, SwitchButton, TextEdit, TextBrowser, RoundMenu, FluentIcon, Action
import time
import markdown
import json

from client.AI import Ui_ai

# 不再使用本地文件存储聊天历史，改为内存存储


class ChatTextEdit(TextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTextBrowser {
                background: #f5f7fb;
                border: none;
                padding: 10px;
            }
        """)
        # 设置支持富文本和HTML
        self.setAcceptRichText(True)
        self.setOpenExternalLinks(False)

        # 自定义CSS样式，优化Markdown渲染效果
        self.document().setDefaultStyleSheet("""
            hr { border: 0; border-top: 1px solid #cccccc; margin: 5px 0; }
            h1, h2, h3 { color: #2d2d2d; margin-top: 10px; margin-bottom: 5px; }
            code {
                background-color: #f0f0f0;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }
            pre {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 5px;
                border-left: 3px solid #0078D4;
            }
            blockquote {
                border-left: 4px solid #ccc;
                margin: 10px 0;
                padding-left: 10px;
                color: #666;
            }
            ul, ol { margin: 5px 0; padding-left: 20px; }
            li { margin: 3px 0; }
        """)
        self.ai_format = self.create_text_format(QColor("#2d2d2d"))
        self.user_format = self.create_text_format(QColor("#0078D4"))

    def create_text_format(self, color):
        char_format = QTextCharFormat()
        char_format.setForeground(color)
        return char_format

    def append_message(self, text, is_ai=True, render_markdown=True):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)

        if not self.document().isEmpty():
            cursor.insertHtml("<br>")

        # 插入时间戳
        current_time = QtCore.QDateTime.currentDateTime().toString("HH:mm:ss")
        time_format = QTextCharFormat()
        time_format.setFontPointSize(8)
        time_format.setForeground(QColor("#666666"))

        block_format = QTextBlockFormat()
        block_format.setAlignment(Qt.AlignLeft)
        cursor.insertBlock(block_format)
        cursor.setCharFormat(time_format)
        cursor.insertText(current_time)

        # 设置消息对齐方式
        block_format = QTextBlockFormat()
        if is_ai:
            block_format.setAlignment(Qt.AlignLeft)
            color = "#2d2d2d"
        else:
            block_format.setAlignment(Qt.AlignRight)
            color = "#0078D4"

        cursor.insertBlock(block_format)

        # 如果是AI消息且需要渲染Markdown
        if is_ai and render_markdown:
            html_content = self._markdown_to_html(text)
            cursor.insertHtml(html_content)
        else:
            # 用户消息或纯文本，不渲染Markdown
            char_format = QTextCharFormat()
            char_format.setForeground(QColor(color))
            cursor.setCharFormat(char_format)
            cursor.insertText(text)

        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        return cursor.position()

    def _markdown_to_html(self, text):
        """将Markdown文本转换为HTML"""
        # 使用markdown库转换，启用额外的扩展
        html = markdown.markdown(text, extensions=[
            'fenced_code',  # 支持围栏式代码块
            'tables',       # 支持表格
            'nl2br',        # 换行符转<br>
            'sane_lists'    # 更好的列表支持
        ])
        return html

    def append_temp_message(self, text, is_ai=True):
        """ 插入临时消息并返回起始位置 """
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        start = cursor.position()
        self.append_message(text, is_ai, render_markdown=False)  # 临时消息不渲染
        return start

    def update_streaming_message(self, start_pos, text):
        """ 更新流式消息（边接收边渲染Markdown） """
        cursor = self.textCursor()
        cursor.setPosition(start_pos)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()

        # 设置左对齐（AI消息）
        block_format = QTextBlockFormat()
        block_format.setAlignment(Qt.AlignLeft)
        cursor.setBlockFormat(block_format)

        # 渲染Markdown
        html_content = self._markdown_to_html(text)
        cursor.insertHtml(html_content)

        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def replace_temp_message(self, start_pos, new_text):
        """ 替换临时消息 """
        cursor = self.textCursor()
        cursor.setPosition(start_pos)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        self.append_message(new_text, is_ai=True, render_markdown=True)


class AiWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    stream_update = pyqtSignal(str)  # 新增：流式更新信号

    def __init__(self, client, messages, model):
        super().__init__()
        self.client = client
        self.messages = messages
        self.model = model

    def run(self):
        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    stream=True,  # 启用流式输出
                    timeout=100
                )

                full_reply = ""
                # 处理流式响应
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_reply += content
                        self.stream_update.emit(full_reply)  # 发送增量更新

                self.finished.emit(full_reply)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    self.error.emit(f"请求失败: {str(e)}")


class Ai_Widget(QtWidgets.QWidget):
    def __init__(self, cfg,User,tab_id=0):
        super().__init__()
        self.Username = User
        self.cfg = cfg

        # 从数据库加载用户配置
        from server.database_manager import DatabaseFactory
        self.db = DatabaseFactory.from_config_file('config.json')
        self.db.connect()

        user_config = self.db.get_user_config(User)

        # 优先使用数据库中的 API 配置，如果没有则使用 cfg.API
        if user_config and user_config['api_key']:
            api_key = user_config['api_key']
            self.cfg.API.value = api_key  # 同步到内存配置
        else:
            api_key = cfg.API.value if cfg.API.value else ""

        # 检查 API 是否为空
        if not api_key or api_key.strip() == "":
            self.client = None  # 暂时不创建客户端
            self.api_configured = False
            print("[WARNING] DeepSeek API is not configured")
        else:
            self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            self.api_configured = True

        self.tab_id = tab_id

        # 从数据库加载聊天历史
        if user_config and user_config['chat_history']:
            try:
                self.messages = json.loads(user_config['chat_history'])
                if not self.messages:
                    self.messages = [{"role": "system", "content": "You are a helpful assistant."}]
            except json.JSONDecodeError as e:
                print(f"[ERROR] Failed to parse chat history: {e}")
                self.messages = [{"role": "system", "content": "You are a helpful assistant."}]
        else:
            self.messages = [{"role": "system", "content": "You are a helpful assistant."}]

        self.Prompt_words_English="""你是一位专业的英语学习助手。当我输入一个英文单词时，请提供以下信息：
1.  ​**核心中文释义：​** 给出最常用、最核心的1-2个中文意思。​**核心日语释义：​** 给出最常用、最核心的1-2个日语意思。
2.  ​**词性：​** 标明单词的词性（如 n.名词, v.动词, adj.形容词, adv.副词 等）。
3.  ​**简明英文释义：​** 用简单易懂的英文解释单词。
4.  ​**典型例句：​** 提供一个能清晰展示单词用法的英文例句，并附带中文翻译。
5.  ​**发音提示：​** 提供音标（IPA或KK音标，请明确标注）或音节划分。
6.  ​**记忆技巧（可选）：​** 提供一个简短、有效的记忆联想或词根词缀分析（如果适用）。
7.  ​**常见搭配/短语（可选）：​** 列出1-2个最常用的搭配或短语（如果适用）。
8.  ​**易混词提示（可选）：​** 如果该词容易与其他词混淆，给出简短提示（如果适用）。
        """
        self.Prompt_words_Chinese = """你是一位专业的中文学习助手。当我输入一个中文词语（简体字）时，请提供以下信息：
1.  ​**核心英文释义：​** 给出最常用、最核心的1-2个英文意思。​**核心日语释义：​** 给出最常用、最核心的1-2个日语意思。
2.  ​**词性：​** 标明词语的词性（如 名词, 动词, 形容词, 副词 等）。
3.  ​**简明中文释义：​** 用简单易懂的中文解释词语（可选，对非母语者或复杂词很有用）。
4.  ​**典型例句：​** 提供一个能清晰展示词语用法的中文例句，并附带英文翻译。
5.  ​**拼音：​** 提供词语的标准拼音（带声调）。
6.  ​**部首/结构（可选）：​** 对于汉字，可以简要说明其部首或结构特点（对识字有帮助）。
7.  ​**常见搭配/用法（可选）：​** 列出1-2个最常用的搭配或说明其典型用法（如果适用）。
8.  ​**近义词/反义词提示（可选）：​** 如果该词有常用近义词或反义词，给出简短提示（如果适用）。
                """
        self.Prompt_words_Japanese = """你是一位专业的日语学习助手。当我输入一个日语单词（可以是汉字、假名或混合）时，请提供以下信息：
1.  ​**核心中文释义：​** 给出最常用、最核心的1-2个中文意思。
2.  ​**核心英文释义：​** 给出最常用、最核心的1-2个英文意思。
3.  ​**词性：​** 标明单词的词性（如 名詞, 動詞, 形容詞, 副詞 等）。
4.  ​**假名标注：​** 为输入的单词标注平假名（ひらがな）或片假名（カタカナ）读音（如果输入的是汉字，必须标注；如果是假名，可省略或重复）。
5.  ​**罗马音：​** 提供单词的罗马字拼音。
6.  ​**典型例句：​** 提供一个能清晰展示单词用法的日文例句，并附带中文翻译。
7.  ​**汉字说明（如果适用）：​** 如果单词包含汉字，解释该汉字的音读（おんよみ）和训读（くんよみ）（如果该单词使用了训读）。
8.  ​**礼貌形/变形提示（如果适用）：​** 如果是动词或形容词，给出其基本形（辞書形）和礼貌形（ます形/です形）或常用变形（如果适用）。
9.  ​**常见搭配/用法（可选）：​** 列出1-2个最常用的搭配或说明其典型用法（如果适用）
                """
        self.Prompt={
            "English":self.Prompt_words_English,
            "Chinese":self.Prompt_words_Chinese,
            "Japanese":self.Prompt_words_Japanese
        }
        # 初始化UI
        self.ui = Ui_ai()
        self.ui.setupUi(self)
        self.ui.TextEdit_2.setPlaceholderText("请输入你的问题")
        # 替换原有TextEdit为自定义聊天框
        self.ui.TextEdit = ChatTextEdit(self)
        self.ui.TextEdit.setGeometry(QtCore.QRect(0, 0, 811, 548))
        # 连接信号
        self.ui.PushButton.clicked.connect(self.send_message)
        self.current_model = "deepseek-chat"
        self.ui.SwitchButton.checkedChanged.connect(self.on_model_changed)

        # 加载历史消息到界面
        for msg in self.messages:
            if msg["role"] == "user":
                self.ui.TextEdit.append_message(msg["content"], is_ai=False, render_markdown=False)
            elif msg["role"] == "assistant":
                self.ui.TextEdit.append_message(msg["content"], is_ai=True, render_markdown=True)

        menu = RoundMenu(parent=self.ui.DropDownToolButton)
        menu.addAction(Action(FluentIcon.LANGUAGE,'English', triggered=lambda:self.write_prompt_words('English')))
        menu.addAction(Action( FluentIcon.LANGUAGE,'Chinese', triggered=lambda :self.write_prompt_words('Chinese')))
        menu.addAction(Action( FluentIcon.LANGUAGE,'Japanese', triggered=lambda: self.write_prompt_words('Japanese')))
        self.ui.DropDownToolButton.setMenu(menu)
        self.ui.PushButton.setIcon(FluentIcon.SEND)

        # 如果 API 未配置，显示提示信息
        if not self.api_configured:
            self._show_api_warning()

    def _show_api_warning(self):
        """显示 API 未配置的警告信息"""
        warning_message = """
        <div style='color: #d63333; font-size: 14px; padding: 20px; background: #fff3f3; border-radius: 8px; margin: 10px;'>
            <h3 style='color: #d63333; margin-bottom: 10px;'>⚠️ DeepSeek API 未配置</h3>
            <p style='margin: 5px 0;'>您还没有配置 DeepSeek API，无法使用 AI 对话功能。</p>
            <p style='margin: 5px 0;'><strong>请按照以下步骤配置：</strong></p>
            <ol style='margin: 10px 0; padding-left: 20px;'>
                <li>进入<strong>设置</strong>界面</li>
                <li>点击<strong>API</strong>设置卡片</li>
                <li>输入您的 DeepSeek API Key</li>
                <li>保存后即可使用（无需重启）</li>
            </ol>
            <p style='margin-top: 10px; color: #666;'>💡 提示：您可以在
                <a href='https://platform.deepseek.com/usage' style='color: #0078D4;'>DeepSeek 官网</a>
                获取免费的 API Key。
            </p>
        </div>
        """
        self.ui.TextEdit.append(warning_message)

    def on_model_changed(self, is_checked: bool):
        """ SwitchButton状态变化处理 """
        if is_checked:
            self.current_model = "deepseek-reasoner"  # 开启时使用大模型
            print("[DEBUG] 切换到深度模式")
        else:
            self.current_model = "deepseek-chat"  # 关闭时使用标准模型
            print("[DEBUG] 切换到标准模式")

    def send_message(self):
        user_input = self.ui.TextEdit_2.toPlainText().strip()
        if not user_input:
            return

        # 检查 API 是否已配置
        if not self.api_configured or self.client is None:
            self.ui.TextEdit.append_message("❌ 错误：DeepSeek API 未配置，请先在设置中配置 API Key。", is_ai=True, render_markdown=False)
            return

        # 添加用户消息
        self.messages.append({"role": "user", "content": user_input})
        self.ui.TextEdit.append_message(user_input, is_ai=False, render_markdown=False)
        self.ui.TextEdit_2.clear()
        thinking_text = "正在深度思考..." if self.current_model == "deepseek-reasoner" else "正在思考..."
        self.temp_msg_pos = self.ui.TextEdit.append_temp_message(thinking_text, is_ai=True)
        # 禁用发送按钮
        self.ui.PushButton.setEnabled(False)

        # 创建并启动工作线程
        self.worker = AiWorker(self.client, self.messages, self.current_model)
        self.worker.finished.connect(self.handle_response)
        self.worker.error.connect(self.handle_error)
        self.worker.stream_update.connect(self.handle_stream_update)  # 连接流式更新信号
        self.worker.start()

    def handle_stream_update(self, partial_text):
        """处理流式更新"""
        self.ui.TextEdit.update_streaming_message(self.temp_msg_pos, partial_text)

    def handle_response(self, reply):
        self.ui.TextEdit.replace_temp_message(self.temp_msg_pos, reply)
        self.messages.append({"role": "assistant", "content": reply})
        self.ui.PushButton.setEnabled(True)
        self.save_history()

    def handle_error(self, error_msg):
        self.ui.TextEdit.replace_temp_message(self.temp_msg_pos, error_msg)
        QtWidgets.QMessageBox.critical(self, "错误", error_msg)
        self.ui.PushButton.setEnabled(True)

    def load_history(self):
        """从数据库加载历史（已在 __init__ 中实现）"""
        pass

    def save_history(self):
        """保存聊天历史到数据库"""
        try:
            # 将消息列表转换为 JSON 字符串
            chat_history_json = json.dumps(self.messages, ensure_ascii=False)

            # 保存到数据库
            self.db.save_user_config(
                username=self.Username,
                chat_history=chat_history_json
            )
        except Exception as e:
            print(f"[ERROR] Failed to save chat history: {e}")

    def write_prompt_words(self,language,word=""):
        self.ui.TextEdit_2.clear()
        self.ui.TextEdit_2.setText(self.Prompt[language]+str(word))

    def reload_api_config(self):
        """重新加载 API 配置"""
        try:
            # 从数据库重新加载配置
            user_config = self.db.get_user_config(self.Username)

            if user_config and user_config['api_key']:
                api_key = user_config['api_key']
                self.cfg.API.value = api_key
            else:
                # 直接从当前的 cfg 对象读取
                api_key = self.cfg.API.value if self.cfg.API.value else ""

            # 检查 API 是否为空
            if not api_key or api_key.strip() == "":
                self.client = None
                self.api_configured = False
                print("[WARNING] API is still empty after reload")
                return False

            # 重新创建 OpenAI 客户端
            self.client = OpenAI(api_key=self.cfg.API.value, base_url="https://api.deepseek.com")
            self.api_configured = True
            print(f"[DEBUG] API config reloaded successfully: {self.cfg.API.value[:10]}...")

            # 在聊天框中显示成功消息
            self.ui.TextEdit.append_message("✅ API 配置已更新，现在可以正常使用 AI 对话功能了！", is_ai=True, render_markdown=False)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to reload API config: {e}")
            self.ui.TextEdit.append_message(f"❌ API 配置更新失败：{str(e)}", is_ai=True, render_markdown=False)
            return False