import random
from typing import List
from PyQt6.QtWidgets import QGraphicsRectItem
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QBrush, QColor, QPen
from PyQt6.QtCore import Qt

from classes import Vehicle, Pedestrian
from traffic_light import TrafficLightController


class VehicleItem(QGraphicsRectItem):
    def __init__(self, vehicle: Vehicle, x: float, y: float, config):
        super().__init__(QRectF(0, 0, config.VEHICLE_WIDTH, config.VEHICLE_HEIGHT))
        self.vehicle = vehicle
        self.config = config
        self.speed = random.uniform(0.5, 2.0)
        self.waiting = False
        self.wait_time = 0

        color = config.VEHICLE_COLORS.get(vehicle.type, config.VEHICLE_COLORS['car'])
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.GlobalColor.black, 1))
        self.setPos(x, y)

        # Поворачиваем вертикальные транспортные средства
        if vehicle.direction == 'vertical':
            self.setRotation(90)

    def move(self, vehicles: List['VehicleItem'], pedestrians: List['PedestrianItem'],
             traffic_light: TrafficLightController) -> bool:
        if self.waiting:
            self.wait_time -= 1
            if self.wait_time <= 0:
                self.waiting = False
            return False

        if self.vehicle.direction == 'horizontal':
            return self._move_horizontal(vehicles, pedestrians, traffic_light)
        else:
            return self._move_vertical(vehicles, pedestrians, traffic_light)

    def _move_horizontal(self, vehicles, pedestrians, traffic_light) -> bool:
        new_x = self.x() + self.speed

        if self._has_collision(vehicles, new_x, self.y()) or \
                self._should_stop_for_crosswalk_horizontal(new_x, pedestrians, traffic_light):
            return False

        self.setX(new_x)
        return new_x > self.config.SCENE_WIDTH

    def _move_vertical(self, vehicles, pedestrians, traffic_light) -> bool:
        new_y = self.y() + self.speed

        if self._has_collision(vehicles, self.x(), new_y) or \
                self._should_stop_for_crosswalk_vertical(new_y, pedestrians, traffic_light):
            return False

        self.setY(new_y)
        return new_y > self.config.SCENE_HEIGHT

    def _has_collision(self, vehicles: List['VehicleItem'], new_x: float, new_y: float) -> bool:
        for other in vehicles:
            if other != self:
                if (other.vehicle.direction == self.vehicle.direction and
                        abs(other.x() - new_x) < self.config.MIN_DISTANCE_BETWEEN_VEHICLES and
                        abs(other.y() - new_y) < 10):
                    return True
        return False

    def _should_stop_for_crosswalk_horizontal(self, new_x: float, pedestrians: List['PedestrianItem'],
                                              traffic_light: TrafficLightController) -> bool:
        crosswalk_start = self.config.HORIZONTAL_CROSSWALK_X
        crosswalk_end = crosswalk_start + self.config.CROSSWALK_WIDTH

        current_on_crosswalk = (self.x() < crosswalk_end and
                                self.x() + self.config.VEHICLE_WIDTH > crosswalk_start)
        will_be_on_crosswalk = (new_x < crosswalk_end and
                                new_x + self.config.VEHICLE_WIDTH > crosswalk_start)

        has_pedestrians = any(p.crossing and p.pedestrian.direction == 'vertical'
                              for p in pedestrians)
        stop_position = crosswalk_start - self.config.VEHICLE_WIDTH

        if will_be_on_crosswalk:
            if current_on_crosswalk:
                return False
            elif traffic_light.vehicle_green and has_pedestrians:
                return True
            elif traffic_light.vehicle_green:
                return False
            elif new_x > stop_position:
                return True
        return False

    def _should_stop_for_crosswalk_vertical(self, new_y: float, pedestrians: List['PedestrianItem'],
                                            traffic_light: TrafficLightController) -> bool:
        crosswalk_start = self.config.VERTICAL_CROSSWALK_Y
        crosswalk_end = crosswalk_start + self.config.CROSSWALK_WIDTH

        current_on_crosswalk = (self.y() < crosswalk_end and
                                self.y() + self.config.VEHICLE_HEIGHT > crosswalk_start)
        will_be_on_crosswalk = (new_y < crosswalk_end and
                                new_y + self.config.VEHICLE_HEIGHT > crosswalk_start)

        has_pedestrians = any(p.crossing and p.pedestrian.direction == 'horizontal'
                              for p in pedestrians)
        stop_position = crosswalk_start - self.config.VEHICLE_HEIGHT

        if will_be_on_crosswalk:
            if current_on_crosswalk:
                return False
            elif traffic_light.vehicle_green and has_pedestrians:
                return True
            elif traffic_light.vehicle_green:
                return False
            elif new_y > stop_position:
                return True
        return False


class PedestrianItem(QGraphicsRectItem):
    def __init__(self, pedestrian: Pedestrian, x: float, y: float, config):
        super().__init__(QRectF(0, 0, config.PEDESTRIAN_WIDTH, config.PEDESTRIAN_HEIGHT))
        self.pedestrian = pedestrian
        self.config = config
        self.speed = random.uniform(0.3, 0.8)
        self.waiting = False
        self.crossing = False
        self.crossed = False

        self.setBrush(QBrush(config.PEDESTRIAN_COLOR))
        self.setPen(QPen(Qt.GlobalColor.black, 1))
        self.setPos(x, y)

    def move(self, vehicles: List[VehicleItem], traffic_light: TrafficLightController) -> bool:
        if self._should_wait_for_vehicles(vehicles) and not self.crossed:
            self.waiting = True
            return False

        self.waiting = False

        if not self.crossing and not self.crossed and traffic_light.pedestrian_green:
            self.crossing = True

        if self.crossing and not self.crossed:
            if self.pedestrian.direction == 'vertical':
                new_y = self.y() - self.speed
                self.setY(new_y)
                if new_y < 50:
                    self.crossed = True
                    self.crossing = False
                    return True
            else:
                new_x = self.x() - self.speed
                self.setX(new_x)
                if new_x < 50:
                    self.crossed = True
                    self.crossing = False
                    return True

        return False

    def _should_wait_for_vehicles(self, vehicles: List[VehicleItem]) -> bool:
        for vehicle in vehicles:
            if self.pedestrian.direction == 'vertical':
                # Проверяем горизонтальные транспортные средства
                if vehicle.vehicle.direction == 'horizontal':
                    vehicle_x = vehicle.x()
                    if (vehicle_x < self.config.HORIZONTAL_CROSSWALK_X + self.config.CROSSWALK_WIDTH and
                            vehicle_x > self.config.HORIZONTAL_CROSSWALK_X):
                        return True
            else:
                # Проверяем вертикальные транспортные средства
                if vehicle.vehicle.direction == 'vertical':
                    vehicle_y = vehicle.y()
                    if (vehicle_y < self.config.VERTICAL_CROSSWALK_Y + self.config.CROSSWALK_WIDTH and
                            vehicle_y > self.config.VERTICAL_CROSSWALK_Y):
                        return True
        return False