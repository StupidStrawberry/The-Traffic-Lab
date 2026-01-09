import random
import os
from typing import List
from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsPixmapItem
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QBrush, QColor, QPen, QPixmap, QPainter, QTransform
from PyQt6.QtCore import Qt

from classes import Vehicle, Pedestrian
from traffic_light import TrafficLightController


class VehicleItem(QGraphicsPixmapItem):
    def __init__(self, vehicle: Vehicle, x: float, y: float, config):
        # Create pixmap with proper initialization
        pixmap = self._create_vehicle_pixmap(vehicle, config)
        
        super().__init__(pixmap)
        self.vehicle = vehicle
        self.config = config
        self.speed = random.uniform(0.5, 2.0)
        self.waiting = False
        self.wait_time = 0

        # True after the vehicle has fully passed at least one crosswalk on its lane.
        # Used to implement: if a car has already passed a crosswalk, it ignores red and drives to the end.
        self.passed_any_crosswalk = False

        # Set initial position
        self.setPos(x, y)

        # Set offset to center the image

        # Rotate vehicles based on direction
        if vehicle.direction == 'horizontal_right':
            self.setRotation(self.config.VEHICLE_ROTATION_RIGHT)
        elif vehicle.direction == 'horizontal_left':
            self.setRotation(self.config.VEHICLE_ROTATION_LEFT)
        elif vehicle.direction == 'vertical_down':
            self.setRotation(self.config.VEHICLE_ROTATION_DOWN)
        elif vehicle.direction == 'vertical_up':
            self.setRotation(self.config.VEHICLE_ROTATION_UP)

    def _create_vehicle_pixmap(self, vehicle: Vehicle, config):
        """Create pixmap for vehicle, using image if available or creating a colored rectangle"""
        # Try to load from file first
        image_files = {
            'car': 'car.png',
            'truck': 'truck.png', 
            'bus': 'bus.png'
        }
        
        filename = image_files.get(vehicle.type, 'car.png')
        
        if os.path.exists(filename):
            pixmap = QPixmap(filename)
            if not pixmap.isNull():
                # Scale to appropriate size
                return pixmap.scaled(
                    int(config.VEHICLE_WIDTH * 1.5),
                    int(config.VEHICLE_HEIGHT * 1.5),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
        
        # If image file not found or failed to load, create a colored rectangle
        return self._create_colored_vehicle_pixmap(vehicle, config)

    def _create_colored_vehicle_pixmap(self, vehicle: Vehicle, config):
        """Create a colored rectangle as fallback when image is not available"""
        pixmap = QPixmap(config.VEHICLE_WIDTH, config.VEHICLE_HEIGHT)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get color from config
        color = config.VEHICLE_COLORS.get(vehicle.type, config.VEHICLE_COLORS['car'])
        
        # Draw vehicle shape
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        
        # Draw different shapes based on vehicle type
        if vehicle.type == 'car':
            # Draw car shape
            painter.drawRoundedRect(2, 2, 
                                   config.VEHICLE_WIDTH - 4, 
                                   config.VEHICLE_HEIGHT - 4, 
                                   3, 3)
        elif vehicle.type == 'truck':
            # Draw truck shape (longer rectangle)
            painter.drawRect(0, 5, config.VEHICLE_WIDTH, config.VEHICLE_HEIGHT - 10)
        elif vehicle.type == 'bus':
            # Draw bus shape (square)
            painter.drawRect(0, 0, config.VEHICLE_WIDTH, config.VEHICLE_HEIGHT)
        else:
            # Default rectangle
            painter.drawRect(0, 0, config.VEHICLE_WIDTH, config.VEHICLE_HEIGHT)
        
        painter.end()
        return pixmap

    def move(self, vehicles: List['VehicleItem'], pedestrians: List['PedestrianItem'],
             traffic_light: TrafficLightController) -> bool:
        if self.waiting:
            self.wait_time -= 1
            if self.wait_time <= 0:
                self.waiting = False
            return False

        if self.vehicle.direction in ['horizontal_right', 'horizontal_left']:
            return self._move_horizontal(vehicles, pedestrians, traffic_light)
        else:
            return self._move_vertical(vehicles, pedestrians, traffic_light)

    def _move_horizontal(self, vehicles, pedestrians, traffic_light) -> bool:
        if self.vehicle.direction == 'horizontal_right':
            new_x = self.x() + self.speed
            if self._has_collision(vehicles, new_x, self.y()) or \
                    self._should_stop_for_crosswalk_horizontal(new_x, pedestrians, traffic_light):
                return False
            self.setX(new_x)
            return new_x > self.config.SCENE_WIDTH
        else:  # horizontal_left
            new_x = self.x() - self.speed
            if self._has_collision(vehicles, new_x, self.y()) or \
                    self._should_stop_for_crosswalk_horizontal(new_x, pedestrians, traffic_light):
                return False
            self.setX(new_x)
            return new_x < -self.config.VEHICLE_WIDTH

    def _move_vertical(self, vehicles, pedestrians, traffic_light) -> bool:
        if self.vehicle.direction == 'vertical_down':
            new_y = self.y() + self.speed
            if self._has_collision(vehicles, self.x(), new_y) or \
                    self._should_stop_for_crosswalk_vertical(new_y, pedestrians, traffic_light):
                return False
            self.setY(new_y)
            return new_y > self.config.SCENE_HEIGHT
        else:  # vertical_up
            new_y = self.y() - self.speed
            if self._has_collision(vehicles, self.x(), new_y) or \
                    self._should_stop_for_crosswalk_vertical(new_y, pedestrians, traffic_light):
                return False
            self.setY(new_y)
            return new_y < -self.config.VEHICLE_WIDTH

    def _has_collision(self, vehicles: List['VehicleItem'], new_x: float, new_y: float) -> bool:
        for other in vehicles:
            if other != self:
                # Only check collision with vehicles going in the same direction
                if (other.vehicle.direction == self.vehicle.direction and
                        abs(other.x() - new_x) < self.config.MIN_DISTANCE_BETWEEN_VEHICLES and
                        abs(other.y() - new_y) < self.config.MIN_DISTANCE_BETWEEN_VEHICLES):
                    return True
        return False

    def _is_green_for_vehicle(self, traffic_light: TrafficLightController) -> bool:
        """True if the current traffic light allows this vehicle's direction to go."""
        # Yellow is treated as stop for everyone
        if traffic_light.vehicle_yellow:
            return False

        # TrafficLightController.vehicle_green means:
        # - horizontal vehicles: green when True
        # - vertical vehicles:   green when False
        if self.vehicle.direction in ['horizontal_right', 'horizontal_left']:
            return traffic_light.vehicle_green
        return not traffic_light.vehicle_green

    def _update_passed_any_crosswalk(self) -> None:
        """Mark that the vehicle has passed at least one crosswalk (once passed, it ignores red)."""
        if self.passed_any_crosswalk:
            return

        h_start = self.config.HORIZONTAL_CROSSWALK_X
        h_end = h_start + self.config.CROSSWALK_WIDTH
        v_start = self.config.VERTICAL_CROSSWALK_Y
        v_end = v_start + self.config.CROSSWALK_WIDTH

        if self.vehicle.direction == 'horizontal_right':
            if self.x() > h_end:
                self.passed_any_crosswalk = True
        elif self.vehicle.direction == 'horizontal_left':
            if self.x() + self.config.VEHICLE_WIDTH < h_start:
                self.passed_any_crosswalk = True
        elif self.vehicle.direction == 'vertical_down':
            if self.y() > v_end:
                self.passed_any_crosswalk = True
        elif self.vehicle.direction == 'vertical_up':
            if self.y() + self.config.VEHICLE_HEIGHT < v_start:
                self.passed_any_crosswalk = True


    def _should_stop_for_crosswalk_horizontal(self, new_x: float, pedestrians: List['PedestrianItem'],
                                              traffic_light: TrafficLightController) -> bool:
        """Decide whether a vehicle must stop for the horizontal crosswalk.

        Требование:
        - Если машина НЕ проехала ни одного перехода и на её полосе КРАСНЫЙ/ЖЁЛТЫЙ — остановиться.
        - Если хотя бы один переход УЖЕ был пройден — игнорировать красный и ехать до конца.
        """
        self._update_passed_any_crosswalk()

        crosswalk_start = self.config.HORIZONTAL_CROSSWALK_X
        crosswalk_end = crosswalk_start + self.config.CROSSWALK_WIDTH

        # If already passed at least one crosswalk, never stop for the light anymore
        if self.passed_any_crosswalk:
            return False

        lane_green = self._is_green_for_vehicle(traffic_light)
        has_pedestrians = any(p.crossing and p.pedestrian.direction == 'vertical' for p in pedestrians)

        if self.vehicle.direction == 'horizontal_right':
            # x is left edge, front is x + VEHICLE_WIDTH
            stop_x = crosswalk_start - self.config.VEHICLE_WIDTH - self.config.VEHICLE_STOP_DISTANCE_HORIZONTAL_RIGHT

            current_on_crosswalk = (self.x() < crosswalk_end and
                                    self.x() + self.config.VEHICLE_WIDTH > crosswalk_start)
            if current_on_crosswalk:
                return False

            # Stop at stop line when red/yellow
            if (not lane_green) and new_x >= stop_x:
                self.setX(stop_x)
                return True

            # On green, still yield to pedestrians already crossing
            if lane_green and has_pedestrians and new_x >= stop_x:
                self.setX(stop_x)
                return True

        else:  # horizontal_left
            # For left moving, front is x (left edge)
            stop_x = crosswalk_end + self.config.VEHICLE_STOP_DISTANCE_HORIZONTAL_LEFT

            current_on_crosswalk = (self.x() > crosswalk_start - self.config.VEHICLE_WIDTH and
                                    self.x() < crosswalk_end)
            if current_on_crosswalk:
                return False

            if (not lane_green) and new_x <= stop_x:
                self.setX(stop_x)
                return True

            if lane_green and has_pedestrians and new_x <= stop_x:
                self.setX(stop_x)
                return True

        return False

    def _should_stop_for_crosswalk_vertical(self, new_y: float, pedestrians: List['PedestrianItem'],
                                            traffic_light: TrafficLightController) -> bool:
        """Decide whether a vehicle must stop for the vertical crosswalk (same rule as horizontal)."""
        self._update_passed_any_crosswalk()

        crosswalk_start = self.config.VERTICAL_CROSSWALK_Y
        crosswalk_end = crosswalk_start + self.config.CROSSWALK_WIDTH

        if self.passed_any_crosswalk:
            return False

        lane_green = self._is_green_for_vehicle(traffic_light)
        has_pedestrians = any(p.crossing and p.pedestrian.direction == 'horizontal' for p in pedestrians)

        if self.vehicle.direction == 'vertical_down':
            # y is top edge, front is y + VEHICLE_HEIGHT
            stop_y = crosswalk_start - self.config.VEHICLE_HEIGHT - self.config.VEHICLE_STOP_DISTANCE_VERTICAL_DOWN

            current_on_crosswalk = (self.y() < crosswalk_end and
                                    self.y() + self.config.VEHICLE_HEIGHT > crosswalk_start)
            if current_on_crosswalk:
                return False

            if (not lane_green) and new_y >= stop_y:
                self.setY(stop_y)
                return True

            if lane_green and has_pedestrians and new_y >= stop_y:
                self.setY(stop_y)
                return True

        else:  # vertical_up
            # For up moving, front is y (top edge)
            stop_y = crosswalk_end + self.config.VEHICLE_STOP_DISTANCE_VERTICAL_UP

            current_on_crosswalk = (self.y() > crosswalk_start - self.config.VEHICLE_HEIGHT and
                                    self.y() < crosswalk_end)
            if current_on_crosswalk:
                return False

            if (not lane_green) and new_y <= stop_y:
                self.setY(stop_y)
                return True

            if lane_green and has_pedestrians and new_y <= stop_y:
                self.setY(stop_y)
                return True

        return False


class PedestrianItem(QGraphicsPixmapItem):  # Changed from QGraphicsRectItem to QGraphicsPixmapItem
    def __init__(self, pedestrian: Pedestrian, x: float, y: float, config):
        # Create pixmap for pedestrian
        pixmap = self._create_pedestrian_pixmap(pedestrian, config)
        
        super().__init__(pixmap)
        self.pedestrian = pedestrian
        self.config = config
        self.speed = random.uniform(0.3, 0.8)
        self.waiting = False
        self.crossing = False
        self.crossed = False
        self.direction = pedestrian.direction

        # Set initial position
        self.setPos(x, y)

        # Set offset to center the imag

        # Apply rotation based on pedestrian direction
        # IMPORTANT: The pedestrian.png should be facing RIGHT by default
        if pedestrian.direction == 'vertical':
            # For vertical movement (up), we need to rotate -90 degrees (facing up)
            self.setRotation(self.config.PEDESTRIAN_ROTATION_VERTICAL)
        else:
            self.setRotation(self.config.PEDESTRIAN_ROTATION_HORIZONTAL)

    def _create_pedestrian_pixmap(self, pedestrian: Pedestrian, config):
        """Create pixmap for pedestrian, using image if available or creating a colored rectangle"""
        # Try to load from file
        filename = "pedestrian.png"
        
        if os.path.exists(filename):
            pixmap = QPixmap(filename)
            if not pixmap.isNull():
                # Scale to appropriate size
                # For pedestrians, we might want a different aspect ratio
                scaled_width = int(config.PEDESTRIAN_WIDTH * 1.5)
                scaled_height = int(config.PEDESTRIAN_HEIGHT * 1.5)
                
                return pixmap.scaled(
                    scaled_width,
                    scaled_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
        
        # If image file not found, create a colored rectangle
        return self._create_colored_pedestrian_pixmap(config)

    def _create_colored_pedestrian_pixmap(self, config):
        """Create a colored rectangle as fallback when pedestrian image is not available"""
        pixmap = QPixmap(config.PEDESTRIAN_WIDTH, config.PEDESTRIAN_HEIGHT)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw pedestrian shape (a simple person shape)
        color = self.config.PEDESTRIAN_COLOR
        
        # Draw head (circle)
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawEllipse(config.PEDESTRIAN_WIDTH//2 - 3, 1, 6, 6)
        
        # Draw body (rectangle)
        painter.drawRect(config.PEDESTRIAN_WIDTH//2 - 2, 7, 4, 8)
        
        # Draw legs
        painter.drawLine(config.PEDESTRIAN_WIDTH//2, 15, 
                        config.PEDESTRIAN_WIDTH//2 - 3, config.PEDESTRIAN_HEIGHT)
        painter.drawLine(config.PEDESTRIAN_WIDTH//2, 15, 
                        config.PEDESTRIAN_WIDTH//2 + 3, config.PEDESTRIAN_HEIGHT)
        
        # Draw arms
        painter.drawLine(config.PEDESTRIAN_WIDTH//2, 9, 
                        config.PEDESTRIAN_WIDTH//2 - 4, 12)
        painter.drawLine(config.PEDESTRIAN_WIDTH//2, 9, 
                        config.PEDESTRIAN_WIDTH//2 + 4, 12)
        
        painter.end()
        return pixmap

    def move(self, vehicles: List[VehicleItem], traffic_light: TrafficLightController) -> bool:
        if self._should_wait_for_vehicles(vehicles) and not self.crossed:
            self.waiting = True
            return False

        self.waiting = False

        if not self.crossing and not self.crossed:
            if traffic_light.pedestrian_green and self.direction == 'vertical':
                self.crossing = True
            elif not traffic_light.pedestrian_green and self.direction == 'horizontal':
                self.crossing = True

        if self.crossing and not self.crossed:
            if self.pedestrian.direction == 'vertical':
                # Vertical pedestrians move up
                new_y = self.y() - self.speed
                self.setY(new_y)
                if new_y < self.config.PEDESTRIAN_VERTICAL_CROSS_END_Y:
                    self.crossed = True
                    self.crossing = False
                    return True
            else:
                # Horizontal pedestrians move left
                new_x = self.x() - self.speed
                self.setX(new_x)
                if new_x < self.config.PEDESTRIAN_HORIZONTAL_CROSS_END_X:
                    self.crossed = True
                    self.crossing = False
                    return True

        return False

    def _should_wait_for_vehicles(self, vehicles: List[VehicleItem]) -> bool:
        for vehicle in vehicles:
            if self.pedestrian.direction == 'vertical':
                # Check both horizontal directions
                if vehicle.vehicle.direction in ['horizontal_right', 'horizontal_left']:
                    vehicle_x = vehicle.x()
                    if (vehicle_x < self.config.HORIZONTAL_CROSSWALK_X + self.config.CROSSWALK_WIDTH and
                            vehicle_x > self.config.HORIZONTAL_CROSSWALK_X):
                        return True
            else:
                # Check both vertical directions
                if vehicle.vehicle.direction in ['vertical_down', 'vertical_up']:
                    vehicle_y = vehicle.y()
                    if (vehicle_y < self.config.VERTICAL_CROSSWALK_Y + self.config.CROSSWALK_WIDTH and
                            vehicle_y > self.config.VERTICAL_CROSSWALK_Y):
                        return True
        return False