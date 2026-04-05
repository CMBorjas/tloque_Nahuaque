"""
Nahua — Desktop Pet for Tloque Nahuaque
A draggable, always-on-top pet that floats on your entire screen.
Click to open a chat window. Right-click to quit.

Features:
  - Random idle chatter with speech bubbles
  - Discord notification listener (shows DMs & mentions as bubbles)
  - Chat window connected to the orchestrator backend
"""

import sys
import os
import random
import threading
import asyncio
import requests

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit, QFrame, QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QCursor, QColor, QFont

# ── Config ──────────────────────────────────────────────────────────
API_BASE = "http://localhost:8000"
PET_IMAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pics", "robot.png")
PET_SIZE = 100

# Try loading Discord token from .env
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

DISCORD_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")

# ── Idle personality lines ──────────────────────────────────────────
IDLE_LINES = [
    "All systems nominal.",
    "CPU looks chill right now.",
    "I wonder if any containers crashed...",
    "Did you check the audit logs today?",
    "Inventory levels looking good!",
    "I'm keeping an eye on things.",
    "Docker is my best friend.",
    "Need me? Just click!",
    "Running self-diagnostics... all clear!",
    "Have you backed up recently?",
    "I live on your desktop now. Deal with it.",
    "Ollama and I are besties.",
    "Fun fact: I never sleep.",
    "Beep boop... just kidding.",
    "Another day, another container to watch.",
    "Plot twist: I AM the orchestrator.",
    "You look like you could use a deploy.",
    "*stretches robot arms*",
    "I should learn more intents...",
    "Pro tip: try asking me about system health!",
]

GREETING_LINES = [
    "Hey! Nahua online and ready!",
    "Systems booting... just kidding, I'm instant!",
    "Your favorite desktop buddy is here!",
    "Nahua reporting for duty!",
]


# ── Signal bridges ──────────────────────────────────────────────────
class Signals(QObject):
    chat_reply = pyqtSignal(str)
    discord_notification = pyqtSignal(str, str)  # (author, message)
    show_bubble = pyqtSignal(str)


SIGNALS = Signals()


# ── Discord listener (runs in background thread) ───────────────────
def _run_discord_listener():
    """Connects to Discord as a bot and emits notifications for DMs and mentions."""
    if not DISCORD_TOKEN:
        return

    try:
        import discord
    except ImportError:
        print("discord.py not installed — Discord notifications disabled.")
        return

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Discord listener connected as {client.user}")
        SIGNALS.show_bubble.emit(f"Discord connected as {client.user.name}!")

    @client.event
    async def on_message(message):
        if message.author.bot:
            return

        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mention = (
            client.user is not None
            and not is_dm
            and client.user in message.mentions
        )

        if is_dm or is_mention:
            author = str(message.author.display_name)
            content = message.content[:200]
            SIGNALS.discord_notification.emit(author, content)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(client.start(DISCORD_TOKEN))
    except Exception as e:
        print(f"Discord listener error: {e}")


# ── Speech Bubble Widget ───────────────────────────────────────────
class SpeechBubble(QWidget):
    """A floating speech bubble that appears above the pet."""

    def __init__(self, parent_pet):
        super().__init__(None)
        self.parent_pet = parent_pet
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.inner = QFrame(self)
        self.inner.setStyleSheet("""
            QFrame {
                background: #1e2a36;
                border: 1px solid #3d9a82;
                border-radius: 12px;
                padding: 8px 12px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        self.inner.setGraphicsEffect(shadow)

        self.text_label = QLabel(self.inner)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("""
            color: #e8edf4; font-size: 12px; font-family: Helvetica, sans-serif;
            background: transparent; border: none; padding: 0;
        """)
        self.text_label.setMaximumWidth(220)

        inner_layout = QVBoxLayout(self.inner)
        inner_layout.setContentsMargins(10, 8, 10, 8)
        inner_layout.addWidget(self.text_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.inner)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._fade_out)

    def show_message(self, text, duration=5000, is_discord=False):
        if is_discord:
            self.inner.setStyleSheet("""
                QFrame {
                    background: #2a1e36;
                    border: 1px solid #7289da;
                    border-radius: 12px;
                    padding: 8px 12px;
                }
            """)
        else:
            self.inner.setStyleSheet("""
                QFrame {
                    background: #1e2a36;
                    border: 1px solid #3d9a82;
                    border-radius: 12px;
                    padding: 8px 12px;
                }
            """)

        self.text_label.setText(text)
        self.text_label.adjustSize()
        self.inner.adjustSize()
        self.adjustSize()
        self._reposition()
        self.show()
        self.raise_()
        self._hide_timer.start(duration)

    def _reposition(self):
        pet_pos = self.parent_pet.pos()
        pet_w = self.parent_pet.width()
        bw = self.width()
        bh = self.height()
        x = pet_pos.x() + (pet_w // 2) - (bw // 2)
        y = pet_pos.y() - bh - 8
        # Keep on screen
        screen = QApplication.primaryScreen().geometry()
        if x < 10:
            x = 10
        if x + bw > screen.width() - 10:
            x = screen.width() - bw - 10
        if y < 10:
            y = pet_pos.y() + self.parent_pet.height() + 8
        self.move(x, y)

    def _fade_out(self):
        self.hide()


# ── Chat Window ────────────────────────────────────────────────────
class ChatWindow(QWidget):
    def __init__(self, pet_x, pet_y):
        super().__init__()
        self.setWindowTitle("Nahua")
        self.setFixedSize(360, 440)
        self.move(pet_x - 370, pet_y - 200)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
        )
        self.setStyleSheet("""
            QWidget { background: #161d26; color: #e8edf4;
                      font-family: Helvetica, sans-serif; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(38)
        header.setStyleSheet("background: #3d9a82;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 0, 8, 0)
        title = QLabel("Nahua")
        title.setStyleSheet("color: #0a0f0d; font-weight: bold; font-size: 14px;")
        close_btn = QPushButton("X")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #0a0f0d; font-weight: bold;
                          font-size: 13px; border: none; border-radius: 4px; }
            QPushButton:hover { background: #2d7a66; }
        """)
        close_btn.clicked.connect(self.close)
        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(close_btn)
        layout.addWidget(header)

        # Messages
        self.messages = QTextEdit()
        self.messages.setReadOnly(True)
        self.messages.setStyleSheet("""
            QTextEdit {
                background: #1a222d; color: #e8edf4; border: none;
                font-size: 13px; padding: 10px;
            }
            QScrollBar:vertical {
                width: 6px; background: #1a222d;
            }
            QScrollBar::handle:vertical {
                background: #2a3544; border-radius: 3px; min-height: 20px;
            }
        """)
        layout.addWidget(self.messages)

        # Composer
        composer = QFrame()
        composer.setStyleSheet("background: #0f1419; padding: 6px;")
        c_layout = QHBoxLayout(composer)
        c_layout.setContentsMargins(6, 6, 6, 6)
        c_layout.setSpacing(6)

        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Ask Nahua...")
        self.entry.setStyleSheet("""
            QLineEdit {
                background: #1c2530; color: #e8edf4; border: 1px solid #2a3544;
                border-radius: 8px; padding: 8px 10px; font-size: 13px;
            }
            QLineEdit:focus { border-color: #3d9a82; }
        """)
        self.entry.returnPressed.connect(self._send)

        self.send_btn = QPushButton("Go")
        self.send_btn.setFixedWidth(48)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: #3d9a82; color: #0a0f0d; font-weight: bold;
                font-size: 12px; border: none; border-radius: 8px; padding: 8px;
            }
            QPushButton:hover { background: #2d7a66; }
            QPushButton:disabled { background: #2a3544; color: #8b9aad; }
        """)
        self.send_btn.clicked.connect(self._send)

        c_layout.addWidget(self.entry)
        c_layout.addWidget(self.send_btn)
        layout.addWidget(composer)

        self.busy = False
        self._append_bot("Hey! Ask me anything — containers, health, inventory...")

        # Connect API signal
        SIGNALS.chat_reply.connect(self._receive)

    def _append_user(self, text):
        self.messages.append(
            f'<div style="text-align:right; margin-bottom:4px;">'
            f'<span style="color:#8b9aad; font-size:10px;">You</span><br>'
            f'<span style="color:#8bc4ff;">{text}</span></div>'
        )

    def _append_bot(self, text):
        escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        escaped = escaped.replace("\n", "<br>")
        self.messages.append(
            f'<div style="margin-bottom:4px;">'
            f'<span style="color:#8b9aad; font-size:10px;">Nahua</span><br>'
            f'<span style="color:#5ee8c5;">{escaped}</span></div>'
        )

    def _send(self):
        text = self.entry.text().strip()
        if not text or self.busy:
            return
        self.entry.clear()
        self._append_user(text)
        self.busy = True
        self.send_btn.setEnabled(False)
        self.entry.setEnabled(False)
        threading.Thread(target=self._call_api, args=(text,), daemon=True).start()

    def _call_api(self, text):
        try:
            r = requests.post(
                f"{API_BASE}/api/chat",
                json={"message": text},
                timeout=120,
            )
            r.raise_for_status()
            data = r.json()
            reply = data.get("agent_reply", "No reply.")
        except Exception as e:
            reply = f"Error: {e}"
        SIGNALS.chat_reply.emit(reply)

    def _receive(self, reply):
        self._append_bot(reply)
        self.busy = False
        self.send_btn.setEnabled(True)
        self.entry.setEnabled(True)
        self.entry.setFocus()


# ── Desktop Pet ────────────────────────────────────────────────────
class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Load pet image
        pixmap = QPixmap(PET_IMAGE).scaled(
            PET_SIZE, PET_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.label = QLabel(self)
        self.label.setPixmap(pixmap)
        self.label.setFixedSize(pixmap.size())
        self.setFixedSize(pixmap.size())

        # Position bottom-right
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - PET_SIZE - 50, screen.height() - PET_SIZE - 100)

        # Drag state
        self._drag_pos = QPoint()
        self._dragged = False

        # Child windows
        self.chat_win = None
        self.bubble = SpeechBubble(self)

        # ── Bounce animation ──
        self._bounce_dir = -1
        self._bounce_step = 0
        self._bounce_timer = QTimer(self)
        self._bounce_timer.timeout.connect(self._bounce)
        self._bounce_timer.start(500)

        # ── Random idle chatter ──
        self._idle_timer = QTimer(self)
        self._idle_timer.timeout.connect(self._idle_chatter)
        self._idle_timer.start(25000)  # every ~25 seconds

        # ── Greeting ──
        QTimer.singleShot(1500, self._greet)

        # ── Connect Discord notifications ──
        SIGNALS.discord_notification.connect(self._on_discord_notification)
        SIGNALS.show_bubble.connect(lambda text: self.bubble.show_message(text, 5000))

        # Start Discord listener
        if DISCORD_TOKEN:
            t = threading.Thread(target=_run_discord_listener, daemon=True)
            t.start()

    def _greet(self):
        line = random.choice(GREETING_LINES)
        self.bubble.show_message(line, 4000)

    def _idle_chatter(self):
        # Don't interrupt Discord notifications or chat
        if self.bubble.isVisible():
            return
        line = random.choice(IDLE_LINES)
        self.bubble.show_message(line, 5000)

    def _on_discord_notification(self, author, content):
        preview = content[:120] + ("..." if len(content) > 120 else "")
        self.bubble.show_message(
            f"Discord from {author}:\n{preview}",
            duration=8000,
            is_discord=True,
        )

    def _bounce(self):
        pos = self.pos()
        self._bounce_step += 1
        if self._bounce_step >= 4:
            self._bounce_step = 0
            self._bounce_dir *= -1
        self.move(pos.x(), pos.y() + self._bounce_dir * 2)

    # ── Mouse events ──
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._dragged = False
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._dragged = True
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self._dragged:
            self._open_chat()
        event.accept()

    def contextMenuEvent(self, event):
        QApplication.quit()

    def _open_chat(self):
        if self.chat_win and self.chat_win.isVisible():
            self.chat_win.raise_()
            self.chat_win.activateWindow()
            return
        self.chat_win = ChatWindow(self.x(), self.y())
        self.chat_win.show()


# ── Main ───────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    pet = DesktopPet()
    pet.show()
    print("Nahua is alive! Drag to move, click to chat, right-click to quit.")
    if DISCORD_TOKEN:
        print("Discord notifications enabled.")
    else:
        print("No DISCORD_BOT_TOKEN found — Discord notifications disabled.")
        print("Set it in .env or environment to enable.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
