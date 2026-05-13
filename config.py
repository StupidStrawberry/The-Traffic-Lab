from dataclasses import dataclass, field

from PyQt6.QtGui import QColor


@dataclass
class SimulationConfig:
    # Тайминги
    UPDATE_INTERVAL: int = 30
    VEHICLE_GENERATION_INTERVAL: int = 5000
    PEDESTRIAN_GENERATION_INTERVAL: int = 5000
    TRAFFIC_LIGHT_UPDATE_INTERVAL: int = 500
    ANALYSIS_UPDATE_INTERVAL: int = 1000

    # Параметры светофора
    TRAFFIC_LIGHT_CYCLE: int = 80
    VEHICLE_GREEN_TIME: int = 40
    VEHICLE_YELLOW_TIME: int = 10
    PEDESTRIAN_GREEN_TIME: int = 30

    # Геометрия перекрестка
    SCENE_WIDTH: int = 800
    SCENE_HEIGHT: int = 600
    HORIZONTAL_LANE_Y: int = 305
    VERTICAL_LANE_X: int = 422
    CROSSWALK_WIDTH: int = 20
    CROSSWALK_LENGTH: int = 60

    # Разделение встречных потоков
    HORIZONTAL_ONCOMING_TRAFFIC_OFFSET: int = -15
    VERTICAL_ONCOMING_TRAFFIC_OFFSET: int = 20

    # Позиции переходов
    HORIZONTAL_CROSSWALK_X: int = 340
    VERTICAL_CROSSWALK_Y: int = 195

    # Размеры объектов
    VEHICLE_WIDTH: int = 40
    VEHICLE_HEIGHT: int = 20
    PEDESTRIAN_WIDTH: int = 10
    PEDESTRIAN_HEIGHT: int = 10
    MIN_DISTANCE_BETWEEN_VEHICLES: int = 45

    # Скорости (используются и для новых, и для уже существующих объектов при обновлении)
    VEHICLE_SPEED_MEAN: float = 1.25
    VEHICLE_SPEED_VARIATION: float = 0.75
    PEDESTRIAN_SPEED_MEAN: float = 0.55
    PEDESTRIAN_SPEED_VARIATION: float = 0.25

    # Точки появления машин (верхний левый угол спрайта)
    VEHICLE_SPAWN_OFFSET: int = 0
    VEHICLE_SPAWN_HORIZONTAL_RIGHT_X: int = -40
    VEHICLE_SPAWN_HORIZONTAL_RIGHT_Y: int = 295
    VEHICLE_SPAWN_HORIZONTAL_LEFT_X: int = 800
    VEHICLE_SPAWN_HORIZONTAL_LEFT_Y: int = 270
    VEHICLE_SPAWN_VERTICAL_DOWN_X: int = 412
    VEHICLE_SPAWN_VERTICAL_DOWN_Y: int = -40
    VEHICLE_SPAWN_VERTICAL_UP_X: int = 432
    VEHICLE_SPAWN_VERTICAL_UP_Y: int = 600

    # Повороты машин
    VEHICLE_ROTATION_RIGHT: int = 0
    VEHICLE_ROTATION_LEFT: int = 180
    VEHICLE_ROTATION_DOWN: int = 90
    VEHICLE_ROTATION_UP: int = 270

    # Настройки поворотов машин
    TURN_PROBABILITY: float = 0.35
    TURN_RADIUS: int = 40
    TURN_WAIT_DISTANCE: int = 12

    # Точки начала поворота машин (верхний левый угол спрайта)
    TURN_POINT_HORIZONTAL_RIGHT_X: int = 372
    TURN_POINT_HORIZONTAL_RIGHT_Y: int = 295
    TURN_POINT_HORIZONTAL_LEFT_X: int = 472
    TURN_POINT_HORIZONTAL_LEFT_Y: int = 270
    TURN_POINT_VERTICAL_DOWN_X: int = 412
    TURN_POINT_VERTICAL_DOWN_Y: int = 230
    TURN_POINT_VERTICAL_UP_X: int = 432
    TURN_POINT_VERTICAL_UP_Y: int = 335

    # Появление пешеходов
    PEDESTRIAN_SPAWN_VERTICAL_X_MIN: int = 320
    PEDESTRIAN_SPAWN_VERTICAL_Y: int = 348
    PEDESTRIAN_SPAWN_HORIZONTAL_X: int = 477
    PEDESTRIAN_SPAWN_HORIZONTAL_Y_MIN: int = 190
    PEDESTRIAN_SPAWN_HORIZONTAL_Y_MAX_OFFSET: int = 17

    # Границы перехода пешеходов
    PEDESTRIAN_VERTICAL_CROSS_END_Y: int = 220
    PEDESTRIAN_HORIZONTAL_CROSS_END_X: int = 360

    # Повороты пешеходов
    PEDESTRIAN_ROTATION_VERTICAL: int = -90
    PEDESTRIAN_ROTATION_HORIZONTAL: int = 180

    # Стоп-линии и проверки перехода
    VEHICLE_STOP_DISTANCE_HORIZONTAL_RIGHT: int = 50
    VEHICLE_STOP_DISTANCE_HORIZONTAL_LEFT: int = 200
    VEHICLE_STOP_DISTANCE_VERTICAL_DOWN: int = 30
    VEHICLE_STOP_DISTANCE_VERTICAL_UP: int = 200
    VEHICLE_EXTENDED_CROSSWALK_CHECK_HORIZONTAL: int = 30
    VEHICLE_EXTENDED_CROSSWALK_CHECK_VERTICAL: int = 40

    # Цвета
    VEHICLE_COLORS: dict = field(
        default_factory=lambda: {
            'car': QColor(65, 105, 225),
            'truck': QColor(139, 0, 0),
            'bus': QColor(255, 140, 0),
        }
    )
    PEDESTRIAN_COLOR: QColor = field(default_factory=lambda: QColor(50, 205, 50))
    LANE_COLOR: QColor = field(default_factory=lambda: QColor(255, 255, 255))
    BACKGROUND_COLOR: QColor = field(default_factory=lambda: QColor(240, 240, 240))

    # Ассеты светофоров
    TRAFFIC_LIGHT_IMAGES: dict = field(
        default_factory=lambda: {
            'vehicle': {
                'red': 'traffic_light_vehicle_red.png',
                'yellow': 'traffic_light_vehicle_yellow.png',
                'green': 'traffic_light_vehicle_green.png',
            },
            'pedestrian': {
                'red': 'traffic_light_pedestrian_red.png',
                'green': 'traffic_light_pedestrian_green.png',
            },
        }
    )

    # Неиспользуемые legacy-поля размеров
    VEHICLE_LIGHT_WIDTH: int = 5
    VEHICLE_LIGHT_HEIGHT: int = 5
    PEDESTRIAN_LIGHT_WIDTH: int = 5
    PEDESTRIAN_LIGHT_HEIGHT: int = 5

    # Legacy-позиции (оставлены для совместимости)
    VEHICLE_LIGHT_HORIZONTAL_POS: tuple = field(default_factory=lambda: (310, 100))
    VEHICLE_LIGHT_VERTICAL_POS: tuple = field(default_factory=lambda: (400, 195))
    PEDESTRIAN_LIGHT_HORIZONTAL_POS: tuple = field(default_factory=lambda: (340, 80))
    PEDESTRIAN_LIGHT_VERTICAL_POS: tuple = field(default_factory=lambda: (420, 220))

    # Позиции светофоров на сцене
    TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_X: int = 300
    TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_Y: int = 270
    TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_ROTATION: int = 0

    TRAFFIC_LIGHT_VEHICLE_VERTICAL_X: int = 355
    TRAFFIC_LIGHT_VEHICLE_VERTICAL_Y: int = 125
    TRAFFIC_LIGHT_VEHICLE_VERTICAL_ROTATION: int = 0

    TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_X: int = 646
    TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_Y: int = -101
    TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_ROTATION: int = 0

    TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_X: int = 520
    TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_Y: int = 160
    TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_ROTATION: int = 0

    TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_X: int = 353
    TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_Y: int = 158
    TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_ROTATION: int = 0

    TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_X: int = 300
    TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_Y: int = 305
    TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_ROTATION: int = 0

    TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_X: int = 486
    TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_Y: int = 373
    TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_ROTATION: int = 0
    TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_MIRROR_FLIP_X: bool = True

    TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_X: int = 520
    TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_Y: int = 193
    TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_ROTATION: int = 0
    TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_MIRROR_FLIP_X: bool = False

    # Масштабы светофоров
    TRAFFIC_LIGHT_VEHICLE_SCALE: float = 0.13
    TRAFFIC_LIGHT_PEDESTRIAN_SCALE: float = 0.05
