from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QGraphicsPixmapItem, QGraphicsSimpleTextItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen, QPixmap
import os


class TrafficLightController:
    def __init__(self, config):
        self.config = config
        self.vehicle_green = True
        self.vehicle_yellow = False
        self.pedestrian_green = False
        self.timer = 0

    def update(self) -> None:
        self.timer += 1
        if self.timer >= self.config.TRAFFIC_LIGHT_CYCLE:
            self.timer = 0

        if self.timer < self.config.VEHICLE_GREEN_TIME:
            self.vehicle_green = True
            self.vehicle_yellow = False
            self.pedestrian_green = False
        elif self.timer < self.config.VEHICLE_GREEN_TIME + self.config.VEHICLE_YELLOW_TIME:
            self.vehicle_green = False
            self.vehicle_yellow = True
            self.pedestrian_green = False
        else:
            self.vehicle_green = False
            self.vehicle_yellow = False
            self.pedestrian_green = True

    def vehicle_state_for(self, axis: str) -> str:
        if self.vehicle_yellow:
            return 'yellow'
        if axis == 'horizontal':
            return 'green' if self.vehicle_green else 'red'
        if axis == 'vertical':
            return 'green' if (not self.vehicle_green) else 'red'
        raise ValueError(f'Unknown axis: {axis}')

    def pedestrian_state_for(self, axis: str) -> str:
        if self.vehicle_yellow:
            return 'red'
        if axis == 'vertical':
            return 'green' if self.pedestrian_green else 'red'
        if axis == 'horizontal':
            return 'green' if (not self.pedestrian_green) else 'red'
        raise ValueError(f'Unknown axis: {axis}')


class TrafficLightItem(QGraphicsPixmapItem):
    def __init__(
        self,
        x: float,
        y: float,
        light_type: str = 'vehicle',
        scale: float = 1.0,
        rotation: float = 0.0,
        name: str | None = None,
        on_changed=None,
        on_selected=None,
    ):
        super().__init__()
        self.light_type = light_type
        self.current_state = 'red'
        self.name = name or light_type
        self.config_key = self.name
        self.role = None
        self.axis = None
        self.mirrored = False
        self.supports_rotation = True
        self.supports_scale = True
        self._editor_enabled = False
        self.on_changed = on_changed
        self.on_selected = on_selected

        self.load_image()
        self.setPos(x, y)
        self.setScale(scale)
        self.setRotation(rotation)
        self.setZValue(10)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

    def load_image(self):
        image_files = {
            'vehicle': {
                'red': 'vehicle_red.png',
                'yellow': 'vehicle_yellow.png',
                'green': 'vehicle_green.png',
            },
            'pedestrian': {
                'red': 'pedestrian_red.png',
                'green': 'pedestrian_green.png',
            },
        }
        filename = image_files.get(self.light_type, {}).get(self.current_state, '')
        if filename and os.path.exists(filename):
            pixmap = QPixmap(filename)
            if not pixmap.isNull():
                self.setPixmap(pixmap)
                self.setTransformOriginPoint(self.boundingRect().center())
                return
        self._create_fallback_pixmap()
        self.setTransformOriginPoint(self.boundingRect().center())

    def _create_fallback_pixmap(self):
        if self.light_type == 'vehicle':
            width, height = 40, 120
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QBrush(QColor(50, 50, 50)))
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.drawRoundedRect(0, 0, width, height, 5, 5)

            colors = {
                'red': QColor(255, 0, 0),
                'yellow': QColor(255, 255, 0),
                'green': QColor(0, 255, 0),
            }

            top_color = colors['red'] if self.current_state == 'red' else QColor(50, 50, 50)
            mid_color = colors['yellow'] if self.current_state == 'yellow' else QColor(50, 50, 50)
            low_color = colors['green'] if self.current_state == 'green' else QColor(50, 50, 50)

            painter.setBrush(QBrush(top_color))
            painter.drawEllipse(width // 2 - 15, 10, 30, 30)
            painter.setBrush(QBrush(mid_color))
            painter.drawEllipse(width // 2 - 15, 45, 30, 30)
            painter.setBrush(QBrush(low_color))
            painter.drawEllipse(width // 2 - 15, 80, 30, 30)
            painter.end()
        else:
            width, height = 60, 60
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QBrush(QColor(50, 50, 50)))
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.drawRoundedRect(0, 0, width, height, 5, 5)
            painter.setPen(QPen(Qt.GlobalColor.white, 1))
            if self.current_state == 'green':
                painter.setBrush(QBrush(QColor(0, 200, 0)))
                painter.drawEllipse(15, 12, 30, 30)
            else:
                painter.setBrush(QBrush(QColor(220, 0, 0)))
                painter.drawEllipse(15, 12, 30, 30)
            painter.end()

        self.setPixmap(pixmap)

    def set_editor_enabled(self, enabled: bool):
        self._editor_enabled = enabled
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, enabled)
        if not enabled and self.isSelected():
            self.setSelected(False)

    def update_state(self, state: str):
        if state == self.current_state:
            return
        self.current_state = state
        self.load_image()
        self.setTransformOriginPoint(self.boundingRect().center())

    def move_to(self, x: float, y: float):
        self.setPos(x, y)
        self._emit_changed()

    def resize(self, scale: float):
        self.setScale(scale)
        self._emit_changed()

    def rotate(self, angle: float):
        self.setRotation(angle)
        self._emit_changed()

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if not self._editor_enabled:
            return result

        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._emit_changed()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged and bool(value):
            if self.on_selected is not None:
                self.on_selected(self)
        return result

    def _emit_changed(self):
        if self.on_changed is not None:
            self.on_changed(self)


class EditableSpawnPointItem(QGraphicsEllipseItem):
    def __init__(self, x: float, y: float, name: str, label: str, color: QColor, on_changed=None, on_selected=None):
        size = 18
        super().__init__(-size / 2, -size / 2, size, size)
        self.name = name
        self.config_key = name
        self.label = label
        self.supports_rotation = False
        self.supports_scale = False
        self._editor_enabled = False
        self.on_changed = on_changed
        self.on_selected = on_selected
        self._base_color = color
        self._selected_color = QColor(255, 220, 0)

        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.setBrush(QBrush(self._base_color))
        self.setPos(x, y)
        self.setZValue(30)
        self.setVisible(False)

        self.text_item = QGraphicsSimpleTextItem(label, self)
        self.text_item.setBrush(QBrush(Qt.GlobalColor.white))
        self.text_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.text_item.setPos(12, -10)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

    def set_editor_enabled(self, enabled: bool):
        self._editor_enabled = enabled
        self.setVisible(enabled)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, enabled)
        if not enabled and self.isSelected():
            self.setSelected(False)
        self._update_style()

    def move_to(self, x: float, y: float):
        self.setPos(x, y)
        self._emit_changed()

    def _update_style(self):
        brush_color = self._selected_color if self.isSelected() else self._base_color
        self.setBrush(QBrush(brush_color))

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if not self._editor_enabled:
            return result

        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._emit_changed()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self._update_style()
            if bool(value) and self.on_selected is not None:
                self.on_selected(self)
        return result

    def _emit_changed(self):
        if self.on_changed is not None:
            self.on_changed(self)
