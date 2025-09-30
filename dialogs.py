# dialogs.py
import os, json
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, 
                             QDialogButtonBox, QMessageBox, QGroupBox, QSpinBox, QSlider,
                             QComboBox, QPushButton, QColorDialog, QHBoxLayout, QLabel,
                             QListWidget, QListWidgetItem, QSplitter, QWidget, QFileDialog, QTabWidget, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

# --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА SettingsDialog С ВОССТАНОВЛЕННОЙ ЛОГИКОЙ (v14.10-fix) ---
class SettingsDialog(QDialog):
    # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА __init__ ДЛЯ ПОДДЕРЖКИ ВКЛАДОК (v3.0) ---
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("Настройки") # <-- Новое название
        self.setMinimumWidth(500)

        main_layout = QVBoxLayout(self)
        
        # СОЗДАЕМ ВИДЖЕТ ВКЛАДОК
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # ВКЛАДКА 1: СТИЛИ
        styles_widget = QWidget()
        styles_layout = QVBoxLayout(styles_widget)
        self.active_widgets = self._create_style_groupbox("Стиль активного элемента (выбран)")
        styles_layout.addWidget(self.active_widgets['group_box'])
        self.inactive_widgets = self._create_style_groupbox("Стиль неактивного элемента")
        styles_layout.addWidget(self.inactive_widgets['group_box'])
        self.relations_widgets = self._create_relations_style_groupbox("Стили связей")
        styles_layout.addWidget(self.relations_widgets['group_box'])
        styles_layout.addStretch()
        self.tabs.addTab(styles_widget, "Внешний вид")

        # ВКЛАДКА 2: РАБОЧАЯ ОБЛАСТЬ
        workspace_widget = QWidget()
        workspace_layout = QFormLayout(workspace_widget)
        self.workspace_path_edit = QLineEdit()
        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(30)
        browse_btn.clicked.connect(self._browse_workspace_folder)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.workspace_path_edit)
        path_layout.addWidget(browse_btn)
        
        workspace_layout.addRow("Папка с проектами (модулями):", path_layout)
        self.tabs.addTab(workspace_widget, "Рабочая область")

        self.populate_ui_from_settings()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_and_accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
# --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА __init__ ДЛЯ ПОДДЕРЖКИ ВКЛАДОК (v3.0) ---

    def _create_style_groupbox(self, title):
        group_box = QGroupBox(title)
        layout = QFormLayout(group_box)
        
        widgets = {
            'line_width': QSpinBox(),
            'line_color_btn': QPushButton("Выбрать..."),
            'line_style_combo': QComboBox(),
            'fill_color_btn': QPushButton("Выбрать..."),
            'fill_opacity_slider': QSlider(Qt.Horizontal)
        }

        widgets['line_width'].setRange(1, 20)
        
        styles = {"Сплошная": Qt.SolidLine, "Штрих": Qt.DashLine, "Точка": Qt.DotLine, 
                  "Штрих-точка": Qt.DashDotLine, "Штрих-точка-точка": Qt.DashDotDotLine}
        for name, style in styles.items():
            widgets['line_style_combo'].addItem(name, style)

        widgets['fill_opacity_slider'].setRange(0, 100)
        
        layout.addRow("Толщина линии:", widgets['line_width'])
        layout.addRow("Цвет линии:", widgets['line_color_btn'])
        layout.addRow("Стиль линии:", widgets['line_style_combo'])
        layout.addRow("Цвет заливки:", widgets['fill_color_btn'])
        layout.addRow("Прозрачность заливки (%):", widgets['fill_opacity_slider'])
        
        widgets['line_color_btn'].clicked.connect(self._choose_color_via_dialog)
        widgets['fill_color_btn'].clicked.connect(self._choose_color_via_dialog)

        widgets['group_box'] = group_box
        return widgets

# --- НАЧАЛО: ФИНАЛЬНЫЙ ФИКС ДЛЯ НАСТРОЕК СВЯЗЕЙ (v2.0.6) ---
    def _create_relations_style_groupbox(self, title):
        group_box = QGroupBox(title)
        form_layout = QFormLayout(group_box)
        widgets = {
            'highlight_primary_btn': QPushButton("Выбрать..."),
            'highlight_secondary_btn': QPushButton("Выбрать..."),
        }
        form_layout.addRow("Цвет осн. элемента:", widgets['highlight_primary_btn'])
        form_layout.addRow("Цвет связ. элемента:", widgets['highlight_secondary_btn'])
        widgets['highlight_primary_btn'].clicked.connect(self._choose_color_via_dialog)
        widgets['highlight_secondary_btn'].clicked.connect(self._choose_color_via_dialog)
        widgets['group_box'] = group_box
        return widgets
    # --- КОНЕЦ: ФИНАЛЬНЫЙ ФИКС ДЛЯ НАСТРОЕК СВЯЗЕЙ (v2.0.6) ---
    
# --- НАЧАЛО: НОВЫЙ МЕТОД ДЛЯ ВЫБОРА ПАПКИ (v3.0) ---
    def _browse_workspace_folder(self):
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку с проектами", self.workspace_path_edit.text())
        if directory:
            self.workspace_path_edit.setText(directory)
    # --- КОНЕЦ: НОВЫЙ МЕТОД ДЛЯ ВЫБОРА ПАПКИ (v3.0) ---

    def _update_button_color(self, button, color_hex):
        button.setStyleSheet(f"background-color: {color_hex};")
        button.setProperty("color_hex", color_hex)

    def _choose_color_via_dialog(self):
        button = self.sender()
        if not button: return

        current_color_hex = button.property("color_hex") or "#ffffff"
        color = QColorDialog.getColor(QColor(current_color_hex), self, "Выберите цвет")
        if color.isValid():
            self._update_button_color(button, color.name())
    
    # --- НАЧАЛО: ФИНАЛЬНЫЙ ФИКС ДЛЯ НАСТРОЕК СВЯЗЕЙ (v2.0.6) ---
    def populate_ui_from_settings(self):
        self._populate_group(self.active_widgets, self.settings_manager.get_style("active"))
        self._populate_group(self.inactive_widgets, self.settings_manager.get_style("inactive"))
        
        # Загружаем настройки связей
        relations_settings = self.settings_manager.get_style("relations")
        self._update_button_color(self.relations_widgets['highlight_primary_btn'], relations_settings.get('highlight_color_primary'))
        self._update_button_color(self.relations_widgets['highlight_secondary_btn'], relations_settings.get('highlight_color_secondary'))

        self.workspace_path_edit.setText(self.settings_manager.settings.get("workspace_path", ""))
    # --- КОНЕЦ: ФИНАЛЬНЫЙ ФИКС ДЛЯ НАСТРОЕК СВЯЗЕЙ (v2.0.6) ---

    def _populate_group(self, widgets, settings):
        widgets['line_width'].setValue(settings['line_width'])
        
        index = widgets['line_style_combo'].findData(settings['line_style'])
        if index != -1:
            widgets['line_style_combo'].setCurrentIndex(index)
        
        widgets['fill_opacity_slider'].setValue(settings['fill_opacity'])
        
        self._update_button_color(widgets['line_color_btn'], settings['line_color'])
        self._update_button_color(widgets['fill_color_btn'], settings['fill_color'])

# --- НАЧАЛО: ФИНАЛЬНЫЙ ФИКС ДЛЯ НАСТРОЕК СВЯЗЕЙ (v2.0.6) ---
    def save_and_accept(self):
        active_settings = self._collect_group_settings(self.active_widgets)
        inactive_settings = self._collect_group_settings(self.inactive_widgets)
        
        # Собираем и сохраняем настройки связей
        relations_settings = {
            "highlight_color_primary": self.relations_widgets['highlight_primary_btn'].property("color_hex"),
            "highlight_color_secondary": self.relations_widgets['highlight_secondary_btn'].property("color_hex"),
        }
        self.settings_manager.set_style("relations", relations_settings)

        self.settings_manager.settings["workspace_path"] = self.workspace_path_edit.text()
        self.settings_manager.set_style("active", active_settings)
        self.settings_manager.set_style("inactive", inactive_settings)
        self.settings_manager.save_settings()
        self.accept()
    # --- КОНЕЦ: ФИНАЛЬНЫЙ ФИКС ДЛЯ НАСТРОЕК СВЯЗЕЙ (v2.0.6) ---

    def _collect_group_settings(self, widgets):
        return {
            "line_width": widgets['line_width'].value(),
            "line_style": widgets['line_style_combo'].currentData(),
            "line_color": widgets['line_color_btn'].property("color_hex"),
            "fill_opacity": widgets['fill_opacity_slider'].value(),
            "fill_color": widgets['fill_color_btn'].property("color_hex")
        }
# --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА SettingsDialog С ВОССТАНОВЛЕННОЙ ЛОГИКОЙ (v14.10-fix) ---

# --- НАЧАЛО: НОВЫЙ КЛАСС ДЛЯ ДИАЛОГА СОХРАНЕНИЯ ШАБЛОНА (v13.1) ---
class SaveTemplateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Сохранить как шаблон")
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)

        form_layout.addRow("Имя шаблона:", self.name_edit)
        form_layout.addRow("Описание:", self.description_edit)
        
        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def validate_and_accept(self):
        """ПРОВЕРЯЕТ, ЧТО ИМЯ НЕ ПУСТОЕ, ПЕРЕД ЗАКРЫТИЕМ."""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Имя шаблона не может быть пустым.")
            return
        self.accept()

    def get_data(self):
        """ВОЗВРАЩАЕТ ВВЕДЕННЫЕ ДАННЫЕ."""
        return {
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip()
        }
# --- КОНЕЦ: НОВЫЙ КЛАСС ДЛЯ ДИАЛОГА СОХРАНЕНИЯ ШАБЛОНА (v13.1) ---



# --- НАЧАЛО: НОВЫЙ КЛАСС ДЛЯ ДИАЛОГА ВЫБОРА ШАБЛОНА (v13.2) ---
class SelectTemplateDialog(QDialog):
    def __init__(self, templates_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Создать из шаблона")
        self.setMinimumSize(500, 300)

        main_layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # ЛЕВАЯ ЧАСТЬ: СПИСОК ШАБЛОНОВ
        left_layout.addWidget(QLabel("Выберите шаблон:"))
        self.list_widget = QListWidget()
        for template in templates_list:
            item = QListWidgetItem(template["name"])
            item.setData(Qt.UserRole, template) # СОХРАНЯЕМ ВСЮ ИНФОРМАЦИЮ В ЭЛЕМЕНТЕ СПИСКА
            self.list_widget.addItem(item)
        left_layout.addWidget(self.list_widget)

        # ПРАВАЯ ЧАСТЬ: ОПИСАНИЕ И КНОПКИ
        right_layout.addWidget(QLabel("Описание:"))
        self.description_display = QTextEdit()
        self.description_display.setReadOnly(True)
        right_layout.addWidget(self.description_display)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        right_layout.addWidget(button_box)

        # СОБИРАЕМ МАКЕТ
        splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget(); left_widget.setLayout(left_layout)
        right_widget = QWidget(); right_widget.setLayout(right_layout)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([200, 300])
        main_layout.addWidget(splitter)
        
        self.list_widget.currentItemChanged.connect(self.update_description)
        self.list_widget.itemDoubleClicked.connect(self.accept) # ДВОЙНОЙ КЛИК = OK

    def update_description(self, current_item, previous_item):
        """ОБНОВЛЯЕТ ОПИСАНИЕ ПРИ ВЫБОРЕ ШАБЛОНА В СПИСКЕ."""
        if not current_item: return
        template_data = current_item.data(Qt.UserRole)
        self.description_display.setText(template_data.get("description", "Нет описания."))

    def get_selected_template_id(self):
        """ВОЗВРАЩАЕТ ID ВЫБРАННОГО ШАБЛОНА."""
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole).get("id")
        return None
# --- КОНЕЦ: НОВЫЙ КЛАСС ДЛЯ ДИАЛОГА ВЫБОРА ШАБЛОНА (v13.2) ---

# --- НАЧАЛО: НОВЫЙ КЛАСС ДЛЯ ДИАЛОГА УПРАВЛЕНИЯ ШАБЛОНАМИ (v15.7) ---
class ManageTemplatesDialog(QDialog):
    def __init__(self, templates_manager, parent=None):
        super().__init__(parent)
        self.templates_manager = templates_manager
        self.setWindowTitle("Управление шаблонами")
        self.setMinimumSize(500, 350)

        main_layout = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        self.list_widget.currentItemChanged.connect(self.on_selection_change)
        main_layout.addWidget(self.list_widget)

        buttons_layout = QHBoxLayout()
        self.rename_btn = QPushButton("Переименовать...")
        self.delete_btn = QPushButton("Удалить")
        close_btn = QPushButton("Закрыть")
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.rename_btn)
        buttons_layout.addWidget(self.delete_btn)
        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(close_btn)

        self.rename_btn.clicked.connect(self.rename_selected_template)
        self.delete_btn.clicked.connect(self.delete_selected_template)
        close_btn.clicked.connect(self.accept)

        self.populate_list()
        self.on_selection_change() # Инициализация состояния кнопок

    def populate_list(self):
        """ЗАПОЛНЯЕТ СПИСОК ШАБЛОНАМИ."""
        self.list_widget.clear()
        templates_list = self.templates_manager.get_templates_list()
        for template in templates_list:
            # ОТОБРАЖАЕМ ИМЯ И ОПИСАНИЕ, ЕСЛИ ЕСТЬ
            text = template['name']
            if template['description']:
                text += f"\n  └ {template['description'][:80]}..." # Показываем часть описания
            
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, template['id']) # Храним только ID
            self.list_widget.addItem(item)
    
    def on_selection_change(self):
        """АКТИВИРУЕТ/ДЕАКТИВИРУЕТ КНОПКИ В ЗАВИСИМОСТИ ОТ ВЫБОРА."""
        is_selected = self.list_widget.currentItem() is not None
        self.rename_btn.setEnabled(is_selected)
        self.delete_btn.setEnabled(is_selected)

    def rename_selected_template(self):
        """ОТКРЫВАЕТ ДИАЛОГ ДЛЯ ПЕРЕИМЕНОВАНИЯ ШАБЛОНА."""
        current_item = self.list_widget.currentItem()
        if not current_item: return

        template_id = current_item.data(Qt.UserRole)
        template_info = self.templates_manager.templates[template_id]

        dialog = SaveTemplateDialog(self)
        dialog.name_edit.setText(template_info.get('name', ''))
        dialog.description_edit.setText(template_info.get('description', ''))
        
        if dialog.exec_() == QDialog.Accepted:
            new_data = dialog.get_data()
            self.templates_manager.rename_template(template_id, new_data['name'], new_data['description'])
            self.populate_list() # Обновляем список

    def delete_selected_template(self):
        """УДАЛЯЕТ ВЫБРАННЫЙ ШАБЛОН ПОСЛЕ ПОДТВЕРЖДЕНИЯ."""
        current_item = self.list_widget.currentItem()
        if not current_item: return
        
        template_id = current_item.data(Qt.UserRole)
        template_name = self.templates_manager.templates[template_id].get('name')

        reply = QMessageBox.question(self, "Подтверждение удаления", 
                                     f"Вы уверены, что хотите удалить шаблон '{template_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.templates_manager.delete_template(template_id)
            self.populate_list() # Обновляем список
# --- КОНЕЦ: НОВЫЙ КЛАСС ДЛЯ ДИАЛОГА УПРАВЛЕНИЯ ШАБЛОНАМИ (v15.7) ---

# --- НАЧАЛО: НОВЫЙ КЛАСС ДЛЯ ДИАЛОГА НАСТРОЙКИ СВЯЗИ (v2.1) ---
class RelationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройка связи")
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Однонаправленная (A -> Б)", "Двунаправленная (A <-> Б)"])
        
        self.description_edit = QTextEdit()
        self.description_edit.setAcceptRichText(False)
        self.description_edit.setMinimumHeight(80)

        form_layout.addRow("Тип связи:", self.type_combo)
        form_layout.addRow("Описание:", self.description_edit)
        
        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_data(self):
        relation_type = "unidirectional" if self.type_combo.currentIndex() == 0 else "bidirectional"
        return {
            "type": relation_type,
            "description": self.description_edit.toPlainText().strip()
        }

    def set_data(self, data):
        index = 1 if data.get('type') == 'bidirectional' else 0
        self.type_combo.setCurrentIndex(index)
        self.description_edit.setPlainText(data.get('description', ''))
# --- КОНЕЦ: НОВЫЙ КЛАСС ДЛЯ ДИАЛОГА НАСТРОЙКИ СВЯЗИ (v2.1) ---

# --- НАЧАЛО: НОВЫЙ КЛАСС ДЛЯ ДИАЛОГА ВСТАВКИ ССЫЛОК (v3.4) ---
class InsertLinkDialog(QDialog):
    # --- ДОБАВЛЕН СИГНАЛ ---
    link_ready_to_insert = pyqtSignal(str)
    def __init__(self, workspace_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Вставить ссылку на компонент")
        self.setMinimumSize(400, 500)

        self.workspace_path = workspace_path
        self.loaded_projects = {} # Кэш для загруженных проектов

        layout = QVBoxLayout(self)

        # Выпадающий список с файлами проектов
        self.projects_combo = QComboBox()
        layout.addWidget(self.projects_combo)

        # Дерево компонентов
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        layout.addWidget(self.tree_widget)

        # Кнопки
        buttons_layout = QHBoxLayout()
        insert_btn = QPushButton("Вставить")
        close_btn = QPushButton("Закрыть")
        buttons_layout.addStretch()
        buttons_layout.addWidget(insert_btn)
        buttons_layout.addWidget(close_btn)
        layout.addLayout(buttons_layout)

        # Подключаем сигналы
        self.projects_combo.currentIndexChanged.connect(self.on_project_selected)
        insert_btn.clicked.connect(self.on_insert_clicked)
        close_btn.clicked.connect(self.reject) # Кнопка "Закрыть" теперь закрывает окно
        close_btn.clicked.connect(self.reject)
        
        self.link_to_insert = None # Здесь будет храниться ссылка для вставки
        self._populate_projects_combo()

    def _populate_projects_combo(self):
        """Наполняет выпадающий список .json файлами из рабочей папки."""
        if not self.workspace_path or not os.path.isdir(self.workspace_path):
            self.projects_combo.addItem("Рабочая папка не задана!")
            return
        
        for filename in os.listdir(self.workspace_path):
            if filename.endswith(".json"):
                self.projects_combo.addItem(filename)

    def on_project_selected(self, index):
        """Загружает и отображает дерево для выбранного проекта."""
        self.tree_widget.clear()
        filename = self.projects_combo.itemText(index)
        
        if filename not in self.loaded_projects:
            try:
                with open(os.path.join(self.workspace_path, filename), 'r', encoding='utf-8') as f:
                    self.loaded_projects[filename] = json.load(f)
            except:
                return # Ошибка загрузки

        project_data = self.loaded_projects[filename]
        self._populate_tree_recursively(self.tree_widget.invisibleRootItem(), project_data.get('tree', {}), filename)
        self.tree_widget.expandAll()
        
    def _populate_tree_recursively(self, parent_item, children_data, filename):
        """Рекурсивно строит дерево компонентов."""
        for item_id, item_data in children_data.items():
            # Сохраняем все нужные данные в элементе дерева
            tree_item = QTreeWidgetItem(parent_item, [item_data.get('name', 'Без имени')])
            tree_item.setData(0, Qt.UserRole, {
                "id": item_id, 
                "name": item_data.get('name', 'Без имени'), 
                "filename": filename
            })
            self._populate_tree_recursively(tree_item, item_data.get('children', {}), filename)

    def on_insert_clicked(self):
        """Формирует строку-ссылку и ОТПРАВЛЯЕТ ЕЕ СИГНАЛОМ, НЕ ЗАКРЫВАЯ ОКНО."""
        selected_item = self.tree_widget.currentItem()
        if not selected_item: return
        
        # Рекурсивно строим путь
        path_parts = []
        temp_item = selected_item
        while temp_item:
            path_parts.append(temp_item.data(0, Qt.UserRole)['name'])
            temp_item = temp_item.parent()
        
        full_path = " >>> ".join(reversed(path_parts))
        data = selected_item.data(0, Qt.UserRole)
        
        self.link_to_insert = f"[{data['filename']} >>> {full_path} (ID: `{data['id'].split('-')[0]}`)]"
        self.link_ready_to_insert.emit(self.link_to_insert) # Отправляем сигнал
# --- КОНЕЦ: ЗАМЕНА InsertLinkDialog НА НЕМОДАЛЬНУЮ ВЕРСИЮ С ПОЛНЫМИ ПУТЯМИ (v3.5) ---
# --- КОНЕЦ: НОВЫЙ КЛАСС ДЛЯ ДИАЛОГА ВСТАВКИ ССЫЛОК (v3.4) ---