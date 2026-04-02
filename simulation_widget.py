import random

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPixmap, QTransform
from PyQt6.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from classes import Crosswalk, Pedestrian, Vehicle
from config import SimulationConfig
from simulation_objects import PedestrianItem, VehicleItem
from statistics import SimulationStatistics
from traffic_light import EditableSpawnPointItem, TrafficLightController, TrafficLightItem


def _format_scalar_for_export(value):
    if isinstance(value, bool):
        return 'True' if value else 'False'
    if isinstance(value, float):
        text = f'{value:.3f}'.rstrip('0').rstrip('.')
        if '.' not in text:
            text += '.0'
        return text
    return str(value)


class SimulationWidget(QGroupBox):
    """Окно симуляции: сцена, движение, редактор объектов и runtime-конфиг."""

    EDITOR_LABELS = {
        'vehicle_horizontal': 'Светофор транспорта: горизонталь',
        'vehicle_vertical': 'Светофор транспорта: вертикаль (вниз)',
        'vehicle_vertical_opposite': 'Светофор транспорта: вертикаль (вверх)',
        'vehicle_horizontal_opposite': 'Светофор транспорта: горизонталь (влево)',
        'pedestrian_horizontal': 'Светофор пешеходов: горизонтальный',
        'pedestrian_vertical': 'Светофор пешеходов: вертикальный',
        'pedestrian_horizontal_mirror': 'Светофор пешеходов: горизонтальный зеркальный',
        'pedestrian_vertical_mirror': 'Светофор пешеходов: вертикальный зеркальный',
        'vehicle_spawn_horizontal_right': 'Старт машин: вправо',
        'vehicle_spawn_horizontal_left': 'Старт машин: влево',
        'vehicle_spawn_vertical_down': 'Старт машин: вниз',
        'vehicle_spawn_vertical_up': 'Старт машин: вверх',
    }

    CONFIG_TABLE_EXCLUDED = {
        'TRAFFIC_LIGHT_CYCLE',  # вычисляется автоматически
        'ANALYSIS_UPDATE_INTERVAL',  # в main.py сейчас используется фиксированное значение
        'VEHICLE_SPAWN_OFFSET',
        'VEHICLE_LIGHT_WIDTH',
        'VEHICLE_LIGHT_HEIGHT',
        'PEDESTRIAN_LIGHT_WIDTH',
        'PEDESTRIAN_LIGHT_HEIGHT',
        'VEHICLE_LIGHT_HORIZONTAL_POS',
        'VEHICLE_LIGHT_VERTICAL_POS',
        'PEDESTRIAN_LIGHT_HORIZONTAL_POS',
        'PEDESTRIAN_LIGHT_VERTICAL_POS',
        # Эти поля удобнее менять визуально на сцене
        'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_X',
        'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_Y',
        'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_ROTATION',
        'TRAFFIC_LIGHT_VEHICLE_VERTICAL_X',
        'TRAFFIC_LIGHT_VEHICLE_VERTICAL_Y',
        'TRAFFIC_LIGHT_VEHICLE_VERTICAL_ROTATION',
        'TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_X',
        'TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_Y',
        'TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_ROTATION',
        'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_X',
        'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_Y',
        'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_ROTATION',
        'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_X',
        'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_Y',
        'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_ROTATION',
        'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_X',
        'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_Y',
        'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_ROTATION',
        'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_X',
        'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_Y',
        'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_ROTATION',
        'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_X',
        'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_Y',
        'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_ROTATION',
        'TRAFFIC_LIGHT_VEHICLE_SCALE',
        'TRAFFIC_LIGHT_PEDESTRIAN_SCALE',
        'VEHICLE_SPAWN_HORIZONTAL_RIGHT_X',
        'VEHICLE_SPAWN_HORIZONTAL_RIGHT_Y',
        'VEHICLE_SPAWN_HORIZONTAL_LEFT_X',
        'VEHICLE_SPAWN_HORIZONTAL_LEFT_Y',
        'VEHICLE_SPAWN_VERTICAL_DOWN_X',
        'VEHICLE_SPAWN_VERTICAL_DOWN_Y',
        'VEHICLE_SPAWN_VERTICAL_UP_X',
        'VEHICLE_SPAWN_VERTICAL_UP_Y',
    }

    CONFIG_LABELS = {
        'UPDATE_INTERVAL': 'Шаг симуляции (мс)',
        'VEHICLE_GENERATION_INTERVAL': 'Интервал генерации машин (мс)',
        'PEDESTRIAN_GENERATION_INTERVAL': 'Интервал генерации пешеходов (мс)',
        'TRAFFIC_LIGHT_UPDATE_INTERVAL': 'Интервал обновления светофора (мс)',
        'VEHICLE_GREEN_TIME': 'Зеленый для машин',
        'VEHICLE_YELLOW_TIME': 'Желтый для машин',
        'PEDESTRIAN_GREEN_TIME': 'Зеленый для пешеходов',
        'SCENE_WIDTH': 'Ширина сцены',
        'SCENE_HEIGHT': 'Высота сцены',
        'HORIZONTAL_LANE_Y': 'Y горизонтальной дороги',
        'VERTICAL_LANE_X': 'X вертикальной дороги',
        'HORIZONTAL_CROSSWALK_X': 'X горизонтального перехода',
        'VERTICAL_CROSSWALK_Y': 'Y вертикального перехода',
        'CROSSWALK_WIDTH': 'Ширина перехода',
        'CROSSWALK_LENGTH': 'Длина перехода',
        'HORIZONTAL_ONCOMING_TRAFFIC_OFFSET': 'Смещение встречного потока по горизонтали',
        'VERTICAL_ONCOMING_TRAFFIC_OFFSET': 'Смещение встречного потока по вертикали',
        'VEHICLE_WIDTH': 'Ширина машины',
        'VEHICLE_HEIGHT': 'Высота машины',
        'PEDESTRIAN_WIDTH': 'Ширина пешехода',
        'PEDESTRIAN_HEIGHT': 'Высота пешехода',
        'MIN_DISTANCE_BETWEEN_VEHICLES': 'Мин. дистанция между машинами',
        'VEHICLE_SPEED_MEAN': 'Средняя скорость машин',
        'VEHICLE_SPEED_VARIATION': 'Разброс скорости машин',
        'PEDESTRIAN_SPEED_MEAN': 'Средняя скорость пешеходов',
        'PEDESTRIAN_SPEED_VARIATION': 'Разброс скорости пешеходов',
        'VEHICLE_ROTATION_RIGHT': 'Поворот машин вправо',
        'VEHICLE_ROTATION_LEFT': 'Поворот машин влево',
        'VEHICLE_ROTATION_DOWN': 'Поворот машин вниз',
        'VEHICLE_ROTATION_UP': 'Поворот машин вверх',
        'PEDESTRIAN_SPAWN_VERTICAL_X_MIN': 'Мин. X спавна вертикальных пешеходов',
        'PEDESTRIAN_SPAWN_VERTICAL_Y': 'Y спавна вертикальных пешеходов',
        'PEDESTRIAN_SPAWN_HORIZONTAL_X': 'X спавна горизонтальных пешеходов',
        'PEDESTRIAN_SPAWN_HORIZONTAL_Y_MIN': 'Мин. Y спавна горизонтальных пешеходов',
        'PEDESTRIAN_SPAWN_HORIZONTAL_Y_MAX_OFFSET': 'Диапазон Y спавна горизонтальных пешеходов',
        'PEDESTRIAN_VERTICAL_CROSS_END_Y': 'Финиш вертикального перехода',
        'PEDESTRIAN_HORIZONTAL_CROSS_END_X': 'Финиш горизонтального перехода',
        'PEDESTRIAN_ROTATION_VERTICAL': 'Поворот вертикальных пешеходов',
        'PEDESTRIAN_ROTATION_HORIZONTAL': 'Поворот горизонтальных пешеходов',
        'VEHICLE_STOP_DISTANCE_HORIZONTAL_RIGHT': 'Стоп-линия машин вправо',
        'VEHICLE_STOP_DISTANCE_HORIZONTAL_LEFT': 'Стоп-линия машин влево',
        'VEHICLE_STOP_DISTANCE_VERTICAL_DOWN': 'Стоп-линия машин вниз',
        'VEHICLE_STOP_DISTANCE_VERTICAL_UP': 'Стоп-линия машин вверх',
        'VEHICLE_EXTENDED_CROSSWALK_CHECK_HORIZONTAL': 'Доп. проверка перехода по горизонтали',
        'VEHICLE_EXTENDED_CROSSWALK_CHECK_VERTICAL': 'Доп. проверка перехода по вертикали',
        'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_FLIP_X': 'Зеркалить горизонтальный пешеходный светофор по X',
        'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_FLIP_X': 'Зеркалить вертикальный пешеходный светофор по X',
    }

    CONFIG_ORDER = [
        'UPDATE_INTERVAL',
        'VEHICLE_GENERATION_INTERVAL',
        'PEDESTRIAN_GENERATION_INTERVAL',
        'TRAFFIC_LIGHT_UPDATE_INTERVAL',
        'VEHICLE_GREEN_TIME',
        'VEHICLE_YELLOW_TIME',
        'PEDESTRIAN_GREEN_TIME',
        'VEHICLE_SPEED_MEAN',
        'VEHICLE_SPEED_VARIATION',
        'PEDESTRIAN_SPEED_MEAN',
        'PEDESTRIAN_SPEED_VARIATION',
        'SCENE_WIDTH',
        'SCENE_HEIGHT',
        'HORIZONTAL_LANE_Y',
        'VERTICAL_LANE_X',
        'HORIZONTAL_CROSSWALK_X',
        'VERTICAL_CROSSWALK_Y',
        'CROSSWALK_WIDTH',
        'CROSSWALK_LENGTH',
        'HORIZONTAL_ONCOMING_TRAFFIC_OFFSET',
        'VERTICAL_ONCOMING_TRAFFIC_OFFSET',
        'VEHICLE_WIDTH',
        'VEHICLE_HEIGHT',
        'PEDESTRIAN_WIDTH',
        'PEDESTRIAN_HEIGHT',
        'MIN_DISTANCE_BETWEEN_VEHICLES',
        'VEHICLE_ROTATION_RIGHT',
        'VEHICLE_ROTATION_LEFT',
        'VEHICLE_ROTATION_DOWN',
        'VEHICLE_ROTATION_UP',
        'PEDESTRIAN_SPAWN_VERTICAL_X_MIN',
        'PEDESTRIAN_SPAWN_VERTICAL_Y',
        'PEDESTRIAN_SPAWN_HORIZONTAL_X',
        'PEDESTRIAN_SPAWN_HORIZONTAL_Y_MIN',
        'PEDESTRIAN_SPAWN_HORIZONTAL_Y_MAX_OFFSET',
        'PEDESTRIAN_VERTICAL_CROSS_END_Y',
        'PEDESTRIAN_HORIZONTAL_CROSS_END_X',
        'PEDESTRIAN_ROTATION_VERTICAL',
        'PEDESTRIAN_ROTATION_HORIZONTAL',
        'VEHICLE_STOP_DISTANCE_HORIZONTAL_RIGHT',
        'VEHICLE_STOP_DISTANCE_HORIZONTAL_LEFT',
        'VEHICLE_STOP_DISTANCE_VERTICAL_DOWN',
        'VEHICLE_STOP_DISTANCE_VERTICAL_UP',
        'VEHICLE_EXTENDED_CROSSWALK_CHECK_HORIZONTAL',
        'VEHICLE_EXTENDED_CROSSWALK_CHECK_VERTICAL',
    ]

    SCENE_RELATED_FIELDS = {
        'SCENE_WIDTH',
        'SCENE_HEIGHT',
        'HORIZONTAL_LANE_Y',
        'VERTICAL_LANE_X',
        'HORIZONTAL_CROSSWALK_X',
        'VERTICAL_CROSSWALK_Y',
        'CROSSWALK_WIDTH',
        'CROSSWALK_LENGTH',
        'HORIZONTAL_ONCOMING_TRAFFIC_OFFSET',
        'VERTICAL_ONCOMING_TRAFFIC_OFFSET',
    }
    VEHICLE_VISUAL_FIELDS = {
        'VEHICLE_WIDTH',
        'VEHICLE_HEIGHT',
        'VEHICLE_ROTATION_RIGHT',
        'VEHICLE_ROTATION_LEFT',
        'VEHICLE_ROTATION_DOWN',
        'VEHICLE_ROTATION_UP',
    }
    PEDESTRIAN_VISUAL_FIELDS = {
        'PEDESTRIAN_WIDTH',
        'PEDESTRIAN_HEIGHT',
        'PEDESTRIAN_ROTATION_VERTICAL',
        'PEDESTRIAN_ROTATION_HORIZONTAL',
    }
    VEHICLE_SPEED_FIELDS = {'VEHICLE_SPEED_MEAN', 'VEHICLE_SPEED_VARIATION'}
    PEDESTRIAN_SPEED_FIELDS = {'PEDESTRIAN_SPEED_MEAN', 'PEDESTRIAN_SPEED_VARIATION'}
    TIMER_FIELDS = {
        'UPDATE_INTERVAL',
        'VEHICLE_GENERATION_INTERVAL',
        'PEDESTRIAN_GENERATION_INTERVAL',
        'TRAFFIC_LIGHT_UPDATE_INTERVAL',
    }

    def __init__(self):
        super().__init__('Окно симулирующее')
        self.config = SimulationConfig()
        self.statistics = SimulationStatistics()
        self.traffic_light = TrafficLightController(self.config)

        self.vehicles = []
        self.vehicle_items = []
        self.pedestrians = []
        self.pedestrian_items = []
        self.crosswalks = []

        self.traffic_lights = []
        self.traffic_light_map = {}
        self.spawn_points = []
        self.spawn_point_map = {}

        self.selected_edit_item = None
        self.editor_callback = None
        self.background_pixmap = None
        self.background_item = None

        self._editor_enabled = False
        self._editor_revision = 0
        self._pending_editor_callback = False
        self._suppress_selection_callbacks = False
        self._applying_external_update = False

        self.setup_ui()
        self.setup_timers()
        self.load_background_image()
        self._apply_timer_intervals_from_config()
        self._recalculate_traffic_cycle(reset_timer=True)

    def setup_ui(self):
        layout = QVBoxLayout()

        self.info_label = QLabel(
            'Транспортные средства движутся по горизонтальной и вертикальной полосам и исчезают в конце. '
            'Пешеходы пересекают дорогу.'
        )
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, self.config.SCENE_WIDTH, self.config.SCENE_HEIGHT)
        self.scene.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
        self.scene.selectionChanged.connect(self._on_scene_selection_changed)

        self.graphics_view = QGraphicsView(self.scene)
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.graphics_view.setMinimumSize(600, 400)

        control_layout = QHBoxLayout()
        self.start_button = QPushButton('Запуск движения')
        self.stop_button = QPushButton('Остановить движение')
        self.clear_button = QPushButton('Очистить')

        self.start_button.clicked.connect(self.start_movement)
        self.stop_button.clicked.connect(self.stop_movement)
        self.clear_button.clicked.connect(self.clear_simulation)

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.clear_button)

        stats_layout = QHBoxLayout()
        self.vehicles_passed_label = QLabel('Проехало машин: 0')
        self.vehicles_current_label = QLabel('Текущее количество: 0')
        self.pedestrians_passed_label = QLabel('Перешло пешеходов: 0')
        self.traffic_light_label = QLabel('Светофор: Зеленый для горизонтального транспорта')

        stats_layout.addWidget(self.vehicles_passed_label)
        stats_layout.addWidget(self.vehicles_current_label)
        stats_layout.addWidget(self.pedestrians_passed_label)
        stats_layout.addWidget(self.traffic_light_label)

        layout.addWidget(self.info_label)
        layout.addWidget(self.graphics_view)
        layout.addLayout(control_layout)
        layout.addLayout(stats_layout)
        self.setLayout(layout)

        self.add_crosswalks()
        self.rebuild_editor_items()

    def setup_timers(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_movement)

        self.vehicle_generator_timer = QTimer()
        self.vehicle_generator_timer.timeout.connect(self.generate_vehicle)

        self.pedestrian_generator_timer = QTimer()
        self.pedestrian_generator_timer.timeout.connect(self.generate_pedestrian)

        self.traffic_light_timer = QTimer()
        self.traffic_light_timer.timeout.connect(self.update_traffic_light)

    def set_editor_callback(self, callback):
        self.editor_callback = callback
        self.notify_editor()

    def get_editor_revision(self):
        return self._editor_revision

    def notify_editor(self):
        if self.editor_callback is None:
            return
        if self._pending_editor_callback:
            return
        self._pending_editor_callback = True
        QTimer.singleShot(0, self._flush_editor_callback)

    def _flush_editor_callback(self):
        self._pending_editor_callback = False
        if self.editor_callback is not None:
            self.editor_callback(self.selected_edit_item)

    def load_background_image(self):
        if self.background_item is not None and self.background_item.scene() is self.scene:
            self.scene.removeItem(self.background_item)
            self.background_item = None

        try:
            self.background_pixmap = QPixmap('Bg main.png')
            if not self.background_pixmap.isNull():
                scaled_pixmap = self.background_pixmap.scaled(
                    self.config.SCENE_WIDTH,
                    self.config.SCENE_HEIGHT,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.background_item = self.scene.addPixmap(scaled_pixmap)
                self.background_item.setZValue(-1)
                self.background_item.setPos(20, 55)
        except Exception as exc:
            print(f'Не удалось загрузить фоновое изображение: {exc}')

    def add_crosswalks(self):
        self.crosswalks = []
        self.crosswalks.append(
            Crosswalk(
                'H_CW',
                (self.config.HORIZONTAL_CROSSWALK_X, self.config.HORIZONTAL_LANE_Y - 15),
                self.config.CROSSWALK_WIDTH,
                'vertical',
            )
        )
        self.crosswalks.append(
            Crosswalk(
                'V_CW',
                (self.config.VERTICAL_LANE_X - 15, self.config.VERTICAL_CROSSWALK_Y),
                self.config.CROSSWALK_WIDTH + 30,
                'horizontal',
            )
        )

    def _register_traffic_light(self, name, x, y, light_type, scale, rotation, role, axis, mirrored=False):
        light = TrafficLightItem(
            x,
            y,
            light_type=light_type,
            scale=scale,
            rotation=rotation,
            name=name,
            on_changed=self._on_item_geometry_changed,
        )
        light.role = role
        light.axis = axis
        light.mirrored = mirrored
        if mirrored:
            light.setTransform(QTransform().scale(-1, 1), True)
        self.scene.addItem(light)
        self.traffic_lights.append(light)
        self.traffic_light_map[name] = light
        return light

    def _register_spawn_point(self, name, x, y, label, color):
        marker = EditableSpawnPointItem(
            x=x,
            y=y,
            name=name,
            label=label,
            color=color,
            on_changed=self._on_item_geometry_changed,
        )
        self.scene.addItem(marker)
        self.spawn_points.append(marker)
        self.spawn_point_map[name] = marker
        return marker

    def add_traffic_lights(self):
        for light in self.traffic_lights:
            if light.scene() is self.scene:
                self.scene.removeItem(light)
        self.traffic_lights.clear()
        self.traffic_light_map.clear()

        self._register_traffic_light(
            'vehicle_horizontal',
            self.config.TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_X,
            self.config.TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_Y,
            'vehicle',
            self.config.TRAFFIC_LIGHT_VEHICLE_SCALE,
            self.config.TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_ROTATION,
            'vehicle',
            'horizontal',
        )
        self._register_traffic_light(
            'vehicle_vertical',
            self.config.TRAFFIC_LIGHT_VEHICLE_VERTICAL_X,
            self.config.TRAFFIC_LIGHT_VEHICLE_VERTICAL_Y,
            'vehicle',
            self.config.TRAFFIC_LIGHT_VEHICLE_SCALE,
            self.config.TRAFFIC_LIGHT_VEHICLE_VERTICAL_ROTATION,
            'vehicle',
            'vertical',
        )
        self._register_traffic_light(
            'vehicle_vertical_opposite',
            self.config.TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_X,
            self.config.TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_Y,
            'vehicle',
            self.config.TRAFFIC_LIGHT_VEHICLE_SCALE,
            self.config.TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_ROTATION,
            'vehicle',
            'vertical',
        )
        self._register_traffic_light(
            'vehicle_horizontal_opposite',
            self.config.TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_X,
            self.config.TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_Y,
            'vehicle',
            self.config.TRAFFIC_LIGHT_VEHICLE_SCALE,
            self.config.TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_ROTATION,
            'vehicle',
            'horizontal',
        )
        self._register_traffic_light(
            'pedestrian_horizontal',
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_X,
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_Y,
            'pedestrian',
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_SCALE,
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_ROTATION,
            'pedestrian',
            'horizontal',
        )
        self._register_traffic_light(
            'pedestrian_vertical',
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_X,
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_Y,
            'pedestrian',
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_SCALE,
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_ROTATION,
            'pedestrian',
            'vertical',
        )
        self._register_traffic_light(
            'pedestrian_horizontal_mirror',
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_X,
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_Y,
            'pedestrian',
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_SCALE,
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_ROTATION,
            'pedestrian',
            'horizontal',
            mirrored=self.config.TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_FLIP_X,
        )
        self._register_traffic_light(
            'pedestrian_vertical_mirror',
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_X,
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_Y,
            'pedestrian',
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_SCALE,
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_ROTATION,
            'pedestrian',
            'vertical',
            mirrored=self.config.TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_FLIP_X,
        )

    def add_spawn_markers(self):
        for marker in self.spawn_points:
            if marker.scene() is self.scene:
                self.scene.removeItem(marker)
        self.spawn_points.clear()
        self.spawn_point_map.clear()

        self._register_spawn_point(
            'vehicle_spawn_horizontal_right',
            self.config.VEHICLE_SPAWN_HORIZONTAL_RIGHT_X,
            self.config.VEHICLE_SPAWN_HORIZONTAL_RIGHT_Y,
            'V→',
            QColor(65, 105, 225),
        )
        self._register_spawn_point(
            'vehicle_spawn_horizontal_left',
            self.config.VEHICLE_SPAWN_HORIZONTAL_LEFT_X,
            self.config.VEHICLE_SPAWN_HORIZONTAL_LEFT_Y,
            'V←',
            QColor(139, 0, 0),
        )
        self._register_spawn_point(
            'vehicle_spawn_vertical_down',
            self.config.VEHICLE_SPAWN_VERTICAL_DOWN_X,
            self.config.VEHICLE_SPAWN_VERTICAL_DOWN_Y,
            'V↓',
            QColor(0, 128, 255),
        )
        self._register_spawn_point(
            'vehicle_spawn_vertical_up',
            self.config.VEHICLE_SPAWN_VERTICAL_UP_X,
            self.config.VEHICLE_SPAWN_VERTICAL_UP_Y,
            'V↑',
            QColor(255, 140, 0),
        )

    def rebuild_editor_items(self):
        selected_name = self.selected_edit_item.name if self.selected_edit_item is not None else None
        self._suppress_selection_callbacks = True
        try:
            self.add_traffic_lights()
            self.add_spawn_markers()

            for item in self.get_editable_items():
                item.set_editor_enabled(self._editor_enabled)

            self.scene.clearSelection()
            self.selected_edit_item = None

            if self._editor_enabled and self.get_editable_items():
                target_name = selected_name if selected_name in self.get_editable_item_map() else self.get_editable_items()[0].name
                item = self.get_editable_item_map()[target_name]
                item.setSelected(True)
                self.selected_edit_item = item
        finally:
            self._suppress_selection_callbacks = False

        self._editor_revision += 1
        self.update_traffic_light_display()
        self.notify_editor()

    def get_editable_item_map(self):
        return {item.name: item for item in self.get_editable_items()}

    def get_editable_items(self):
        return list(self.traffic_lights) + list(self.spawn_points)

    def get_editor_item_descriptors(self):
        descriptors = []
        for item in self.get_editable_items():
            descriptors.append(
                {
                    'key': item.name,
                    'label': self.EDITOR_LABELS.get(item.name, item.name),
                }
            )
        return descriptors

    def set_editor_enabled(self, enabled: bool):
        self._editor_enabled = enabled
        self._suppress_selection_callbacks = True
        try:
            for item in self.get_editable_items():
                item.set_editor_enabled(enabled)

            if not enabled:
                self.scene.clearSelection()
                self.selected_edit_item = None
            elif self.selected_edit_item is None and self.get_editable_items():
                first_item = self.get_editable_items()[0]
                first_item.setSelected(True)
                self.selected_edit_item = first_item
            elif self.selected_edit_item is not None and self.selected_edit_item.scene() is self.scene:
                self.selected_edit_item.setSelected(True)
        finally:
            self._suppress_selection_callbacks = False
        self.notify_editor()

    def set_traffic_light_edit_mode(self, enabled: bool):
        self.set_editor_enabled(enabled)

    def select_edit_item_by_name(self, name: str):
        item = self.get_editable_item_map().get(name)
        if item is None:
            return
        if self.selected_edit_item is item and item.isSelected():
            self.notify_editor()
            return

        self._suppress_selection_callbacks = True
        try:
            self.scene.clearSelection()
            item.setSelected(True)
            self.selected_edit_item = item
        finally:
            self._suppress_selection_callbacks = False
        self.notify_editor()

    def select_traffic_light(self, key: str):
        self.select_edit_item_by_name(key)

    def _on_scene_selection_changed(self):
        if self._suppress_selection_callbacks:
            return

        selected_item = None
        editable_by_id = {id(item): item for item in self.get_editable_items()}
        for item in self.scene.selectedItems():
            selected_item = editable_by_id.get(id(item))
            if selected_item is not None:
                break

        if selected_item is self.selected_edit_item:
            self.notify_editor()
            return

        self.selected_edit_item = selected_item
        self.notify_editor()

    def update_selected_item_geometry(self, x=None, y=None, rotation=None, scale=None):
        item = self.selected_edit_item
        if item is None:
            return

        self._applying_external_update = True
        try:
            if x is not None or y is not None:
                item.setPos(item.x() if x is None else x, item.y() if y is None else y)

            if getattr(item, 'supports_rotation', False) and rotation is not None:
                item.setRotation(rotation)

            if getattr(item, 'supports_scale', False) and scale is not None and isinstance(item, TrafficLightItem):
                if item.role == 'vehicle':
                    self.config.TRAFFIC_LIGHT_VEHICLE_SCALE = float(scale)
                    for light in self.traffic_lights:
                        if getattr(light, 'role', None) == 'vehicle':
                            light.setScale(scale)
                elif item.role == 'pedestrian':
                    self.config.TRAFFIC_LIGHT_PEDESTRIAN_SCALE = float(scale)
                    for light in self.traffic_lights:
                        if getattr(light, 'role', None) == 'pedestrian':
                            light.setScale(scale)
        finally:
            self._applying_external_update = False

        self._sync_item_back_to_config(item)
        self.notify_editor()

    def update_traffic_light_properties(self, key, x=None, y=None, rotation=None, scale=None):
        if self.selected_edit_item is None or self.selected_edit_item.name != key:
            self.select_edit_item_by_name(key)
        self.update_selected_item_geometry(x=x, y=y, rotation=rotation, scale=scale)

    def get_editor_item_state(self, key: str):
        item = self.get_editable_item_map().get(key)
        if item is None:
            return None
        return {
            'key': item.name,
            'name': item.name,
            'x': float(item.x()),
            'y': float(item.y()),
            'rotation': float(item.rotation()) if getattr(item, 'supports_rotation', False) else 0.0,
            'scale': float(item.scale()) if getattr(item, 'supports_scale', False) else 1.0,
            'supports_rotation': bool(getattr(item, 'supports_rotation', False)),
            'supports_scale': bool(getattr(item, 'supports_scale', False)),
        }

    def get_traffic_light_state(self, key: str):
        return self.get_editor_item_state(key)

    def _sync_item_back_to_config(self, item):
        if item is None:
            return

        export_mapping = {
            'vehicle_horizontal': (
                'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_X',
                'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_Y',
                'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_ROTATION',
            ),
            'vehicle_vertical': (
                'TRAFFIC_LIGHT_VEHICLE_VERTICAL_X',
                'TRAFFIC_LIGHT_VEHICLE_VERTICAL_Y',
                'TRAFFIC_LIGHT_VEHICLE_VERTICAL_ROTATION',
            ),
            'vehicle_vertical_opposite': (
                'TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_X',
                'TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_Y',
                'TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_ROTATION',
            ),
            'vehicle_horizontal_opposite': (
                'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_X',
                'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_Y',
                'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_ROTATION',
            ),
            'pedestrian_horizontal': (
                'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_X',
                'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_Y',
                'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_ROTATION',
            ),
            'pedestrian_vertical': (
                'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_X',
                'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_Y',
                'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_ROTATION',
            ),
            'pedestrian_horizontal_mirror': (
                'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_X',
                'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_Y',
                'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_ROTATION',
            ),
            'pedestrian_vertical_mirror': (
                'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_X',
                'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_Y',
                'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_ROTATION',
            ),
            'vehicle_spawn_horizontal_right': ('VEHICLE_SPAWN_HORIZONTAL_RIGHT_X', 'VEHICLE_SPAWN_HORIZONTAL_RIGHT_Y', None),
            'vehicle_spawn_horizontal_left': ('VEHICLE_SPAWN_HORIZONTAL_LEFT_X', 'VEHICLE_SPAWN_HORIZONTAL_LEFT_Y', None),
            'vehicle_spawn_vertical_down': ('VEHICLE_SPAWN_VERTICAL_DOWN_X', 'VEHICLE_SPAWN_VERTICAL_DOWN_Y', None),
            'vehicle_spawn_vertical_up': ('VEHICLE_SPAWN_VERTICAL_UP_X', 'VEHICLE_SPAWN_VERTICAL_UP_Y', None),
        }

        mapping = export_mapping.get(item.name)
        if mapping is None:
            return

        x_key, y_key, rotation_key = mapping
        setattr(self.config, x_key, round(item.x()))
        setattr(self.config, y_key, round(item.y()))
        if rotation_key and getattr(item, 'supports_rotation', False):
            setattr(self.config, rotation_key, round(item.rotation()))

    def _make_config_spec(self, name: str, value):
        spec = {
            'name': name,
            'label': self.CONFIG_LABELS.get(name, name),
        }
        if isinstance(value, bool):
            spec['kind'] = 'bool'
            return spec

        if isinstance(value, float):
            spec.update({'kind': 'float', 'min': -100000.0, 'max': 100000.0, 'step': 0.1, 'decimals': 3})
            if 'SPEED' in name:
                spec.update({'min': 0.0, 'max': 20.0, 'step': 0.05, 'decimals': 3})
            elif 'SCALE' in name:
                spec.update({'min': 0.01, 'max': 10.0, 'step': 0.01, 'decimals': 3})
            return spec

        spec.update({'kind': 'int', 'min': -100000, 'max': 100000, 'step': 1})
        if 'INTERVAL' in name or 'TIME' in name or 'CYCLE' in name:
            spec.update({'min': 0, 'max': 60000})
        elif 'ROTATION' in name:
            spec.update({'min': -360, 'max': 360, 'step': 5})
        elif 'WIDTH' in name or 'HEIGHT' in name or 'X' in name or 'Y' in name or 'OFFSET' in name or 'DISTANCE' in name:
            spec.update({'min': -5000, 'max': 5000})
        return spec

    def get_runtime_config_specs(self):
        scalar_specs = []
        for name, value in vars(self.config).items():
            if name in self.CONFIG_TABLE_EXCLUDED:
                continue
            if not isinstance(value, (int, float, bool)) or isinstance(value, tuple):
                continue
            scalar_specs.append(self._make_config_spec(name, value))

        order_lookup = {name: idx for idx, name in enumerate(self.CONFIG_ORDER)}
        scalar_specs.sort(key=lambda item: (order_lookup.get(item['name'], 10_000), item['label']))
        return scalar_specs

    def _apply_timer_intervals_from_config(self):
        self.timer.setInterval(self.config.UPDATE_INTERVAL)
        self.vehicle_generator_timer.setInterval(self.config.VEHICLE_GENERATION_INTERVAL)
        self.pedestrian_generator_timer.setInterval(self.config.PEDESTRIAN_GENERATION_INTERVAL)
        self.traffic_light_timer.setInterval(self.config.TRAFFIC_LIGHT_UPDATE_INTERVAL)

    def _recalculate_traffic_cycle(self, reset_timer=False):
        self.config.TRAFFIC_LIGHT_CYCLE = max(
            1,
            int(self.config.VEHICLE_GREEN_TIME + self.config.VEHICLE_YELLOW_TIME + self.config.PEDESTRIAN_GREEN_TIME),
        )
        if reset_timer:
            self.traffic_light.timer = 0
        else:
            self.traffic_light.timer %= max(1, self.config.TRAFFIC_LIGHT_CYCLE)
        self.update_traffic_light_display()

    def _refresh_vehicle_items_from_config(self, refresh_speed=False):
        for vehicle_item in self.vehicle_items:
            vehicle_item.refresh_from_config(refresh_speed=refresh_speed)

    def _refresh_pedestrian_items_from_config(self, refresh_speed=False):
        for pedestrian_item in self.pedestrian_items:
            pedestrian_item.refresh_from_config(refresh_speed=refresh_speed)

    def apply_config_value(self, name: str, value):
        if not hasattr(self.config, name):
            return

        old_value = getattr(self.config, name)
        if old_value == value:
            return

        setattr(self.config, name, value)

        if name in self.TIMER_FIELDS:
            self._apply_timer_intervals_from_config()

        if name in {'VEHICLE_GREEN_TIME', 'VEHICLE_YELLOW_TIME', 'PEDESTRIAN_GREEN_TIME'}:
            self._recalculate_traffic_cycle(reset_timer=False)

        if name in self.SCENE_RELATED_FIELDS:
            self.scene.setSceneRect(0, 0, self.config.SCENE_WIDTH, self.config.SCENE_HEIGHT)
            self.load_background_image()
            self.add_crosswalks()

        if name in {'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_FLIP_X', 'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_FLIP_X'}:
            self.rebuild_editor_items()

        if name in self.VEHICLE_VISUAL_FIELDS:
            self._refresh_vehicle_items_from_config(refresh_speed=False)

        if name in self.PEDESTRIAN_VISUAL_FIELDS:
            self._refresh_pedestrian_items_from_config(refresh_speed=False)

        if name in self.VEHICLE_SPEED_FIELDS:
            self._refresh_vehicle_items_from_config(refresh_speed=True)

        if name in self.PEDESTRIAN_SPEED_FIELDS:
            self._refresh_pedestrian_items_from_config(refresh_speed=True)

        self.update_traffic_light_display()
        self.notify_editor()

    def get_config_export_text(self):
        lines = []

        traffic_mapping = {
            'vehicle_horizontal': (
                'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_X',
                'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_Y',
                'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_ROTATION',
            ),
            'vehicle_vertical': (
                'TRAFFIC_LIGHT_VEHICLE_VERTICAL_X',
                'TRAFFIC_LIGHT_VEHICLE_VERTICAL_Y',
                'TRAFFIC_LIGHT_VEHICLE_VERTICAL_ROTATION',
            ),
            'vehicle_vertical_opposite': (
                'TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_X',
                'TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_Y',
                'TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_ROTATION',
            ),
            'vehicle_horizontal_opposite': (
                'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_X',
                'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_Y',
                'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_ROTATION',
            ),
            'pedestrian_horizontal': (
                'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_X',
                'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_Y',
                'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_ROTATION',
            ),
            'pedestrian_vertical': (
                'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_X',
                'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_Y',
                'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_ROTATION',
            ),
            'pedestrian_horizontal_mirror': (
                'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_X',
                'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_Y',
                'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_ROTATION',
            ),
            'pedestrian_vertical_mirror': (
                'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_X',
                'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_Y',
                'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_ROTATION',
            ),
        }
        spawn_mapping = {
            'vehicle_spawn_horizontal_right': ('VEHICLE_SPAWN_HORIZONTAL_RIGHT_X', 'VEHICLE_SPAWN_HORIZONTAL_RIGHT_Y'),
            'vehicle_spawn_horizontal_left': ('VEHICLE_SPAWN_HORIZONTAL_LEFT_X', 'VEHICLE_SPAWN_HORIZONTAL_LEFT_Y'),
            'vehicle_spawn_vertical_down': ('VEHICLE_SPAWN_VERTICAL_DOWN_X', 'VEHICLE_SPAWN_VERTICAL_DOWN_Y'),
            'vehicle_spawn_vertical_up': ('VEHICLE_SPAWN_VERTICAL_UP_X', 'VEHICLE_SPAWN_VERTICAL_UP_Y'),
        }

        lines.append('# Traffic lights')
        for name in traffic_mapping:
            item = self.traffic_light_map.get(name)
            if item is None:
                continue
            x_key, y_key, rot_key = traffic_mapping[name]
            lines.append(f'{x_key}: int = {round(item.x())}')
            lines.append(f'{y_key}: int = {round(item.y())}')
            lines.append(f'{rot_key}: int = {round(item.rotation())}')
            lines.append('')

        lines.append(f'TRAFFIC_LIGHT_VEHICLE_SCALE: float = {_format_scalar_for_export(self.config.TRAFFIC_LIGHT_VEHICLE_SCALE)}')
        lines.append(f'TRAFFIC_LIGHT_PEDESTRIAN_SCALE: float = {_format_scalar_for_export(self.config.TRAFFIC_LIGHT_PEDESTRIAN_SCALE)}')
        lines.append(f'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_FLIP_X: bool = {_format_scalar_for_export(self.config.TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_FLIP_X)}')
        lines.append(f'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_FLIP_X: bool = {_format_scalar_for_export(self.config.TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_FLIP_X)}')
        lines.append('')

        lines.append('# Vehicle spawn points')
        for name in spawn_mapping:
            item = self.spawn_point_map.get(name)
            if item is None:
                continue
            x_key, y_key = spawn_mapping[name]
            lines.append(f'{x_key}: int = {round(item.x())}')
            lines.append(f'{y_key}: int = {round(item.y())}')
            lines.append('')

        lines.append('# Runtime parameters')
        for spec in self.get_runtime_config_specs():
            name = spec['name']
            value = getattr(self.config, name)
            py_type = 'bool' if isinstance(value, bool) else 'float' if isinstance(value, float) else 'int'
            lines.append(f'{name}: {py_type} = {_format_scalar_for_export(value)}')

        return '\n'.join(lines).strip()

    def export_traffic_light_config(self):
        return self.get_config_export_text()

    def _on_item_geometry_changed(self, item):
        if self._applying_external_update:
            return
        self.selected_edit_item = item
        self._sync_item_back_to_config(item)
        self.notify_editor()

    def update_traffic_light_display(self):
        if not hasattr(self, 'traffic_light_label') or self.traffic_light_label is None:
            return

        for light_item in self.traffic_lights:
            role = getattr(light_item, 'role', None)
            axis = getattr(light_item, 'axis', None)
            if not axis or role not in ('vehicle', 'pedestrian'):
                continue
            if role == 'vehicle':
                state = self.traffic_light.vehicle_state_for(axis)
            else:
                state = self.traffic_light.pedestrian_state_for(axis)
            light_item.update_state(state)

        if self.traffic_light.vehicle_yellow:
            self.traffic_light_label.setText('Светофор: Желтый для всех направлений')
        elif self.traffic_light.vehicle_green:
            self.traffic_light_label.setText('Светофор: Зеленый для горизонтального транспорта')
        else:
            self.traffic_light_label.setText('Светофор: Зеленый для вертикального транспорта')

    def update_traffic_light(self):
        self.traffic_light.update()
        self.update_traffic_light_display()

    def get_vehicle_spawn_position(self, direction: str):
        mapping = {
            'horizontal_right': (
                self.config.VEHICLE_SPAWN_HORIZONTAL_RIGHT_X,
                self.config.VEHICLE_SPAWN_HORIZONTAL_RIGHT_Y,
            ),
            'horizontal_left': (
                self.config.VEHICLE_SPAWN_HORIZONTAL_LEFT_X,
                self.config.VEHICLE_SPAWN_HORIZONTAL_LEFT_Y,
            ),
            'vertical_down': (
                self.config.VEHICLE_SPAWN_VERTICAL_DOWN_X,
                self.config.VEHICLE_SPAWN_VERTICAL_DOWN_Y,
            ),
            'vertical_up': (
                self.config.VEHICLE_SPAWN_VERTICAL_UP_X,
                self.config.VEHICLE_SPAWN_VERTICAL_UP_Y,
            ),
        }
        return mapping[direction]

    def add_vehicle(self, vehicle_type='car', direction='horizontal_right'):
        vehicle_id = f'V{self.statistics.vehicle_count:03d}'
        vehicle = Vehicle(vehicle_id, vehicle_type, direction)
        x, y = self.get_vehicle_spawn_position(direction)

        vehicle_item = VehicleItem(vehicle, x, y, self.config)
        self.scene.addItem(vehicle_item)

        self.vehicles.append(vehicle)
        self.vehicle_items.append(vehicle_item)
        self.statistics.vehicle_added()
        self.update_stats()
        return vehicle

    def add_pedestrian(self, direction='vertical'):
        pedestrian_id = f'P{self.statistics.pedestrian_count:03d}'
        pedestrian = Pedestrian(pedestrian_id, direction)

        if direction == 'vertical':
            x = random.randint(
                self.config.PEDESTRIAN_SPAWN_VERTICAL_X_MIN,
                self.config.HORIZONTAL_CROSSWALK_X + self.config.CROSSWALK_WIDTH - self.config.PEDESTRIAN_WIDTH,
            )
            y = self.config.PEDESTRIAN_SPAWN_VERTICAL_Y
        else:
            x = self.config.PEDESTRIAN_SPAWN_HORIZONTAL_X
            y = random.randint(
                self.config.PEDESTRIAN_SPAWN_HORIZONTAL_Y_MIN,
                self.config.VERTICAL_CROSSWALK_Y
                + self.config.CROSSWALK_WIDTH
                + self.config.PEDESTRIAN_SPAWN_HORIZONTAL_Y_MAX_OFFSET
                - self.config.PEDESTRIAN_HEIGHT,
            )

        pedestrian_item = PedestrianItem(pedestrian, x, y, self.config)
        self.scene.addItem(pedestrian_item)

        self.pedestrians.append(pedestrian)
        self.pedestrian_items.append(pedestrian_item)

        crosswalk = next((cw for cw in self.crosswalks if cw.direction == direction), None)
        if crosswalk:
            crosswalk.add_pedestrian(pedestrian)

        self.statistics.pedestrian_added()
        self.update_stats()
        return pedestrian

    def add_car(self, direction='horizontal_right'):
        self.add_vehicle('car', direction)

    def add_truck(self, direction='horizontal_right'):
        self.add_vehicle('truck', direction)

    def add_bus(self, direction='horizontal_right'):
        self.add_vehicle('bus', direction)

    def start_movement(self):
        if not self.timer.isActive():
            self.timer.start(self.config.UPDATE_INTERVAL)
        if not self.vehicle_generator_timer.isActive():
            self.vehicle_generator_timer.start(self.config.VEHICLE_GENERATION_INTERVAL)
        if not self.pedestrian_generator_timer.isActive():
            self.pedestrian_generator_timer.start(self.config.PEDESTRIAN_GENERATION_INTERVAL)
        if not self.traffic_light_timer.isActive():
            self.traffic_light_timer.start(self.config.TRAFFIC_LIGHT_UPDATE_INTERVAL)

    def stop_movement(self):
        if self.timer.isActive():
            self.timer.stop()
        if self.vehicle_generator_timer.isActive():
            self.vehicle_generator_timer.stop()
        if self.pedestrian_generator_timer.isActive():
            self.pedestrian_generator_timer.stop()
        if self.traffic_light_timer.isActive():
            self.traffic_light_timer.stop()

    def generate_vehicle(self):
        vehicle_type = random.choice(['car', 'truck', 'bus'])
        direction = random.choice(['horizontal_right', 'horizontal_left', 'vertical_down', 'vertical_up'])
        self.add_vehicle(vehicle_type, direction)

    def generate_pedestrian(self):
        if random.random() < 0.5:
            direction = random.choice(['horizontal', 'vertical'])
            self.add_pedestrian(direction)

    def update_movement(self):
        vehicles_to_remove = []
        pedestrians_to_remove = []

        for i, vehicle_item in enumerate(self.vehicle_items):
            if vehicle_item.move(self.vehicle_items, self.pedestrian_items, self.traffic_light):
                vehicles_to_remove.append(i)

        for i, pedestrian_item in enumerate(self.pedestrian_items):
            if pedestrian_item.move(self.vehicle_items, self.traffic_light):
                pedestrians_to_remove.append(i)

        for i in sorted(vehicles_to_remove, reverse=True):
            self.scene.removeItem(self.vehicle_items[i])
            self.vehicle_items.pop(i)
            self.vehicles.pop(i)
            self.statistics.vehicle_passed()
            self.statistics.vehicle_removed()

        for i in sorted(pedestrians_to_remove, reverse=True):
            self.scene.removeItem(self.pedestrian_items[i])
            pedestrian = self.pedestrian_items[i].pedestrian
            for crosswalk in self.crosswalks:
                if pedestrian in crosswalk.pedestrians:
                    crosswalk.remove_pedestrian(pedestrian)
            self.pedestrian_items.pop(i)
            self.pedestrians.pop(i)
            self.statistics.pedestrian_passed()
            self.statistics.pedestrian_removed()

        if vehicles_to_remove or pedestrians_to_remove:
            self.update_stats()

    def update_stats(self):
        self.vehicles_passed_label.setText(f'Проехало машин: {self.statistics.vehicles_passed}')
        self.vehicles_current_label.setText(f'Текущее количество: {self.statistics.vehicle_count}')
        self.pedestrians_passed_label.setText(f'Перешло пешеходов: {self.statistics.pedestrians_passed}')

    def clear_simulation(self):
        self.stop_movement()
        self._suppress_selection_callbacks = True
        try:
            self.vehicles = []
            self.vehicle_items = []
            self.pedestrians = []
            self.pedestrian_items = []
            self.crosswalks = []
            self.traffic_lights = []
            self.traffic_light_map = {}
            self.spawn_points = []
            self.spawn_point_map = {}
            self.selected_edit_item = None
            self.background_item = None
            self.scene.clear()
        finally:
            self._suppress_selection_callbacks = False

        self.traffic_light = TrafficLightController(self.config)
        self.statistics.reset()
        self.update_stats()
        self.load_background_image()
        self.add_crosswalks()
        self.rebuild_editor_items()
        self.update_traffic_light_display()
