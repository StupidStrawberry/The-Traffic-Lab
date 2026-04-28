import random

from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QBrush, QColor, QPainter, QPixmap, QTransform
from PyQt6.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QGraphicsItem,
    QGraphicsItemGroup
)

from classes import Vehicle
from config import SimulationConfig
from simulation_objects import VehicleItem
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


class EditableStripeGroup(QGraphicsItemGroup):
    geometryChanged = pyqtSignal(object)

    def __init__(self, name, transform_config, on_changed=None):
        super().__init__()
        self.name = name
        self.transform_config = transform_config
        self._on_changed = on_changed
        self.spawn_marker = None          # связанный маркер старта
        self.spawn_offset = QPointF(0, 0) # смещение маркера относительно группы
        self.direction = None             # направление движения машин на этой полосе

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

    def boundingRect(self):
        return self.childrenBoundingRect()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value
            scene_rect = self.scene().sceneRect()
            new_pos.setX(max(scene_rect.left(), min(new_pos.x(), scene_rect.right() - self.boundingRect().width())))
            new_pos.setY(max(scene_rect.top(), min(new_pos.y(), scene_rect.bottom() - self.boundingRect().height())))
            return new_pos
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # обновим позицию привязанного маркера старта
            if self.spawn_marker is not None:
                self.spawn_marker.setPos(self.pos() + self.spawn_offset)
            if self._on_changed:
                self._on_changed(self)
        return super().itemChange(change, value)

    def set_editor_enabled(self, enabled):
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, enabled)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, enabled)

    def supports_rotation(self):
        return True   # было False

    def supports_scale(self):
        return True   # было False

    def setRotation(self, angle):
        """Переопределяем для обновления позиции маркера."""
        super().setRotation(angle)
        self._update_spawn_marker_position()

    def setScale(self, scale):
        """Переопределяем для обновления позиции маркера."""
        super().setScale(scale)
        self._update_spawn_marker_position()

    def _update_spawn_marker_position(self):
        """Обновляет мировую позицию маркера старта на основе текущей трансформации группы."""
        if self.spawn_marker is not None:
            # Применяем трансформацию группы к локальному смещению
            local_offset = self.spawn_offset
            # Преобразуем локальную точку в сцену с учётом трансформации группы
            mapped_point = self.mapToScene(local_offset)
            self.spawn_marker.setPos(mapped_point)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            # Убираем ограничение границами сцены — разрешаем любое положение
            return value   # было: new_pos = value ... return new_pos
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            if self.spawn_marker is not None:
                self.spawn_marker.setPos(self.pos() + self.spawn_offset)
            if self._on_changed:
                self._on_changed(self)
        return super().itemChange(change, value)



class SimulationWidget(QGroupBox):
    """Окно симуляции: машины стартуют на фоновых полосах (по одной точке старта на полосу)."""

    EDITOR_LABELS = {
        'vehicle_horizontal': 'Светофор транспорта: горизонталь',
        'vehicle_vertical': 'Светофор транспорта: вертикаль (вниз)',
        'vehicle_vertical_opposite': 'Светофор транспорта: вертикаль (вверх)',
        'vehicle_horizontal_opposite': 'Светофор транспорта: горизонталь (влево)',
        'stripe_0': 'Фоновая полоса 0 (оригинал)',
        'stripe_1': 'Фоновая полоса 1 (зеркало гор.)',
        'stripe_2': 'Фоновая полоса 2 (поворот 90°)',
        'stripe_3': 'Фоновая полоса 3 (зеркало + поворот)',
        # маркеры старта автоматически связаны с полосами и не требуют отдельных записей
    }

    CONFIG_TABLE_EXCLUDED = {
        'TRAFFIC_LIGHT_CYCLE',
        'ANALYSIS_UPDATE_INTERVAL',
        'VEHICLE_SPAWN_OFFSET',
        'VEHICLE_LIGHT_WIDTH',
        'VEHICLE_LIGHT_HEIGHT',
        'PEDESTRIAN_LIGHT_WIDTH',
        'PEDESTRIAN_LIGHT_HEIGHT',
        'VEHICLE_LIGHT_HORIZONTAL_POS',
        'VEHICLE_LIGHT_VERTICAL_POS',
        'PEDESTRIAN_LIGHT_HORIZONTAL_POS',
        'PEDESTRIAN_LIGHT_VERTICAL_POS',
        # исключаем все пешеходные поля
        'PEDESTRIAN_GENERATION_INTERVAL',
        'PEDESTRIAN_GREEN_TIME',
        'PEDESTRIAN_SPEED_MEAN',
        'PEDESTRIAN_SPEED_VARIATION',
        'PEDESTRIAN_WIDTH',
        'PEDESTRIAN_HEIGHT',
        'PEDESTRIAN_SPAWN_VERTICAL_X_MIN',
        'PEDESTRIAN_SPAWN_VERTICAL_Y',
        'PEDESTRIAN_SPAWN_HORIZONTAL_X',
        'PEDESTRIAN_SPAWN_HORIZONTAL_Y_MIN',
        'PEDESTRIAN_SPAWN_HORIZONTAL_Y_MAX_OFFSET',
        'PEDESTRIAN_VERTICAL_CROSS_END_Y',
        'PEDESTRIAN_HORIZONTAL_CROSS_END_X',
        'PEDESTRIAN_ROTATION_VERTICAL',
        'PEDESTRIAN_ROTATION_HORIZONTAL',
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
        'TRAFFIC_LIGHT_PEDESTRIAN_SCALE',
        'TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_FLIP_X',
        'TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_FLIP_X',
        # старые spawn-точки больше не используются
        'VEHICLE_SPAWN_HORIZONTAL_RIGHT_X',
        'VEHICLE_SPAWN_HORIZONTAL_RIGHT_Y',
        'VEHICLE_SPAWN_HORIZONTAL_LEFT_X',
        'VEHICLE_SPAWN_HORIZONTAL_LEFT_Y',
        'VEHICLE_SPAWN_VERTICAL_DOWN_X',
        'VEHICLE_SPAWN_VERTICAL_DOWN_Y',
        'VEHICLE_SPAWN_VERTICAL_UP_X',
        'VEHICLE_SPAWN_VERTICAL_UP_Y',
        # геометрия светофоров (редактируется на сцене)
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
        'TRAFFIC_LIGHT_VEHICLE_SCALE',
        'BACKGROUND_STRIPE_0_ROTATION',
        'BACKGROUND_STRIPE_0_SCALE',
        'BACKGROUND_STRIPE_1_ROTATION',
        'BACKGROUND_STRIPE_1_SCALE',
        'BACKGROUND_STRIPE_2_ROTATION',
        'BACKGROUND_STRIPE_2_SCALE',
        'BACKGROUND_STRIPE_3_ROTATION',
        'BACKGROUND_STRIPE_3_SCALE',
    }

    CONFIG_LABELS = {
        'UPDATE_INTERVAL': 'Шаг симуляции (мс)',
        'VEHICLE_GENERATION_INTERVAL': 'Интервал генерации машин (мс)',
        'TRAFFIC_LIGHT_UPDATE_INTERVAL': 'Интервал обновления светофора (мс)',
        'VEHICLE_GREEN_TIME': 'Зеленый для машин',
        'VEHICLE_YELLOW_TIME': 'Желтый для машин',
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
        'MIN_DISTANCE_BETWEEN_VEHICLES': 'Мин. дистанция между машинами',
        'VEHICLE_SPEED_MEAN': 'Средняя скорость машин',
        'VEHICLE_SPEED_VARIATION': 'Разброс скорости машин',
        'VEHICLE_ROTATION_RIGHT': 'Поворот машин вправо',
        'VEHICLE_ROTATION_LEFT': 'Поворот машин влево',
        'VEHICLE_ROTATION_DOWN': 'Поворот машин вниз',
        'VEHICLE_ROTATION_UP': 'Поворот машин вверх',
        'VEHICLE_STOP_DISTANCE_HORIZONTAL_RIGHT': 'Стоп-линия машин вправо',
        'VEHICLE_STOP_DISTANCE_HORIZONTAL_LEFT': 'Стоп-линия машин влево',
        'VEHICLE_STOP_DISTANCE_VERTICAL_DOWN': 'Стоп-линия машин вниз',
        'VEHICLE_STOP_DISTANCE_VERTICAL_UP': 'Стоп-линия машин вверх',
        'VEHICLE_EXTENDED_CROSSWALK_CHECK_HORIZONTAL': 'Доп. проверка перехода по горизонтали',
        'VEHICLE_EXTENDED_CROSSWALK_CHECK_VERTICAL': 'Доп. проверка перехода по вертикали',
        'BACKGROUND_STRIPE_0_X': 'Полоса 0 X',
        'BACKGROUND_STRIPE_0_Y': 'Полоса 0 Y',
        'BACKGROUND_STRIPE_1_X': 'Полоса 1 X',
        'BACKGROUND_STRIPE_1_Y': 'Полоса 1 Y',
        'BACKGROUND_STRIPE_2_X': 'Полоса 2 X',
        'BACKGROUND_STRIPE_2_Y': 'Полоса 2 Y',
        'BACKGROUND_STRIPE_3_X': 'Полоса 3 X',
        'BACKGROUND_STRIPE_3_Y': 'Полоса 3 Y',
        'BACKGROUND_STRIPE_0_ROTATION': 'Полоса 0 поворот (град)',
        'BACKGROUND_STRIPE_0_SCALE': 'Полоса 0 масштаб',
        'BACKGROUND_STRIPE_1_ROTATION': 'Полоса 1 поворот (град)',
        'BACKGROUND_STRIPE_1_SCALE': 'Полоса 1 масштаб',
        'BACKGROUND_STRIPE_2_ROTATION': 'Полоса 2 поворот (град)',
        'BACKGROUND_STRIPE_2_SCALE': 'Полоса 2 масштаб',
        'BACKGROUND_STRIPE_3_ROTATION': 'Полоса 3 поворот (град)',
        'BACKGROUND_STRIPE_3_SCALE': 'Полоса 3 масштаб',
    }

    CONFIG_ORDER = [
        'UPDATE_INTERVAL',
        'VEHICLE_GENERATION_INTERVAL',
        'TRAFFIC_LIGHT_UPDATE_INTERVAL',
        'VEHICLE_GREEN_TIME',
        'VEHICLE_YELLOW_TIME',
        'VEHICLE_SPEED_MEAN',
        'VEHICLE_SPEED_VARIATION',
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
        'MIN_DISTANCE_BETWEEN_VEHICLES',
        'VEHICLE_ROTATION_RIGHT',
        'VEHICLE_ROTATION_LEFT',
        'VEHICLE_ROTATION_DOWN',
        'VEHICLE_ROTATION_UP',
        'VEHICLE_STOP_DISTANCE_HORIZONTAL_RIGHT',
        'VEHICLE_STOP_DISTANCE_HORIZONTAL_LEFT',
        'VEHICLE_STOP_DISTANCE_VERTICAL_DOWN',
        'VEHICLE_STOP_DISTANCE_VERTICAL_UP',
        'VEHICLE_EXTENDED_CROSSWALK_CHECK_HORIZONTAL',
        'VEHICLE_EXTENDED_CROSSWALK_CHECK_VERTICAL',
        'BACKGROUND_STRIPE_0_X',
        'BACKGROUND_STRIPE_0_Y',
        'BACKGROUND_STRIPE_0_ROTATION',
        'BACKGROUND_STRIPE_0_SCALE',
        'BACKGROUND_STRIPE_1_X',
        'BACKGROUND_STRIPE_1_Y',
        'BACKGROUND_STRIPE_1_ROTATION',
        'BACKGROUND_STRIPE_1_SCALE',
        'BACKGROUND_STRIPE_2_X',
        'BACKGROUND_STRIPE_2_Y',
        'BACKGROUND_STRIPE_2_ROTATION',
        'BACKGROUND_STRIPE_2_SCALE',
        'BACKGROUND_STRIPE_3_X',
        'BACKGROUND_STRIPE_3_Y',
        'BACKGROUND_STRIPE_3_ROTATION',
        'BACKGROUND_STRIPE_3_SCALE',    ]

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
    VEHICLE_SPEED_FIELDS = {'VEHICLE_SPEED_MEAN', 'VEHICLE_SPEED_VARIATION'}
    TIMER_FIELDS = {
        'UPDATE_INTERVAL',
        'VEHICLE_GENERATION_INTERVAL',
        'TRAFFIC_LIGHT_UPDATE_INTERVAL',
    }

    def __init__(self):
        super().__init__('Окно симулирующее')
        self.config = SimulationConfig()
        self.statistics = SimulationStatistics()
        self.traffic_light = TrafficLightController(self.config)

        self.vehicles = []
        self.vehicle_items = []

        self.traffic_lights = []
        self.traffic_light_map = {}
        self.spawn_points = []          # маркеры старта, привязанные к полосам

        self.selected_edit_item = None
        self.editor_callback = None
        self.stripe_groups = []

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
            'Транспортные средства движутся по горизонтальной и вертикальной полосам и исчезают в конце.'
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
        self.traffic_light_label = QLabel('Светофор: Зеленый для горизонтального транспорта')

        stats_layout.addWidget(self.vehicles_passed_label)
        stats_layout.addWidget(self.vehicles_current_label)
        stats_layout.addWidget(self.traffic_light_label)

        layout.addWidget(self.info_label)
        layout.addWidget(self.graphics_view)
        layout.addLayout(control_layout)
        layout.addLayout(stats_layout)
        self.setLayout(layout)

        self.rebuild_editor_items()

    def setup_timers(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_movement)

        self.vehicle_generator_timer = QTimer()
        self.vehicle_generator_timer.timeout.connect(self.generate_vehicle)

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
        # Удаляем старые группы и связанные маркеры
        for group in self.stripe_groups:
            if group.scene() is self.scene:
                self.scene.removeItem(group)
        for marker in self.spawn_points:
            if marker.scene() is self.scene:
                self.scene.removeItem(marker)
        self.stripe_groups.clear()
        self.spawn_points.clear()

        try:
            original_pixmap = QPixmap('bordur_sploshnaya.png')
            if original_pixmap.isNull():
                print("Не удалось загрузить изображение bordur_sploshnaya.png")
                return

            base_pixmap = original_pixmap.scaled(
                original_pixmap.width() // 3,
                original_pixmap.height() // 3,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            scene_width = self.config.SCENE_WIDTH
            scene_height = self.config.SCENE_HEIGHT

            # Конфигурации четырёх полос с определением направления движения
            configs = [
                {'name': 'stripe_0', 'mirror_x': False, 'mirror_y': False, 'rotate_90': False, 'suffix': '0',
                 'direction': 'horizontal_right', 'offset_factor': (0.1, 0.5)},
                {'name': 'stripe_1', 'mirror_x': False, 'mirror_y': True,  'rotate_90': False, 'suffix': '1',
                 'direction': 'horizontal_left',  'offset_factor': (0.9, 0.5)},
                {'name': 'stripe_2', 'mirror_x': False, 'mirror_y': False, 'rotate_90': True,  'suffix': '2',
                 'direction': 'vertical_down',    'offset_factor': (0.5, 0.1)},
                {'name': 'stripe_3', 'mirror_x': True,  'mirror_y': False, 'rotate_90': True,  'suffix': '3',
                 'direction': 'vertical_up',      'offset_factor': (0.5, 0.9)},
            ]

            for cfg in configs:
                # Применяем трансформации
                pix = base_pixmap
                transform = QTransform()
                if cfg['mirror_x']:
                    transform.scale(-1, 1)
                if cfg['mirror_y']:
                    transform.scale(1, -1)
                if cfg['rotate_90']:
                    transform.rotate(90)

                pix = pix.transformed(transform, Qt.TransformationMode.SmoothTransformation)

                tile_width = pix.width()
                tile_height = pix.height()

                if cfg['rotate_90']:
                    cols = 1
                    rows = (scene_height + tile_height - 1) // tile_height
                else:
                    cols = (scene_width + tile_width - 1) // tile_width
                    rows = 1

                group = EditableStripeGroup(
                    name=cfg['name'],
                    transform_config=cfg,
                    on_changed=self._on_item_geometry_changed
                )
                group.setZValue(-1)

                # Создаём тайлы и добавляем в группу
                for row in range(rows):
                    for col in range(cols):
                        item = self.scene.addPixmap(pix)
                        item.setPos(col * tile_width, row * tile_height)
                        group.addToGroup(item)

                self.scene.addItem(group)

                x_attr = f'BACKGROUND_STRIPE_{cfg["suffix"]}_X'
                y_attr = f'BACKGROUND_STRIPE_{cfg["suffix"]}_Y'
                group.setPos(getattr(self.config, x_attr, 0), getattr(self.config, y_attr, 0))

                # Загружаем поворот и масштаб, если они есть в конфиге
                rot_attr = f'BACKGROUND_STRIPE_{cfg["suffix"]}_ROTATION'
                scale_attr = f'BACKGROUND_STRIPE_{cfg["suffix"]}_SCALE'
                if hasattr(self.config, rot_attr):
                    group.setRotation(getattr(self.config, rot_attr))
                if hasattr(self.config, scale_attr):
                    group.setScale(getattr(self.config, scale_attr))

                # Определяем смещение маркера старта относительно группы
                group_rect = group.boundingRect()
                offset_x = group_rect.width() * cfg['offset_factor'][0]
                offset_y = group_rect.height() * cfg['offset_factor'][1]
                group.spawn_offset = QPointF(offset_x, offset_y)

                # Создаём маркер старта
                marker = EditableSpawnPointItem(
                    x=group.x() + offset_x,
                    y=group.y() + offset_y,
                    name=f'{cfg["name"]}_spawn',
                    label='🚗',
                    color=QColor(0, 200, 0),
                    on_changed=self._on_spawn_marker_moved
                )
                marker.set_editor_enabled(self._editor_enabled)
                marker.associated_stripe = group   # обратная ссылка для обновления смещения
                self.scene.addItem(marker)

                group.spawn_marker = marker
                group.direction = cfg['direction']
                self.spawn_points.append(marker)
                self.stripe_groups.append(group)

                print(f"Создана группа {cfg['name']} (размер {tile_width}x{tile_height}, тайлов: {cols}x{rows})")

            print(f"Всего создано групп: {len(self.stripe_groups)}")

        except Exception as exc:
            print(f'Не удалось загрузить фоновое изображение: {exc}')

    def _on_spawn_marker_moved(self, marker):
        """Вызывается при перемещении маркера старта пользователем."""
        if not hasattr(marker, 'associated_stripe'):
            return
        group = marker.associated_stripe
        if group is None:
            return
        # Пересчитываем смещение в локальных координатах группы с учётом её трансформации
        # Преобразуем мировую позицию маркера в локальную систему группы
        local_pos = group.mapFromScene(marker.pos())
        group.spawn_offset = local_pos

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

    def rebuild_editor_items(self):
        selected_name = self.selected_edit_item.name if self.selected_edit_item is not None else None
        self._suppress_selection_callbacks = True
        try:
            self.add_traffic_lights()

            # Обновляем флаг редактирования для всех элементов
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

    def get_editable_items(self):
        # Редактируемыми считаем светофоры, полосы и маркеры старта
        return list(self.traffic_lights) + list(self.stripe_groups) + list(self.spawn_points)

    def get_editable_item_map(self):
        return {item.name: item for item in self.get_editable_items()}

    def get_editor_item_descriptors(self):
        descriptors = []
        for item in self.get_editable_items():
            label = self.EDITOR_LABELS.get(item.name, item.name)
            if hasattr(item, 'associated_stripe'):
                # Для маркеров старта даём понятное имя
                label = f'Старт: {item.associated_stripe.name}'
            descriptors.append({'key': item.name, 'label': label})
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

        # Полосы
        if item.name in ('stripe_0', 'stripe_1', 'stripe_2', 'stripe_3'):
            suffix = item.name.split('_')[-1].upper()
            setattr(self.config, f'BACKGROUND_STRIPE_{suffix}_X', round(item.x()))
            setattr(self.config, f'BACKGROUND_STRIPE_{suffix}_Y', round(item.y()))
            # Сохраняем поворот и масштаб
            setattr(self.config, f'BACKGROUND_STRIPE_{suffix}_ROTATION', round(item.rotation()))
            setattr(self.config, f'BACKGROUND_STRIPE_{suffix}_SCALE', item.scale())
            return

        # Светофоры
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
        }
        mapping = export_mapping.get(item.name)
        if mapping:
            x_key, y_key, rotation_key = mapping
            setattr(self.config, x_key, round(item.x()))
            setattr(self.config, y_key, round(item.y()))
            if rotation_key and getattr(item, 'supports_rotation', False):
                setattr(self.config, rotation_key, round(item.rotation()))

        # Маркеры старта: ничего не сохраняем в конфиг, их положение определяется смещением
        # и позицией полосы. При желании можно сохранять смещение, но для простоты опустим.

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
        self.traffic_light_timer.setInterval(self.config.TRAFFIC_LIGHT_UPDATE_INTERVAL)

    def _recalculate_traffic_cycle(self, reset_timer=False):
        self.config.TRAFFIC_LIGHT_CYCLE = max(1, int(self.config.VEHICLE_GREEN_TIME + self.config.VEHICLE_YELLOW_TIME))
        if reset_timer:
            self.traffic_light.timer = 0
        else:
            self.traffic_light.timer %= max(1, self.config.TRAFFIC_LIGHT_CYCLE)
        self.update_traffic_light_display()

    def _refresh_vehicle_items_from_config(self, refresh_speed=False):
        for vehicle_item in self.vehicle_items:
            vehicle_item.refresh_from_config(refresh_speed=refresh_speed)

    def apply_config_value(self, name: str, value):
        if not hasattr(self.config, name):
            return

        old_value = getattr(self.config, name)
        if old_value == value:
            return

        setattr(self.config, name, value)

        if name in self.TIMER_FIELDS:
            self._apply_timer_intervals_from_config()

        for i, group in enumerate(self.stripe_groups):
            if name == f'BACKGROUND_STRIPE_{i}_X':
                group.setPos(value, group.y())
            elif name == f'BACKGROUND_STRIPE_{i}_Y':
                group.setPos(group.x(), value)

        if name in {'VEHICLE_GREEN_TIME', 'VEHICLE_YELLOW_TIME'}:
            self._recalculate_traffic_cycle(reset_timer=False)

        if name in self.SCENE_RELATED_FIELDS:
            self.scene.setSceneRect(0, 0, self.config.SCENE_WIDTH, self.config.SCENE_HEIGHT)
            self.load_background_image()

        if name in self.VEHICLE_VISUAL_FIELDS:
            self._refresh_vehicle_items_from_config(refresh_speed=False)

        if name in self.VEHICLE_SPEED_FIELDS:
            self._refresh_vehicle_items_from_config(refresh_speed=True)

        self.update_traffic_light_display()
        self.notify_editor()

    def get_config_export_text(self):
        lines = []

        lines.append('')
        lines.append('# Background stripes')
        for i, group in enumerate(self.stripe_groups):
            lines.append(f'BACKGROUND_STRIPE_{i}_X: int = {round(group.x())}')
            lines.append(f'BACKGROUND_STRIPE_{i}_Y: int = {round(group.y())}')
            lines.append('')

        lines.append('# Traffic lights (vehicles only)')
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
        }
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
            if not axis or role != 'vehicle':
                continue
            state = self.traffic_light.vehicle_state_for(axis)
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

    def add_vehicle(self, vehicle_type='car', direction='horizontal_right', x=None, y=None):
        """Добавляет машину в указанной позиции (или на спавн-точке полосы, если x,y не заданы)."""
        if x is None or y is None:
            # Найти полосу с нужным направлением? Нет, лучше вызывать с явными координатами из генератора.
            # Для совместимости оставим старый способ, но он не используется.
            return None
        vehicle_id = f'V{self.statistics.vehicle_count:03d}'
        vehicle = Vehicle(vehicle_id, vehicle_type, direction)
        vehicle_item = VehicleItem(vehicle, x, y, self.config)
        self.scene.addItem(vehicle_item)
        self.vehicles.append(vehicle)
        self.vehicle_items.append(vehicle_item)
        self.statistics.vehicle_added()
        self.update_stats()
        return vehicle

    def start_movement(self):
        if not self.timer.isActive():
            self.timer.start(self.config.UPDATE_INTERVAL)
        if not self.vehicle_generator_timer.isActive():
            self.vehicle_generator_timer.start(self.config.VEHICLE_GENERATION_INTERVAL)
        if not self.traffic_light_timer.isActive():
            self.traffic_light_timer.start(self.config.TRAFFIC_LIGHT_UPDATE_INTERVAL)

    def stop_movement(self):
        if self.timer.isActive():
            self.timer.stop()
        if self.vehicle_generator_timer.isActive():
            self.vehicle_generator_timer.stop()
        if self.traffic_light_timer.isActive():
            self.traffic_light_timer.stop()

    def generate_vehicle(self):
        if not self.stripe_groups:
            return
        # Выбираем случайную полосу
        group = random.choice(self.stripe_groups)
        if group.spawn_marker is None:
            return
        pos = group.spawn_marker.pos()
        direction = group.direction
        vehicle_type = random.choice(['car', 'truck', 'bus'])
        self.add_vehicle(vehicle_type, direction, pos.x(), pos.y())

    def update_movement(self):
        vehicles_to_remove = []

        for i, vehicle_item in enumerate(self.vehicle_items):
            if vehicle_item.move(self.vehicle_items, [], self.traffic_light):
                vehicles_to_remove.append(i)

        for i in sorted(vehicles_to_remove, reverse=True):
            self.scene.removeItem(self.vehicle_items[i])
            self.vehicle_items.pop(i)
            self.vehicles.pop(i)
            self.statistics.vehicle_passed()
            self.statistics.vehicle_removed()

        if vehicles_to_remove:
            self.update_stats()

    def update_stats(self):
        self.vehicles_passed_label.setText(f'Проехало машин: {self.statistics.vehicles_passed}')
        self.vehicles_current_label.setText(f'Текущее количество: {self.statistics.vehicle_count}')

    def clear_simulation(self):
        self.stop_movement()
        self._suppress_selection_callbacks = True
        try:
            self.vehicles = []
            self.vehicle_items = []
            self.traffic_lights = []
            self.traffic_light_map = {}
            self.spawn_points = []
            self.selected_edit_item = None
            self.stripe_groups = []
            self.scene.clear()
        finally:
            self._suppress_selection_callbacks = False

        self.traffic_light = TrafficLightController(self.config)
        self.statistics.reset()
        self.update_stats()
        self.load_background_image()
        self.rebuild_editor_items()
        self.update_traffic_light_display()
