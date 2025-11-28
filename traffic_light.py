from PyQt6.QtWidgets import QGraphicsRectItem
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QBrush, QColor, QPen
from PyQt6.QtCore import Qt


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

class TrafficLightItem(QGraphicsRectItem):
    def __init__(self, x: float, y: float, direction: str):
        super().__init__(QRectF(0, 0, 20, 60))
        self.direction = direction
        self.setPos(x, y)
        self.setPen(QPen(Qt.GlobalColor.black, 2))

        # Создаем огни светофора
        self.lights = {
            'red': QGraphicsRectItem(5, 5, 10, 10, self),
            'yellow': QGraphicsRectItem(5, 25, 10, 10, self),
            'green': QGraphicsRectItem(5, 45, 10, 10, self),
        }

        self.set_initial_state()

    def set_initial_state(self) -> None:
        for light in self.lights.values():
            light.setBrush(QBrush(QColor(100, 100, 100)))

    def update_lights(self, green: bool, yellow: bool, red: bool) -> None:
        self.set_initial_state()

        if green:
            self.lights['green'].setBrush(QBrush(QColor(0, 255, 0)))
        elif yellow:
            self.lights['yellow'].setBrush(QBrush(QColor(255, 255, 0)))
        else:
            self.lights['red'].setBrush(QBrush(QColor(255, 0, 0)))