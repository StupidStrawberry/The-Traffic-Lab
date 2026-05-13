from PyQt6.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)
from PyQt6.QtGui import QBrush, QPainter, QPixmap, QTransform, QColor
from PyQt6.QtCore import QTimer, Qt
import random

from config import SimulationConfig
from classes import Crosswalk, Pedestrian, Vehicle
from traffic_light import EditableSpawnPointItem, TrafficLightController, TrafficLightItem
from simulation_objects import PedestrianItem, VehicleItem
from statistics import SimulationStatistics


class SimulationWidget(QGroupBox):
    """Окно симуляции с визуальной сценой и редактором объектов."""

    def __init__(self):
        super().__init__("Окно симулирующее")
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
        self._editor_enabled = False
        self._applying_external_update = False
        self._suppress_item_callbacks = False

        self.setup_ui()
        self.setup_timers()
        self.load_background_image()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.info_label = QLabel(
            "Транспортные средства движутся по горизонтальной и вертикальной полосам и исчезают в конце. "
            "Пешеходы пересекают дорогу."
        )
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, self.config.SCENE_WIDTH, self.config.SCENE_HEIGHT)
        self.scene.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))

        self.graphics_view = QGraphicsView(self.scene)
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.graphics_view.setMinimumSize(600, 400)

        control_layout = QHBoxLayout()
        self.start_button = QPushButton("Запуск движения")
        self.stop_button = QPushButton("Остановить движение")
        self.clear_button = QPushButton("Очистить")

        self.start_button.clicked.connect(self.start_movement)
        self.stop_button.clicked.connect(self.stop_movement)
        self.clear_button.clicked.connect(self.clear_simulation)

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.clear_button)

        stats_layout = QHBoxLayout()
        self.vehicles_passed_label = QLabel("Проехало машин: 0")
        self.vehicles_current_label = QLabel("Текущее количество: 0")
        self.pedestrians_passed_label = QLabel("Перешло пешеходов: 0")
        self.traffic_light_label = QLabel("Светофор: Зеленый для горизонтального транспорта")

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

    def notify_editor(self):
        if self.editor_callback is not None:
            self.editor_callback(self.selected_edit_item)

    def load_background_image(self):
        try:
            self.background_pixmap = QPixmap("Bg main.png")
            if not self.background_pixmap.isNull():
                scaled_pixmap = self.background_pixmap.scaled(
                    self.config.SCENE_WIDTH,
                    self.config.SCENE_HEIGHT,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                background_item = self.scene.addPixmap(scaled_pixmap)
                background_item.setZValue(-1)
                background_item.setPos(20, 55)
        except Exception as exc:
            print(f"Не удалось загрузить фоновое изображение: {exc}")

    def add_crosswalks(self):
        self.crosswalks = []
        h_crosswalk = Crosswalk(
            "H_CW",
            (self.config.HORIZONTAL_CROSSWALK_X, self.config.HORIZONTAL_LANE_Y - 15),
            self.config.CROSSWALK_WIDTH,
            'vertical',
        )
        self.crosswalks.append(h_crosswalk)

        v_crosswalk = Crosswalk(
            "V_CW",
            (self.config.VERTICAL_LANE_X - 15, self.config.VERTICAL_CROSSWALK_Y),
            self.config.CROSSWALK_WIDTH + 30,
            'horizontal',
        )
        self.crosswalks.append(v_crosswalk)

    def _register_traffic_light(self, name, x, y, light_type, scale, rotation, role, axis, mirrored=False):
        light = TrafficLightItem(
            x,
            y,
            light_type=light_type,
            scale=scale,
            rotation=rotation,
            name=name,
            on_changed=self._on_item_geometry_changed,
            on_selected=self._on_item_selected,
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
            on_selected=self._on_item_selected,
        )
        self.scene.addItem(marker)
        self.spawn_points.append(marker)
        self.spawn_point_map[name] = marker
        return marker

    def add_traffic_lights(self):
        for light in self.traffic_lights:
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
        self.add_traffic_lights()
        self.add_spawn_markers()

        for item in self.get_editable_items():
            item.set_editor_enabled(self._editor_enabled)

        self.update_traffic_light_display()

        if selected_name and selected_name in self.get_editable_item_map():
            self.select_edit_item_by_name(selected_name)
        elif self._editor_enabled and self.get_editable_items():
            self.select_edit_item_by_name(self.get_editable_items()[0].name)
        else:
            self.selected_edit_item = None
            self.notify_editor()

    def get_editable_item_map(self):
        return {item.name: item for item in self.get_editable_items()}

    def get_editable_items(self):
        return list(self.traffic_lights) + list(self.spawn_points)

    def get_traffic_light_editor_items(self):
        items = []
        for item in self.get_editable_items():
            if item.name.startswith('vehicle_spawn_'):
                label = f"{item.name} (точка спавна)"
            else:
                label = item.name
            items.append({'key': item.name, 'label': label})
        return items

    def set_editor_enabled(self, enabled: bool):
        self._editor_enabled = enabled
        self._suppress_item_callbacks = True
        try:
            for item in self.get_editable_items():
                item.set_editor_enabled(enabled)

            if not enabled:
                self.selected_edit_item = None
            elif self.selected_edit_item is None and self.get_editable_items():
                self.selected_edit_item = self.get_editable_items()[0]
                self.selected_edit_item.setSelected(True)
        finally:
            self._suppress_item_callbacks = False
        self.notify_editor()

    def set_traffic_light_edit_mode(self, enabled: bool):
        self.set_editor_enabled(enabled)

    def select_edit_item_by_name(self, name: str):
        item = self.get_editable_item_map().get(name)
        if item is None:
            return
        if self.selected_edit_item is item and item.isSelected():
            return

        self._suppress_item_callbacks = True
        try:
            self.scene.clearSelection()
            item.setSelected(True)
            self.selected_edit_item = item
        finally:
            self._suppress_item_callbacks = False
        self.notify_editor()

    def select_traffic_light(self, key: str):
        self.select_edit_item_by_name(key)

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

            if getattr(item, 'supports_scale', False) and scale is not None:
                new_scale = scale
                if isinstance(item, TrafficLightItem):
                    if item.role == 'vehicle':
                        self.config.TRAFFIC_LIGHT_VEHICLE_SCALE = new_scale
                        for light in self.traffic_lights:
                            if light.role == 'vehicle':
                                light.setScale(new_scale)
                    elif item.role == 'pedestrian':
                        self.config.TRAFFIC_LIGHT_PEDESTRIAN_SCALE = new_scale
                        for light in self.traffic_lights:
                            if light.role == 'pedestrian':
                                light.setScale(new_scale)
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
            'vehicle_horizontal': ('TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_X', 'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_Y', 'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_ROTATION'),
            'vehicle_vertical': ('TRAFFIC_LIGHT_VEHICLE_VERTICAL_X', 'TRAFFIC_LIGHT_VEHICLE_VERTICAL_Y', 'TRAFFIC_LIGHT_VEHICLE_VERTICAL_ROTATION'),
            'vehicle_vertical_opposite': ('TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_X', 'TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_Y', 'TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_ROTATION'),
            'vehicle_horizontal_opposite': ('TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_X', 'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_Y', 'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_ROTATION'),
            'pedestrian_horizontal': ('TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_X', 'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_Y', 'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_ROTATION'),
            'pedestrian_vertical': ('TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_X', 'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_Y', 'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_ROTATION'),
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

    def get_config_export_text(self):
        lines = []

        traffic_mapping = {
            'vehicle_horizontal': ('TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_X', 'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_Y', 'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_ROTATION'),
            'vehicle_vertical': ('TRAFFIC_LIGHT_VEHICLE_VERTICAL_X', 'TRAFFIC_LIGHT_VEHICLE_VERTICAL_Y', 'TRAFFIC_LIGHT_VEHICLE_VERTICAL_ROTATION'),
            'vehicle_vertical_opposite': ('TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_X', 'TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_Y', 'TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_ROTATION'),
            'vehicle_horizontal_opposite': ('TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_X', 'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_Y', 'TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_ROTATION'),
            'pedestrian_horizontal': ('TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_X', 'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_Y', 'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_ROTATION'),
            'pedestrian_vertical': ('TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_X', 'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_Y', 'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_ROTATION'),
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
        for name, item in self.traffic_light_map.items():
            mapping = traffic_mapping.get(name)
            if mapping is None:
                continue
            x_key, y_key, rot_key = mapping
            lines.append(f'{x_key}: int = {round(item.x())}')
            lines.append(f'{y_key}: int = {round(item.y())}')
            lines.append(f'{rot_key}: int = {round(item.rotation())}')
            lines.append('')

        lines.append(f'TRAFFIC_LIGHT_VEHICLE_SCALE: float = {self.config.TRAFFIC_LIGHT_VEHICLE_SCALE:.3f}')
        lines.append(f'TRAFFIC_LIGHT_PEDESTRIAN_SCALE: float = {self.config.TRAFFIC_LIGHT_PEDESTRIAN_SCALE:.3f}')
        lines.append('')
        lines.append(f'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_FLIP_X: bool = {self.config.TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_FLIP_X}')
        lines.append(f'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_FLIP_X: bool = {self.config.TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_FLIP_X}')
        lines.append('')

        lines.append('# Vehicle spawn points')
        for name, item in self.spawn_point_map.items():
            x_key, y_key = spawn_mapping[name]
            lines.append(f'{x_key}: int = {round(item.x())}')
            lines.append(f'{y_key}: int = {round(item.y())}')
            lines.append('')

        return '\n'.join(lines).strip()

    def export_traffic_light_config(self):
        return self.get_config_export_text()

    def _on_item_selected(self, item):
        if self._suppress_item_callbacks:
            return
        self.selected_edit_item = item
        self.notify_editor()

    def _on_item_geometry_changed(self, item):
        if self._suppress_item_callbacks or self._applying_external_update:
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
            self.traffic_light_label.setText("Светофор: Желтый для всех направлений")
        elif self.traffic_light.vehicle_green:
            self.traffic_light_label.setText("Светофор: Зеленый для горизонтального транспорта")
        else:
            self.traffic_light_label.setText("Светофор: Зеленый для вертикального транспорта")

    def update_traffic_light(self):
        self.traffic_light.update()
        self.update_traffic_light_display()

    def get_vehicle_spawn_position(self, direction: str):
        mapping = {
            'horizontal_right': (self.config.VEHICLE_SPAWN_HORIZONTAL_RIGHT_X, self.config.VEHICLE_SPAWN_HORIZONTAL_RIGHT_Y),
            'horizontal_left': (self.config.VEHICLE_SPAWN_HORIZONTAL_LEFT_X, self.config.VEHICLE_SPAWN_HORIZONTAL_LEFT_Y),
            'vertical_down': (self.config.VEHICLE_SPAWN_VERTICAL_DOWN_X, self.config.VEHICLE_SPAWN_VERTICAL_DOWN_Y),
            'vertical_up': (self.config.VEHICLE_SPAWN_VERTICAL_UP_X, self.config.VEHICLE_SPAWN_VERTICAL_UP_Y),
        }
        return mapping[direction]

    def add_vehicle(self, vehicle_type='car', direction='horizontal_right'):
        vehicle_id = f"V{self.statistics.vehicle_count:03d}"
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
        pedestrian_id = f"P{self.statistics.pedestrian_count:03d}"
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
            should_remove = vehicle_item.move(self.vehicle_items, self.pedestrian_items, self.traffic_light)
            if should_remove:
                vehicles_to_remove.append(i)

        for i, pedestrian_item in enumerate(self.pedestrian_items):
            should_remove = pedestrian_item.move(self.vehicle_items, self.traffic_light)
            if should_remove:
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
        self.vehicles_passed_label.setText(f"Проехало машин: {self.statistics.vehicles_passed}")
        self.vehicles_current_label.setText(f"Текущее количество: {self.statistics.vehicle_count}")
        self.pedestrians_passed_label.setText(f"Перешло пешеходов: {self.statistics.pedestrians_passed}")

    def clear_simulation(self):
        self.stop_movement()
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

        self.scene.clear()
        self.load_background_image()
        self.add_crosswalks()
        self.rebuild_editor_items()

        self.statistics.reset()
        self.update_stats()
        self.update_traffic_light_display()
