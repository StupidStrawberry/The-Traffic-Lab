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
    HORIZONTAL_LANE_Y: int = 305
    VERTICAL_LANE_X: int = 422
    CROSSWALK_WIDTH: int = 20
    CROSSWALK_LENGTH: int = 60
    
    # Oncoming traffic separation (distance between opposite-direction vehicles on same road)
    HORIZONTAL_ONCOMING_TRAFFIC_OFFSET: int = -15  # Vertical offset between left and right moving traffic
    VERTICAL_ONCOMING_TRAFFIC_OFFSET: int = 20  # Horizontal offset between up and down moving traffic

    # Позиции переходов
    HORIZONTAL_CROSSWALK_X: int = 340
    VERTICAL_CROSSWALK_Y: int = 195

    # Размеры объектов
    VEHICLE_WIDTH: int = 40
    VEHICLE_HEIGHT: int = 20
    PEDESTRIAN_WIDTH: int = 10
    PEDESTRIAN_HEIGHT: int = 10
    MIN_DISTANCE_BETWEEN_VEHICLES: int = 45

    # Vehicle spawn positions (offsets and boundaries)
    VEHICLE_SPAWN_OFFSET: int = 0  # Spawn at the edge
    
    # Vehicle rotations (degrees)
    VEHICLE_ROTATION_RIGHT: int = 0
    VEHICLE_ROTATION_LEFT: int = 180
    VEHICLE_ROTATION_DOWN: int = 90
    VEHICLE_ROTATION_UP: int = 270
    
    # Pedestrian spawn positions
    PEDESTRIAN_SPAWN_VERTICAL_X_MIN: int = 320  # HORIZONTAL_CROSSWALK_X - 20
    PEDESTRIAN_SPAWN_VERTICAL_Y: int = 348  # HORIZONTAL_LANE_Y + 38
    PEDESTRIAN_SPAWN_HORIZONTAL_X: int = 477  # VERTICAL_LANE_X + 55
    PEDESTRIAN_SPAWN_HORIZONTAL_Y_MIN: int = 190  # VERTICAL_CROSSWALK_Y - 5
    PEDESTRIAN_SPAWN_HORIZONTAL_Y_MAX_OFFSET: int = 17
    
    # Pedestrian crossing boundaries
    PEDESTRIAN_VERTICAL_CROSS_END_Y: int = 220
    PEDESTRIAN_HORIZONTAL_CROSS_END_X: int = 360
    
    # Pedestrian rotations (degrees)
    PEDESTRIAN_ROTATION_VERTICAL: int = -90  # For vertical movement
    PEDESTRIAN_ROTATION_HORIZONTAL: int = 180  # For horizontal movement
    
    # Vehicle stop positions relative to crosswalks
    VEHICLE_STOP_DISTANCE_HORIZONTAL_RIGHT: int = 50  # Distance before horizontal crosswalk for right-moving vehicles
    VEHICLE_STOP_DISTANCE_HORIZONTAL_LEFT: int = 200  # Distance before horizontal crosswalk for left-moving vehicles
    VEHICLE_STOP_DISTANCE_VERTICAL_DOWN: int = 30  # Distance before vertical crosswalk for down-moving vehicles
    VEHICLE_STOP_DISTANCE_VERTICAL_UP: int = 200  # Distance before vertical crosswalk for up-moving vehicles
    VEHICLE_EXTENDED_CROSSWALK_CHECK_HORIZONTAL: int = 30
    VEHICLE_EXTENDED_CROSSWALK_CHECK_VERTICAL: int = 40

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

    # Traffic light actual positions (in scene)
    TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_X: int = 300  # Для движения вправо/восток
    TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_Y: int = 310
    TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_ROTATION: int = 0

    TRAFFIC_LIGHT_VEHICLE_VERTICAL_X: int = 352  # Для движения вниз/юг
    TRAFFIC_LIGHT_VEHICLE_VERTICAL_Y: int = 215
    TRAFFIC_LIGHT_VEHICLE_VERTICAL_ROTATION: int = 180

    TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_X: int = 500  # Для движения вверх/север
    TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_Y: int = 450
    TRAFFIC_LIGHT_VEHICLE_VERTICAL_OPPOSITE_ROTATION: int = 180

    TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_X: int = 500  # Для движения влево/запад
    TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_Y: int = 100
    TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_OPPOSITE_ROTATION: int = 0
    
    TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_X: int = 320  # HORIZONTAL_CROSSWALK_X + CROSSWALK_WIDTH - 60
    TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_Y: int = 230  # HORIZONTAL_LANE_Y - 80
    TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_ROTATION: int = 0
    
    TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_X: int = 352  # VERTICAL_LANE_X - 70
    TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_Y: int = 225  # VERTICAL_CROSSWALK_Y + CROSSWALK_WIDTH + 10
    TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_ROTATION: int = -90
    
    # Traffic light scales
    TRAFFIC_LIGHT_VEHICLE_SCALE: float = 0.13
    TRAFFIC_LIGHT_PEDESTRIAN_SCALE: float = 0.05