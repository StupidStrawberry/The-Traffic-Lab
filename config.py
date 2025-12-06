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
    TRAFFIC_LIGHT_CYCLE: int = 90
    VEHICLE_GREEN_TIME: int = 40
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
    HORIZONTAL_LANE_Y: int = 310
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
    MIN_DISTANCE_BETWEEN_VEHICLES: int = 45

    # Цвета
    VEHICLE_COLORS: dict = field(default_factory=lambda: {
        'car': QColor(65, 105, 225),
        'truck': QColor(139, 0, 0),
        'bus': QColor(255, 140, 0)
    })
    PEDESTRIAN_COLOR: QColor = field(default_factory=lambda: QColor(50, 205, 50))
    LANE_COLOR: QColor = field(default_factory=lambda: QColor(255, 255, 255))
    BACKGROUND_COLOR: QColor = field(default_factory=lambda: QColor(240, 240, 240))

    # Traffic light settings
    TRAFFIC_LIGHT_IMAGES: dict = field(default_factory=lambda: {
        'vehicle': {
            'red': 'traffic_light_vehicle_red.png',
            'yellow': 'traffic_light_vehicle_yellow.png',
            'green': 'traffic_light_vehicle_green.png'
        },
        'pedestrian': {
            'red': 'traffic_light_pedestrian_red.png',
            'green': 'traffic_light_pedestrian_green.png'
        }
    })
    
    # Traffic light default sizes
    VEHICLE_LIGHT_WIDTH: int = 5
    VEHICLE_LIGHT_HEIGHT: int = 5
    PEDESTRIAN_LIGHT_WIDTH: int = 5
    PEDESTRIAN_LIGHT_HEIGHT: int = 5
    
    # Traffic light positions (you can adjust these)
    VEHICLE_LIGHT_HORIZONTAL_POS: tuple = field(default_factory=lambda: (310, 100))
    VEHICLE_LIGHT_VERTICAL_POS: tuple = field(default_factory=lambda: (400, 195))
    PEDESTRIAN_LIGHT_HORIZONTAL_POS: tuple = field(default_factory=lambda: (340, 80))
    PEDESTRIAN_LIGHT_VERTICAL_POS: tuple = field(default_factory=lambda: (420, 220))