"""
UI module for QuickMeaning.
Provides a modern dark-themed, fixed-size command-palette popup using PySide6.
Supports mouse-drag repositioning and clickable Esc-to-close badge.
Clears previous query on reopen for a fresh lookup experience.
"""

from PySide6.QtCore import Qt, QThread, Signal, QPoint
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QLabel, QFrame, QGraphicsDropShadowEffect, QApplication,
    QProgressBar, QScrollArea
)
from PySide6.QtGui import QFont, QColor, QKeyEvent, QCursor, QMouseEvent

from config import (
    APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT,
    COLOR_BG, COLOR_CARD, COLOR_BORDER, COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED, COLOR_ACCENT, COLOR_PRONUNCIATION, COLOR_ERROR
)
from dictionary import DictionaryService, LookupResult


class LookupWorker(QThread):
    """Background worker thread for fetching dictionary results without freezing UI."""
    result_ready = Signal(LookupResult)

    def __init__(self, service: DictionaryService, word: str):
        super().__init__()
        self.service = service
        self.word = word

    def run(self):
        result = self.service.lookup(self.word)
        self.result_ready.emit(result)


class QuickMeaningWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.dict_service = DictionaryService()
        self.worker = None

        self._drag_pos = QPoint()
        self._is_dragging = False

        self._init_window_flags()
        self._init_ui()
        self._center_on_screen()

    def _init_window_flags(self):
        """Configure frameless, translucent, always-on-top window with fixed dimensions."""
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle(APP_NAME)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

    def _init_ui(self):
        # Outer layout for shadow padding
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)

        # Container Frame (Card)
        self.container = QFrame(self)
        self.container.setObjectName("Container")
        self.container.setStyleSheet(f"""
            QFrame#Container {{
                background-color: {COLOR_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 14px;
            }}
        """)

        # Drop Shadow Effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

        # Main Layout inside Card (Pinned to Top)
        self.card_layout = QVBoxLayout(self.container)
        self.card_layout.setContentsMargins(16, 12, 16, 12)
        self.card_layout.setSpacing(8)

        # Header / Search Input Row
        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        search_row.setSpacing(10)

        # Search Icon Label
        self.icon_label = QLabel("🔍")
        self.icon_label.setStyleSheet("font-size: 16px; background: transparent;")
        search_row.addWidget(self.icon_label, 0, Qt.AlignVCenter)

        # Input Field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a word...")
        self.input_field.setFont(QFont("Segoe UI", 12))
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {COLOR_TEXT_PRIMARY};
                selection-background-color: {COLOR_ACCENT};
                selection-color: #11111b;
            }}
            QLineEdit::placeholder {{
                color: {COLOR_TEXT_MUTED};
            }}
        """)
        self.input_field.returnPressed.connect(self._on_search_triggered)
        search_row.addWidget(self.input_field, 1, Qt.AlignVCenter)

        # Shortcut Hint Badge (Clickable, compact Esc to close button)
        self.hint_label = QLabel("Esc to close")
        self.hint_label.setFont(QFont("Segoe UI", 8))
        self.hint_label.setFixedHeight(24)
        self.hint_label.setCursor(Qt.PointingHandCursor)
        self.hint_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLOR_CARD};
                color: {COLOR_TEXT_MUTED};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 3px 8px;
            }}
            QLabel:hover {{
                background-color: {COLOR_BORDER};
                color: {COLOR_TEXT_PRIMARY};
            }}
        """)
        self.hint_label.mousePressEvent = self._on_hint_clicked
        search_row.addWidget(self.hint_label, 0, Qt.AlignVCenter)

        self.card_layout.addLayout(search_row)

        # Separator Line (Always visible below search input)
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setStyleSheet(f"background-color: {COLOR_BORDER}; border: none; min-height: 1px; max-height: 1px;")
        self.separator.setVisible(True)
        self.card_layout.addWidget(self.separator)

        # Progress / Loading Indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate mode
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: transparent;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_ACCENT};
                border-radius: 1px;
            }}
        """)
        self.progress_bar.setVisible(False)
        self.card_layout.addWidget(self.progress_bar)

        # Scrollable Area for Results (Occupies all remaining vertical space)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                margin: 0px 0px 0px 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLOR_BORDER};
                min-height: 24px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COLOR_TEXT_MUTED};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

        # Result Display Area Widget inside Scroll Area
        self.result_container = QWidget()
        self.result_container.setStyleSheet("background: transparent;")
        self.result_layout = QVBoxLayout(self.result_container)
        self.result_layout.setContentsMargins(2, 4, 6, 4)
        self.result_layout.setSpacing(6)

        # Title Row (Word & Meta)
        self.word_title_label = QLabel()
        self.word_title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.word_title_label.setStyleSheet(f"color: {COLOR_ACCENT}; background: transparent;")
        self.word_title_label.setVisible(False)
        self.result_layout.addWidget(self.word_title_label)

        self.meta_label = QLabel()
        self.meta_label.setFont(QFont("Segoe UI", 9, QFont.DemiBold))
        self.meta_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; background: transparent;")
        self.meta_label.setVisible(False)
        self.result_layout.addWidget(self.meta_label)

        # Pronunciation Label
        self.pronunciation_label = QLabel()
        self.pronunciation_label.setFont(QFont("Segoe UI", 9))
        self.pronunciation_label.setStyleSheet(f"color: {COLOR_PRONUNCIATION}; background: transparent;")
        self.pronunciation_label.setVisible(False)
        self.result_layout.addWidget(self.pronunciation_label)

        # Definition Body Label
        self.definition_label = QLabel()
        self.definition_label.setFont(QFont("Segoe UI", 10))
        self.definition_label.setWordWrap(True)
        self.definition_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; background: transparent; line-height: 1.4;")
        self.definition_label.setVisible(False)
        self.result_layout.addWidget(self.definition_label)

        # Error Message Label
        self.error_label = QLabel()
        self.error_label.setFont(QFont("Segoe UI", 10, QFont.Medium))
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet(f"color: {COLOR_ERROR}; background: transparent; padding: 4px 0;")
        self.error_label.setVisible(False)
        self.result_layout.addWidget(self.error_label)

        self.scroll_area.setWidget(self.result_container)
        self.scroll_area.setVisible(True)
        
        # Add scroll area with stretch factor 1 to fill all remaining height
        self.card_layout.addWidget(self.scroll_area, 1)

        outer_layout.addWidget(self.container)

    def _center_on_screen(self):
        """Center the popup window on the screen containing the mouse cursor."""
        screen = QApplication.screenAt(QCursor.pos())
        if not screen:
            screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = screen_geometry.x() + (screen_geometry.width() - WINDOW_WIDTH) // 2
        y = screen_geometry.y() + (screen_geometry.height() // 4)
        self.move(x, y)

    def _reset_to_empty_state(self):
        """Reset search field and hide previous result labels for a fresh lookup."""
        self.input_field.clear()
        self.progress_bar.setVisible(False)
        self.word_title_label.setVisible(False)
        self.meta_label.setVisible(False)
        self.pronunciation_label.setVisible(False)
        self.definition_label.setVisible(False)
        self.error_label.setVisible(False)
        self.scroll_area.verticalScrollBar().setValue(0)

    def show_and_focus(self):
        """Show popup with clean empty state and focus input field."""
        self._reset_to_empty_state()
        self.show()
        self.raise_()
        self.activateWindow()
        self.input_field.setFocus()

    def hide_popup(self):
        """Hide the popup window."""
        self.hide()

    def _on_hint_clicked(self, event: QMouseEvent):
        """Handle click on 'Esc to close' badge."""
        if event.button() == Qt.LeftButton:
            self.hide_popup()

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press to start dragging the frameless window."""
        if event.button() == Qt.LeftButton:
            child = self.childAt(event.position().toPoint())
            # Do not initiate drag if user clicked interactive controls
            if child not in (self.input_field, self.hint_label):
                self._is_dragging = True
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse movement during drag."""
        if self._is_dragging and (event.buttons() & Qt.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """End mouse dragging."""
        self._is_dragging = False
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle Esc key to hide popup."""
        if event.key() == Qt.Key_Escape:
            self.hide_popup()
        else:
            super().keyPressEvent(event)

    def _on_search_triggered(self):
        word = self.input_field.text().strip()
        if not word:
            return

        # Show loading state
        self.progress_bar.setVisible(True)

        # Start lookup in worker thread
        if self.worker and self.worker.isRunning():
            self.worker.terminate()

        self.worker = LookupWorker(self.dict_service, word)
        self.worker.result_ready.connect(self._on_result_received)
        self.worker.start()

    def _on_result_received(self, result: LookupResult):
        self.progress_bar.setVisible(False)

        if result.error_message:
            self._display_error(result.error_message)
        else:
            self._display_result(result)

    def _display_error(self, message: str):
        self.scroll_area.verticalScrollBar().setValue(0)

        self.word_title_label.setVisible(False)
        self.meta_label.setVisible(False)
        self.pronunciation_label.setVisible(False)
        self.definition_label.setVisible(False)

        self.error_label.setText(message)
        self.error_label.setVisible(True)

    def _display_result(self, result: LookupResult):
        self.scroll_area.verticalScrollBar().setValue(0)
        self.error_label.setVisible(False)

        # Word Header (Preserves user's original query)
        self.word_title_label.setText(result.word)
        self.word_title_label.setVisible(True)

        # Meta: Language & Part of Speech
        meta_parts = []
        if result.language:
            meta_parts.append(result.language)
        if result.part_of_speech:
            meta_parts.append(result.part_of_speech)

        meta_text = " · ".join(meta_parts)
        if meta_text:
            self.meta_label.setText(meta_text)
            self.meta_label.setVisible(True)
        else:
            self.meta_label.setVisible(False)

        # Pronunciation
        if result.pronunciation:
            self.pronunciation_label.setText(f"Pronunciation: {result.pronunciation}")
            self.pronunciation_label.setVisible(True)
        else:
            self.pronunciation_label.setVisible(False)

        # Definition Body
        self.definition_label.setText(result.definition or "")
        self.definition_label.setVisible(True)
