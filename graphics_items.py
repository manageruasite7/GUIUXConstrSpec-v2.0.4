# graphics_items.py

from PyQt5.QtWidgets import QGraphicsView, QGraphicsObject, QGraphicsRectItem, QGraphicsPixmapItem
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPointF, QPoint
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor

# --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА КЛАССА CANVASVIEW НА СТАБИЛЬНУЮ ВЕРСИЮ (v8.6) ---
class CanvasView(QGraphicsView):
    rect_drawn = pyqtSignal(QRectF)
    item_selected_on_canvas = pyqtSignal(str)

    # --- НАЧАЛО: ДОБАВЛЕН СИГНАЛ ДЛЯ ИЗМЕНЕНИЯ МАСШТАБА (v10.3) ---
    zoom_changed = pyqtSignal(float)
    # --- КОНЕЦ: ДОБАВЛЕН СИГНАЛ ДЛЯ ИЗМЕНЕНИЯ МАСШТАБА (v10.3) ---
    # --- НАЧАЛО: ДОБАВЛЕН СИГНАЛ ДЛЯ КООРДИНАТ КУРСОРА (v10.8) ---
    mouse_moved_on_scene = pyqtSignal(QPointF)
    # --- КОНЕЦ: ДОБАВЛЕН СИГНАЛ ДЛЯ КООРДИНАТ КУРСОРА (v10.8) ---


    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.start_pos = None
        self.current_rect_item = None
        self.drawing_mode = False
        
        # --- ПАРАМЕТРЫ ДЛЯ РУЧНОГО ПЕРЕМЕЩЕНИЯ ХОЛСТА (ПАНА) ---
        self._panning = False
        self._pan_start_pos = QPoint()

        # --- НАЧАЛО: ВКЛЮЧАЕМ ОТСЛЕЖИВАНИЕ ДВИЖЕНИЯ МЫШИ (v10.8) ---
        self.setMouseTracking(True)
        # --- КОНЕЦ: ВКЛЮЧАЕМ ОТСЛЕЖИВАНИЕ ДВИЖЕНИЯ МЫШИ (v10.8) ---

        # УСТАНАВЛИВАЕМ РЕЖИМ, КОТОРЫЙ НЕ МЕШАЕТ РУЧНОЙ ОБРАБОТКЕ СОБЫТИЙ
        self.setDragMode(QGraphicsView.NoDrag)
        # УЛУЧШАЕМ КАЧЕСТВО РИСОВАНИЯ
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)

    def set_drawing_mode(self, enabled):
        self.drawing_mode = enabled
        self.viewport().setCursor(Qt.CrossCursor if enabled else Qt.ArrowCursor)

    def mousePressEvent(self, event):
        # НАЖАТИЕ СРЕДНЕЙ КНОПКИ МЫШИ - НАЧАЛО ПЕРЕМЕЩЕНИЯ ХОЛСТА
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start_pos = event.pos()
            self.viewport().setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        # НАЖАТИЕ ЛЕВОЙ КНОПКИ МЫШИ В РЕЖИМЕ РИСОВАНИЯ
        if self.drawing_mode and event.button() == Qt.LeftButton:
            self.start_pos = self.mapToScene(event.pos())
            pen = QPen(Qt.gray, 1, Qt.DashLine)
            self.current_rect_item = self.scene().addRect(QRectF(self.start_pos, self.start_pos), pen)
            event.accept()
            return
        
        # ВО ВСЕХ ОСТАЛЬНЫХ СЛУЧАЯХ (КЛИК ЛЕВОЙ КНОПКОЙ ДЛЯ ВЫДЕЛЕНИЯ И Т.Д.)
        # ПЕРЕДАЕМ СОБЫТИЕ БАЗОВОМУ КЛАССУ ДЛЯ СТАНДАРТНОЙ ОБРАБОТКИ
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # --- НАЧАЛО: ОТПРАВКА СИГНАЛА С КООРДИНАТАМИ КУРСОРА (v10.8) ---
        scene_pos = self.mapToScene(event.pos())
        self.mouse_moved_on_scene.emit(scene_pos)
        # --- КОНЕЦ: ОТПРАВКА СИГНАЛА С КООРДИНАТАМИ КУРСОРА (v10.8) ---
        # ЕСЛИ ВКЛЮЧЕНО ПЕРЕМЕЩЕНИЕ ХОЛСТА
        if self._panning:
            delta = event.pos() - self._pan_start_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self._pan_start_pos = event.pos()
            event.accept()
            return
        
        # ЕСЛИ ВКЛЮЧЕНО РИСОВАНИЕ
        if self.drawing_mode and self.current_rect_item:
            end_pos = self.mapToScene(event.pos())
            rect = QRectF(self.start_pos, end_pos).normalized()
            self.current_rect_item.setRect(rect)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        # ОТПУСКАНИЕ СРЕДНЕЙ КНОПКИ МЫШИ - КОНЕЦ ПЕРЕМЕЩЕНИЯ
        if event.button() == Qt.MiddleButton and self._panning:
            self._panning = False
            self.viewport().setCursor(Qt.ArrowCursor if not self.drawing_mode else Qt.CrossCursor)
            event.accept()
            return
        
        # ОТПУСКАНИЕ ЛЕВОЙ КНОПКИ МЫШИ ПОСЛЕ РИСОВАНИЯ
        if self.drawing_mode and self.current_rect_item:
            final_rect = self.current_rect_item.rect()
            self.scene().removeItem(self.current_rect_item)
            self.current_rect_item = None
            self.set_drawing_mode(False) # АВТОМАТИЧЕСКИ ВЫКЛЮЧАЕМ РЕЖИМ РИСОВАНИЯ
            self.rect_drawn.emit(final_rect)
            event.accept()
            return
        
        super().mouseReleaseEvent(event)
        
        # ПОСЛЕ СТАНДАРТНОЙ ОБРАБОТКИ ПРОВЕРЯЕМ, НЕ ВЫБРАЛСЯ ЛИ ЭЛЕМЕНТ
        selected_items = self.scene().selectedItems()
        if selected_items and isinstance(selected_items[0], BoundRectItem):
            self.item_selected_on_canvas.emit(selected_items[0].item_id)

# --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА wheelEvent С ОГРАНИЧЕНИЕМ МАСШТАБА (v10.4) ---
    def wheelEvent(self, event):
        """ОБРАБАТЫВАЕТ ПРОКРУТКУ КОЛЕСА МЫШИ С ОГРАНИЧЕНИЯМИ МАСШТАБА."""
        if event.modifiers() == Qt.ControlModifier:
            MIN_ZOOM = 0.05  # 10%
            MAX_ZOOM = 10.0 # 1000%
            
            # ТЕКУЩИЙ УРОВЕНЬ МАСШТАБА
            current_scale = self.transform().m11()
            
            # ОПРЕДЕЛЯЕМ НАПРАВЛЕНИЕ И БАЗОВЫЙ ФАКТОР
            delta = event.angleDelta().y()
            if delta > 0:
                zoom_factor = 1.25
            else:
                zoom_factor = 0.8
            
            # ПРЕДПОЛАГАЕМЫЙ НОВЫЙ МАСШТАБ
            new_scale = current_scale * zoom_factor
            
            # ПРОВЕРЯЕМ, НЕ ВЫХОДИМ ЛИ МЫ ЗА ГРАНИЦЫ
            if new_scale < MIN_ZOOM:
                # ЕСЛИ ВЫХОДИМ, ВЫЧИСЛЯЕМ ФАКТОР, ЧТОБЫ УСТАНОВИТЬ ТОЧНО МИНИМАЛЬНЫЙ ЗУМ
                zoom_factor = MIN_ZOOM / current_scale
            elif new_scale > MAX_ZOOM:
                # АНАЛОГИЧНО ДЛЯ МАКСИМАЛЬНОГО ЗУМА
                zoom_factor = MAX_ZOOM / current_scale
            
            # ПРИМЕНЯЕМ ВЫЧИСЛЕННЫЙ ФАКТОР
            self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
            self.scale(zoom_factor, zoom_factor)
            
            # ОТПРАВЛЯЕМ СИГНАЛ С НОВЫМ ЗНАЧЕНИЕМ
            current_zoom = self.transform().m11() * 100
            self.zoom_changed.emit(current_zoom)
        else:
            super().wheelEvent(event)
    # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА wheelEvent С ОГРАНИЧЕНИЕМ МАСШТАБА (v10.4) ---
# --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА КЛАССА CANVASVIEW НА СТАБИЛЬНУЮ ВЕРСИЮ (v8.6) ---

# --- НАЧАЛО: НОВЫЙ МЕТОД ДЛЯ ПРОГРАММНОЙ УСТАНОВКИ МАСШТАБА (v10.6) ---
    def set_zoom(self, scale_factor):
        """УСТАНАВЛИВАЕТ АБСОЛЮТНЫЙ МАСШТАБ ДЛЯ ХОЛСТА."""
        # ПОЛУЧАЕМ ТЕКУЩИЙ МАСШТАБ
        current_scale = self.transform().m11()
        if current_scale == 0: return # ИЗБЕГАЕМ ДЕЛЕНИЯ НА НОЛЬ

        # ВЫЧИСЛЯЕМ ОТНОСИТЕЛЬНЫЙ ФАКТОР ДЛЯ МАСШТАБИРОВАНИЯ
        factor = scale_factor / current_scale
        
        # УСТАНАВЛИВАЕМ "ЯКОРЬ" В ЦЕНТРЕ ВИДИМОЙ ОБЛАСТИ
        self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
        self.scale(factor, factor)
    # --- КОНЕЦ: НОВЫЙ МЕТОД ДЛЯ ПРОГРАММНОЙ УСТАНОВКИ МАСШТАБА (v10.6) ---

# --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА BOUNDRECTITEM НА ФИНАЛЬНУЮ СТАБИЛЬНУЮ ВЕРСИЮ (v8.9-final-stable) ---
class BoundRectItem(QGraphicsObject):
    geometryChanged = pyqtSignal(str, QRectF)

    HANDLE_SIZE = 10.0 # УВЕЛИЧИМ ОБЛАСТЬ МАРКЕРА ДЛЯ УДОБСТВА
    HANDLE_SQUARE = QRectF(-HANDLE_SIZE / 2, -HANDLE_SIZE / 2, HANDLE_SIZE, HANDLE_SIZE)

    def __init__(self, rect, item_id):
        super().__init__()
        self.item_id = item_id
        
        # --- НАЧАЛО: ДОБАВЛЕНЫ ХРАНИЛИЩА ДЛЯ СТИЛЕЙ (v9.9) ---
        self.active_style = {}
        self.inactive_style = {}
        # --- КОНЕЦ: ДОБАВЛЕНЫ ХРАНИЛИЩА ДЛЯ СТИЛЕЙ (v9.9) ---

        self.rect_item = QGraphicsRectItem(QRectF(0, 0, rect.width(), rect.height()), self)
        self.setPos(rect.topLeft())
        
        self.rect_item.setPen(QPen(Qt.gray, 1, Qt.DashLine))
        self.rect_item.setBrush(QBrush(Qt.NoBrush))
        
        self.handles = {}
        self.selected_handle = None
        self.mouse_press_pos = None
        self.mouse_press_scene_rect = None

        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        
        self.update_handles()
        self.update_handle_cursors()

# --- НАЧАЛО: ИЗМЕНЕНИЕ set_relation_highlight ДЛЯ ПРИЕМА СТИЛЕЙ (v2.0.5) ---
    def set_relation_highlight(self, is_primary, style_settings):
        pen = self.rect_item.pen()
        
        # БЕРЕМ ЦВЕТ ИЗ ПЕРЕДАННЫХ НАСТРОЕК
        color_key = "highlight_color_primary" if is_primary else "highlight_color_secondary"
        color = style_settings.get(color_key, "#0078D4") # Синий цвет - запасной вариант
        pen.setColor(QColor(color))
        
        pen.setStyle(Qt.SolidLine)
        pen.setWidth(2 if is_primary else 1)
        self.rect_item.setPen(pen)
    # --- КОНЕЦ: ИЗМЕНЕНИЕ set_relation_highlight ДЛЯ ПРИЕМА СТИЛЕЙ (v2.0.5) ---

    def reset_to_default_style(self, is_selected):
        self.set_selected_visual(is_selected)
    # --- КОНЕЦ: НОВЫЕ МЕТОДЫ ДЛЯ ПОДСВЕТКИ СВЯЗАННЫХ ЭЛЕМЕНТОВ (v2.1) ---

    def boundingRect(self):
        # РАСШИРИМ ГРАНИЦЫ, ЧТОБЫ МАРКЕРЫ ТОЖЕ ПОПАДАЛИ В ОБЛАСТЬ ОБНОВЛЕНИЯ
        padding = self.HANDLE_SIZE
        return self.rect_item.boundingRect().adjusted(-padding, -padding, padding, padding)

    def paint(self, painter, option, widget=None):
        pass # РИСОВАНИЕ ПРОИСХОДИТ В ДОЧЕРНИХ ЭЛЕМЕНТАХ
    
    def rect_in_scene_coords(self):
        return self.sceneTransform().mapRect(self.rect_item.rect())

    def setRect(self, rect):
        self.setPos(rect.topLeft())
        self.rect_item.setRect(QRectF(0, 0, rect.width(), rect.height()))
        self.update_handles()
        self.prepareGeometryChange()

    # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА set_selected_visual И ДОБАВЛЕНИЕ apply_styles (v9.9) ---
    def apply_styles(self, active_style, inactive_style):
        """ПОЛУЧАЕТ И СОХРАНЯЕТ СЛОВАРИ С НАСТРОЙКАМИ СТИЛЕЙ."""
        self.active_style = active_style
        self.inactive_style = inactive_style
        # СРАЗУ ПРИМЕНЯЕМ СТИЛЬ В ЗАВИСИМОСТИ ОТ ТЕКУЩЕГО СОСТОЯНИЯ ВЫДЕЛЕНИЯ
        self.set_selected_visual(self.isSelected())

    def set_selected_visual(self, is_selected):
        """ПРИМЕНЯЕТ СОХРАНЕННЫЕ СТИЛИ К ЭЛЕМЕНТУ."""
        style_to_apply = self.active_style if is_selected else self.inactive_style
        if not style_to_apply:
            return # ЕСЛИ СТИЛИ ЕЩЕ НЕ ЗАГРУЖЕНЫ, НИЧЕГО НЕ ДЕЛАЕМ

        # 1. НАСТРОЙКА ЛИНИИ (ПЕРА)
        pen = QPen()
        pen.setWidth(style_to_apply.get('line_width', 1))
        pen.setColor(QColor(style_to_apply.get('line_color', '#000000')))
        pen.setStyle(style_to_apply.get('line_style', Qt.SolidLine))
        
        # 2. НАСТРОЙКА ЗАЛИВКИ (КИСТИ)
        brush = QBrush()
        fill_color = QColor(style_to_apply.get('fill_color', '#ffffff'))
        # ПРЕОБРАЗУЕМ ПРОЗРАЧНОСТЬ ИЗ % (0-100) В ЗНАЧЕНИЕ ALPHA-КАНАЛА (0-255)
        opacity = style_to_apply.get('fill_opacity', 0)
        fill_color.setAlpha(int(opacity * 2.55))
        brush.setColor(fill_color)
        brush.setStyle(Qt.SolidPattern)

        # 3. ПРИМЕНЕНИЕ К ЭЛЕМЕНТУ
        self.rect_item.setPen(pen)
        self.rect_item.setBrush(brush)
    # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА set_selected_visual И ДОБАВЛЕНИЕ apply_styles (v9.9) ---

    def itemChange(self, change, value):
        if change == QGraphicsObject.ItemSelectedChange:
            for handle in self.handles.values():
                handle.setVisible(value)
        elif change == QGraphicsObject.ItemPositionHasChanged and self.scene():
            self.geometryChanged.emit(self.item_id, self.rect_in_scene_coords())
        return super().itemChange(change, value)

    def update_handles(self):
        rect = self.rect_item.rect()
        positions = {
            'topLeft': rect.topLeft(), 'topRight': rect.topRight(),
            'bottomLeft': rect.bottomLeft(), 'bottomRight': rect.bottomRight(),
            'top': (rect.topLeft() + rect.topRight()) / 2,
            'bottom': (rect.bottomLeft() + rect.bottomRight()) / 2,
            'left': (rect.topLeft() + rect.bottomLeft()) / 2,
            'right': (rect.topRight() + rect.bottomRight()) / 2,
        }
        for name, pos in positions.items():
            if name not in self.handles:
                handle = QGraphicsRectItem(self.HANDLE_SQUARE, self)
                handle.setBrush(QBrush(Qt.white))
                handle.setPen(QPen(Qt.black, 1.0))
                handle.setFlag(QGraphicsRectItem.ItemIsMovable, False)
                handle.setVisible(False)
                self.handles[name] = handle
            self.handles[name].setPos(pos)

    def update_handle_cursors(self):
        self.handles['topLeft'].setCursor(Qt.SizeFDiagCursor)
        self.handles['topRight'].setCursor(Qt.SizeBDiagCursor)
        self.handles['bottomLeft'].setCursor(Qt.SizeBDiagCursor)
        self.handles['bottomRight'].setCursor(Qt.SizeFDiagCursor)
        self.handles['top'].setCursor(Qt.SizeVerCursor)
        self.handles['bottom'].setCursor(Qt.SizeVerCursor)
        self.handles['left'].setCursor(Qt.SizeHorCursor)
        self.handles['right'].setCursor(Qt.SizeHorCursor)
    
    # --- НАДЕЖНАЯ ПРОВЕРКА ПОПАДАНИЯ В МАРКЕР ---
    def _get_handle_at(self, pos):
        for name, handle in self.handles.items():
            if handle.isVisible() and handle.boundingRect().contains(handle.mapFromParent(pos)):
                return name
        return None

    def hoverMoveEvent(self, event):
        handle_name = self._get_handle_at(event.pos())
        if handle_name:
            self.setCursor(self.handles[handle_name].cursor())
        else:
            self.setCursor(Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        self.selected_handle = self._get_handle_at(event.pos())
        if self.selected_handle:
            self.mouse_press_pos = event.scenePos()
            self.mouse_press_scene_rect = self.rect_in_scene_coords()
            event.accept()
            return
        super().mousePressEvent(event)

     # --- НАЧАЛО: ПОЛНАЯ ЗАМЕНА mouseMoveEvent С ИСПРАВЛЕНИЕМ РЕГИСТРА БУКВ (v9.1-final) ---
    def mouseMoveEvent(self, event):
        if self.selected_handle:
            # ПРИВОДИМ ИМЯ МАРКЕРА К НИЖНЕМУ РЕГИСТРУ ОДИН РАЗ
            handle_name_lower = self.selected_handle.lower()
            
            new_rect = QRectF(self.mouse_press_scene_rect)
            delta = event.scenePos() - self.mouse_press_pos

            # ИСПОЛЬЗУЕМ ПРОВЕРКИ В НИЖНЕМ РЕГИСТРЕ - ЭТО ИСПРАВЛЯЕТ ВСЕ ОШИБКИ
            if 'left' in handle_name_lower:
                new_rect.setLeft(new_rect.left() + delta.x())
            if 'right' in handle_name_lower:
                new_rect.setRight(new_rect.right() + delta.x())
            if 'top' in handle_name_lower:
                new_rect.setTop(new_rect.top() + delta.y())
            if 'bottom' in handle_name_lower:
                new_rect.setBottom(new_rect.bottom() + delta.y())
            
            self.setRect(new_rect.normalized())
            return
            
        super().mouseMoveEvent(event)
    # --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА mouseMoveEvent С ИСПРАВЛЕНИЕМ РЕГИСТРА БУКВ (v9.1-final) ---

    def mouseReleaseEvent(self, event):
        if self.selected_handle:
            self.selected_handle = None
            self.geometryChanged.emit(self.item_id, self.rect_in_scene_coords())
            event.accept()
            return
        super().mouseReleaseEvent(event)
# --- КОНЕЦ: ПОЛНАЯ ЗАМЕНА BOUNDRECTITEM НА ФИНАЛЬНУЮ СТАБИЛЬНУЮ ВЕРСИЮ (v8.9-final-stable) ---