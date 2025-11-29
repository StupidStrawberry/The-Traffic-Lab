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
    TRAFFIC_LIGHT_CYCLE: int = 100
    VEHICLE_GREEN_TIME: int = 60
    VEHICLE_YELLOW_TIME: int = 10
    PEDESTRIAN_GREEN_TIME: int = 30

    # Геометрия
    SCENE_WIDTH: int = 800
    SCENE_HEIGHT: int = 200
    LANE_Y: int = 100
    CROSSWALK_X: int = 350
    CROSSWALK_WIDTH: int = 20

    # Геометрия перекрестка
    SCENE_WIDTH: int = 800
    SCENE_HEIGHT: int = 600
    HORIZONTAL_LANE_Y: int = 300
    VERTICAL_LANE_X: int = 422
    CROSSWALK_WIDTH: int = 20
    CROSSWALK_LENGTH: int = 60

    # Позиции переходов
    HORIZONTAL_CROSSWALK_X: int = 340
    VERTICAL_CROSSWALK_Y: int = 195

    # Размеры объектов
    VEHICLE_WIDTH: int = 40
    VEHICLE_HEIGHT: int = 20
    PEDESTRIAN_WIDTH: int = 10
    PEDESTRIAN_HEIGHT: int = 10
    MIN_DISTANCE_BETWEEN_VEHICLES: int = 60

    # Цвета
    VEHICLE_COLORS: dict = field(default_factory=lambda: {
        'car': QColor(65, 105, 225),
        'truck': QColor(139, 0, 0),
        'bus': QColor(255, 140, 0)
    })
    PEDESTRIAN_COLOR: QColor = field(default_factory=lambda: QColor(50, 205, 50))
    LANE_COLOR: QColor = field(default_factory=lambda: QColor(255, 255, 255))
    BACKGROUND_COLOR: QColor = field(default_factory=lambda: QColor(240, 240, 240))