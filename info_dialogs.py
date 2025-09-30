# info_dialogs.py

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser, 
                             QDialogButtonBox, QWidget)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

# --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА AboutDialog НА НАДЕЖНУЮ ВЕРСИЮ С QLABEL (v16.0-final) ---
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        
        # Убираем кнопку "?"
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(15)
        
        # Иконка
        icon_label = QLabel(self)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ico", "GUIUXConstrSpec.png")
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            icon_label.setPixmap(pixmap.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        main_layout.addWidget(icon_label)

        # Правая часть с текстом
        right_widget = QWidget(self)
        right_layout = QVBoxLayout(right_widget)
        
        title_label = QLabel("GUIUXConstrSpec v2.0.4", self)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 5px;")
        
        # ИСПОЛЬЗУЕМ QLABEL ВМЕСТО QTEXTBROWSER
        description_label = QLabel(self)
        description_label.setTextFormat(Qt.RichText) # Разрешаем HTML-теги
        description_label.setWordWrap(True) # Включаем перенос слов
        description_label.setOpenExternalLinks(True) # Делаем ссылки кликабельными

        # Загружаем HTML
        about_html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "about.html")
        if os.path.exists(about_html_path):
            with open(about_html_path, 'r', encoding='utf-8') as f:
                description_label.setText(f.read())
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok, self)
        button_box.accepted.connect(self.accept)

        right_layout.addWidget(title_label)
        right_layout.addWidget(description_label)
        right_layout.addStretch() # Добавляем растяжитель, чтобы кнопка была внизу
        right_layout.addWidget(button_box, 0, Qt.AlignRight)
        
        main_layout.addWidget(right_widget)
        
        # Устанавливаем минимальную ширину для правой части, чтобы текст не сжимался
        right_widget.setMinimumWidth(350)
# --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА AboutDialog НА НАДЕЖНУЮ ВЕРСИЮ С QLABEL (v16.0-final) ---


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Справка")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)
        
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        
        # ЗАГРУЖАЕМ HTML ИЗ ФАЙЛА
        help_html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "help.html")
        if os.path.exists(help_html_path):
            with open(help_html_path, 'r', encoding='utf-8') as f:
                text_browser.setHtml(f.read())
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)

        layout.addWidget(text_browser)
        layout.addWidget(button_box)