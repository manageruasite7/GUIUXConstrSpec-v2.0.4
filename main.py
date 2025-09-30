# main.py

import sys
import os
import json
import uuid
import copy

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QSplitter, 
                             QFrame, QTreeWidget, QTreeWidgetItem, QVBoxLayout, 
                             QPushButton, QInputDialog, QLabel, QFormLayout, QLineEdit, 
                             QTextEdit, QAction, QFileDialog, QMessageBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QComboBox, QTabWidget, QMenu, QGridLayout, 
                             QDialog, QDialogButtonBox, QTreeWidgetItemIterator, QStatusBar, QFontDialog, 
                             QGraphicsScene, QGraphicsPixmapItem, QColorDialog, QListWidget, QListWidgetItem, QStackedWidget)

from PyQt5.QtGui import QFont, QPixmap, QColor, QBrush, QPen

from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QTranslator, QTimer, pyqtSlot
# --- НАЧАЛО: ИМПОРТЫ ИЗ НОВЫХ ФАЙЛОВ ПРОЕКТА (v14.0-refactor) ---
from data_manager import DataManager
from managers import TemplatesManager, StyleSettingsManager
# --- НАЧАЛО: ИМПОРТ НОВОГО МЕНЕДЖЕРА (v3.3) ---
from managers import TemplatesManager, StyleSettingsManager, ScenariosManager
# --- КОНЕЦ: ИМПОРТ НОВОГО МЕНЕДЖЕРА (v3.3) ---
# --- НАЧАЛО: ДОБАВЛЕН ИМПОРТ InsertLinkDialog (v3.4-fix2) ---
from dialogs import (SettingsDialog, SaveTemplateDialog, SelectTemplateDialog, 
                     ManageTemplatesDialog, RelationDialog, InsertLinkDialog)
# --- КОНЕЦ: ДОБАВЛЕН ИМПОРТ InsertLinkDialog (v3.4-fix2) ---
from info_dialogs import AboutDialog, HelpDialog
from graphics_items import CanvasView, BoundRectItem
# --- КОНЕЦ: ИМПОРТЫ ИЗ НОВЫХ ФАЙЛОВ ПРОЕКТА (v14.0-refactor) ---

# --- НАЧАЛО: ВОЗВРАТ К СТАБИЛЬНОЙ ВЕРСИИ ACTIONPARAMETERWIDGET (v3.2) ---
class ActionParameterWidget(QWidget):
    parameterChanged = pyqtSignal() # ПРОСТОЙ СИГНАЛ БЕЗ АРГУМЕНТОВ

    def __init__(self, action_data, all_project_items_data, global_variables, parent=None):
        super().__init__(parent)
        self.action_data = action_data; self.all_items_data = all_project_items_data
        self.global_variables = global_variables
        self.controls = {} # Словарь для хранения ссылок на виджеты

        layout = QHBoxLayout(self); layout.setContentsMargins(5, 5, 5, 5); layout.setAlignment(Qt.AlignLeft)
        
        action_type = self.action_data.get('type'); action_name = self.action_data.get('name', '')
        params = self.action_data.get('params', {}); layout.addWidget(QLabel(f"-> {action_name}:"))

        if action_type in ["openScreen", "setFocus", "closeWindow"]:
            label_text = {"openScreen": "Экран/Диалог:", "closeWindow": "Окно:", "setFocus": "Элемент:"}.get(action_type)
            combo = QComboBox(); self.controls['target_id'] = combo
            for item in self.all_items_data.values(): combo.addItem(item['name'], item['id'])
            if params.get('target_id'):
                index = combo.findData(params['target_id']); 
                if index != -1: combo.setCurrentIndex(index)
            combo.currentIndexChanged.connect(self.parameterChanged.emit)
            layout.addWidget(QLabel(label_text)); layout.addWidget(combo)
            self._improve_combo_box_view(combo)

        elif action_type in ["toggleVisibility", "setEnabled"]:
            target_combo = QComboBox(); self.controls['target_id'] = target_combo
            for item_id, item_data in self.all_items_data.items(): target_combo.addItem(item_data['name'], item_id)
            if params.get('target_id'):
                index = target_combo.findData(params['target_id']); 
                if index != -1: target_combo.setCurrentIndex(index)
            
            op_combo = QComboBox(); self.controls['operation'] = op_combo
            items = ["Переключить", "Показать", "Скрыть"] if action_type == "toggleVisibility" else ["Переключить", "Включить", "Выключить"]
            op_combo.addItems(items)
            if params.get('operation'): op_combo.setCurrentText(params.get('operation'))

            target_combo.currentIndexChanged.connect(self.parameterChanged.emit)
            op_combo.currentTextChanged.connect(self.parameterChanged.emit)
            
            layout.addWidget(QLabel("Элемент:")); layout.addWidget(target_combo)
            layout.addWidget(op_combo)
            self._improve_combo_box_view(target_combo)
            self._improve_combo_box_view(op_combo)

        elif action_type == "setProperty":
            self.target_combo = QComboBox(); self.controls['target_id'] = self.target_combo
            for item_id, item_data in self.all_items_data.items(): self.target_combo.addItem(item_data['name'], item_id)
            if params.get('target_id'):
                index = self.target_combo.findData(params['target_id']); 
                if index != -1: self.target_combo.setCurrentIndex(index)
            
            self.prop_combo = QComboBox(); self.controls['key'] = self.prop_combo
            self.val_edit = QLineEdit(params.get('value', '')); self.controls['value'] = self.val_edit
            
            self.update_properties_combo(False)
            if params.get('key'):
                index = self.prop_combo.findText(params['key']); 
                if index != -1: self.prop_combo.setCurrentIndex(index)
                
            self.target_combo.currentIndexChanged.connect(lambda: self.update_properties_combo(True))
            self.target_combo.currentIndexChanged.connect(self.parameterChanged.emit)
            self.prop_combo.currentTextChanged.connect(self.parameterChanged.emit)
            self.val_edit.textChanged.connect(self.parameterChanged.emit)

            layout.addWidget(QLabel("Элемент:")); layout.addWidget(self.target_combo)
            layout.addWidget(QLabel("Свойство:")); layout.addWidget(self.prop_combo)
            layout.addWidget(QLabel("Значение:"))
            
            value_layout = QHBoxLayout(); value_layout.setContentsMargins(0,0,0,0); value_layout.setSpacing(2)
            value_layout.addWidget(self.val_edit)
            globals_btn = QPushButton("@"); globals_btn.setFixedSize(24, 24)
            globals_btn.clicked.connect(self.show_globals_menu)
            value_layout.addWidget(globals_btn)
            layout.addLayout(value_layout)
            self._improve_combo_box_view(self.target_combo)
            self._improve_combo_box_view(self.prop_combo)
        
        else:
            self.editor = QLineEdit(params.get('description', '')); self.controls['description'] = self.editor
            self.editor.textChanged.connect(self.parameterChanged.emit)
            layout.addWidget(self.editor)

        layout.addStretch()

    def update_properties_combo(self, should_emit_signal=True):
        self.prop_combo.clear()
        target_id = self.target_combo.currentData()
        if target_id and target_id in self.all_items_data:
            for prop in self.all_items_data[target_id].get('properties', []):
                self.prop_combo.addItem(prop.get('key'))
        
        if should_emit_signal:
            self.val_edit.clear()
            self.parameterChanged.emit()
    
    def show_globals_menu(self):
        menu = QMenu(self)
        filtered_globals = {k: v for k, v in self.global_variables.items() if k.startswith('@')}
        if not filtered_globals:
            no_vars_action = QAction("Нет доступных переменных (@...)", self); no_vars_action.setEnabled(False); menu.addAction(no_vars_action)
        else:
            for name in filtered_globals.keys():
                action = QAction(name, self)
                action.triggered.connect(lambda checked=False, var_name=name: self.insert_global_variable(var_name))
                menu.addAction(action)
        globals_btn = self.sender()
        menu.exec_(globals_btn.mapToGlobal(globals_btn.rect().bottomLeft()))

    def insert_global_variable(self, var_name):
        link_text = f"@globals.{var_name[1:]}"
        self.val_edit.setText(link_text)
        
    def _improve_combo_box_view(self, combo_box):
        combo_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        combo_box.view().setMinimumWidth(combo_box.sizeHint().width())
        combo_box.setMaxVisibleItems(25)
# --- КОНЕЦ: ВОЗВРАТ К СТАБИЛЬНОЙ ВЕРСИИ ACTIONPARAMETERWIDGET (v3.2) ---

# --- НАЧАЛО: ОБНОВЛЕНИЕ ХЕЛПЕРА ДЛЯ УВЕЛИЧЕНИЯ ВЫСОТЫ СПИСКА (v14.8) ---
    def _improve_combo_box_view(self, combo_box):
        """Применяет настройки для лучшего отображения выпадающего списка."""
        combo_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        combo_box.view().setMinimumWidth(combo_box.sizeHint().width())
        # --- ДОБАВЛЕНА СТРОКА НИЖЕ ---
        combo_box.setMaxVisibleItems(20) # ПОКАЗЫВАТЬ ДО 20 ЭЛЕМЕНТОВ
    # --- КОНЕЦ: ОБНОВЛЕНИЕ ХЕЛПЕРА ДЛЯ УВЕЛИЧЕНИЯ ВЫСОТЫ СПИСКА (v14.8) ---
# --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА КЛАССОВ ActionParameterWidget и TextActionWidget НА ОДИН НОВЫЙ ---

class MainWindow(QMainWindow):
    APP_VERSION_TITLE = "GUIUXConstrSpec v2.0.4"
    # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА ВСЕХ СПИСКОВ КОНСТАНТ (v1.2) ---
    PREDEFINED_PROPERTIES = [
        # --- Основные ---
        ("Имя (ID)", "name"), ("Тип элемента", "type"), ("Доступность", "enabled"), ("Видимость", "visible"),
        ("Положение (X, Y)", "position"), ("Размер (Width, Height)", "size"),
        ("Привязка к краям", "dock"), ("Порядок (Z-Order)", "z_order"),
        ("Курсор", "cursor"), ("Подсказка (Tooltip)", "tooltip"),
        # --- Внешний вид ---
        ("Текст", "text"), ("Текст-анкор", "anchor_text"), ("Текст-ссылка", "text-link"), ("Шрифт", "font"), ("Цвет текста", "color"), 
        ("Цвет фона", "background-color"), ("Фоновое изображение", "background-image"),
        ("Стиль рамки", "border-style"), ("Внутренний отступ", "padding"),
        ("Внешний отступ", "margin"), ("Прозрачность", "opacity"),
        ("Выравнивание текста", "text-align"), ("Выравнивание текста по вертикале", "text_align_vertical"), ("Перенос текста", "text_wrapping"), ("Иконка", "icon"),("Стиль линии", "line_style"),

        # --- Специфические ---
        ("Значение", "value"), ("Значения списка", "list_value"), ("Макс. длина", "max_length"), ("Только чтение", "read_only"),
        ("Многострочность", "multiline"), ("Мин. значение", "min_value"), ("Макс. значение", "max_value"),
        ("Шаг", "step"), ("Интервал (таймер)", "interval"),

        # --- Для окон ---
        ("Стиль окна", "window_style"), ("Состояние окна", "window_state"), ("Поверх всех окон", "top_most"),
         ("Позиция окна", "window_position"),

         # --- Рамка и фон ---
        ("Толщина рамки", "border-width"),
        ("Цвет рамки", "border-color"),
        ("Радиус скругления", "border-radius"),
        ("Повторение фона", "background-repeat"),
        ("Позиция фона", "background-position"),
        ("Размер фона", "background-size"),
        ("Цвет заливки", "color-fill"),

        # --- Шрифты и текст ---
        ("Семейство шрифта", "font-family"),
        ("Размер шрифта", "font-size"),
        ("Насыщенность шрифта", "font-weight"),
        ("Стиль шрифта (курсив)", "font-italic"),
        ("Стиль шрифта (подчеркнутый)", "font-underlined"),
        ("Стиль шрифта (зачеркнутый)", "font-strike"),
        ("Цвет шрифта", "font-color"),
        ("Выделение цветом шрифта", "font-background"),
        ("Высота строки", "string-height"),
        ("Ширина строки", "string-width"),
        ("Межбуквенный интервал", "letter-spacing"),
        ("Декорирование текста", "text-decoration"),
        ("Тень текста", "text-shadow"),

        # --- Блочная модель и позиционирование ---
        ("Тип отображения", "display"),
        ("Отступ сверху", "margin-top"),
        ("Отступ справа", "margin-right"),
        ("Отступ снизу", "margin-bottom"),
        ("Отступ слева", "margin-left"),
        ("Внутренний отступ сверху", "padding-top"),
        ("Внутренний отступ справа", "padding-right"),
        ("Внутренний отступ снизу", "padding-bottom"),
        ("Внутренний отступ слева", "padding-left"),
        

        # --- Состояния (для интерактивности) ---
        ("Цвет фона (наведение)", "hover-background-color"),
        ("Цвет текста (наведение)", "hover-color"),
        ("Цвет рамки (наведение)", "hover-border-color"),
        ("Стиль рамки (фокус)", "focus-border-style"),
        ("Тень (фокус)", "focus-box-shadow"),

        # --- Flexbox (для компоновки дочерних элементов) ---
        ("Направление Flex", "flex-direction"),
        ("Выравнивание (основная ось)", "justify-content"),
        ("Выравнивание (поперечная ось)", "align-items"),
        ("Перенос строк Flex", "flex-wrap"),
    ]
    # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА СПИСКА СОБЫТИЙ НА МАКСИМАЛЬНО ПОЛНЫЙ (v14.6) ---
    PREDEFINED_EVENTS = [
        # --- Мышь (Основные) ---
        ("Клик (левая кнопка)", "onClick"),
        ("Двойной клик", "onDoubleClick"),
        ("Клик (правая кнопка)", "onRightClick"),
        ("Клик (средняя кнопка)", "onMiddleClick"),

        # --- Мышь (Детализированные) ---
        ("Нажатие кнопки мыши", "onMouseDown"),
        ("Отпускание кнопки мыши", "onMouseUp"),
        ("Наведение курсора", "onMouseEnter"),
        ("Уход курсора", "onMouseLeave"),
        ("Движение мыши", "onMouseMove"),
        ("Прокрутка колеса", "onMouseWheel"),
        
        # --- Клавиатура ---
        ("Нажатие клавиши", "onKeyDown"),
        ("Отпускание клавиши", "onKeyUp"),
        ("Ввод текста", "onKeyPress"), # Добавлено для полноты

        # --- Формы и ввод ---
        ("Изменение значения", "onChange"),
        ("Получение фокуса", "onFocus"),
        ("Потеря фокуса", "onBlur"),
        ("Выделение текста", "onSelect"),
        ("Отправка формы", "onSubmit"),
        ("Сброс формы", "onReset"),
        ("Вставка из буфера", "onPaste"),

        # --- Окно и компонент ---
        ("Загрузка/Инициализация", "onLoad"),
        ("Изменение размера", "onResize"),
        ("Закрытие", "onClose"),
        ("Прокрутка (скролл)", "onScroll"), # Добавлено

        # --- Drag & Drop ---
        ("Начало перетаскивания", "onDragStart"),
        ("Элемент над зоной (Drag Over)", "onDragOver"), # Добавлено
        ("Окончание перетаскивания (Drop)", "onDrop"),

        # --- Медиа ---
        ("Начало воспроизведения", "onPlay"),
        ("Пауза", "onPause"),
        ("Окончание воспроизведения", "onEnded"),
        ("Изменение времени", "onTimeUpdate"), # Добавлено

        # --- Системные ---
        ("Таймер сработал", "onTimer"),
        ("Ошибка", "onError"),
        ("Успех", "onSuccess"),

        # --- Сенсорный ввод (Touch) ---
        ("Начало касания", "onTouchStart"),
        ("Окончание касания", "onTouchEnd"),
        ("Движение пальца", "onTouchMove"),
        ("Жест (свайп)", "onSwipe"),
        ("Жест (щипок для зума)", "onPinch"),

        # --- Пользовательское ---
        ("-- Создать своё событие --", "customEvent"),
    ]
    # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА СПИСКА СОБЫТИЙ НА МАКСИМАЛЬНО ПОЛНЫЙ (v14.6) ---
    PREDEFINED_ACTIONS = [
        # --- UI ---
        ("Изменить свойство", "setProperty"),
        ("Открыть экран/диалог", "openScreen"),
        ("Закрыть окно", "closeWindow"),
        ("Показать/скрыть элемент", "toggleVisibility"),
        ("Включить/Выключить элемент", "setEnabled"),
        ("Фокус на элемент", "setFocus"),
        ("Показать сообщение", "showMessage"),
        ("Скопировать в буфер обмена", "copyToClipboard"), # <-- НОВОЕ

        # --- Данные и переменные ---
        ("Установить/Изменить переменную", "setVariable"), # <-- НОВОЕ
        ("Очистить значение", "clearValue"), # <-- НОВОЕ
        ("Сохранить данные", "saveData"),
        ("Загрузить данные", "loadData"),
        ("Обновить/Пересчитать", "refreshData"),
        ("Валидация данных", "validateData"),

        # --- БД и Файлы ---
        ("Добавить в БД", "dbInsert"),
        ("Изменить в БД", "dbUpdate"),
        ("Удалить из БД", "dbDelete"),
        ("Создать файл", "createFile"),
        ("Открыть файл", "openFile"),
        ("Сохранить файл", "saveFile"),

        # --- Навигация и Сеть ---
        ("Перейти по URL", "openURL"), # <-- НОВОЕ
        ("Отправить API запрос", "sendApiRequest"), # <-- НОВОЕ

        # --- Системные ---
        ("Запуск таймера", "startTimer"),
        ("Остановка таймера", "stopTimer"),
        ("Выполнить команду", "executeCommand"),
        ("Записать в лог", "writeLog"),

        # --- Пользовательское ---
        ("-- Своё действие (описание) --", "customAction"),
    ]
    # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА СПИСКА ТИПОВ ЭЛЕМЕНТОВ (v1.1) ---
    ELEMENT_TYPES = [
        ("3D-сцена <Viewport3D>", "Viewport3D"), 
        ("API вызов компонент <ApiRequestControl>", "ApiRequestControl"),
        ("Dock-панель <DockPanel>", "DockPanel"), 
        ("Flow-панель <FlowLayoutPanel>", "FlowLayoutPanel"), 
        ("Stack-панель <StackPanel>", "StackPanel"),
        ("WebSocket контрол <WebSocketControl>", "WebSocketControl"),
        ("Аудио плеер <AudioPlayer>", "AudioPlayer"), 
        ("Веб-браузер <WebBrowserControl>", "WebBrowserControl"), 
        ("Видео плеер <VideoPlayer>", "VideoPlayer"),
        ("Видеопоток <MediaStreamView>", "MediaStreamView"), 
        ("Вкладки вертикальные <TabControlVertical>", "TabControlVertical"),
        ("Вкладки горизонтальные <TabControlGorizontal>", "TabControlGorizontal"),
        ("Всплывающее меню <FlyoutMenu>", "FlyoutMenu"), 
        ("Всплывающее уведомление <Popup>", "Popup"),
        ("Выпадающий список <ComboBox>", "ComboBox"), 
        ("Гиперссылка <Hyperlink>", "Hyperlink"),
        ("Графическая сцена <SceneView>", "SceneView"),
        ("Грид-компоновка <Grid>", "Grid"), 
        ("Группа элементов <GroupBox>", "GroupBox"),
        ("Дерево навигации <NavigationTree>", "NavigationTree"), 
        ("Диаграмма/График <Chart>", "Chart"),
        ("Диалог выбора цвета <ColorDialog>", "ColorDialog"), 
        ("Диалог выбора шрифта <FontDialog>", "FontDialog"),
        ("Диалог печати <PrintDialog>", "PrintDialog"), 
        ("Диалог предварительного просмотра печати <PrintPreviewDialog>", "PrintPreviewDialog"),
        ("Диалоговое окно <Dialog>", "Dialog"), 
        ("Диапазонный ползунок <RangeSlider>", "RangeSlider"), 
        ("Документ-просмотрщик <DocumentViewer>", "DocumentViewer"),
        ("Древовидный список <TreeView>", "TreeView"), 
        ("Журнал событий <EventLogViewer>", "EventLogViewer"),
        ("Заголовок колонки <ColumnHeader>", "ColumnHeader"), 
        ("Закрепляемая панель <DockablePanel>", "DockablePanel"),
        ("Изображение <PictureBox>", "PictureBox"), 
        ("Иконка в трее <TrayIcon>", "TrayIcon"),
        ("Индикатор <Gauge>", "Gauge"), 
        ("Индикатор выполнения <ProgressBar>", "ProgressBar"),
        ("Интерфейс: Главный-Подробности <MasterDetailInterface>", "MasterDetailInterface"),
        ("Источник данных <DataSourceControl>", "DataSourceControl"),
        ("Календарь <Calendar>", "Calendar"), 
        ("Карта/Холст <Canvas>", "Canvas"),
        ("Карточка <Card>", "Card"), 
        ("Карточное представление <CardView>", "CardView"),
        ("Карусель/Pivot <Carousel>", "Carousel"),
        ("Кнопка <Button>", "Button"), 
        ("Кнопка выбора файла <FilePickerButton>", "FilePickerButton"),
        ("Кнопка переключатель <ToggleButton>", "ToggleButton"), 
        ("Кнопка с изображением <ImageButton>", "ImageButton"),
        ("Контейнер разметки <LayoutPanel>", "LayoutPanel"),
        ("Контекстное меню <ContextMenu>", "ContextMenu"), 
        ("Круг <Circle>", "Circle"), 
        ("Круговой индикатор прогресса <CircularProgressBar>", "CircularProgressBar"), 
        ("Линия <Line>", "Line"), 
        ("Лист свойств <PropertySheet>", "PropertySheet"), 
        ("Листание страниц <PageView>", "PageView"),
        ("Маскированное поле ввода <MaskedTextBox>", "MaskedTextBox"), 
        ("Масштабируемый контейнер/DPI <DpiAwareContainer>", "DpiAwareContainer"), 
        ("Медиапанель <MediaControl>", "MediaControl"),
        ("Менеджер ресурсов <ResourceManager>", "ResourceManager"), 
        ("Меню <MenuBar>", "MenuBar"),
        ("Меню-гамбургер <HamburgerMenu>", "HamburgerMenu"), 
        ("Многострочное текстовое поле <TextArea>", "TextArea"),
        ("Модальное окно <ModalDialog>", "ModalDialog"), 
        ("Монитор процессов <ProcessMonitor>", "ProcessMonitor"),
        ("Навигационная кнопка <NavigationButton>", "NavigationButton"), 
        ("Навигационная панель <NavigationView>", "NavigationView"),
        ("Немодальное окно <ModelessDialog>", "ModelessDialog"),
        ("Область ввода кода/моноширинный редактор <CodeEditor>", "CodeEditor"), 
        ("Область уведомлений <NotificationArea>", "NotificationArea"),
        ("Окно <Window>", "Window"), 
        ("Окно сообщения <MessageBox>", "MessageBox"),
        ("Оценка/Звёздочки <RatingControl>", "RatingControl"), 
        ("Панель <Panel>", "Panel"),
        ("Панель вкладок с документами <DocumentTabView>", "DocumentTabView"), 
        ("Панель заголовка окна <TitleBar>", "TitleBar"), 
        ("Панель задач <TaskBarControl>", "TaskBarControl"),
        ("Панель инструментов <ToolBar>", "ToolBar"),
        ("Панель команд <CommandBar>", "CommandBar"), 
        ("Панель навигации <NavigationBar>", "NavigationBar"), 
        ("Панель прокрутки <ScrollBar>", "ScrollBar"), 
        ("Панель разделителей <Splitter>", "Splitter"),
        ("Панель свойств <PropertyGrid>", "PropertyGrid"), 
        ("Панель фильтров <FilterPanel>", "FilterPanel"),
        ("Переключатель <RadioButton>", "RadioButton"), 
        ("Плавающая панель <FloatingPanel>", "FloatingPanel"),
        ("Плитка <Tile>", "Tile"), 
        ("Подсказка <ToolTip>", "ToolTip"), 
        ("Поле ввода текста <TextBox>", "TextBox"),
        ("Поле выбора времени <TimePicker>", "TimePicker"),
        ("Поле выбора даты <DatePicker>", "DatePicker"),
        ("Поле выбора папки <FolderDialog>", "FolderDialog"), 
        ("Поле выбора файла <FileDialog>", "FileDialog"),
        ("Поле выбора цвета <ColorPicker>", "ColorPicker"), 
        ("Поле для IP-адреса <IPAddressControl>", "IPAddressControl"), 
        ("Поле для пароля <PasswordBox>", "PasswordBox"),
        ("Поле поиска <SearchBox>", "SearchBox"), 
        ("Поле со списком <ListView>", "ListView"), 
        ("Ползунок/Слайдер <Slider>", "Slider"),
        ("Пошаговый процесс/Stepper <Stepper>", "Stepper"),
        ("Просмотр PDF <PDFViewer>", "PDFViewer"), 
        ("Прямоугольник <Shape>", "Shape"), 
        ("Разделённый вид <Split View>", "Split View"),
        ("Раскрывающаяся секция <Accordion>", "Accordion"),
        ("Расширитель/Expander <Expander>", "Expander"),
        ("Рисовальная область <DrawingArea>", "DrawingArea"),
        ("Сервис уведомлений <NotificationService>", "NotificationService"), 
        ("Сеточное представление <GridView>", "GridView"), 
        ("Система индикатор батареи <BatteryIndicator>", "BatteryIndicator"), 
        ("Система индикатор сети <NetworkIndicator>", "NetworkIndicator"), 
        ("Список <ListBox>", "ListBox"),
        ("Столбец таблицы <GridColumn>", "GridColumn"), 
        ("Строка состояния <StatusBar>", "StatusBar"),
        ("Строка таблицы <GridRow>", "GridRow"), 
        ("Таблица/Сетка <DataGrid>", "DataGrid"), 
        ("Таймер <Timer>", "Timer"),
        ("Текстовая метка <Label>", "Label"),
        ("Текстовый редактор/Документ <RichTextBox>", "RichTextBox"),
        ("Тумблер/Переключатель <ToggleSwitch>", "ToggleSwitch"), 
        ("Флажок <CheckBox>", "CheckBox"),
        ("Флип-вью <FlipView>", "FlipView"), 
        ("Фоновый поток <BackgroundWorker>", "BackgroundWorker"),
        ("Форма входа <LoginForm>", "LoginForm"),
        ("Форма регистрации <RegisterForm>", "RegisterForm"), 
        ("Фрейм/Панель <Frame>", "Frame"),
        ("Хлебные крошки <BreadcrumbItem>", "BreadcrumbItem"), 
        ("Хлебные крошки, навигация <BreadcrumbBar>", "BreadcrumbBar"),
        ("Холст для OpenGL/DirectX <GLCanvas>", "GLCanvas"), 
        ("Числовое поле со стрелками <SpinBox>", "SpinBox"),
        ("Элемент ActiveX/OCX <ActiveXControl>", "ActiveXControl"), 
        ("Элемент выбора шрифта <FontPicker>", "FontPicker"), 
        ("Элемент дерева узел <TreeNode>", "TreeNode"),
        ("Элемент для drag&drop <DragDropArea>", "DragDropArea"), 
        ("Элемент для записи звука <AudioRecorder>", "AudioRecorder"),
        ("Элемент для съемки с камеры <CameraView>", "CameraView"), 
        ("Элемент карты (гео) <MapControl>", "MapControl"),
        ("Элемент карты-плитки <MapTile>", "MapTile"),   
        ("--- Свой тип (в описании) ---", "customType"),
    ]
# --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА СПИСКА ТИПОВ ЭЛЕМЕНТОВ (v1.1) ---
# --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА ВСЕХ СПИСКОВ КОНСТАНТ (v1.2) ---
    def __init__(self):
        super().__init__(); 
        # --- НАЧАЛО: ИНИЦИАЛИЗАЦИЯ МЕНЕДЖЕРА НАСТРОЕК (v9.7) ---
        self.settings_manager = StyleSettingsManager()
        # --- КОНЕЦ: ИНИЦИАЛИЗАЦИЯ МЕНЕДЖЕРА НАСТРОЕК (v9.7) ---
        # --- НАЧАЛО: ИНИЦИАЛИЗАЦИЯ МЕНЕДЖЕРА ШАБЛОНОВ (v13.0) ---
        self.templates_manager = TemplatesManager()
        # --- КОНЕЦ: ИНИЦИАЛИЗАЦИЯ МЕНЕДЖЕРА ШАБЛОНОВ (v13.0) ---
         # --- НАЧАЛО: ИНИЦИАЛИЗАЦИЯ МЕНЕДЖЕРА СЦЕНАРИЕВ (v3.3) ---
        self.scenarios_manager = ScenariosManager()
        # --- КОНЕЦ: ИНИЦИАЛИЗАЦИЯ МЕНЕДЖЕРА СЦЕНАРИЕВ (v3.3) ---
        # --- НАЧАЛО: ДОБАВЛЕНА КАРТА ЭЛЕМЕНТОВ СЦЕНЫ (v8.0) ---
        self.scene_items_map = {}
        # --- КОНЕЦ: ДОБАВЛЕНА КАРТА ЭЛЕМЕНТОВ СЦЕНЫ (v8.0) ---
        # --- НАЧАЛО: ДОБАВЛЕНЫ ПЕРЕМЕННЫЕ ДЛЯ РЕЖИМА СВЯЗЕЙ (v2.1) ---
        self.relation_mode_active = False
        self.relation_source_id = None
        # --- КОНЕЦ: ДОБАВЛЕНЫ ПЕРЕМЕННЫЕ ДЛЯ РЕЖИМА СВЯЗЕЙ (v2.1) ---
        self.data_manager = DataManager(); self._init_project_data(); self._setup_ui(); self._create_menu_bar(); 
        # --- НАЧАЛО: ДОБАВЛЕН ВЫЗОВ СОЗДАНИЯ СТАТУС-БАРА (v10.1) ---
        self._create_status_bar()
        # --- КОНЕЦ: ДОБАВЛЕН ВЫЗОВ СОЗДАНИЯ СТАТУС-БАРА (v10.1) ---
        self._update_ui_for_new_project()
    
    # --- ИЗМЕНЕНИЕ: ДОБАВЛЕН РАЗДЕЛ 'globals' В МОДЕЛЬ ДАННЫХ ---
    def _init_project_data(self):
        # --- НАЧАЛО: ДОБАВЛЕН РАЗДЕЛ ДЛЯ ГЛОБАЛЬНОГО ХРАНЕНИЯ СВЯЗЕЙ (v2.1) ---
        self.project_data = {'concept': {}, 'globals': {}, 'tree': {}, 'relations': {}}
        # --- КОНЕЦ: ДОБАВЛЕН РАЗДЕЛ ДЛЯ ГЛОБАЛЬНОГО ХРАНЕНИЯ СВЯЗЕЙ (v2.1) ---
        self.current_project_path = None
        # --- НАЧАЛО: ДОБАВЛЕН "ГРЯЗНЫЙ" ФЛАГ ---
        self.is_dirty = False
        # --- КОНЕЦ: ДОБАВЛЕН "ГРЯЗНЫЙ" ФЛАГ ---

     # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА _setup_ui С ИСПОЛЬЗОВАНИЕМ QSTACKEDWIDGET (v3.2) ---
    def _setup_ui(self):
        self.setWindowTitle(self.APP_VERSION_TITLE)
        self.resize(1400, 900)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # СОЗДАЕМ ВСЕ ПАНЕЛИ
        left_panel = self._create_left_panel()
        center_panel = self._create_center_panel()
        self.right_panel = self._create_right_panel() # Панель для Концепции, Глобальных, Компонентов
        self.scenarios_panel = self._create_scenarios_panel() # Панель для Сценариев

        # ИСПОЛЬЗУЕМ QSTACKEDWIDGET ДЛЯ УПРАВЛЕНИЯ ПРАВЫМИ ПАНЕЛЯМИ
        self.right_stack = QStackedWidget()
        self.right_stack.addWidget(self.right_panel)
        self.right_stack.addWidget(self.scenarios_panel)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(self.right_stack)
        
        splitter.setSizes([350, 750, 350])
    # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА _setup_ui С ИСПОЛЬЗОВАНИЕМ QSTACKEDWIDGET (v3.2) ---
    

   # --- НАЧАЛО: ФУНКЦИЯ _create_left_panel ПОЛНАЯ ЗАМЕНА (Graph.v2.1.1) ---
    def _create_left_panel(self):
        left_panel = QWidget()
        layout = QVBoxLayout(left_panel)
        
        self.project_tree = QTreeWidget(); self.project_tree.setHeaderLabels(["Структура проекта"])

    # --- НАЧАЛО: ВКЛЮЧЕНИЕ КОНТЕКСТНОГО МЕНЮ (v13.1) ---
        self.project_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.project_tree.customContextMenuRequested.connect(self.show_tree_context_menu)
        # --- КОНЕЦ: ВКЛЮЧЕНИЕ КОНТЕКСТНОГО МЕНЮ (v13.1) ---
        layout.addWidget(self.project_tree)
        
       
        bold_font = QFont("Segoe UI", 10, QFont.Bold)
        self.concept_item = QTreeWidgetItem(self.project_tree, ["Концепция проекта"]); self.concept_item.setData(0, Qt.UserRole, "concept_id"); self.concept_item.setFont(0, bold_font)
        self.globals_item = QTreeWidgetItem(self.project_tree, ["Глобальные сущности"]); self.globals_item.setData(0, Qt.UserRole, "globals_id"); self.globals_item.setFont(0, bold_font)

        # --- НАЧАЛО: ДОБАВЛЕН НОВЫЙ РАЗДЕЛ "СЦЕНАРИИ" (v3.1) ---
        self.scenarios_item = QTreeWidgetItem(self.project_tree, ["Сценарии"])
        self.scenarios_item.setData(0, Qt.UserRole, "scenarios_id")
        self.scenarios_item.setFont(0, bold_font)
        # --- КОНЕЦ: ДОБАВЛЕН НОВЫЙ РАЗДЕЛ "СЦЕНАРИИ" (v3.1) ---

        self.components_root_item = QTreeWidgetItem(self.project_tree, ["Компоненты / Иерархия"]); self.components_root_item.setData(0, Qt.UserRole, "components_root_id"); self.components_root_item.setFont(0, bold_font)
        
        tools_layout = QGridLayout()
        add_child_btn = QPushButton("+ Дочерний")
        add_sibling_btn = QPushButton("+ На том же уровне")
        remove_btn = QPushButton("– Удалить")
        move_up_btn = QPushButton("↑ Вверх")
        move_down_btn = QPushButton("↓ Вниз")
        reparent_btn = QPushButton("Сменить родителя")
        self.add_from_template_btn = QPushButton("+ Из шаблона")
        # --- НАЧАЛО: ДОБАВЛЕНА КНОПКА ДЛЯ СОЗДАНИЯ СВЯЗЕЙ (v2.1) ---
        self.create_relation_btn = QPushButton("🔗 Создать связь")
        # --- КОНЕЦ: ДОБАВЛЕНА КНОПКА ДЛЯ СОЗДАНИЯ СВЯЗЕЙ (v2.1) ---
        self.load_bg_btn = QPushButton("Загрузить Прототип")
        self.draw_rect_btn = QPushButton("Привязать/Изменить область")

        # --- НАЧАЛО: ПЕРЕИМЕНОВЫВАЕМ КНОПКУ (v3.0) ---
        self.settings_btn = QPushButton("Настройки")
        # --- КОНЕЦ: ПЕРЕИМЕНОВЫВАЕМ КНОПКУ (v3.0) ---

        # --- НАЧАЛО: ДОБАВЛЕНА КНОПКА УПРАВЛЕНИЯ ШАБЛОНАМИ (v15.7) ---
        self.manage_templates_btn = QPushButton("Управление шаблонами")
        # --- КОНЕЦ: ДОБАВЛЕНА КНОПКА УПРАВЛЕНИЯ ШАБЛОНАМИ (v15.7) ---

        tools_layout.addWidget(add_child_btn, 0, 0); tools_layout.addWidget(add_sibling_btn, 0, 1); tools_layout.addWidget(remove_btn, 0, 2)
        tools_layout.addWidget(move_up_btn, 1, 0); tools_layout.addWidget(move_down_btn, 1, 1); tools_layout.addWidget(reparent_btn, 1, 2)

        # --- НАЧАЛО: ДОБАВЛЕНИЕ КНОПКИ В МАКЕТ (v2.1) ---
        tools_layout.addWidget(self.create_relation_btn, 2, 0, 1, 3)
        tools_layout.addWidget(self.add_from_template_btn, 3, 0, 1, 3) # Сдвигаем
        tools_layout.addWidget(self.load_bg_btn, 4, 0, 1, 3) # Сдвигаем
        tools_layout.addWidget(self.draw_rect_btn, 5, 0, 1, 3) # Сдвигаем
        # --- НАЧАЛО: ИЗМЕНЯЕМ ИМЯ ОБЪЕКТА КНОПКИ В МАКЕТЕ (v3.0) ---
        tools_layout.addWidget(self.create_relation_btn, 6, 0, 1, 3)
        tools_layout.addWidget(self.settings_btn, 7, 0, 1, 3)
        tools_layout.addWidget(self.manage_templates_btn, 8, 0, 1, 3)
        # --- КОНЕЦ: ИЗМЕНЯЕМ ИМЯ ОБЪЕКТА КНОПКИ В МАКЕТЕ (v3.0) ---
        # --- КОНЕЦ: ДОБАВЛЕНИЕ КНОПКИ В МАКЕТ (v2.1) ---
        layout.addLayout(tools_layout)

        self.project_tree.currentItemChanged.connect(self.on_tree_item_selected)
        add_child_btn.clicked.connect(self.add_child_item); add_sibling_btn.clicked.connect(self.add_sibling_item); remove_btn.clicked.connect(self.remove_item)
        move_up_btn.clicked.connect(lambda: self.move_item(-1)); move_down_btn.clicked.connect(lambda: self.move_item(1))
        reparent_btn.clicked.connect(self.reparent_item); 
        # --- НАЧАЛО: ПОДКЛЮЧЕНИЕ СИГНАЛА КНОПКИ (v2.1) ---
        self.create_relation_btn.clicked.connect(self.activate_relation_mode)
        # --- КОНЕЦ: ПОДКЛЮЧЕНИЕ СИГНАЛА КНОПКИ (v2.1) ---
         # --- НАЧАЛО: ПОДКЛЮЧЕНИЕ СИГНАЛА КНОПКИ (v13.2) ---
        self.add_from_template_btn.clicked.connect(self.add_item_from_template)
        # --- КОНЕЦ: ПОДКЛЮЧЕНИЕ СИГНАЛА КНОПКИ (v13.2) ---
        self.load_bg_btn.clicked.connect(self.load_background_image)
        self.draw_rect_btn.clicked.connect(self.activate_drawing_mode)
        # --- НАЧАЛО: ИЗМЕНЯЕМ ИМЯ ОБЪЕКТА КНОПКИ В ПОДКЛЮЧЕНИИ (v3.0) ---
        self.settings_btn.clicked.connect(self.open_settings_dialog)
        # --- КОНЕЦ: ИЗМЕНЯЕМ ИМЯ ОБЪЕКТА КНОПКИ В ПОДКЛЮЧЕНИИ (v3.0) ---
        # --- НАЧАЛО: ПОДКЛЮЧЕНИЕ СИГНАЛА КНОПКИ (v15.7) ---
        self.manage_templates_btn.clicked.connect(self.open_manage_templates_dialog)
        # --- КОНЕЦ: ПОДКЛЮЧЕНИЕ СИГНАЛА КНОПКИ (v15.7) ---

        return left_panel
# --- КОНЕЦ: ФУНКЦИЯ _create_left_panel ПОЛНАЯ ЗАМЕНА (Graph.v2.1.1) ---

# --- НАЧАЛО: НОВЫЙ МЕТОД ДЛЯ ОБНОВЛЕНИЯ МАСШТАБА В СТАТУС-БАРЕ (v10.3) ---
    def update_zoom_combo(self, zoom_value):
        """ОБНОВЛЯЕТ ЗНАЧЕНИЕ ВЫПАДАЮЩЕГО СПИСКА МАСШТАБА."""
        # БЛОКИРУЕМ СИГНАЛЫ, ЧТОБЫ ИЗБЕЖАТЬ БЕСКОНЕЧНОГО ЦИКЛА
        self.zoom_combo.blockSignals(True)
        
        # ФОРМАТИРУЕМ ТЕКСТ В ВИДЕ "125%"
        zoom_text = f"{zoom_value:.0f}%"
        
        # --- НАЧАЛО: УДАЛЕНА ЛОГИКА ДОБАВЛЕНИЯ НОВЫХ ЭЛЕМЕНТОВ В СПИСОК (v10.4) ---
        # БОЛЬШЕ НЕТ НЕОБХОДИМОСТИ ПРОВЕРЯТЬ И ДОБАВЛЯТЬ, ТАК КАК ПОЛЕ РЕДАКТИРУЕМОЕ
        # --- КОНЕЦ: УДАЛЕНА ЛОГИКА ДОБАВЛЕНИЯ НОВЫХ ЭЛЕМЕНТОВ В СПИСОК (v10.4) ---
        
        self.zoom_combo.setCurrentText(zoom_text)
        
        self.zoom_combo.blockSignals(False)
    # --- КОНЕЦ: НОВЫЙ МЕТОД ДЛЯ ОБНОВЛЕНИЯ МАСШТАБА В СТАТУС-БАРЕ (v10.3) ---   

# --- НАЧАЛО: НОВЫЙ МЕТОД ДЛЯ УСТАНОВКИ МАСШТАБА ИЗ СТАТУС-БАРА (v10.6) ---
    def set_zoom_from_combo(self):
        """СЧИТЫВАЕТ ЗНАЧЕНИЕ ИЗ QCOMBOBOX И ПРИМЕНЯЕТ МАСШТАБ."""
        # ПОЛУЧАЕМ ТЕКСТ И УБИРАЕМ ЗНАК '%'
        text = self.zoom_combo.currentText().replace('%', '').strip()
        
        try:
            # ПРЕОБРАЗУЕМ В ЧИСЛО
            percent_value = int(text)
            
            # ПРЕОБРАЗУЕМ ПРОЦЕНТЫ В ФАКТОР (100% -> 1.0)
            scale_factor = percent_value / 100.0
            
            # ВЫЗЫВАЕМ МЕТОД ХОЛСТА ДЛЯ УСТАНОВКИ МАСШТАБА
            self.view.set_zoom(scale_factor)
            
            # СИНХРОНИЗИРУЕМ ТЕКСТ В COMBOBOX ПОСЛЕ ИЗМЕНЕНИЯ
            # ЭТО ТАКЖЕ ПОМОЖЕТ, ЕСЛИ МАСШТАБ БЫЛ ОГРАНИЧЕН
            current_zoom_factor = self.view.transform().m11()
            self.update_zoom_combo(current_zoom_factor * 100)

        except ValueError:
            # ЕСЛИ ПОЛЬЗОВАТЕЛЬ ВВЕЛ НЕ ЧИСЛО, ВОЗВРАЩАЕМ ПРЕДЫДУЩЕЕ ЗНАЧЕНИЕ
            current_zoom_factor = self.view.transform().m11()
            self.update_zoom_combo(current_zoom_factor * 100)
    # --- КОНЕЦ: НОВЫЙ МЕТОД ДЛЯ УСТАНОВКИ МАСШТАБА ИЗ СТАТУС-БАРА (v10.6) ---

# --- НАЧАЛО: НОВЫЙ МЕТОД ДЛЯ ОБНОВЛЕНИЯ КООРДИНАТ В СТАТУС-БАРЕ (v10.8) ---
    def update_coords_label(self, scene_pos):
        """ОБНОВЛЯЕТ ТЕКСТ С КООРДИНАТАМИ КУРСОРА."""
        self.coords_label.setText(f"X: {scene_pos.x():.0f}, Y: {scene_pos.y():.0f}")
    # --- КОНЕЦ: НОВЫЙ МЕТОД ДЛЯ ОБНОВЛЕНИЯ КООРДИНАТ В СТАТУС-БАРЕ (v10.8) ---


# --- НАЧАЛО: ФУНКЦИЯ _create_center_panel ПОЛНАЯ ЗАМЕНА (Graph.v2.0) ---
    def _create_center_panel(self):
        center_panel = QWidget(); layout = QVBoxLayout(center_panel); layout.setContentsMargins(0, 0, 0, 0)
        self.scene = QGraphicsScene()
        self.background_item = QGraphicsPixmapItem()
        self.scene.addItem(self.background_item)
        self.view = CanvasView(self.scene)
        # --- НАЧАЛО: УДАЛЕНА СТАРАЯ СТРОКА (v10.5) ---
        # self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        # --- КОНЕЦ: УДАЛЕНА СТАРАЯ СТРОКА (v10.5) ---
        self.view.rect_drawn.connect(self.update_item_rect) # <-- ИЗМЕНЕНО
        self.view.item_selected_on_canvas.connect(self.select_item_in_tree)
         # --- НАЧАЛО: ПОДКЛЮЧЕНИЕ СИГНАЛА МАСШТАБИРОВАНИЯ (v10.3) ---
        self.view.zoom_changed.connect(self.update_zoom_combo)
        # --- КОНЕЦ: ПОДКЛЮЧЕНИЕ СИГНАЛА МАСШТАБИРОВАНИЯ (v10.3) ---
        # --- НАЧАЛО: ПОДКЛЮЧЕНИЕ СИГНАЛА КООРДИНАТ (v10.8) ---
        self.view.mouse_moved_on_scene.connect(self.update_coords_label)
        # --- КОНЕЦ: ПОДКЛЮЧЕНИЕ СИГНАЛА КООРДИНАТ (v10.8) ---
        layout.addWidget(self.view)
        return center_panel
# --- КОНЕЦ: ФУНКЦИЯ _create_center_panel ПОЛНАЯ ЗАМЕНА (Graph.v2.0) ---

# --- НАЧАЛО: ДОБАВЛЕНА НОВАЯ ФУНКЦИЯ (Graph.v2.1) ---
    def activate_drawing_mode(self):
        selected_item = self.project_tree.currentItem()
        if not selected_item or not selected_item.parent():
            QMessageBox.warning(self, "Ошибка", "Для привязки области сначала выберите элемент в иерархии компонентов.")
            return
        self.view.set_drawing_mode(True)
# --- КОНЕЦ: ДОБАВЛЕНА НОВАЯ ФУНКЦИЯ (Graph.v2.1) ---
    
    # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА _create_right_panel С ДОБАВЛЕНИЕМ КНОПОК КЛОНИРОВАНИЯ (v11.0-fix) ---
    def _create_right_panel(self):
        right_panel = QWidget(); self.right_layout = QVBoxLayout(right_panel)
        self.concept_editor_widget = QWidget()
        concept_layout = QVBoxLayout(self.concept_editor_widget); concept_layout.setContentsMargins(0,0,0,0)
        concept_title = QLabel("Общая концепция и UX"); concept_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.concept_editor = QTextEdit(); self.concept_editor.setPlaceholderText("Опишите здесь общую логику...")
        self.concept_editor.textChanged.connect(self.update_concept_description)
        concept_layout.addWidget(concept_title); concept_layout.addWidget(self.concept_editor)
        self.right_layout.addWidget(self.concept_editor_widget)

        self.globals_editor_widget = QWidget()
        globals_layout = QVBoxLayout(self.globals_editor_widget)
        globals_layout.setContentsMargins(0,0,0,0)
        globals_title = QLabel("Глобальные сущности (переменные, ссылки, файлы, БД, API)")
        globals_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.globals_table = QTableWidget(0, 2)
        self.globals_table.setHorizontalHeaderLabels(["Имя (ключ)", "Значение"])
        self.globals_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.globals_table.itemChanged.connect(self.save_globals_from_table)
        globals_layout.addWidget(globals_title); globals_layout.addWidget(self.globals_table)
        globals_buttons = QHBoxLayout(); add_global_btn = QPushButton("+ Добавить"); remove_global_btn = QPushButton("– Удалить")
        globals_buttons.addStretch(); globals_buttons.addWidget(add_global_btn); globals_buttons.addWidget(remove_global_btn)
        add_global_btn.clicked.connect(self.add_global_variable)
        remove_global_btn.clicked.connect(lambda: self.globals_table.removeRow(self.globals_table.currentRow()))
        globals_layout.addLayout(globals_buttons)
        self.right_layout.addWidget(self.globals_editor_widget)

        self.properties_widget = QWidget()
        props_main_layout = QVBoxLayout(self.properties_widget)
        props_main_layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Vertical)
        
        top_widget = QWidget(); top_layout = QFormLayout(top_widget); top_layout.setContentsMargins(0, 0, 0, 0)
        self.name_editor = QLineEdit(); self.name_editor.editingFinished.connect(self.update_item_name); top_layout.addRow("Имя:", self.name_editor)

        # --- НАЧАЛО: ДОБАВЛЕНО ПОЛЕ ДЛЯ ОТОБРАЖЕНИЯ ID (v3.5) ---
        self.id_display = QLineEdit(); self.id_display.setReadOnly(True)
        self.id_display.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        top_layout.addRow("ID:", self.id_display)
        # --- КОНЕЦ: ДОБАВЛЕНО ПОЛЕ ДЛЯ ОТОБРАЖЕНИЯ ID (v3.5) ---
        
        self.type_combo = QComboBox()
        for name, key in self.ELEMENT_TYPES:
            self.type_combo.addItem(name, key)
        # --- НАЧАЛО: УЛУЧШЕНИЕ ОТОБРАЖЕНИЯ ВЫПАДАЮЩЕГО СПИСКА (v14.7) ---
        self.type_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.type_combo.view().setMinimumWidth(self.type_combo.sizeHint().width())
         # --- НАЧАЛО: УВЕЛИЧЕНИЕ ВЫСОТЫ СПИСКА (v14.8) ---
        self.type_combo.setMaxVisibleItems(20)
        # --- КОНЕЦ: УВЕЛИЧЕНИЕ ВЫСОТЫ СПИСКА (v14.8) ---
        # --- КОНЕЦ: УЛУЧШЕНИЕ ОТОБРАЖЕНИЯ ВЫПАДАЮЩЕГО СПИСКА (v14.7) ---    
        self.type_combo.currentIndexChanged.connect(self.update_item_type)
        top_layout.addRow("Тип элемента:", self.type_combo)
        
        self.description_editor = QTextEdit(); self.description_editor.textChanged.connect(self.update_item_description); top_layout.addRow("Описание:", self.description_editor)
        splitter.addWidget(top_widget)
        
        bottom_widget = QWidget(); bottom_layout = QVBoxLayout(bottom_widget); bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.properties_tabs_widget = QTabWidget()
        
        # --- ВКЛАДКА "СВОЙСТВА" ---
        props_tab = QWidget(); props_layout = QVBoxLayout(props_tab)
        props_table_title = QLabel("Свойства"); props_table_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        props_layout.addWidget(props_table_title)
        self.properties_table = QTableWidget(0, 3)
        self.properties_table.setHorizontalHeaderLabels(["Название", "Свойство (для ИИ)", "Значение"])
        self.properties_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
         # --- НАЧАЛО: ПОДКЛЮЧЕНИЕ СИГНАЛА ДВОЙНОГО КЛИКА (v12.0) ---
        self.properties_table.cellDoubleClicked.connect(self.on_property_cell_double_clicked)
        # --- КОНЕЦ: ПОДКЛЮЧЕНИЕ СИГНАЛА ДВОЙНОГО КЛИКА (v12.0) ---
        self.properties_table.itemChanged.connect(self.save_properties_from_table)
        props_layout.addWidget(self.properties_table)
        
        props_buttons_layout = QHBoxLayout()
        clone_props_btn = QPushButton("Клонировать свойства")
        add_prop_btn = QPushButton("Добавить свойство")
        remove_prop_btn = QPushButton("Удалить свойство")
        props_buttons_layout.addStretch()
        props_buttons_layout.addWidget(clone_props_btn)
        props_buttons_layout.addWidget(add_prop_btn)
        props_buttons_layout.addWidget(remove_prop_btn)
        props_layout.addLayout(props_buttons_layout)
        
        clone_props_btn.clicked.connect(lambda: self.open_clone_dialog('properties')) # <-- ВОТ ЭТОГО НЕ ХВАТАЛО
        add_prop_btn.clicked.connect(self.add_custom_property)
        remove_prop_btn.clicked.connect(self.remove_custom_property)
        
        self.properties_tabs_widget.addTab(props_tab, "Свойства")
        
        # --- ВКЛАДКА "СОБЫТИЯ И ДЕЙСТВИЯ" ---
        events_tab = QWidget(); events_layout = QVBoxLayout(events_tab)
        self.events_tree = QTreeWidget()
        self.events_tree.setHeaderLabels(["События и Действия"])
        self.events_tree.setEditTriggers(QTreeWidget.DoubleClicked | QTreeWidget.SelectedClicked)
        self.events_tree.itemChanged.connect(self.update_custom_event_or_action_text)
        events_layout.addWidget(self.events_tree)
        
        events_buttons_layout = QHBoxLayout()
        clone_events_btn = QPushButton("Клонировать события")
        add_event_btn = QPushButton("+ Событие")
        add_action_btn = QPushButton("+ Действие")
        remove_btn = QPushButton("– Удалить")
        events_buttons_layout.addStretch()
        events_buttons_layout.addWidget(clone_events_btn)
        events_buttons_layout.addWidget(add_event_btn)
        events_buttons_layout.addWidget(add_action_btn)
        events_buttons_layout.addWidget(remove_btn)
        events_layout.addLayout(events_buttons_layout)

        clone_events_btn.clicked.connect(lambda: self.open_clone_dialog('events')) # <-- И ВОТ ЭТОГО
        add_event_btn.clicked.connect(self.add_event)
        add_action_btn.clicked.connect(self.add_action)
        remove_btn.clicked.connect(self.remove_event_or_action)
        
        self.properties_tabs_widget.addTab(events_tab, "События и Действия")
        
# --- НАЧАЛО: ДОБАВЛЕНА ВКЛАДКА "СВЯЗИ" (v2.1) ---
        relations_tab = QWidget()
        relations_layout = QVBoxLayout(relations_tab)
        self.relations_list = QListWidget()
        relations_layout.addWidget(self.relations_list)
        
        relations_buttons_layout = QHBoxLayout()
        self.edit_relation_btn = QPushButton("Изменить")
        self.remove_relation_btn = QPushButton("Удалить")
        relations_buttons_layout.addStretch()
        relations_buttons_layout.addWidget(self.edit_relation_btn)
        relations_buttons_layout.addWidget(self.remove_relation_btn)
        
        self.edit_relation_btn.clicked.connect(self.edit_selected_relation)
        self.remove_relation_btn.clicked.connect(self.remove_selected_relation)
        
        relations_layout.addLayout(relations_buttons_layout)
        self.properties_tabs_widget.addTab(relations_tab, "Связи")
        # --- КОНЕЦ: ДОБАВЛЕНА ВКЛАДКА "СВЯЗИ" (v2.1) ---

        bottom_layout.addWidget(self.properties_tabs_widget)
        splitter.addWidget(bottom_widget)
        splitter.setSizes([200, 400])
        props_main_layout.addWidget(splitter)
        self.right_layout.addWidget(self.properties_widget)
        return right_panel
    # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА _create_right_panel С ДОБАВЛЕНИЕМ КНОПОК КЛОНИРОВАНИЯ (v11.0-fix) ---

# --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА _create_scenarios_panel НА РАБОЧИЙ РЕДАКТОР (v3.4) ---
    def _create_scenarios_panel(self):
        """СОЗДАЕТ ПОЛНОЦЕННЫЙ ВИДЖЕТ-РЕДАКТОР ДЛЯ СЦЕНАРИЕВ."""
        scenarios_widget = QWidget()
        main_layout = QHBoxLayout(scenarios_widget)
        
        # --- ЛЕВАЯ ЧАСТЬ СО СПИСКОМ СЦЕНАРИЕВ ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_widget.setMaximumWidth(250)
        
        self.scenarios_list = QListWidget()
        self.scenarios_list.currentItemChanged.connect(self.on_scenario_selected)
        
        left_buttons_layout = QHBoxLayout()
        add_scenario_btn = QPushButton("Создать")
        remove_scenario_btn = QPushButton("Удалить")
        add_scenario_btn.clicked.connect(self.add_new_scenario)
        remove_scenario_btn.clicked.connect(self.delete_selected_scenario)
        left_buttons_layout.addWidget(add_scenario_btn)
        left_buttons_layout.addWidget(remove_scenario_btn)
        
        left_layout.addWidget(QLabel("Список сценариев:"))
        left_layout.addWidget(self.scenarios_list)
        left_layout.addLayout(left_buttons_layout)
        
        # --- ПРАВАЯ ЧАСТЬ С РЕДАКТОРОМ ---
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        
        self.scenario_name_edit = QLineEdit()
        self.scenario_name_edit.setPlaceholderText("Имя сценария...")
        self.scenario_name_edit.editingFinished.connect(self.save_current_scenario)
        
        self.scenario_editor = QTextEdit()
        self.scenario_editor.setPlaceholderText("Опишите шаги сценария здесь...")
        self.scenario_editor.textChanged.connect(self.save_current_scenario_text)

        right_buttons_layout = QHBoxLayout()
        insert_link_btn = QPushButton("🔗 Вставить ссылку на компонент")
        insert_link_btn.clicked.connect(self.open_insert_link_dialog)
        right_buttons_layout.addStretch()
        right_buttons_layout.addWidget(insert_link_btn)
        
        editor_layout.addWidget(self.scenario_name_edit)
        editor_layout.addWidget(self.scenario_editor)
        editor_layout.addLayout(right_buttons_layout)
        
        main_layout.addWidget(left_widget)
        main_layout.addWidget(editor_widget)
        
        return scenarios_widget
    # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА _create_scenarios_panel НА РАБОЧИЙ РЕДАКТОР (v3.4) ---

# --- НАЧАЛО: НОВЫЕ МЕТОДЫ ДЛЯ ЛОГИКИ СЦЕНАРИЕВ (v3.4) ---
    def populate_scenarios_list(self):
        """ЗАПОЛНЯЕТ СПИСОК СЦЕНАРИЕВ."""
        self.scenarios_list.blockSignals(True)
        self.scenarios_list.clear()
        for scenario in self.scenarios_manager.get_scenarios_list():
            item = QListWidgetItem(scenario['name'])
            item.setData(Qt.UserRole, scenario['id'])
            self.scenarios_list.addItem(item)
        self.scenarios_list.blockSignals(False)

    def on_scenario_selected(self, current, previous):
        """ЗАГРУЖАЕТ ДАННЫЕ ВЫБРАННОГО СЦЕНАРИЯ В РЕДАКТОР."""
        if not current:
            self.scenario_name_edit.clear()
            self.scenario_editor.clear()
            self.scenario_name_edit.setEnabled(False)
            self.scenario_editor.setEnabled(False)
            return

        scenario_id = current.data(Qt.UserRole)
        scenario_data = self.scenarios_manager.scenarios.get(scenario_id)
        if scenario_data:
            self.scenario_name_edit.setEnabled(True)
            self.scenario_editor.setEnabled(True)
            self.scenario_name_edit.setText(scenario_data.get('name', ''))
            self.scenario_editor.setText(scenario_data.get('description', ''))

    def add_new_scenario(self):
        """ДОБАВЛЯЕТ НОВЫЙ СЦЕНАРИЙ."""
        name, ok = QInputDialog.getText(self, "Новый сценарий", "Введите имя сценария:")
        if ok and name:
            new_id, success = self.scenarios_manager.add_scenario(name)
            if success:
                self.populate_scenarios_list()
                # Автоматически выбираем только что созданный сценарий
                for i in range(self.scenarios_list.count()):
                    if self.scenarios_list.item(i).data(Qt.UserRole) == new_id:
                        self.scenarios_list.setCurrentRow(i)
                        break

    def delete_selected_scenario(self):
        """УДАЛЯЕТ ВЫБРАННЫЙ СЦЕНАРИЙ."""
        current = self.scenarios_list.currentItem()
        if not current: return
        
        scenario_id = current.data(Qt.UserRole)
        name = current.text()
        reply = QMessageBox.question(self, "Подтверждение", f"Удалить сценарий '{name}'?")
        if reply == QMessageBox.Yes:
            if self.scenarios_manager.delete_scenario(scenario_id):
                self.populate_scenarios_list()

    @pyqtSlot()
    def save_current_scenario_text(self):
        # Используем таймер, чтобы не сохранять на каждое нажатие клавиши
        if hasattr(self, '_save_timer'):
            self._save_timer.stop()
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self.save_current_scenario)
        self._save_timer.start(500) # Сохраняем через 0.5с после последнего изменения

    def save_current_scenario(self):
        """СОХРАНЯЕТ ИЗМЕНЕНИЯ В ТЕКУЩЕМ СЦЕНАРИИ."""
        current = self.scenarios_list.currentItem()
        if not current: return
        
        scenario_id = current.data(Qt.UserRole)
        new_name = self.scenario_name_edit.text()
        new_description = self.scenario_editor.toPlainText()
        
        # Обновляем и текст в списке, если имя изменилось
        if current.text() != new_name:
            current.setText(new_name)
            
        self.scenarios_manager.update_scenario(scenario_id, new_name, new_description)

    def open_insert_link_dialog(self):
        """ОТКРЫВАЕТ ДИАЛОГ ВСТАВКИ ССЫЛКИ."""
        workspace_path = self.settings_manager.settings.get("workspace_path")
        if not workspace_path:
            QMessageBox.warning(self, "Ошибка", "Сначала укажите папку с проектами в Настройках -> Рабочая область.")
            return

        dialog = InsertLinkDialog(workspace_path, self)
        # Делаем диалог немодальным
        dialog.setModal(False)
        dialog.show()
        # Подключаем сигнал о вставке
        dialog.accepted.connect(lambda: self.scenario_editor.insertPlainText(dialog.link_to_insert))
        # --- НАЧАЛО: ОБНОВЛЕНА ЛОГИКА ДЛЯ НЕМОДАЛЬНОГО ОКНА (v3.5) ---
        # Создаем диалог только один раз, чтобы он не плодился
        if not hasattr(self, '_insert_link_dialog') or not self._insert_link_dialog.isVisible():
            self._insert_link_dialog = InsertLinkDialog(workspace_path, self)
            self._insert_link_dialog.link_ready_to_insert.connect(self.scenario_editor.insertPlainText)
            self._insert_link_dialog.show()
        else:
            self._insert_link_dialog.activateWindow() # Если уже открыт, просто показываем поверх
    # --- КОНЕЦ: ОБНОВЛЕНА ЛОГИКА ДЛЯ НЕМОДАЛЬНОГО ОКНА (v3.5) ---
    # --- КОНЕЦ: НОВЫЕ МЕТОДЫ ДЛЯ ЛОГИКИ СЦЕНАРИЕВ (v3.4) ---

 # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА export_scenarios_to_markdown С ДОБАВЛЕНИЕМ "ШАПКИ" (v3.9) ---
    def export_scenarios_to_markdown(self):
        """ЭКСПОРТИРУЕТ ВСЕ СЦЕНАРИИ В ОДИН MD-ФАЙЛ С ПОЯСНЕНИЯМИ."""
        self.save_current_scenario() # Убедимся, что все последние изменения сохранены

        scenarios_list = self.scenarios_manager.get_scenarios_list()
        if not scenarios_list:
            QMessageBox.information(self, "Информация", "Нет сценариев для экспорта.")
            return

        output_dir = "scenarios"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "scenarios.md")

        md_content = []

        # --- "ШАПКА" ДОКУМЕНТА ---
        from datetime import datetime
        generation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        header = f"""# Пользовательские сценарии (User Flow)

**Дата генерации:** {generation_date}

Этот документ описывает ключевые пользовательские сценарии взаимодействия с интерфейсом. Каждый сценарий представляет собой последовательность действий пользователя и реакций системы.

---

## Условные обозначения

*   **`## Сценарий: [Имя сценария]`**: Заголовок, описывающий конкретный сценарий.
*   **`**scenario_id:** `[уникальный_id]`**: Уникальный идентификатор сценария.
*   **`[файл.json >>> Путь >>> Компонент (ID: `aabbccdd`)]`**: Стандартизированная ссылка на конкретный компонент интерфейса.
    *   **`файл.json`**: Имя файла спецификации (модуля), в котором описан компонент.
    *   **`Путь`**: Иерархия вложенности компонента. Разделитель `>>>` обозначает вложенность.
    *   **`Компонент`**: Имя самого компонента.
    *   **`ID`**: Уникальный идентификатор компонента для однозначной привязки.

---
"""
        md_content.append(header)
        # --- КОНЕЦ "ШАПКИ" ---

        for scenario in scenarios_list:
            md_content.append(f"## Сценарий: {scenario['name']}")
            md_content.append(f"**scenario_id:** `{scenario['id']}`\n")
            md_content.append(scenario.get('description', 'Нет описания.'))
            md_content.append("\n---\n")

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(md_content))
            QMessageBox.information(self, "Успех", f"Сценарии успешно экспортированы в:\n{output_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл сценариев:\n{e}")
    # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА export_scenarios_to_markdown С ДОБАВЛЕНИЕМ "ШАПКИ" (v3.9) ---

    def _create_menu_bar(self):
        menu_bar = self.menuBar(); file_menu = menu_bar.addMenu("Файл"); new_action = QAction("Новый проект", self); new_action.triggered.connect(self.new_project); file_menu.addAction(new_action); open_action = QAction("Открыть проект...", self); open_action.triggered.connect(self.open_project); file_menu.addAction(open_action); 
        
        
        # --- НАЧАЛО: ДОБАВЛЕНА ГОРЯЧАЯ КЛАВИША ДЛЯ СОХРАНЕНИЯ (v9.5) ---
        # --- БЫЛО: save_action = QAction("Сохранить", self); save_action.triggered.connect(self.save_project); file_menu.addAction(save_action);
        # --- СТАЛО: ---
        save_action = QAction("Сохранить (Ctrl+S)", self); save_action.setShortcut("Ctrl+S"); save_action.triggered.connect(self.save_project); file_menu.addAction(save_action)
        # --- КОНЕЦ: ДОБАВЛЕНА ГОРЯЧАЯ КЛАВИША ДЛЯ СОХРАНЕНИЯ (v9.5) ---
        
        save_as_action = QAction("Сохранить как...", self); save_as_action.triggered.connect(self.save_project_as); file_menu.addAction(save_as_action); file_menu.addSeparator() 
        # --- НАЧАЛО: ДОБАВЛЕН ПУНКТ ЭКСПОРТА ---
        export_action = QAction("Экспорт в Markdown...", self)
        export_action.triggered.connect(self.export_to_markdown)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        # --- КОНЕЦ: ДОБАВЛЕН ПУНКТ ЭКСПОРТА ---

        exit_action = QAction("Выход", self); exit_action.triggered.connect(self.close); file_menu.addAction(exit_action)

        # --- НАЧАЛО: ДОБАВЛЕНО МЕНЮ "СЦЕНАРИИ" (v3.8) ---
        scenarios_menu = menu_bar.addMenu("Сценарии")
        export_scenarios_action = QAction("Экспорт в Markdown...", self)
        export_scenarios_action.triggered.connect(self.export_scenarios_to_markdown)
        scenarios_menu.addAction(export_scenarios_action)
        # --- КОНЕЦ: ДОБАВЛЕНО МЕНЮ "СЦЕНАРИИ" (v3.8) ---

         # --- НАЧАЛО: ДОБАВЛЕНО МЕНЮ "СПРАВКА" (v15.8) ---
        help_menu = menu_bar.addMenu("Справка")
        
        help_action = QAction("Показать справку", self)
        help_action.triggered.connect(self.show_help_dialog)
        help_menu.addAction(help_action)

        help_menu.addSeparator()

        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        # --- КОНЕЦ: ДОБАВЛЕНО МЕНЮ "СПРАВКА" (v15.8) ---

# --- НАЧАЛО: НОВЫЙ МЕТОД ДЛЯ СОЗДАНИЯ И НАПОЛНЕНИЯ СТАТУС-БАРА (v10.1) ---
    def _create_status_bar(self):
        """СОЗДАЕТ СТАТУС-БАР И РАЗМЕЩАЕТ НА НЕМ ВИДЖЕТЫ."""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # 1. ВИДЖЕТ ДЛЯ ОТОБРАЖЕНИЯ ПУТИ К ФАЙЛУ ПРОЕКТА
        self.project_path_label = QLabel("Проект не сохранен")
        self.project_path_label.setMinimumWidth(300)
        # --- НАЧАЛО: ИЗМЕНЕН СПОСОБ ДОБАВЛЕНИЯ ВИДЖЕТА ДЛЯ ВЫРАВНИВАНИЯ ПО ЛЕВОМУ КРАЮ (v10.2) ---
        # --- БЫЛО: self.statusBar.addPermanentWidget(self.project_path_label)
        # --- СТАЛО: ---
        self.statusBar.addWidget(self.project_path_label)
        # --- КОНЕЦ: ИЗМЕНЕН СПОСОБ ДОБАВЛЕНИЯ ВИДЖЕТА ДЛЯ ВЫРАВНИВАНИЯ ПО ЛЕВОМУ КРАЮ (v10.2) ---

        # 2. ВИДЖЕТ ДЛЯ ОТОБРАЖЕНИЯ КООРДИНАТ КУРСОРА
        self.coords_label = QLabel("X: ---, Y: ---")
        self.coords_label.setMinimumWidth(150)
        self.statusBar.addPermanentWidget(self.coords_label)
        
        # 3. ВИДЖЕТЫ ДЛЯ УПРАВЛЕНИЯ МАСШТАБОМ
        self.zoom_label = QLabel("Масштаб:")
        self.statusBar.addPermanentWidget(self.zoom_label)
        
        self.zoom_combo = QComboBox()
        zoom_levels = ["25%", "50%", "75%", "100%", "150%", "200%", "400%"]
        self.zoom_combo.addItems(zoom_levels)
        self.zoom_combo.setCurrentText("100%")
        # --- НАЧАЛО: РАЗРЕШАЕМ РЕДАКТИРОВАНИЕ ДЛЯ ОТОБРАЖЕНИЯ ПРОМЕЖУТОЧНЫХ ЗНАЧЕНИЙ (v10.4) ---
        self.zoom_combo.setEditable(True)
        # --- КОНЕЦ: РАЗРЕШАЕМ РЕДАКТИРОВАНИЕ ДЛЯ ОТОБРАЖЕНИЯ ПРОМЕЖУТОЧНЫХ ЗНАЧЕНИЙ (v10.4) ---
         # --- НАЧАЛО: ИСПРАВЛЕНИЕ НЕПРАВИЛЬНОГО ПОДКЛЮЧЕНИЯ СИГНАЛОВ (v10.7) ---
        # --- БЫЛО: self.zoom_combo.editingFinished.connect(self.set_zoom_from_combo)
        # --- СТАЛО: ---
        # ПОДКЛЮЧАЕМ ДВА СИГНАЛА ДЛЯ ПОЛНОЙ ФУНКЦИОНАЛЬНОСТИ:
        # 1. ДЛЯ РУЧНОГО ВВОДА (КОГДА НАЖАТ ENTER)
        self.zoom_combo.lineEdit().editingFinished.connect(self.set_zoom_from_combo)
        # 2. ДЛЯ ВЫБОРА ИЗ СПИСКА
        self.zoom_combo.activated.connect(self.set_zoom_from_combo)
        # --- КОНЕЦ: ИСПРАВЛЕНИЕ НЕПРАВИЛЬНОГО ПОДКЛЮЧЕНИЯ СИГНАЛОВ (v10.7) ---
        self.statusBar.addPermanentWidget(self.zoom_combo)
    # --- КОНЕЦ: НОВЫЙ МЕТОД ДЛЯ СОЗДАНИЯ И НАПОЛНЕНИЯ СТАТУС-БАРА (v10.1) ---

# --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА open_settings_dialog НА ФИНАЛЬНУЮ ЧИСТУЮ ВЕРСИЮ (v16.2) ---
    def open_settings_dialog(self):
        """СОЗДАЕТ, ПОКАЗЫВАЕТ ДИАЛОГ НАСТРОЕК И ПРИМЕНЯЕТ ИЗМЕНЕНИЯ."""
        dialog = SettingsDialog(self.settings_manager, self)
        
        if dialog.exec_() == QDialog.Accepted:
            # ЕСЛИ ПОЛЬЗОВАТЕЛЬ НАЖАЛ "OK", ПРОСТО ПРИМЕНЯЕМ НОВЫЕ СТИЛИ
            self.apply_styles_to_all_items()
            # --- НАЧАЛО: ДОБАВЬ ЭТУ СТРОКУ (v2.0.5) ---
            self.on_tree_item_selected(self.project_tree.currentItem(), None)
            # --- КОНЕЦ: ДОБАВЬ ЭТУ СТРОКУ (v2.0.5) ---
        else:
            # ЕСЛИ ПОЛЬЗОВАТЕЛЬ НАЖАЛ "ОТМЕНА", МЫ ДОЛЖНЫ ВЕРНУТЬ СТАРЫЕ НАСТРОЙКИ,
            # ТАК КАК В ДИАЛОГЕ ОНИ МОГЛИ БЫТЬ ВРЕМЕННО ИЗМЕНЕНЫ
            self.settings_manager.settings = self.settings_manager.load_settings()
    # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА open_settings_dialog НА ФИНАЛЬНУЮ ЧИСТУЮ ВЕРСИЮ (v16.2) ---

    # --- НАЧАЛО: НОВЫЙ МЕТОД ДЛЯ ВЫЗОВА УПРАВЛЕНИЯ ШАБЛОНАМИ (v15.7) ---
    def open_manage_templates_dialog(self):
        """Открывает диалог для управления (переименования/удаления) шаблонов."""
        dialog = ManageTemplatesDialog(self.templates_manager, self)
        dialog.exec_()
    # --- КОНЕЦ: НОВЫЙ МЕТОД ДЛЯ ВЫЗОВА УПРАВЛЕНИЯ ШАБЛОНАМИ (v15.7) ---

    # --- НАЧАЛО: НОВЫЕ МЕТОДЫ ДЛЯ ПОКАЗА СПРАВКИ И "О ПРОГРАММЕ" (v15.8) ---
    def show_help_dialog(self):
        """Показывает диалоговое окно со справкой."""
        dialog = HelpDialog(self)
        dialog.exec_()
        
    def show_about_dialog(self):
        """Показывает диалоговое окно "О программе"."""
        dialog = AboutDialog(self)
        dialog.exec_()
    # --- КОНЕЦ: НОВЫЕ МЕТОДЫ ДЛЯ ПОКАЗА СПРАВКИ И "О ПРОГРАММЕ" (v15.8) ---

 # --- НАЧАЛО: НОВЫЙ МЕТОД ДЛЯ ПРИМЕНЕНИЯ СТИЛЕЙ (v9.9) ---
    def apply_styles_to_all_items(self):
        """ПЕРЕДАЕТ ТЕКУЩИЕ НАСТРОЙКИ СТИЛЕЙ ВСЕМ ЭЛЕМЕНТАМ НА СЦЕНЕ."""
        active_style = self.settings_manager.get_style("active")
        inactive_style = self.settings_manager.get_style("inactive")
        for item in self.scene_items_map.values():
            item.apply_styles(active_style, inactive_style)
    # --- КОНЕЦ: НОВЫЙ МЕТОД ДЛЯ ПРИМЕНЕНИЯ СТИЛЕЙ (v9.9) ---

   # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА load_background_image С ПРОВЕРКОЙ НА СОХРАНЕНИЕ ПРОЕКТА (v9.4) ---
    def load_background_image(self):
        selected = self.project_tree.currentItem()
        # НАВИГАЦИЯ К КОРНЕВОМУ ЭЛЕМЕНТУ
        if selected:
            while selected.parent() and selected.parent() != self.components_root_item:
                selected = selected.parent()
        
        if not selected or selected.parent() != self.components_root_item:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите экран (элемент верхнего уровня) для загрузки фона.")
            return

        # --- КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: ПРОВЕРКА, СОХРАНЕН ЛИ ПРОЕКТ ---
        if not self.current_project_path:
            QMessageBox.information(self, "Требуется сохранение", "Для добавления фона необходимо сначала сохранить проект.")
            if not self.save_project_as(): # ВЫЗЫВАЕМ ДИАЛОГ "СОХРАНИТЬ КАК..."
                return # ЕСЛИ ПОЛЬЗОВАТЕЛЬ НАЖАЛ "ОТМЕНА", ВЫХОДИМ

        item_id = selected.data(0, Qt.UserRole)
        item_data = self._find_item_data(item_id)
        if not item_data: return

        # ПРОДОЛЖАЕМ РАБОТУ, ТЕПЕРЬ У НАС ТОЧНО ЕСТЬ ПУТЬ К ПРОЕКТУ
        last_path = os.path.dirname(self.current_project_path)
        path, _ = QFileDialog.getOpenFileName(self, "Выбрать изображение-прототип", last_path, "Image Files (*.png *.jpg *.jpeg *.bmp)")
        
        if path:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                project_dir = os.path.dirname(self.current_project_path)
                relative_path = os.path.relpath(path, project_dir)
                item_data['background_image'] = relative_path
                self._mark_as_dirty()
                
                # ОБНОВЛЯЕМ ИНТЕРФЕЙС, ЧТОБЫ ФОН СРАЗУ ПОЯВИЛСЯ
                self.on_tree_item_selected(self.project_tree.currentItem(), None)
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение.")
# --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА load_background_image С ПРОВЕРКОЙ НА СОХРАНЕНИЕ ПРОЕКТА (v9.4) ---

# --- НАЧАЛО: ФУНКЦИЯ _mark_as_dirty ПОЛНАЯ ЗАМЕНА (v1.2) ---
    def _mark_as_dirty(self):
        """ПОМЕЧАЕТ ПРОЕКТ КАК ИЗМЕНЕННЫЙ."""
        if not self.is_dirty:
            self.is_dirty = True
            self.setWindowTitle(self.windowTitle() + " -> (необходимо сохранить проект!!)")
# --- КОНЕЦ: ФУНКЦИЯ _mark_as_dirty ПОЛНАЯ ЗАМЕНА (v1.2) ---



# --- НАЧАЛО: ФУНКЦИЯ _update_ui_for_new_project ПОЛНАЯ ЗАМЕНА (Graph.v2.3) ---
    def _update_ui_for_new_project(self):
        self.project_tree.setUpdatesEnabled(False)
        
        # --- ИСПРАВЛЕНИЕ: ОЧИЩАЕМ ВСЕ, ВКЛЮЧАЯ ФОН ---
        self.scene.clear()
        # --- НАЧАЛО: ДОБАВЛЕНА ОЧИСТКА КАРТЫ ЭЛЕМЕНТОВ (v8.0) ---
        self.scene_items_map.clear()
        # --- КОНЕЦ: ДОБАВЛЕНА ОЧИСТКА КАРТЫ ЭЛЕМЕНТОВ (v8.0) ---
        self.background_item = QGraphicsPixmapItem() # Создаем новый пустой фон
        self.scene.addItem(self.background_item)
        
        self.components_root_item.takeChildren()
        self._populate_tree_and_canvas_recursively(self.components_root_item, self.project_data.get('tree', {}))
        
        self.project_tree.expandAll()
        self.project_tree.setUpdatesEnabled(True)
        self.concept_editor.setPlainText(self.project_data.get('concept', {}).get('description', ''))
        
        # Сбрасываем флаг и заголовок
        self.is_dirty = False
        self.setWindowTitle(f"{self.APP_VERSION_TITLE} - Новый проект")
        # --- НАЧАЛО: ОБНОВЛЕНИЕ СТАТУС-БАРА ПРИ СОЗДАНИИ НОВОГО ПРОЕКТА (v10.1) ---
        self.project_path_label.setText("Новый проект (не сохранен)")
        # --- КОНЕЦ: ОБНОВЛЕНИЕ СТАТУС-БАРА ПРИ СОЗДАНИИ НОВОГО ПРОЕКТА (v10.1) ---
        self.on_tree_item_selected(None, None) # Вызываем с пустым значением, чтобы все очистилось
        # --- НАЧАЛО: ПРИМЕНЯЕМ СТИЛИ ПОСЛЕ ЗАГРУЗКИ ПРОЕКТА (v9.9) ---
        self.apply_styles_to_all_items()
        # --- КОНЕЦ: ПРИМЕНЯЕМ СТИЛИ ПОСЛЕ ЗАГРУЗКИ ПРОЕКТА (v9.9) ---
# --- КОНЕЦ: ФУНКЦИЯ _update_ui_for_new_project ПОЛНАЯ ЗАМЕНА (Graph.v2.3) ---


 # --- НАЧАЛО: ФУНКЦИЯ _populate_tree_and_canvas_recursively ПОЛНАЯ ЗАМЕНА (Graph.v2.0) ---
    def _populate_tree_and_canvas_recursively(self, parent_item, children_data):
        for item_id, item_data in children_data.items():
            child_item = QTreeWidgetItem(parent_item, [item_data.get('name', '')])
            child_item.setData(0, Qt.UserRole, item_id)
            
            # ДОБАВЛЯЕМ ПРЯМОУГОЛЬНИК НА СЦЕНУ, ЕСЛИ ЕСТЬ ДАННЫЕ
            pos_prop = next((p for p in item_data.get('properties', []) if p['key'] == 'position'), None)
            size_prop = next((p for p in item_data.get('properties', []) if p['key'] == 'size'), None)
            if pos_prop and size_prop:
                try:
                    x, y = map(int, pos_prop['value'].split(','))
                    w, h = map(int, size_prop['value'].split(','))
                    rect_item = BoundRectItem(QRectF(x, y, w, h), item_id)
                    self.scene.addItem(rect_item)
                    # --- НАЧАЛО: ДОБАВЛЕНА РЕГИСТРАЦИЯ ЭЛЕМЕНТА И ПОДПИСКА НА СОБЫТИЯ (v8.0) ---
                    self.scene_items_map[item_id] = rect_item
                     # --- НАЧАЛО: ПРИМЕНЯЕМ СТИЛИ К НОВОМУ ЭЛЕМЕНТУ (v9.9) ---
                    rect_item.apply_styles(self.settings_manager.get_style("active"), self.settings_manager.get_style("inactive"))
                    # --- КОНЕЦ: ПРИМЕНЯЕМ СТИЛИ К НОВОМУ ЭЛЕМЕНТУ (v9.9) ---
                    rect_item.geometryChanged.connect(self.on_item_geometry_changed_on_canvas)
                    # --- КОНЕЦ: ДОБАВЛЕНА РЕГИСТРАЦИЯ ЭЛЕМЕНТА И ПОДПИСКА НА СОБЫТИЯ (v8.0) ---
                except:
                    pass # Игнорируем ошибки парсинга
            
            self._populate_tree_and_canvas_recursively(child_item, item_data.get('children', {}))
# --- КОНЕЦ: ФУНКЦИЯ _populate_tree_and_canvas_recursively ПОЛНАЯ ЗАМЕНА (Graph.v2.0) ---

 # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА on_tree_item_selected С QSTACKEDWIDGET (v3.2-fix) ---
    def on_tree_item_selected(self, current_item, previous_item):
        # Если ничего не выбрано (например, при запуске), скрываем все панели
        if not current_item:
            self.right_stack.setCurrentWidget(self.right_panel)
            self.concept_editor_widget.hide()
            self.globals_editor_widget.hide()
            self.properties_widget.hide()
            return

        item_id = current_item.data(0, Qt.UserRole)
        is_scenarios = (item_id == "scenarios_id")
        
        # ШАГ 1: ПЕРЕКЛЮЧАЕМ ОСНОВНУЮ ПРАВУЮ ПАНЕЛЬ
        if is_scenarios:
            self.right_stack.setCurrentWidget(self.scenarios_panel)
            self.populate_scenarios_list() # <--- ДОБАВЬТЕ ЭТУ СТРОКУ
            # Для сценариев холст не нужен, очищаем его
            for item in self.scene_items_map.values(): item.setVisible(False)
            self.background_item.setPixmap(QPixmap())
            return # Завершаем, так как для сценариев больше ничего делать не нужно
        else:
            self.right_stack.setCurrentWidget(self.right_panel)

        # ШАГ 2: УПРАВЛЯЕМ ВИДИМОСТЬЮ ВНУТРЕННИХ ПАНЕЛЕЙ (Концепция, Глобальные, Свойства)
        is_concept = (item_id == "concept_id")
        is_globals = (item_id == "globals_id")
        is_components_root = (item_id == "components_root_id")
        is_regular_item = not (is_concept or is_globals or is_scenarios or is_components_root)

        self.concept_editor_widget.setVisible(is_concept)
        self.globals_editor_widget.setVisible(is_globals)
        self.properties_widget.setVisible(is_regular_item)
        
        # ШАГ 3: ОБНОВЛЯЕМ ХОЛСТ
        # Сбрасываем выделение и скрываем все графические элементы
        for item in self.scene_items_map.values():
            item.reset_to_default_style(is_selected=False)
            item.setVisible(False)
        self.background_item.setPixmap(QPixmap())

        # Если выбран компонент, показываем его "экран"
        if is_regular_item or is_components_root:
            top_level_item = current_item
            if is_components_root and top_level_item.childCount() > 0:
                 top_level_item = top_level_item.child(0) # Если выбран корень, покажем первый экран
            
            while top_level_item.parent() and top_level_item.parent() != self.components_root_item:
                top_level_item = top_level_item.parent()
            
            if top_level_item and top_level_item.parent() == self.components_root_item:
                parent_id = top_level_item.data(0, Qt.UserRole)
                parent_data = self._find_item_data(parent_id)
                if parent_data:
                    bg_path = parent_data.get('background_image')
                    if bg_path and self.current_project_path:
                        project_dir = os.path.dirname(self.current_project_path)
                        full_path = os.path.join(project_dir, bg_path)
                        if os.path.exists(full_path):
                            pixmap = QPixmap(full_path)
                            self.background_item.setPixmap(pixmap)
                            self.scene.setSceneRect(QRectF(pixmap.rect()))
                
                def show_children_recursively(item_data_to_show):
                    for child_id, child_data in item_data_to_show.get('children', {}).items():
                        if child_id in self.scene_items_map:
                            self.scene_items_map[child_id].setVisible(True)
                        show_children_recursively(child_data)
                
                if parent_id in self.scene_items_map:
                    self.scene_items_map[parent_id].setVisible(True)
                if parent_data:
                    show_children_recursively(parent_data)

        # ШАГ 4: ЗАПОЛНЯЕМ ПАНЕЛИ ДАННЫМИ И ПРИМЕНЯЕМ СТИЛИ
        if is_regular_item:
            self._populate_properties_panel(current_item, item_id)
            self._populate_events_panel(current_item, item_id)
            self._populate_relations_panel(current_item, item_id) # Передаем item, а не id
            
            if item_id in self.scene_items_map:
                scene_item = self.scene_items_map[item_id]
                scene_item.reset_to_default_style(is_selected=True)
                scene_item.setSelected(True)
                self._apply_relation_highlights(item_id)
    # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА on_tree_item_selected С QSTACKEDWIDGET (v3.2-fix) ---

    # --- НАЧАЛО: ФУНКЦИЯ _populate_properties_panel ПОЛНАЯ ЗАМЕНА (v1.2) ---
    def _populate_properties_panel(self, item, item_id):
        item_data = self._find_item_data(item_id)
        if not item_data: return
        
        # БЛОКИРУЕМ ВСЕ СИГНАЛЫ ПЕРЕД ЗАПОЛНЕНИЕМ
        self.name_editor.blockSignals(True); self.description_editor.blockSignals(True)
        self.properties_table.blockSignals(True); self.type_combo.blockSignals(True)
        
        self.name_editor.setText(item_data.get('name', ''))
        
         # --- НАЧАЛО: ОТОБРАЖАЕМ КОРОТКИЙ ID (v3.6) ---
        self.id_display.setText(item_id.split('-')[0])
        # --- КОНЕЦ: ОТОБРАЖАЕМ КОРОТКИЙ ID (v3.6) ---

        # ИЩЕМ ИНДЕКС ПО ТЕХНИЧЕСКОМУ ИМЕНИ (ДАННЫМ)
        item_type_key = item_data.get('type', 'Custom')
        index = self.type_combo.findData(item_type_key)
        if index != -1:
            self.type_combo.setCurrentIndex(index)
        else: # Если типа нет в списке, ставим "Пользовательский"
            index = self.type_combo.findData('Custom')
            if index != -1: self.type_combo.setCurrentIndex(index)

        self.description_editor.setPlainText(item_data.get('description', ''))
        
        self.properties_table.setRowCount(0)
        for prop in item_data.get('properties', []):
            row = self.properties_table.rowCount()
            self.properties_table.insertRow(row)
            name_item = QTableWidgetItem(prop.get('name', ''))
            key_item = QTableWidgetItem(prop.get('key', ''))
            # --- НАЧАЛО: ДОБАВЛЕНА СТРОКА ДЛЯ СОХРАНЕНИЯ ФЛАГА СВОЙСТВА (v7.2) ---
            key_item.setData(Qt.UserRole, prop.get('is_predefined', False))
            # --- КОНЕЦ: ДОБАВЛЕНА СТРОКА ДЛЯ СОХРАНЕНИЯ ФЛАГА СВОЙСТВА (v7.2) ---
            value_item = QTableWidgetItem(prop.get('value', ''))
            if prop.get('is_predefined', False):
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
            self.properties_table.setItem(row, 0, name_item)
            self.properties_table.setItem(row, 1, key_item)
            self.properties_table.setItem(row, 2, value_item)
            # --- НАЧАЛО: РАСКРАШИВАЕМ ЯЧЕЙКУ ПРИ ЗАГРУЗКЕ (v12.0) ---
            self._colorize_property_cell(row, 2)
            # --- КОНЕЦ: РАСКРАШИВАЕМ ЯЧЕЙКУ ПРИ ЗАГРУЗКЕ (v12.0) ---

        # РАЗБЛОКИРУЕМ СИГНАЛЫ ПОСЛЕ ЗАПОЛНЕНИЯ
        self.name_editor.blockSignals(False); self.description_editor.blockSignals(False)
        self.properties_table.blockSignals(False); self.type_combo.blockSignals(False)
# --- КОНЕЦ: ФУНКЦИЯ _populate_properties_panel ПОЛНАЯ ЗАМЕНА (v1.2) ---
    
    def _find_item_data(self, item_id, data_root=None, delete=False):
        if data_root is None: data_root = self.project_data['tree']
        if item_id in data_root:
            if delete: data = data_root[item_id]; del data_root[item_id]; return data
            return data_root[item_id]
        for key, value in data_root.items():
            found = self._find_item_data(item_id, value.get('children', {}), delete);
            if found: return found
        return None
    
    # --- НАЧАЛО: ДОБАВЛЕНА НОВАЯ УНИВЕРСАЛЬНАЯ ФУНКЦИЯ ADD_ITEM ---
    def add_item(self):
        selected_item = self.project_tree.currentItem()
        
        # ОПРЕДЕЛЯЕМ РОДИТЕЛЯ ДЛЯ НОВОГО ЭЛЕМЕНТА
        parent_item = None
        if not selected_item or selected_item in [self.concept_item, self.globals_item, self.components_root_item]:
            parent_item = self.components_root_item
        else:
            parent_item = selected_item
        
        name, ok = QInputDialog.getText(self, "Новый элемент", "Имя элемента:")
        if ok and name:
            self._add_item_to_tree(parent_item, name)
# --- КОНЕЦ: ДОБАВЛЕНА НОВАЯ УНИВЕРСАЛЬНАЯ ФУНКЦИЯ ADD_ITEM ---
    
    # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА ЛОГИКИ ДОБАВЛЕНИЯ ЭЛЕМЕНТОВ ---
    def add_child_item(self):
        selected_item = self.project_tree.currentItem()
        
        # Определяем родителя: либо выбранный элемент, либо корень компонентов
        if not selected_item or selected_item in [self.concept_item, self.globals_item, self.components_root_item]:
            parent_item = self.components_root_item
        else:
            parent_item = selected_item
        self._add_item_to_tree(parent_item)

    def add_sibling_item(self):
        selected_item = self.project_tree.currentItem()

        # Определяем родителя: либо родитель выбранного, либо корень компонентов
        if not selected_item or not selected_item.parent() or selected_item.parent() == self.project_tree.invisibleRootItem():
            parent_item = self.components_root_item
        else:
            parent_item = selected_item.parent()
        self._add_item_to_tree(parent_item)

# --- НАЧАЛО: ФУНКЦИЯ _add_item_to_tree ПОЛНАЯ ЗАМЕНА (Graph.v1.5.1) ---
    def _add_item_to_tree(self, parent_item, name=None):
        if name is None:
            name, ok = QInputDialog.getText(self, "Новый элемент", "Имя элемента:")
            if not (ok and name): return None # Возвращаем None, если пользователь нажал "Отмена"
        
        item_id = str(uuid.uuid4())
        
        default_properties = [
            {'name': 'Видимость', 'key': 'visible', 'value': 'true', 'is_predefined': True},
            {'name': 'Доступность', 'key': 'enabled', 'value': 'true', 'is_predefined': True}
        ]
        # --- ИЗМЕНЕНИЕ: ДОБАВЛЕНО ПОЛЕ ДЛЯ ФОНА ---
        new_data = {'name': name, 'type': 'Frame', 'background_image': None, 'description': '', 'properties': default_properties, 'events': [], 'children': {}}

        # Добавляем данные в модель
        if parent_item == self.components_root_item:
            self.project_data['tree'][item_id] = new_data
        else:
            parent_id = parent_item.data(0, Qt.UserRole)
            parent_data = self._find_item_data(parent_id)
            if parent_data:
                if 'children' not in parent_data: parent_data['children'] = {}
                parent_data['children'][item_id] = new_data
        
        # Добавляем элемент в UI
        new_ui_item = QTreeWidgetItem(parent_item, [name])
        new_ui_item.setData(0, Qt.UserRole, item_id)
        parent_item.setExpanded(True)
        self.project_tree.setCurrentItem(new_ui_item)
        
        # --- ДОБАВЛЕНА УСТАНОВКА ФЛАГА ИЗМЕНЕНИЙ ---
        self._mark_as_dirty()
        
        # --- ВОЗВРАЩАЕМ СОЗДАННЫЙ ЭЛЕМЕНТ ---
        return new_ui_item
# --- КОНЕЦ: ФУНКЦИЯ _add_item_to_tree ПОЛНАЯ ЗАМЕНА (Graph.v1.5.1) ---

# --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА add_item_from_template С ИСПРАВЛЕНИЕМ ОБНОВЛЕНИЯ UI (v13.4) ---
    def add_item_from_template(self):
        """ОТКРЫВАЕТ ДИАЛОГ ВЫБОРА ШАБЛОНА И СОЗДАЕТ НОВЫЙ ЭЛЕМЕНТ."""
        templates_list = self.templates_manager.get_templates_list()
        if not templates_list:
            QMessageBox.information(self, "Информация", "Нет сохраненных шаблонов.")
            return

        dialog = SelectTemplateDialog(templates_list, self)
        if dialog.exec() != QDialog.Accepted:
            return

        template_id = dialog.get_selected_template_id()
        if not template_id:
            return

        template_data = self.templates_manager.get_template_data(template_id)
        if not template_data:
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить данные шаблона.")
            return

        selected_item = self.project_tree.currentItem()
        parent_ui_item = self.components_root_item
        
        if selected_item and selected_item.parent():
            parent_ui_item = selected_item

        parent_data_dict = self.project_data['tree']
        if parent_ui_item != self.components_root_item:
            parent_id = parent_ui_item.data(0, Qt.UserRole)
            parent_model_data = self._find_item_data(parent_id)
            if parent_model_data:
                if 'children' not in parent_model_data:
                    parent_model_data['children'] = {}
                parent_data_dict = parent_model_data['children']
            else:
                QMessageBox.critical(self, "Ошибка", f"Не удалось найти данные для родительского элемента {parent_ui_item.text(0)}.")
                return

        def remap_uuids_and_recreate_items(parent_ui, parent_data_container, template_node_data):
            """РЕКУРСИВНО СОЗДАЕТ НОВЫЕ ЭЛЕМЕНТЫ В UI И МОДЕЛИ С НОВЫМИ ID."""
            new_id = str(uuid.uuid4())
            new_data = template_node_data # ИСПОЛЬЗУЕМ КОПИЮ ИЗ МЕНЕДЖЕРА
            
            parent_data_container[new_id] = new_data
            
            # СОЗДАЕМ UI ЭЛЕМЕНТ
            new_ui_item = QTreeWidgetItem(parent_ui, [new_data.get('name', 'Без имени')])
            new_ui_item.setData(0, Qt.UserRole, new_id)
            
            # СОЗДАЕМ ЭЛЕМЕНТ НА ХОЛСТЕ
            pos_prop = next((p for p in new_data.get('properties', []) if p['key'] == 'position'), None)
            size_prop = next((p for p in new_data.get('properties', []) if p['key'] == 'size'), None)
            if pos_prop and size_prop:
                try:
                    x, y = map(int, pos_prop['value'].split(','))
                    w, h = map(int, size_prop['value'].split(','))
                    rect_item = BoundRectItem(QRectF(x, y, w, h), new_id)
                    self.scene.addItem(rect_item)
                    self.scene_items_map[new_id] = rect_item
                    rect_item.apply_styles(self.settings_manager.get_style("active"), self.settings_manager.get_style("inactive"))
                    rect_item.geometryChanged.connect(self.on_item_geometry_changed_on_canvas)
                except (ValueError, IndexError):
                    pass
            
            # РЕКУРСИЯ ДЛЯ ДОЧЕРНИХ ЭЛЕМЕНТОВ
            children_data = new_data.get('children', {})
            if children_data:
                new_data['children'] = {}
                for _, child_data in children_data.items():
                    remap_uuids_and_recreate_items(new_ui_item, new_data['children'], child_data)
        
        remap_uuids_and_recreate_items(parent_ui_item, parent_data_dict, template_data)
        
        parent_ui_item.setExpanded(True)
        self._mark_as_dirty() # <-- УСТАНАВЛИВАЕМ ФЛАГ ИЗМЕНЕНИЙ

        # ВМЕСТО ПОЛНОЙ ПЕРЕЗАГРУЗКИ ПРОСТО ОБНОВЛЯЕМ ВИД ХОЛСТА
        self.on_tree_item_selected(self.project_tree.currentItem(), None)
    # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА add_item_from_template С ИСПРАВЛЕНИЕМ ОБНОВЛЕНИЯ UI (v13.4) ---

 # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА update_item_rect НА БЕЗОПАСНУЮ ВЕРСИЮ (v16.7) ---
    def update_item_rect(self, rect):
        """ПРИВЯЗЫВАЕТ ИЛИ ОБНОВЛЯЕТ ГЕОМЕТРИЮ ВЫБРАННОГО ЭЛЕМЕНТА."""
        selected_item = self.project_tree.currentItem()
        if not selected_item or not selected_item.parent():
            QMessageBox.warning(self, "Ошибка", "Сначала выберите элемент в иерархии компонентов.")
            return

        item_id = selected_item.data(0, Qt.UserRole)
        item_data = self._find_item_data(item_id)
        if not item_data: return

        # ПРОВЕРЯЕМ, СУЩЕСТВУЕТ ЛИ УЖЕ ПРЯМОУГОЛЬНИК ДЛЯ ЭТОГО ЭЛЕМЕНТА
        if item_id in self.scene_items_map:
            # ЕСЛИ ДА - ПРОСТО ОБНОВЛЯЕМ ЕГО ГЕОМЕТРИЮ
            scene_item = self.scene_items_map[item_id]
            scene_item.setRect(rect)
        else:
            # ЕСЛИ НЕТ - СОЗДАЕМ НОВЫЙ
            rect_item = BoundRectItem(rect, item_id)
            self.scene.addItem(rect_item)
            self.scene_items_map[item_id] = rect_item
            rect_item.apply_styles(self.settings_manager.get_style("active"), self.settings_manager.get_style("inactive"))
            rect_item.geometryChanged.connect(self.on_item_geometry_changed_on_canvas)

        # ПОДСВЕЧИВАЕМ ЭЛЕМЕНТ
        self.scene_items_map[item_id].setSelected(True)
        self.scene_items_map[item_id].set_selected_visual(True)
        
        # ОБНОВЛЯЕМ СВОЙСТВА В МОДЕЛИ ДАННЫХ
        pos_str = f"{int(rect.x())}, {int(rect.y())}"
        size_str = f"{int(rect.width())}, {int(rect.height())}"
        
        pos_prop = next((p for p in item_data['properties'] if p.get('key') == 'position'), None)
        if pos_prop: pos_prop['value'] = pos_str
        else: item_data['properties'].append({'name': 'Положение (X, Y)', 'key': 'position', 'value': pos_str, 'is_predefined': True})
        
        size_prop = next((p for p in item_data['properties'] if p.get('key') == 'size'), None)
        if size_prop: size_prop['value'] = size_str
        else: item_data['properties'].append({'name': 'Размер (Width, Height)', 'key': 'size', 'value': size_str, 'is_predefined': True})

        self._populate_properties_panel(selected_item, item_id)
        self._mark_as_dirty()
    # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА update_item_rect НА БЕЗОПАСНУЮ ВЕРСИЮ (v16.7) ---


 # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА select_item_in_tree ДЛЯ ОБРАБОТКИ РЕЖИМА СВЯЗЕЙ (v2.1-fix) ---
    def select_item_in_tree(self, item_id):
        """ОБРАБАТЫВАЕТ КЛИК ПО ЭЛЕМЕНТУ НА ХОЛСТЕ."""
        # ЕСЛИ АКТИВЕН РЕЖИМ СОЗДАНИЯ СВЯЗЕЙ, ПЕРЕДАЕМ УПРАВЛЕНИЕ ЕМУ
        if self.relation_mode_active:
            self.handle_item_click_in_relation_mode(item_id)
            return

        # В ОБЫЧНОМ РЕЖИМЕ - ПРОСТО ВЫДЕЛЯЕМ ЭЛЕМЕНТ В ДЕРЕВЕ
        if self.project_tree.signalsBlocked():
            return
            
        self.project_tree.blockSignals(True)
        iterator = QTreeWidgetItemIterator(self.project_tree)
        while iterator.value():
            item = iterator.value()
            if item and item.data(0, Qt.UserRole) == item_id:
                self.project_tree.setCurrentItem(item)
                # Вызываем on_tree_item_selected вручную, чтобы обновить все
                self.on_tree_item_selected(item, None)
                break
            iterator += 1
        self.project_tree.blockSignals(False)
    # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА select_item_in_tree ДЛЯ ОБРАБОТКИ РЕЖИМА СВЯЗЕЙ (v2.1-fix) ---

    # --- НАЧАЛО: ИЗМЕНЕНИЕ ФУНКЦИИ УДАЛЕНИЯ С ОЧИСТКОЙ СЦЕНЫ (v8.0) ---
    def remove_item(self):
        sel = self.project_tree.currentItem();
        if not sel or not sel.parent() or sel in [self.concept_item, self.globals_item, self.components_root_item]: return
        
        reply = QMessageBox.question(self, 'Удаление', f"Удалить '{sel.text(0)}' и всех его потомков?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # СОБИРАЕМ ID ВСЕХ УДАЛЯЕМЫХ ЭЛЕМЕНТОВ (ВКЛЮЧАЯ ДОЧЕРНИЕ)
            ids_to_remove = []
            iterator = QTreeWidgetItemIterator(sel)
            while iterator.value():
                ids_to_remove.append(iterator.value().data(0, Qt.UserRole))
                iterator += 1
            
            # УДАЛЯЕМ ЭЛЕМЕНТЫ СО СЦЕНЫ И ИЗ КАРТЫ
            for item_id in ids_to_remove:
                if item_id in self.scene_items_map:
                    self.scene.removeItem(self.scene_items_map[item_id])
                    del self.scene_items_map[item_id]

            # УДАЛЯЕМ ЭЛЕМЕНТ ИЗ МОДЕЛИ ДАННЫХ И ДЕРЕВА UI
            item_id = sel.data(0, Qt.UserRole)
            self._find_item_data(item_id, delete=True)
            (sel.parent() or self.project_tree.invisibleRootItem()).removeChild(sel)

            self._mark_as_dirty()
    # --- КОНЕЦ: ИЗМЕНЕНИЕ ФУНКЦИИ УДАЛЕНИЯ С ОЧИСТКОЙ СЦЕНЫ (v8.0) ---

# --- НАЧАЛО: ФУНКЦИЯ move_item ПОЛНАЯ ЗАМЕНА (Graph.vFINAL) ---
    def move_item(self, direction):
        """ПЕРЕМЕЩАЕТ ВЫБРАННЫЙ ЭЛЕМЕНТ ВВЕРХ (-1) ИЛИ ВНИЗ (1) В ДЕРЕВЕ."""
        item = self.project_tree.currentItem()
        if not item or not item.parent(): return

        parent = item.parent()
        index = parent.indexOfChild(item)
        new_index = index + direction
        
        if 0 <= new_index < parent.childCount():
            parent.takeChild(index)
            parent.insertChild(new_index, item)
            self.project_tree.setCurrentItem(item)
            
            parent_id = parent.data(0, Qt.UserRole)
            parent_data_children = {}
            if parent_id == 'components_root_id':
                parent_data_children = self.project_data['tree']
            else:
                parent_data = self._find_item_data(parent_id)
                if parent_data: parent_data_children = parent_data.get('children', {})
            
            updated_children = {}
            for i in range(parent.childCount()):
                child_item = parent.child(i)
                child_id = child_item.data(0, Qt.UserRole)
                if child_id in parent_data_children:
                    updated_children[child_id] = parent_data_children[child_id]
            
            if parent_id == 'components_root_id':
                self.project_data['tree'] = updated_children
            elif parent_data:
                parent_data['children'] = updated_children
            
            # --- ДОБАВЛЕНА ЭТА СТРОКА ---
            self._mark_as_dirty()
             # --- НАЧАЛО: УДАЛИТЕ ЭТУ СТРОКУ (v7.2) ---
            # if self.current_project_path: self.save_project()
            # --- КОНЕЦ: УДАЛИТЕ ЭТУ СТРОКУ (v7.2) ---
# --- КОНЕЦ: ФУНКЦИЯ move_item ПОЛНАЯ ЗАМЕНА (Graph.vFINAL) ---


# --- НАЧАЛО: ДОБАВЛЕНА НОВАЯ ФУНКЦИЯ "СМЕНА РОДИТЕЛЯ" ---
    def reparent_item(self):
        selected = self.project_tree.currentItem()
        if not selected or not selected.parent():
            QMessageBox.warning(self, "Ошибка", "Нельзя перемещать корневые разделы.")
            return

        # --- СОЗДАЕМ ДИАЛОГОВОЕ ОКНО С ДЕРЕВОМ ДЛЯ ВЫБОРА ---
        dialog = QDialog(self)
        dialog.setWindowTitle("Выберите нового родителя")
        layout = QVBoxLayout(dialog)
        
        tree = QTreeWidget()
        tree.setHeaderHidden(True)
        # КОПИРУЕМ СТРУКТУРУ, ДОБАВЛЯЯ КОРНЕВОЙ ЭЛЕМЕНТ
        root_clone = self.components_root_item.clone()
        tree.addTopLevelItem(root_clone)
        tree.expandAll()
        
        # УБИРАЕМ ИЗ ДЕРЕВА ВЫБОРА САМ ПЕРЕМЕЩАЕМЫЙ ЭЛЕМЕНТ И ЕГО ДЕТЕЙ
        iterator = QTreeWidgetItemIterator(tree)
        while iterator.value():
            item = iterator.value()
            if item and item.data(0, Qt.UserRole) == selected.data(0, Qt.UserRole):
                (item.parent() or tree.invisibleRootItem()).removeChild(item)
                break
            iterator += 1

        layout.addWidget(tree)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            new_parent_item_clone = tree.currentItem()
            if not new_parent_item_clone: return
                
            # НАХОДИМ ОРИГИНАЛЬНЫЕ ЭЛЕМЕНТЫ В ОСНОВНОМ ДЕРЕВЕ
            new_parent_id = new_parent_item_clone.data(0, Qt.UserRole)
            iterator = QTreeWidgetItemIterator(self.project_tree)
            new_parent_original = None
            while iterator.value():
                item = iterator.value()
                if item and item.data(0, Qt.UserRole) == new_parent_id:
                    new_parent_original = item
                    break
                iterator += 1
            
            if new_parent_original:
                # --- ОБНОВЛЯЕМ МОДЕЛЬ ДАННЫХ ---
                item_id = selected.data(0, Qt.UserRole)
                item_data = self._find_item_data(item_id, delete=True) # Удаляем из старого места
                
                parent_data = self._find_item_data(new_parent_id)
                if parent_data:
                    if 'children' not in parent_data: parent_data['children'] = {}
                    parent_data['children'][item_id] = item_data
                
                # --- ОБНОВЛЯЕМ UI ---
                old_parent = selected.parent()
                old_parent.removeChild(selected)
                new_parent_original.addChild(selected)
                new_parent_original.setExpanded(True)
                # --- НАЧАЛО: ДОБАВЬТЕ ЭТУ СТРОКУ ---
                self._mark_as_dirty()
                # --- КОНЕЦ: ДОБАВЬТЕ ЭТУ СТРОКУ ---
                 # --- НАЧАЛО: УДАЛИТЕ ЭТУ СТРОКУ (v7.2) ---
                # if self.current_project_path: self.save_project()
                # --- КОНЕЦ: УДАЛИТЕ ЭТУ СТРОКУ (v7.2) ---
# --- КОНЕЦ: ДОБАВЛЕНА НОВАЯ ФУНКЦИЯ "СМЕНА РОДИТЕЛЯ" ---

 # --- НАЧАЛО: ДОБАВЛЕНЫ МЕТОДЫ ДЛЯ КЛОНИРОВАНИЯ СВОЙСТВ/СОБЫТИЙ (v11.0) ---
    def open_clone_dialog(self, data_key_to_clone):
        """ОТКРЫВАЕТ ДИАЛОГ ДЛЯ ВЫБОРА ЦЕЛЕВОГО ЭЛЕМЕНТА ДЛЯ КЛОНИРОВАНИЯ."""
        source_item = self.project_tree.currentItem()
        if not source_item or not source_item.parent():
            QMessageBox.warning(self, "Ошибка", "Выберите элемент, из которого нужно клонировать данные.")
            return

        dialog = QDialog(self)
        title = "Клонировать свойства" if data_key_to_clone == 'properties' else "Клонировать события"
        dialog.setWindowTitle(f"{title}")
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel(f"Выберите целевой элемент для копирования в него:"))
        
        tree = QTreeWidget()
        tree.setHeaderHidden(True)
        root_clone = self.components_root_item.clone()
        tree.addTopLevelItem(root_clone)
        tree.expandAll()
        
        # УБИРАЕМ ИЗ ДЕРЕВА ВЫБОРА САМ ИСХОДНЫЙ ЭЛЕМЕНТ
        iterator = QTreeWidgetItemIterator(tree)
        while iterator.value():
            item = iterator.value()
            if item and item.data(0, Qt.UserRole) == source_item.data(0, Qt.UserRole):
                (item.parent() or tree.invisibleRootItem()).removeChild(item)
                break
            iterator += 1

        layout.addWidget(tree)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            target_item_clone = tree.currentItem()
            if not target_item_clone or not target_item_clone.parent():
                QMessageBox.warning(self, "Ошибка", "Необходимо выбрать конкретный элемент.")
                return
            
            source_id = source_item.data(0, Qt.UserRole)
            target_id = target_item_clone.data(0, Qt.UserRole)
            self.clone_data(source_id, target_id, data_key_to_clone)

    def clone_data(self, source_id, target_id, data_key):
        """КОПИРУЕТ ДАННЫЕ (СВОЙСТВА ИЛИ СОБЫТИЯ) ИЗ ОДНОГО ЭЛЕМЕНТА В ДРУГОЙ."""
        import copy # ИСПОЛЬЗУЕМ ГЛУБОКОЕ КОПИРОВАНИЕ
        
        source_data = self._find_item_data(source_id)
        target_data = self._find_item_data(target_id)

        if not source_data or not target_data:
            QMessageBox.critical(self, "Критическая ошибка", "Не удалось найти исходный или целевой элемент в данных проекта.")
            return

        data_to_copy = source_data.get(data_key, [])
        # ИСПОЛЬЗУЕМ deepcopy, ЧТОБЫ ИЗБЕЖАТЬ ССЫЛОК НА ОДНИ И ТЕ ЖЕ ОБЪЕКТЫ
        target_data[data_key] = copy.deepcopy(data_to_copy)
        
        self._mark_as_dirty()
        
        # ОБНОВЛЯЕМ ПАНЕЛЬ СВОЙСТВ, ЕСЛИ ЦЕЛЕВОЙ ЭЛЕМЕНТ СЕЙЧАС ВЫБРАН
        current_item = self.project_tree.currentItem()
        if current_item and current_item.data(0, Qt.UserRole) == target_id:
            if data_key == 'properties':
                self._populate_properties_panel(current_item, target_id)
            elif data_key == 'events':
                self._populate_events_panel(current_item, target_id)
        
        QMessageBox.information(self, "Успех", f"Данные '{data_key}' успешно клонированы.")
    # --- КОНЕЦ: ДОБАВЛЕНЫ МЕТОДЫ ДЛЯ КЛОНИРОВАНИЯ СВОЙСТВ/СОБЫТИЙ (v11.0) ---

# --- НАЧАЛО: ДОБАВЛЕНЫ МЕТОДЫ ДЛЯ КОНТЕКСТНОГО МЕНЮ И СОХРАНЕНИЯ ШАБЛОНА (v13.1) ---
    def show_tree_context_menu(self, position):
        """ПОКАЗЫВАЕТ КОНТЕКСТНОЕ МЕНЮ ДЛЯ ЭЛЕМЕНТА ДЕРЕВА."""
        item = self.project_tree.currentItem()
        if not item or not item.parent() or item in [self.concept_item, self.globals_item, self.components_root_item]:
            return # МЕНЮ ТОЛЬКО ДЛЯ РЕАЛЬНЫХ КОМПОНЕНТОВ

        menu = QMenu()
        save_as_template_action = menu.addAction("Сохранить как шаблон...")
        
        action = menu.exec_(self.project_tree.mapToGlobal(position))

        if action == save_as_template_action:
            self.save_item_as_template(item)

    def save_item_as_template(self, item):
        """СОХРАНЯЕТ ВЫБРАННЫЙ ЭЛЕМЕНТ КАК ШАБЛОН."""
        item_id = item.data(0, Qt.UserRole)
        item_data = self._find_item_data(item_id)
        if not item_data:
            QMessageBox.critical(self, "Ошибка", "Не удалось найти данные для выбранного элемента.")
            return
            
        dialog = SaveTemplateDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            template_info = dialog.get_data()
            if self.templates_manager.add_template(template_info["name"], template_info["description"], item_data):
                QMessageBox.information(self, "Успех", f"Шаблон '{template_info['name']}' успешно сохранен.")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить шаблон в файл.")
    # --- КОНЕЦ: ДОБАВЛЕНЫ МЕТОДЫ ДЛЯ КОНТЕКСТНОГО МЕНЮ И СОХРАНЕНИЯ ШАБЛОНА (v13.1) ---

# --- НАЧАЛО: ОБНОВЛЕНИЕ ФОРМАТТЕРА ШРИФТА (v12.5) ---
    def _format_font_to_string(self, font):
        """Преобразует объект QFont в красивую строку, включая все стили."""
        style_parts = []
        # ПОРЯДОК ВАЖЕН ДЛЯ ЧИТАЕМОСТИ
        if font.bold():
            style_parts.append("Полужирный")
        if font.italic():
            style_parts.append("Курсив")
        if font.underline():
            style_parts.append("Подчеркнутый") # <-- ДОБАВЛЕНО
        if font.strikeOut():
            style_parts.append("Зачеркнутый") # <-- ДОБАВЛЕНО
            
        # ЕСЛИ НЕТ ДРУГИХ СТИЛЕЙ, СЧИТАЕМ ЕГО ОБЫЧНЫМ
        if not style_parts:
            style_parts.append("Обычный")
            
        style_str = " ".join(style_parts)
        return f"{font.family()}, {font.pointSize()}, {style_str}"
    # --- КОНЕЦ: ОБНОВЛЕНИЕ ФОРМАТТЕРА ШРИФТА (v12.5) ---

    def _parse_string_to_font(self, font_string):
        """Пытается разобрать красивую строку и вернуть объект QFont."""
        font = QFont()
        parts = [p.strip() for p in font_string.split(',')]
        if not parts: return font

        font.setFamily(parts[0])
        if len(parts) > 1 and parts[1].isdigit():
            font.setPointSize(int(parts[1]))
        if len(parts) > 2:
            style_str = parts[2].lower()
            if "полужирный" in style_str:
                font.setBold(True)
            if "курсив" in style_str:
                font.setItalic(True)
        return font
    # --- КОНЕЦ: НОВЫЕ ФУНКЦИИ-ХЕЛПЕРЫ ДЛЯ ЧИТАЕМОГО ФОРМАТА ШРИФТА (v12.4) ---

# --- НАЧАЛО: ДОБАВЛЕНЫ МЕТОДЫ ДЛЯ ВИЗУАЛИЗАЦИИ ЦВЕТА В ТАБЛИЦЕ (v12.0) ---
    def on_property_cell_double_clicked(self, row, column):
        """ОТКРЫВАЕТ ДИАЛОГ ВЫБОРА ЦВЕТА ПО ДВОЙНОМУ КЛИКУ НА ЯЧЕЙКУ ЗНАЧЕНИЯ."""
        if column != 2: # РАБОТАЕМ ТОЛЬКО С КОЛОНКОЙ "ЗНАЧЕНИЕ"
            return
            
        key_item = self.properties_table.item(row, 1) # ПОЛУЧАЕМ СВОЙСТВО (ДЛЯ ИИ)
        value_item = self.properties_table.item(row, 2)
        if not key_item or not value_item: return

        # ПРОВЕРЯЕМ, ЯВЛЯЕТСЯ ЛИ СВОЙСТВО СВЯЗАННЫМ С ЦВЕТОМ
        property_key = key_item.text().lower()

         # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА ЛОГИКИ ШРИФТА ДЛЯ ЧИТАЕМОГО ФОРМАТА (v12.4) ---
        if 'font' in property_key and 'color' not in property_key:
            # ИСПОЛЬЗУЕМ НАШ ПАРСЕР ДЛЯ ЧТЕНИЯ КРАСИВОЙ СТРОКИ
            current_font = self._parse_string_to_font(value_item.text())
            
            new_font, ok = QFontDialog.getFont(current_font, self, "Выберите шрифт")
            
            if ok:
                # ИСПОЛЬЗУЕМ НАШ ФОРМАТТЕР ДЛЯ СОЗДАНИЯ КРАСИВОЙ СТРОКИ
                value_item.setText(self._format_font_to_string(new_font))
            return
        # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА ЛОГИКИ ШРИФТА ДЛЯ ЧИТАЕМОГО ФОРМАТА (v12.4) ---

        if 'color' not in property_key and 'фон' not in key_item.text().lower():
            return

        current_color = QColor(value_item.text())
        new_color = QColorDialog.getColor(current_color if current_color.isValid() else Qt.white, self)

        if new_color.isValid():
            value_item.setText(new_color.name()) # new_color.name() ВОЗВРАЩАЕТ HEX (#rrggbb)
            # ОБНОВЛЕНИЕ ЦВЕТА ПРОИЗОЙДЕТ АВТОМАТИЧЕСКИ ЧЕРЕЗ СИГНАЛ itemChanged -> save_properties_from_table

    def _colorize_property_cell(self, row, column):
        """РАСКРАШИВАЕТ ЯЧЕЙКУ, ЕСЛИ В НЕЙ СОДЕРЖИТСЯ ЗНАЧЕНИЕ ЦВЕТА."""
        if column != 2: return # ТОЛЬКО КОЛОНКА "ЗНАЧЕНИЕ"
            
        value_item = self.properties_table.item(row, 2)
        key_item = self.properties_table.item(row, 1)
        if not value_item or not key_item: return
        
        # ПРОВЕРЯЕМ, ЧТО СВОЙСТВО ПРЕДПОЛАГАЕТ ЦВЕТ
        property_key = key_item.text().lower()
        if 'color' not in property_key and 'фон' not in key_item.text().lower():
            value_item.setBackground(QBrush(Qt.white)) # СБРАСЫВАЕМ ЦВЕТ ДЛЯ ДРУГИХ СВОЙСТВ
            value_item.setForeground(QBrush(Qt.black))
            return
        
        color = QColor(value_item.text())
        if color.isValid():
            value_item.setBackground(color)
            # ВЫЧИСЛЯЕМ ЯРКОСТЬ ЦВЕТА, ЧТОБЫ ВЫБРАТЬ КОНТРАСТНЫЙ ЦВЕТ ТЕКСТА
            luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue())
            text_color = Qt.black if luminance > 128 else Qt.white
            value_item.setForeground(QBrush(text_color))
        else:
            # ЕСЛИ ЦВЕТ НЕВАЛИДНЫЙ, СБРАСЫВАЕМ ФОН
            value_item.setBackground(QBrush(Qt.white))
            value_item.setForeground(QBrush(Qt.black))
    # --- КОНЕЦ: ДОБАВЛЕНЫ МЕТОДЫ ДЛЯ ВИЗУАЛИЗАЦИИ ЦВЕТА В ТАБЛИЦЕ (v12.0) ---

    def update_item_name(self):
        sel = self.project_tree.currentItem(); item_data = self._find_item_data(sel.data(0, Qt.UserRole)) if sel and sel.data(0, Qt.UserRole) != "concept_id" else None
        if item_data: new_name = self.name_editor.text(); item_data['name'] = new_name; sel.setText(0, new_name)
        self._mark_as_dirty()
    def update_item_description(self):
        sel = self.project_tree.currentItem(); item_data = self._find_item_data(sel.data(0, Qt.UserRole)) if sel and sel.data(0, Qt.UserRole) != "concept_id" else None
        if item_data: item_data['description'] = self.description_editor.toPlainText()
        self._mark_as_dirty()

   # --- НАЧАЛО: ИЗМЕНЕНИЕ ФУНКЦИИ update_item_type (Graph.vFINAL-2) ---
    def update_item_type(self):
        """ОБНОВЛЯЕТ ТИП ЭЛЕМЕНТА В МОДЕЛИ ДАННЫХ."""
        selected = self.project_tree.currentItem()
        if not selected or not selected.parent(): return

        item_data = self._find_item_data(selected.data(0, Qt.UserRole))
        if item_data:
            new_type = self.type_combo.currentData()
            if item_data.get('type') != new_type:
                item_data['type'] = new_type
                # --- ДОБАВЬТЕ ЭТУ СТРОКУ ---
                self._mark_as_dirty()
                # --- НАЧАЛО: УДАЛИТЕ ЭТУ СТРОКУ (v7.2) ---
                # if self.current_project_path: self.save_project()
                # --- КОНЕЦ: УДАЛИТЕ ЭТУ СТРОКУ (v7.2) ---
# --- КОНЕЦ: ИЗМЕНЕНИЕ ФУНКЦИИ update_item_type (Graph.vFINAL-2) ---

   # --- НАЧАЛО: ФУНКЦИЯ update_concept_description ПОЛНАЯ ЗАМЕНА (v1.1) ---
    def update_concept_description(self):
        new_description = self.concept_editor.toPlainText()
        # ПРОВЕРЯЕМ, ИЗМЕНИЛСЯ ЛИ ТЕКСТ, ЧТОБЫ НЕ СТАВИТЬ ФЛАГ ЛИШНИЙ РАЗ
        if self.project_data['concept'].get('description') != new_description:
            self.project_data['concept']['description'] = new_description
        self._mark_as_dirty()
# --- КОНЕЦ: ФУНКЦИЯ update_concept_description ПОЛНАЯ ЗАМЕНА (v1.1) ---
        
    # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА add_custom_property С ИСПРАВЛЕННЫМ МЕТОДОМ (v14.9-final) ---
    def add_custom_property(self):
        selected_item = self.project_tree.currentItem()
        if not selected_item or selected_item.data(0, Qt.UserRole) == "concept_id":
            return

        items = [f"{h} ({t})" for h, t in self.PREDEFINED_PROPERTIES] + ["-- Своё свойство --"]
        
        dialog = QInputDialog(self)
        dialog.setLabelText("Выберите свойство для добавления:")
        dialog.setWindowTitle("Добавить свойство")
        dialog.setComboBoxItems(items)
        dialog.setComboBoxEditable(False)
        
        combo_box = dialog.findChild(QComboBox)
        if combo_box:
            combo_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
            combo_box.setMaxVisibleItems(25)
            # --- ИСПРАВЛЕНА НЕВЕРНАЯ СТРОКА ---
            # --- БЫЛО: combo_box.view().setMinimumWidth(combo_box.sizeHintForColumn(0) + 20)
            # --- СТАЛО: ---
            combo_box.view().setMinimumWidth(combo_box.sizeHint().width())

        if dialog.exec_() == QDialog.Accepted and dialog.textValue():
            item_text = dialog.textValue()
            
            row = self.properties_table.rowCount()
            self.properties_table.insertRow(row)
            name, key, is_pre = "Новое свойство", "custom-property", False

            if item_text != "-- Своё свойство --":
                for h, t in self.PREDEFINED_PROPERTIES:
                    if item_text == f"{h} ({t})":
                        name, key, is_pre = h, t, True
                        break
            
            name_item = QTableWidgetItem(name)
            key_item = QTableWidgetItem(key)
            val_item = QTableWidgetItem("значение")
            key_item.setData(Qt.UserRole, is_pre)

            if is_pre:
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
            
            self.properties_table.setItem(row, 0, name_item)
            self.properties_table.setItem(row, 1, key_item)
            self.properties_table.setItem(row, 2, val_item)
            self.save_properties_from_table()
        
        self._mark_as_dirty()
    # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА add_custom_property С ИСПРАВЛЕННЫМ МЕТОДОМ (v14.9-final) ---

    def remove_custom_property(self):
        sel = self.project_tree.currentItem();
        if not sel or sel.data(0, Qt.UserRole) == "concept_id": return
        row = self.properties_table.currentRow();
        if row > -1: self.properties_table.removeRow(row); self.save_properties_from_table()
        self._mark_as_dirty()

    def save_properties_from_table(self):
        sel = self.project_tree.currentItem(); item_data = self._find_item_data(sel.data(0, Qt.UserRole)) if sel and sel.data(0, Qt.UserRole) != "concept_id" else None
        if item_data:
            props = [];
            for row in range(self.properties_table.rowCount()):
                key_item = self.properties_table.item(row, 1) 
                # --- НАЧАЛО: ИЗМЕНЕНА ЛОГИКА ПОЛУЧЕНИЯ ФЛАГА (v7.2) ---
                # --- БЫЛО: is_pre = key_item.data(Qt.UserRole) if key_item else False; name_item = self.properties_table.item(row, 0); value_item = self.properties_table.item(row, 2)
                # --- СТАЛО: ---
                is_pre = key_item.data(Qt.UserRole) if key_item and key_item.data(Qt.UserRole) is not None else False
                name_item = self.properties_table.item(row, 0)
                value_item = self.properties_table.item(row, 2)
                # --- КОНЕЦ: ИЗМЕНЕНА ЛОГИКА ПОЛУЧЕНИЯ ФЛАГА (v7.2) ---
                props.append({'name': name_item.text() if name_item else "", 'key': key_item.text() if key_item else "", 'value': value_item.text() if value_item else "", 'is_predefined': is_pre})
                 # --- НАЧАЛО: РАСКРАШИВАЕМ ЯЧЕЙКУ ПОСЛЕ РЕДАКТИРОВАНИЯ (v12.0) ---
                self._colorize_property_cell(row, 2)
                # --- КОНЕЦ: РАСКРАШИВАЕМ ЯЧЕЙКУ ПОСЛЕ РЕДАКТИРОВАНИЯ (v12.0) ---
            item_data['properties'] = props
            # --- НАЧАЛО: ДОБАВЛЕНА СИНХРОНИЗАЦИЯ ИЗ ПАНЕЛИ СВОЙСТВ НА ХОЛСТ (v8.0) ---
            item_id = sel.data(0, Qt.UserRole)
            if item_id in self.scene_items_map:
                scene_item = self.scene_items_map[item_id]
                
                pos_prop = next((p for p in props if p['key'] == 'position'), None)
                size_prop = next((p for p in props if p['key'] == 'size'), None)
                
                try:
                    # --- НАЧАЛО: ИСПРАВЛЕН ВЫЗОВ НЕИСПРАВНОГО МЕТОДА (v9.2) ---
                    # --- БЫЛО: current_rect = scene_item.rect()
                    # --- СТАЛО: ---
                    current_rect = scene_item.rect_in_scene_coords()
                    # --- КОНЕЦ: ИСПРАВЛЕН ВЫЗОВ НЕИСПРАВНОГО МЕТОДА (v9.2) ---
                    new_x, new_y = current_rect.x(), current_rect.y()
                    new_w, new_h = current_rect.width(), current_rect.height()
                    
                    if pos_prop:
                        new_x, new_y = map(int, pos_prop['value'].split(','))
                    if size_prop:
                        new_w, new_h = map(int, size_prop['value'].split(','))

                    # --- НАЧАЛО: ИЗМЕНЕН СПОСОБ ОБНОВЛЕНИЯ ГЕОМЕТРИИ (v8.8-final) ---
                    scene_item.setRect(QRectF(new_x, new_y, new_w, new_h))
                    # --- КОНЕЦ: ИЗМЕНЕН СПОСОБ ОБНОВЛЕНИЯ ГЕОМЕТРИИ (v8.8-final) ---
                except (ValueError, IndexError):
                    pass # ИГНОРИРУЕМ ОШИБКИ, ЕСЛИ ВВЕДЕНО НЕКОРРЕКТНОЕ ЗНАЧЕНИЕ
            # --- КОНЕЦ: ДОБАВЛЕНА СИНХРОНИЗАЦИЯ ИЗ ПАНЕЛИ СВОЙСТВ НА ХОЛСТ (v8.0) ---
            # --- НАЧАЛО: ДОБАВЛЕНА ПРОВЕРКА ИЗМЕНЕНИЙ (v7.2) ---
            self._mark_as_dirty()
            # --- КОНЕЦ: ДОБАВЛЕНА ПРОВЕРКА ИЗМЕНЕНИЙ (v7.2) ---

# --- НАЧАЛО: ДОБАВЛЕНА СИНХРОНИЗАЦИЯ СВОЙСТВ ПРИ ИЗМЕНЕНИИ НА ХОЛСТЕ (v8.0) ---
    def on_item_geometry_changed_on_canvas(self, item_id, new_rect):
        """ОБРАБАТЫВАЕТ ИЗМЕНЕНИЕ ПОЛОЖЕНИЯ/РАЗМЕРА ЭЛЕМЕНТА НА ХОЛСТЕ."""
        item_data = self._find_item_data(item_id)
        if not item_data: return

        pos_str = f"{int(new_rect.x())}, {int(new_rect.y())}"
        size_str = f"{int(new_rect.width())}, {int(new_rect.height())}"
        
        changed = False # ДОБАВИМ ФЛАГ, ЧТОБЫ НЕ ОБНОВЛЯТЬ ПАНЕЛЬ ЛИШНИЙ РАЗ
        pos_prop = next((p for p in item_data['properties'] if p.get('key') == 'position'), None)
        if pos_prop and pos_prop['value'] != pos_str:
             pos_prop['value'] = pos_str
        
        size_prop = next((p for p in item_data['properties'] if p.get('key') == 'size'), None)
        if size_prop and size_prop['value'] != size_str:
            size_prop['value'] = size_str
        
        self._mark_as_dirty()

        # ОБНОВЛЯЕМ ПАНЕЛЬ СВОЙСТВ, ЕСЛИ ВЫБРАН ИМЕННО ЭТОТ ЭЛЕМЕНТ
        selected_item = self.project_tree.currentItem()
        if selected_item and selected_item.data(0, Qt.UserRole) == item_id:
            self._populate_properties_panel(selected_item, item_id)
    # --- КОНЕЦ: ДОБАВЛЕНА СИНХРОНИЗАЦИЯ СВОЙСТВ ПРИ ИЗМЕНЕНИИ НА ХОЛСТЕ (v8.0) ---

# --- НАЧАЛО: ПОЛНАЯ РЕАЛИЗАЦИЯ ЛОГИКИ СВЯЗЕЙ (v2.1) ---
    def activate_relation_mode(self):
        self.relation_mode_active = True
        self.relation_source_id = None
        self.coords_label.setText("<b><font color='red'>РЕЖИМ СВЯЗЕЙ: Выберите исходный элемент.</font></b>")

    def handle_item_click_in_relation_mode(self, item_id):
        if not self.relation_source_id:
            self.relation_source_id = item_id
            source_item_data = self._find_item_data(self.relation_source_id)
            self.coords_label.setText(f"<b><font color='red'>Источник: '{source_item_data.get('name')}'. Выберите цель. (ПКМ для отмены)</font></b>")
        else:
            target_id = item_id
            if self.relation_source_id == target_id: return

            dialog = RelationDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                relation_info = dialog.get_data()
                relation_id = str(uuid.uuid4())
                
                self.project_data['relations'][relation_id] = {
                    "id": relation_id, "source_id": self.relation_source_id,
                    "target_id": target_id, "type": relation_info['type'],
                    "description": relation_info['description']
                }
                self._mark_as_dirty()

            self.deactivate_relation_mode()
            self.on_tree_item_selected(self.project_tree.currentItem(), None)

    def deactivate_relation_mode(self):
        self.relation_mode_active = False
        self.relation_source_id = None
        self.update_coords_label(self.view.mapToScene(self.view.mapFromGlobal(self.cursor().pos())))
        
     # --- НАЧАЛО: ИСПРАВЛЕНИЕ АРГУМЕНТОВ _populate_relations_panel (v3.2-fix2) ---
    def _populate_relations_panel(self, item, item_id):
        """ЗАПОЛНЯЕТ СПИСОК СВЯЗЕЙ В ПРАВОЙ ПАНЕЛИ В НОВОМ ФОРМАТЕ."""
    # --- КОНЕЦ: ИСПРАВЛЕНИЕ АРГУМЕНТОВ _populate_relations_panel (v3.2-fix2) ---
        self.relations_list.clear()
        
        all_items_flat = self._get_all_project_items_flat()
        if not item_id or not all_items_flat: return

        for rel_id, relation in self.project_data.get('relations', {}).items():
            if item_id == relation['source_id'] or item_id == relation['target_id']:
                source_path = self._get_item_path_string(relation['source_id'], all_items_flat)
                target_path = self._get_item_path_string(relation['target_id'], all_items_flat)
                description = relation.get('description', '')

                if relation.get('type') == 'bidirectional':
                    list_item_text = f"Синхронизированы: [{source_path}] <-> [{target_path}]"
                else: # unidirectional
                    list_item_text = f"[{source_path}] влияет на -> [{target_path}]"
                
                if description:
                    list_item_text += f": ({description})"
                
                list_item = QListWidgetItem(list_item_text)
                list_item.setData(Qt.UserRole, rel_id)
                self.relations_list.addItem(list_item)
    # --- КОНЕЦ: ЗАМЕНА _populate_relations_panel НА ФИНАЛЬНЫЙ ФОРМАТ (v3.3) ---
    
     # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА _apply_relation_highlights (v2.0.5) ---
    def _apply_relation_highlights(self, selected_item_id):
        """НАХОДИТ СВЯЗАННЫЕ ЭЛЕМЕНТЫ, ПОЛУЧАЕТ АКТУАЛЬНЫЕ СТИЛИ И ПОДСВЕЧИВАЕТ ИХ."""
        # Получаем самые свежие настройки стилей
        relation_styles = self.settings_manager.get_style("relations")
        
        # Если в настройках выбран режим "Подсветка", то работаем
        if relation_styles.get("display_mode") == "Подсветка":
            for relation in self.project_data.get('relations', {}).values():
                partner_id = None
                if selected_item_id == relation['source_id']:
                    partner_id = relation['target_id']
                elif selected_item_id == relation['target_id']:
                    partner_id = relation['source_id']
                
                if partner_id and partner_id in self.scene_items_map and selected_item_id in self.scene_items_map:
                    # Передаем стили в метод подсветки
                    self.scene_items_map[selected_item_id].set_relation_highlight(True, relation_styles)
                    self.scene_items_map[partner_id].set_relation_highlight(False, relation_styles)
    # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА _apply_relation_highlights (v2.0.5) ---

    def edit_selected_relation(self):
        selected_list_item = self.relations_list.currentItem()
        if not selected_list_item: return
        relation_id = selected_list_item.data(Qt.UserRole)
        relation_data = self.project_data['relations'].get(relation_id)
        if not relation_data: return
            
        dialog = RelationDialog(self)
        dialog.set_data(relation_data)
        
        if dialog.exec_() == QDialog.Accepted:
            new_data = dialog.get_data()
            relation_data['type'] = new_data['type']
            relation_data['description'] = new_data['description']
            self._mark_as_dirty()
            self.on_tree_item_selected(self.project_tree.currentItem(), None)

    def remove_selected_relation(self):
        selected_list_item = self.relations_list.currentItem()
        if not selected_list_item: return
        relation_id = selected_list_item.data(Qt.UserRole)
        
        if relation_id in self.project_data['relations']:
            del self.project_data['relations'][relation_id]
            self._mark_as_dirty()
            self.on_tree_item_selected(self.project_tree.currentItem(), None)
    # --- КОНЕЦ: ПОЛНАЯ РЕАЛИЗАЦИЯ ЛОГИКИ СВЯЗЕЙ (v2.1) ---

    def _get_all_project_items_flat(self):
        items = {};
        def recurse(parent_id, children_data):
            for item_id, item_data in children_data.items():
                items[item_id] = {'id': item_id, 'name': item_data.get('name', ''), 'parent_id': parent_id, 'properties': item_data.get('properties', [])}; recurse(item_id, item_data.get('children', {}))
        recurse(None, self.project_data.get('tree', {}))
        return items

   # --- НАЧАЛО: ФИНАЛЬНЫЙ ФИКС ДЛЯ ПУТЕЙ И ПАРАМЕТРОВ (v4.1) ---
    def _get_item_path_string(self, item_id, all_items_flat):
        """Строит читаемую строку пути для элемента по его ID, ВКЛЮЧАЯ ID."""
        if item_id not in all_items_flat:
            return f"(Неизвестный элемент ID: `{item_id.split('-')[0]}`)"

        path_parts = []
        current_item = all_items_flat.get(item_id)
        
        while current_item:
            name = current_item.get('name', 'Без имени')
            short_id = current_item.get('id', '').split('-')[0]
            # --- ВОТ ИСПРАВЛЕНИЕ: ДОБАВЛЯЕМ ID К КАЖДОЙ ЧАСТИ ПУТИ ---
            path_parts.append(f"{name} (ID: `{short_id}`)")
            
            parent_id = current_item.get('parent_id')
            current_item = all_items_flat.get(parent_id)
            
        return " >>> ".join(reversed(path_parts))
    
# --- НАДЕЖНЫЙ ОБРАБОТЧИК ДЛЯ СОХРАНЕНИЯ ДЕЙСТВИЙ (v3.2) ---
    def on_action_params_ui_changed(self):
        widget = self.sender()
        if not isinstance(widget, ActionParameterWidget):
            iterator = QTreeWidgetItemIterator(self.events_tree)
            while iterator.value():
                item = iterator.value()
                if item and self.events_tree.itemWidget(item, 0) == self.sender():
                    widget = self.sender(); break
                iterator += 1
        if not widget: return

        action_id = widget.action_data.get('action_id')
        if not action_id: return

        current_item_data = self._find_item_data(self.project_tree.currentItem().data(0, Qt.UserRole))
        if not current_item_data: return

        found_action = None
        for event in current_item_data.get('events', []):
            for action in event.get('actions', []):
                if action.get('action_id') == action_id:
                    found_action = action; break
            if found_action: break
        if not found_action: return

        new_params = {}
        for key, control in widget.controls.items():
            if isinstance(control, QComboBox):
                if control.currentData() is not None and control.currentData() != "": new_params[key] = control.currentData()
                else: new_params[key] = control.currentText()
            elif isinstance(control, QLineEdit):
                new_params[key] = control.text()
        
        found_action['params'] = new_params
        self._mark_as_dirty()

# --- НАЧАЛО: ДОБАВЬТЕ ЭТИ ДВЕ НОВЫЕ ФУНКЦИИ ---
    def _populate_globals_panel(self):
        self.globals_table.blockSignals(True)
        self.globals_table.setRowCount(0)
        for key, value in self.project_data.get('globals', {}).items():
            row = self.globals_table.rowCount()
            self.globals_table.insertRow(row)
            self.globals_table.setItem(row, 0, QTableWidgetItem(key))
            self.globals_table.setItem(row, 1, QTableWidgetItem(value))
        self.globals_table.blockSignals(False)
        
    def save_globals_from_table(self):
        self.project_data['globals'] = {}
        for row in range(self.globals_table.rowCount()):
            key_item = self.globals_table.item(row, 0)
            value_item = self.globals_table.item(row, 1)
            key = key_item.text() if key_item else ""
            value = value_item.text() if value_item else ""
            if key:
                self.project_data['globals'][key] = value
         # --- НАЧАЛО: УДАЛИТЕ ЭТИ ДВЕ СТРОКИ (v7.2) ---
        # if self.current_project_path:
        #     self.save_project()
        # --- КОНЕЦ: УДАЛИТЕ ЭТИ ДВЕ СТРОКИ (v7.2) ---
        self._mark_as_dirty()    
# --- КОНЕЦ: ДОБАВЬТЕ ЭТИ ДВЕ НОВЫЕ ФУНКЦИИ ---

# --- НАЧАЛО: ДОБАВЛЕНА НОВАЯ ФУНКЦИЯ ---
    def add_global_variable(self):
        row = self.globals_table.rowCount()
        self.globals_table.insertRow(row)
        # УСТАНАВЛИВАЕМ ЗНАЧЕНИЕ ПО УМОЛЧАНИЮ С @
        self.globals_table.setItem(row, 0, QTableWidgetItem("@имя_переменной"))
        self.globals_table.setItem(row, 1, QTableWidgetItem("значение"))
        self._mark_as_dirty()
# --- КОНЕЦ: ДОБАВЛЕНА НОВАЯ ФУНКЦИЯ ---

    
     # --- НАДЕЖНЫЙ POPULATE_EVENTS_PANEL (v3.2) ---
    def _populate_events_panel(self, item, item_id):
        self.events_tree.blockSignals(True)
        self.events_tree.clear()
        item_data = self._find_item_data(item_id)
        if not item_data:
            self.events_tree.blockSignals(False); return
        
        all_items_data = self._get_all_project_items_flat()
        for event_data in item_data.get('events', []):
            event_name = event_data.get('name', '')
            event_type = event_data.get('type', '')
            display_name = event_name if event_type.startswith("customEvent") else f"{event_name} ({event_type})"
            
            event_item = QTreeWidgetItem(self.events_tree, [display_name])
            event_item.setData(0, Qt.UserRole, event_data)
            
            base_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
            if event_type.startswith("customEvent"): event_item.setFlags(base_flags | Qt.ItemIsEditable)
            else: event_item.setFlags(base_flags)

            for action_data in event_data.get('actions', []):
                action_item = QTreeWidgetItem(event_item)
                action_item.setData(0, Qt.UserRole, action_data)
                
                widget = ActionParameterWidget(action_data, all_items_data, self.project_data.get('globals', {}))
                widget.parameterChanged.connect(self.on_action_params_ui_changed)
                self.events_tree.setItemWidget(action_item, 0, widget)
                action_item.setSizeHint(0, widget.sizeHint())

        self.events_tree.expandAll()
        self.events_tree.blockSignals(False)

    # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА add_event С УЛУЧШЕННЫМ ДИАЛОГОМ (v14.10) ---
    def add_event(self):
        sel = self.project_tree.currentItem()
        if not sel or sel.data(0, Qt.UserRole) == "concept_id": return
        
        items = [f"{h} ({t})" for h, t in self.PREDEFINED_EVENTS]
        
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Добавить событие")
        dialog.setLabelText("Выберите:")
        dialog.setComboBoxItems(items)
        dialog.setComboBoxEditable(False)
        
        combo_box = dialog.findChild(QComboBox)
        if combo_box:
            combo_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
            combo_box.setMaxVisibleItems(25)
            combo_box.view().setMinimumWidth(combo_box.sizeHint().width())

        if dialog.exec_() == QDialog.Accepted and dialog.textValue():
            item_text = dialog.textValue()
            name, type = "", ""
            for h, t in self.PREDEFINED_EVENTS:
                if item_text == f"{h} ({t})": name, type = h, t; break
            
            event_id = type
            if type == "customEvent": event_id = f"customEvent_{uuid.uuid4().hex[:6]}"; name = "Новое событие"
            
            item_data = self._find_item_data(sel.data(0, Qt.UserRole))
            if item_data:
                if 'events' not in item_data: item_data['events'] = []
                # ПРОВЕРЯЕМ, ЕСТЬ ЛИ УЖЕ ТАКОЕ СОБЫТИЕ
                if any(e.get('type') == type and not type.startswith("custom") for e in item_data['events']):
                     QMessageBox.warning(self, "Ошибка", "Событие такого типа уже добавлено."); return
                item_data['events'].append({'name': name, 'type': type, 'event_id': event_id, 'actions': []})
                self._populate_events_panel(sel, sel.data(0, Qt.UserRole))
        self._mark_as_dirty()
    # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА add_event С УЛУЧШЕННЫМ ДИАЛОГОМ (v14.10) ---   

     # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА add_action С УЛУЧШЕННЫМ ДИАЛОГОМ (v14.10) ---
    def add_action(self):
        sel_event = self.events_tree.currentItem()
        if not sel_event or sel_event.parent(): 
            QMessageBox.warning(self, "Ошибка", "Сначала выберите событие."); return
        
        items = [f"{h} ({t})" for h, t in self.PREDEFINED_ACTIONS]
        
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Добавить действие")
        dialog.setLabelText("Выберите:")
        dialog.setComboBoxItems(items)
        dialog.setComboBoxEditable(False)

        combo_box = dialog.findChild(QComboBox)
        if combo_box:
            combo_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
            combo_box.setMaxVisibleItems(25)
            combo_box.view().setMinimumWidth(combo_box.sizeHint().width())

        if dialog.exec_() == QDialog.Accepted and dialog.textValue():
            item_text = dialog.textValue()
            name, type = "", ""
            for h, t in self.PREDEFINED_ACTIONS:
                if item_text == f"{h} ({t})": name, type = h, t; break
            
            action_id = f"{type}_{uuid.uuid4().hex[:6]}"
            new_action_data = {'name': name, 'type': type, 'action_id': action_id, 'params': {}}
            if type == 'customAction': new_action_data['params']['description'] = '-> Своё действие...'
            
            sel_item = self.project_tree.currentItem()
            item_data = self._find_item_data(sel_item.data(0, Qt.UserRole))
            event_data_from_tree = sel_event.data(0, Qt.UserRole)
            event_id_to_find = event_data_from_tree.get('event_id')

            if item_data:
                for event_in_storage in item_data.get('events', []):
                    if event_in_storage.get('event_id') == event_id_to_find:
                        if 'actions' not in event_in_storage: event_in_storage['actions'] = []
                        event_in_storage['actions'].append(new_action_data)
                        self._populate_events_panel(sel_item, sel_item.data(0, Qt.UserRole))
                        return
        self._mark_as_dirty()
    # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА add_action С УЛУЧШЕННЫМ ДИАЛОГОМ (v14.10) ---

   # --- НАЧАЛО: ФУНКЦИЯ remove_event_or_action ПОЛНАЯ ЗАМЕНА (vFINAL) ---
    def remove_event_or_action(self):
        sel_event_tree = self.events_tree.currentItem();
        if not sel_event_tree: return
        sel_item = self.project_tree.currentItem(); item_data = self._find_item_data(sel_item.data(0, Qt.UserRole));
        if not item_data: return
        
        if not sel_event_tree.parent():
            event_to_remove = sel_event_tree.data(0, Qt.UserRole)
            item_data['events'] = [e for e in item_data.get('events', []) if e.get('event_id') != event_to_remove.get('event_id')]
        else:
            action_to_remove = sel_event_tree.data(0, Qt.UserRole)
            parent_event_data = sel_event_tree.parent().data(0, Qt.UserRole)
            for event in item_data.get('events', []):
                if event.get('event_id') == parent_event_data.get('event_id'):
                    event['actions'] = [a for a in event.get('actions', []) if a.get('action_id') != action_to_remove.get('action_id')]; break
        
        self._populate_events_panel(sel_item, sel_item.data(0, Qt.UserRole));
        # --- НАЧАЛО: УДАЛИТЕ ЭТУ СТРОКУ (v7.2) ---
        # if self.current_project_path: self.save_project()
        # --- КОНЕЦ: УДАЛИТЕ ЭТУ СТРОКУ (v7.2) ---
        self._mark_as_dirty()
# --- КОНЕЦ: ФУНКЦИЯ remove_event_or_action ПОЛНАЯ ЗАМЕНА (vFINAL) ---

    # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА update_custom_event_or_action_text С ИСПРАВЛЕНИЕМ СОХРАНЕНИЯ (v17.0) ---
    def update_custom_event_or_action_text(self, item, column):
        # Убедимся, что это событие, а не действие
        if item.parent():
            return
            
        data_from_ui = item.data(0, Qt.UserRole)
        if not isinstance(data_from_ui, dict) or not data_from_ui.get('type', '').startswith('customEvent'):
            return

        # Получаем данные текущего ВЫБРАННОГО В ОСНОВНОМ ДЕРЕВЕ элемента
        selected_component_item = self.project_tree.currentItem()
        if not selected_component_item: return
        
        component_id = selected_component_item.data(0, Qt.UserRole)
        component_data = self._find_item_data(component_id)
        if not component_data or 'events' not in component_data: return

        # Находим нужное событие в модели данных по его ID и обновляем его
        event_id_to_find = data_from_ui.get('event_id')
        for event_in_model in component_data['events']:
            if event_in_model.get('event_id') == event_id_to_find:
                new_text = item.text(0)
                # Если текст действительно изменился
                if event_in_model.get('name') != new_text:
                    event_in_model['name'] = new_text
                    self._mark_as_dirty()
                break # Выходим из цикла, так как нашли и обновили
    # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА update_custom_event_or_action_text С ИСПРАВЛЕНИЕМ СОХРАНЕНИЯ (v17.0) ---

    # --- НАЧАЛО: ФУНКЦИИ new_project и open_project ПОЛНАЯ ЗАМЕНА (Graph.v2.3.3) ---
    def new_project(self):
        if self.is_dirty:
            reply = QMessageBox.question(self, 'Новый проект',
                                         "У вас есть несохраненные изменения. Сохранить текущий проект?",
                                         QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                         QMessageBox.Cancel)
            
            if reply == QMessageBox.Save:
                if not self.save_project():
                    return
            elif reply == QMessageBox.Cancel:
                return

        self._init_project_data()
        self._update_ui_for_new_project()
        self.setWindowTitle(f"{self.APP_VERSION_TITLE} - Новый проект")

    def open_project(self):
        if self.is_dirty:
            reply = QMessageBox.question(self, 'Открыть проект',
                                         "У вас есть несохраненные изменения. Сохранить текущий проект?",
                                         QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                         QMessageBox.Cancel)
            if reply == QMessageBox.Save:
                if not self.save_project():
                    return
            elif reply == QMessageBox.Cancel:
                return

        path, _ = QFileDialog.getOpenFileName(self, "Открыть проект", "", "JSON Files (*.json)");
        if path:
            data = self.data_manager.load_project(path)
            if data:
                if 'globals' not in data: data['globals'] = {}
                if 'relations' not in data: data['relations'] = {} # <-- ДОБАВЛЕНО
                self._migrate_project_data(data.get('tree', {})); 
                self.project_data = {'concept': data.get('concept', {}), 'globals': data.get('globals', {}), 'tree': data.get('tree', {}), 'relations': data.get('relations', {})} # <-- ДОБАВЛЕНО
                self.current_project_path = path;
                self._update_ui_for_new_project()
                self.is_dirty = False
                self.setWindowTitle(f"{self.APP_VERSION_TITLE} - {os.path.basename(path)}")
                # --- НАЧАЛО: ОБНОВЛЕНИЕ СТАТУС-БАРА ПРИ ОТКРЫТИИ ПРОЕКТА (v10.1) ---
                self.project_path_label.setText(path)
                # --- КОНЕЦ: ОБНОВЛЕНИЕ СТАТУС-БАРА ПРИ ОТКРЫТИИ ПРОЕКТА (v10.1) ---
# --- КОНЕЦ: ФУНКЦИИ new_project и open_project ПОЛНАЯ ЗАМЕНА (Graph.v2.3.3) ---
    
    def _migrate_project_data(self, tree_data):
        for item_id, item_data in tree_data.items():
            if 'events' not in item_data: item_data['events'] = []
            if 'children' in item_data: self._migrate_project_data(item_data['children'])
            for event in item_data.get('events', []):
                if 'event_id' not in event: event['event_id'] = event.get('type') if not event.get('type','').startswith('custom') else f"customEvent_{uuid.uuid4().hex[:6]}"
                for action in event.get('actions', []):
                    if 'action_id' not in action: action['action_id'] = f"{action.get('type')}_{uuid.uuid4().hex[:6]}"
    
   # --- НАЧАЛО: ФУНКЦИИ save_project и save_project_as ПОЛНАЯ ЗАМЕНА (v1.1) ---
    def save_project(self):
        if self.current_project_path:
            if self.data_manager.save_project(self.project_data, self.current_project_path):
                self.is_dirty = False
                # УБИРАЕМ СУФФИКС ИЗ ЗАГОЛОВКА
                title = self.windowTitle()
                suffix = " -> (необходимо сохранить проект!!)"
                if title.endswith(suffix):
                    self.setWindowTitle(title[:-len(suffix)])
                return True
        else:
            return self.save_project_as()
        return False
            
    def save_project_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить проект как...", "", "JSON Files (*.json)")
        if path:
            if not path.endswith('.json'): path += '.json'
            self.current_project_path = path
            success = self.data_manager.save_project(self.project_data, path)
            if success:
                self.is_dirty = False
                self.setWindowTitle(f"{self.APP_VERSION_TITLE} - {os.path.basename(path)}")
                # --- НАЧАЛО: ОБНОВЛЕНИЕ СТАТУС-БАРА ПРИ СОХРАНЕНИИ ПРОЕКТА (v10.1) ---
                self.project_path_label.setText(path)
                # --- КОНЕЦ: ОБНОВЛЕНИЕ СТАТУС-БАРА ПРИ СОХРАНЕНИИ ПРОЕКТА (v10.1) ---
                return True
        return False
# --- КОНЕЦ: ФУНКЦИИ save_project и save_project_as ПОЛНАЯ ЗАМЕНА (v1.1) ---

# --- НАЧАЛО: ДОБАВЛЕНА НОВАЯ ФУНКЦИЯ-ПЕРЕХВАТЧИК ЗАКРЫТИЯ ---
    def closeEvent(self, event):
        """ПЕРЕХВАТЫВАЕТ СОБЫТИЕ ЗАКРЫТИЯ ОКНА."""
        if self.is_dirty:
            reply = QMessageBox.question(self, 'Выход',
                                         "У вас есть несохраненные изменения.\nСохранить их перед выходом?",
                                         QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                         QMessageBox.Save)

            if reply == QMessageBox.Save:
                if self.save_project():
                    event.accept() # РАЗРЕШАЕМ ЗАКРЫТИЕ
                else:
                    event.ignore() # ОТКЛОНЯЕМ ЗАКРЫТИЕ (если пользователь нажал "Отмена" в диалоге сохранения)
            elif reply == QMessageBox.Discard:
                event.accept() # РАЗРЕШАЕМ ЗАКРЫТИЕ БЕЗ СОХРАНЕНИЯ
            else: # QMessageBox.Cancel
                event.ignore() # ОТКЛОНЯЕМ ЗАКРЫТИЕ
        else:
            event.accept() # ЕСЛИ ИЗМЕНЕНИЙ НЕТ, ПРОСТО ЗАКРЫВАЕМ
# --- КОНЕЦ: ДОБАВЛЕНА НОВАЯ ФУНКЦИЯ-ПЕРЕХВАТЧИК ЗАКРЫТИЯ ---

# --- НАЧАЛО: ДОБАВЛЕНЫ ФУНКЦИИ ЭКСПОРТА В MARKDOWN ---
    def export_to_markdown(self):
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт в Markdown", "", "Markdown Files (*.md)")
        if not path:
            return

        md_content = []
        
# --- НАЧАЛО: ДОБАВЛЕНА "ШАПКА" ДОКУМЕНТА С ПОЯСНЕНИЯМИ (v3.5) ---
        from datetime import datetime
        project_name = os.path.basename(self.current_project_path) if self.current_project_path else "Новый проект"
        generation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        header = f"""# UI/UX Спецификация Проекта: {project_name}

**Дата генерации:** {generation_date}

Этот документ является машиночитаемой и человеко-понятной спецификацией для пользовательского интерфейса. Он описывает иерархию компонентов, их свойства, события, действия, и логические связи между ними.

---

## Условные обозначения

*   **`### Имя компонента (ID: `aabbccdd`)`**: Заголовок, описывающий компонент. `Имя` - человеко-понятное название. `ID` - уникальный идентификатор.
*   **`**Тип:** `[Тип компонента]`**: Технический тип элемента (например, `Button`, `TextBox`).
*   **`> **Путь:** `Компонент А >>> Компонент Б``**: Иерархия вложенности. Разделитель `>>>` обозначает вложенность.
*   **`**Описание:**`**: Пользовательское описание функционала компонента.
*   **Свойства**: Таблица атрибутов компонента.
*   **События и Действия**: Описание интерактивной логики.
    *   **Событие**: Триггер, инициируемый пользователем или системой.
    *   **Действие**: Операция, выполняемая в ответ на событие.
    *   **Параметры**: `target` указывает на компонент, на который направлено действие.
*   **Связи**: Описание логических отношений между компонентами.
    *   **`[А] влияет на -> [Б]`**: Однонаправленная связь. Изменения в `А` влияют на `Б`.
    *   **`Синхронизированы: [А] <-> [Б]`**: Двунаправленная связь. Компоненты взаимосвязаны.
*   **Глобальные сущности**: Переменные (`@имя`), доступные в параметрах действий.

---
"""
        md_content.append(header)
        # --- КОНЕЦ: ДОБАВЛЕНА "ШАПКА" ДОКУМЕНТА С ПОЯСНЕНИЯМИ (v3.5) ---

        # 1. КОНЦЕПЦИЯ
        md_content.append("# 1. Общая концепция проекта")
        md_content.append(self.project_data.get('concept', {}).get('description', "Не задано."))
        md_content.append("\n---\n")

        # 2. ГЛОБАЛЬНЫЕ СУЩНОСТИ
        md_content.append("# 2. Глобальные сущности")
        globals_data = self.project_data.get('globals', {})
        if not globals_data:
            md_content.append("Нет глобальных сущностей.")
        else:
            md_content.append("| Имя (ключ) | Значение |")
            md_content.append("| :--- | :--- |")
            for key, value in globals_data.items():
                md_content.append(f"| `{key}` | `{value}` |")
        md_content.append("\n---\n")

        # 3. ИЕРАРХИЯ КОМПОНЕНТОВ
        md_content.append("# 3. Иерархия и свойства компонентов")
        # --- НАЧАЛО: ПЕРЕДАЕМ ДОПОЛНИТЕЛЬНЫЙ АРГУМЕНТ СО ВСЕМИ ЭЛЕМЕНТАМИ (v15.2-final) ---
        all_items_flat = self._get_all_project_items_flat()
        self._generate_markdown_recursive(self.project_data.get('tree', {}), all_items_flat, md_content, 1)
        # --- КОНЕЦ: ПЕРЕДАЕМ ДОПОЛНИТЕЛЬНЫЙ АРГУМЕНТ СО ВСЕМИ ЭЛЕМЕНТАМИ (v15.2-final) ---

        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write("\n".join(md_content))
            QMessageBox.information(self, "Успех", f"Проект успешно экспортирован в {path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить Markdown файл:\n{e}")

    # main.py
# (В классе MainWindow)

    def _generate_markdown_recursive(self, children_data, all_items_flat, md_content, level):
        for item_id, item_data in children_data.items():
            short_id = item_id.split('-')[0]
            item_path = self._get_item_path_string(item_id, all_items_flat)
            
            md_content.append(f"{'#' * (level + 2)} {item_data.get('name', 'Без имени')} (ID: `{short_id}`)")
             # --- НАЧАЛО: ДОБАВЛЕН ВЫВОД ТИПА КОМПОНЕНТА (v3.13) ---
            md_content.append(f"**Тип:** `{item_data.get('type', 'Не указан')}`")
            # --- КОНЕЦ: ДОБАВЛЕН ВЫВОД ТИПА КОМПОНЕНТА (v3.13) ---
            md_content.append(f"> **Путь:** `{item_path}`")

            description = item_data.get('description')
            if description:
                md_content.append(f"**Описание:** {description.strip()}")
            
            # --- Свойства (без изменений) ---
            properties = item_data.get('properties', [])
            if properties:
                md_content.append("\n**Свойства:**")
                md_content.append("| Название | Свойство (для ИИ) | Значение |")
                md_content.append("| :--- | :--- | :--- |")
                for prop in properties:
                    md_content.append(f"| {prop.get('name', '')} | `{prop.get('key', '')}` | `{prop.get('value', '')}` |")

            # --- События и Действия (с исправлением) ---
            events = item_data.get('events', [])
            if events:
                md_content.append("\n**События и Действия:**")
                for event in events:
                    md_content.append(f"- **{event.get('name', '')}** (`{event.get('type', '')}`):")
                    for action in event.get('actions', []):
                        params_list = []
                        action_params = action.get('params', {})
                        
                        # --- ВОТ ВТОРОЕ ИСПРАВЛЕНИЕ: ЯВНО ЧИТАЕМ TARGET_ID ---
                        target_id_from_params = action_params.get('target_id')
                        
                        if target_id_from_params:
                            target_path = self._get_item_path_string(target_id_from_params, all_items_flat)
                            params_list.append(f"target='{target_path}'")
                        elif action.get('type') in ["setProperty", "toggleVisibility", "setEnabled", "setFocus"]:
                            target_path = self._get_item_path_string(item_id, all_items_flat)
                            params_list.append(f"target='{target_path}'")
                        
                        for key, value in action_params.items():
                            if key != 'target_id':
                                params_list.append(f"{key}='{value}'")

                        params_str = ", ".join(params_list)
                        md_content.append(f"  - **{action.get('name', '')}** (`{action.get('type', '')}`) - Параметры: {params_str if params_str else 'нет'}")

            # --- Связи (без изменений) ---
            relations_found = [rel for rel in self.project_data.get('relations', {}).values() if item_id in (rel['source_id'], rel['target_id'])]
            if relations_found:
                md_content.append("\n**Связи:**")
                for relation in relations_found:
                    source_path = self._get_item_path_string(relation['source_id'], all_items_flat)
                    target_path = self._get_item_path_string(relation['target_id'], all_items_flat)
                    arrow = "->" if relation.get('type') == 'unidirectional' else "<->"
                    desc = relation.get('description', '')

                    if relation.get('type') == 'bidirectional':
                        text = f"Синхронизированы: `[{source_path}]` ↔ `[{target_path}]`"
                    else:
                        text = f"`[{source_path}]` влияет на →`[{target_path}]`"
                    
                    if desc: text += f": ({desc})"
                    md_content.append(f"- {text}")

            md_content.append("\n" + "---" + "\n")

            if 'children' in item_data and item_data['children']:
                self._generate_markdown_recursive(item_data.get('children', {}), all_items_flat, md_content, level + 1)
    # --- КОНЕЦ: ФИНАЛЬНЫЙ ФИКС ДЛЯ ПУТЕЙ И ПАРАМЕТРОВ (v4.1) ---

# --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА БЛОКА ЗАПУСКА С ИСПРАВЛЕНИЕМ ОШИБКИ ОТСТУПА (v16.3) ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    translator = QTranslator(app)
    translations_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "translations")
    
    if translator.load("qtbase_ru.qm", translations_path):
        app.installTranslator(translator)
    else:
        # ЭТОТ БЛОК ДОЛЖЕН СОДЕРЖАТЬ 'pass', ЧТОБЫ НЕ БЫЛО ОШИБКИ
        pass
        
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
# --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА БЛОКА ЗАПУСКА С ИСПРАВЛЕНИЕМ ОШИБКИ ОТСТУПА (v16.3) ---