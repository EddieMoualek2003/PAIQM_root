import sys
import os
import json
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QObject
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QMovie

from .game_launcher import game_launcher_main, game_verifier_main


class Card(QFrame):
    cardClicked = pyqtSignal(str)

    def __init__(self, game_info: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setMinimumHeight(160)
        self._game_id = game_info["id"]

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        # Icon
        self.icon_label = QLabel()
        self._pixmap = None

        if "icon" in game_info:
            icon_path = os.path.join(os.path.dirname(__file__), game_info["icon"])
            icon_path = os.path.normpath(icon_path)

            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                self._pixmap = pixmap
                self.update_icon_size()
            else:
                self.icon_label.setText("[no icon]")

        self.icon_label.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.icon_label)

        # Title
        title = QLabel(game_info["name"])
        title.setObjectName("CardTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 14pt;
            font-weight: bold;
            color: #860b67;
        """)
        lay.addWidget(title)

        # Optional description
        if "description" in game_info:
            desc = QLabel(game_info["description"])
            desc.setWordWrap(True)
            desc.setAlignment(Qt.AlignCenter)
            desc.setObjectName("CardDescription")
            desc.setStyleSheet("""
                font-size: 14pt;
                font-weight: bold;
                color: #333333;
            """)
            lay.addWidget(desc)

        # Button
        self.button = QPushButton("Open")
        self.button.setObjectName("CardButton")
        self.button.setCursor(Qt.PointingHandCursor)
        lay.addWidget(self.button, alignment=Qt.AlignCenter)

        # Re-emit click
        self.button.clicked.connect(lambda _checked=False: self.cardClicked.emit(self._game_id))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_icon_size()

    def update_icon_size(self):
        if self._pixmap:
            window = self.window()
            if window:
                size = int(max(32, window.height() // 3))
            else:
                size = 64
            scaled = self._pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(scaled)


class HeaderBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HeaderBar")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(12)

        title = QLabel("PAIQM")
        title.setObjectName("AppTitle")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search games…")

        updates = QPushButton("Check Updates")
        updates.setObjectName("SecondaryButton")

        lay.addWidget(title)
        lay.addSpacing(8)
        lay.addWidget(self.search, 2)
        lay.addStretch(1)
        lay.addWidget(updates)


class Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        h = QLabel("Filters")
        h.setObjectName("SectionTitle")
        lay.addWidget(h)

        lay.addWidget(QLabel("• Level"))
        lay.addWidget(QLabel("• Learning Time"))
        lay.addWidget(QLabel("• Watson Support"))
        lay.addStretch(1)


class ContentArea(QFrame):
    def __init__(self, parent=None, on_card_clicked=None):
        super().__init__(parent)
        self.setObjectName("ContentArea")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; }")
        outer.addWidget(scroll)

        # Container inside scroll area
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(20)
        scroll.setWidget(container)

        # Load game data
        games_path = os.path.join(os.path.dirname(__file__), "data", "games.json")
        with open(games_path, "r", encoding="utf-8") as f:
            games = json.load(f)

        # Add cards
        for idx, game in enumerate(games):
            r, c = divmod(idx, 3)
            card = Card(game)
            card.setFixedHeight(400)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            if on_card_clicked is not None:
                card.cardClicked.connect(on_card_clicked)
            grid.addWidget(card, r, c)

        # Stretch columns evenly
        for i in range(3):
            grid.setColumnStretch(i, 1)


# Worker for background verification
class GameVerifierWorker(QObject):
    finished = pyqtSignal(str)

    def __init__(self, game_id):
        super().__init__()
        self.game_id = game_id

    def run(self):
        game_verifier_main(self.game_id)
        self.finished.emit(self.game_id)


# Splash screen window
class SplashScreen(QWidget):
    def __init__(self, gif_path, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        self.movie = QMovie(gif_path)
        label.setMovie(self.movie)
        self.movie.start()

        self.resize(self.movie.frameRect().size())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PAIQM Launcher")
        self.resize(1280, 820)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # Top header
        self.header = HeaderBar()
        root.addWidget(self.header)

        # Body
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(12)
        root.addLayout(body, 1)

        self.sidebar = Sidebar()
        self.sidebar.setFixedWidth(300)

        self.content = ContentArea(on_card_clicked=self.launch_game)

        body.addWidget(self.sidebar, 0)
        body.addWidget(self.content, 1)

        self.setCentralWidget(central)

    def launch_game(self, game_id: str):
        print(f"Launching: {game_id}")

        gif_path = os.path.join(os.path.dirname(__file__), "assets", "loading.gif")
        self.splash = SplashScreen(gif_path)
        self.splash.show()

        # Background thread for verification
        self.thread = QThread()
        self.worker = GameVerifierWorker(game_id)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # When done: close splash + run game
        self.worker.finished.connect(self.on_verifier_finished)

        self.thread.start()

    def on_verifier_finished(self, game_id: str):
        self.splash.close()
        if game_id == "quantum-dice":
            game_launcher_main("quantum-dice")
        else:
            QMessageBox.information(self, "Launch Game", f"No launcher linked for {game_id}")


def load_theme(app):
    qss_path = os.path.join(os.path.dirname(__file__), "theme.qss")
    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            qss = f.read()
        base_dir = os.path.dirname(qss_path)
        qss = qss.replace("assets/", os.path.join(base_dir, "assets/").replace("\\", "/"))
        app.setStyleSheet(qss)
    except FileNotFoundError:
        print(f"Error Loading Style from {qss_path}")


def main():
    app = QApplication(sys.argv)
    load_theme(app)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
