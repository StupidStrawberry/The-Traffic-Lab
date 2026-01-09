from PyQt6.QtWidgets import QGraphicsPixmapItem
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QPixmap, QTransform
from PyQt6.QtCore import Qt
import os


class TrafficLightController:
    def __init__(self, config):
        self.config = config
        self.vehicle_green = True
        self.vehicle_yellow = False
        self.pedestrian_green = False
        self.timer = 0

    def update(self) -> None:
        """Advance the traffic-light phase timer and update internal state flags."""
        self.timer += 1
        if self.timer >= self.config.TRAFFIC_LIGHT_CYCLE:
            self.timer = 0

        # Phase layout (must match config.TRAFFIC_LIGHT_CYCLE):
        #   0 .. VEHICLE_GREEN_TIME-1                  -> vehicles green (horizontal), pedestrians red
        #   VEHICLE_GREEN_TIME .. +VEHICLE_YELLOW_TIME -> vehicles yellow, pedestrians red
        #   rest                                      -> pedestrians green (vertical), vehicles red
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

    def vehicle_state_for(self, axis: str) -> str:
        """Return 'red'/'yellow'/'green' for a vehicle light on the given axis.

        axis: 'horizontal' or 'vertical'
        """
        if self.vehicle_yellow:
            return 'yellow'

        if axis == 'horizontal':
            return 'green' if self.vehicle_green else 'red'
        if axis == 'vertical':
            return 'green' if (not self.vehicle_green) else 'red'
        raise ValueError(f"Unknown axis: {axis}")

    def pedestrian_state_for(self, axis: str) -> str:
        """Return 'red'/'green' for a pedestrian light on the given axis.

        In the simulation logic:
          - pedestrian_green == True means vertical pedestrians may cross
          - horizontal pedestrians may cross when pedestrian_green == False
        """
        if self.vehicle_yellow:
            return 'red'

        if axis == 'vertical':
            return 'green' if self.pedestrian_green else 'red'
        if axis == 'horizontal':
            return 'green' if (not self.pedestrian_green) else 'red'
        raise ValueError(f"Unknown axis: {axis}")


class TrafficLightItem(QGraphicsPixmapItem):
    def __init__(self, x: float, y: float, light_type: str = 'vehicle', scale: float = 1.0, rotation: float = 0):
        super().__init__()
        self.light_type = light_type  # 'vehicle' or 'pedestrian'
        self.current_state = 'red'  # Initial state

        # Load the appropriate image based on type and state
        self.load_image()

        # Set position
        self.setPos(x, y)

        # Apply scaling
        if scale != 1.0:
            self.setScale(scale)

        # Apply rotation if needed
        if rotation != 0:
            self.setRotation(rotation)

        # Set transformation anchor to center for proper rotation
        # self.setTransformOriginPoint(self.pixmap().width() / 2, self.pixmap().height() / 2)

    def load_image(self):
        """Load the appropriate PNG image based on light type and state"""
        # Define image filenames based on type and state
        image_files = {
            'vehicle': {
                'red': 'vehicle_red.png',
                'yellow': 'vehicle_yellow.png',
                'green': 'vehicle_green.png'
            },
            'pedestrian': {
                'red': 'pedestrian_red.png',
                'green': 'pedestrian_green.png'
            }
        }

        # Get filename
        filename = image_files.get(self.light_type, {}).get(self.current_state, '')

        if filename and os.path.exists(filename):
            pixmap = QPixmap(filename)
            if not pixmap.isNull():
                self.setPixmap(pixmap)
                return

        # Fallback: create a colored rectangle if image not found

        self._create_fallback_pixmap()

    def _create_fallback_pixmap(self):
        """Create a simple colored rectangle as fallback"""
        from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
        from PyQt6.QtCore import Qt

        if self.light_type == 'vehicle':
            width, height = 40, 120
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Draw traffic light body
            painter.setBrush(QBrush(QColor(50, 50, 50)))
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.drawRoundedRect(0, 0, width, height, 5, 5)

            # Draw lights based on state
            colors = {
                'red': QColor(255, 0, 0),
                'yellow': QColor(255, 255, 0),
                'green': QColor(0, 255, 0)
            }

            # Red light (top)
            color = colors.get(self.current_state, QColor(100, 100, 100))
            if self.current_state != 'red':
                color = QColor(50, 50, 50)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(width // 2 - 15, 10, 30, 30)

            # Yellow light (middle)
            color = colors.get(self.current_state, QColor(100, 100, 100))
            if self.current_state != 'yellow':
                color = QColor(50, 50, 50)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(width // 2 - 15, 45, 30, 30)

            # Green light (bottom)
            color = colors.get(self.current_state, QColor(100, 100, 100))
            if self.current_state != 'green':
                color = QColor(50, 50, 50)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(width // 2 - 15, 80, 30, 30)

            painter.end()
        else:  # pedestrian
            width, height = 60, 60
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Draw pedestrian light body
            painter.setBrush(QBrush(QColor(50, 50, 50)))
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.drawRoundedRect(0, 0, width, height, 5, 5)

            # Draw walking or standing figure
            if self.current_state == 'green':
                # Green walking figure
                painter.setBrush(QBrush(QColor(0, 255, 0)))
                # Draw walking person symbol
                painter.drawText(10, 30, "🚶")
            else:
                # Red standing figure
                painter.setBrush(QBrush(QColor(255, 0, 0)))
                # Draw standing person symbol
                painter.drawText(10, 30, "🚸")

            painter.end()

        self.setPixmap(pixmap)

    def update_state(self, state: str):
        """Update the traffic light state"""
        self.current_state = state
        self.load_image()

    def move_to(self, x: float, y: float):
        """Move traffic light to new position"""
        self.setPos(x, y)

    def resize(self, scale: float):
        """Resize the traffic light"""
        self.setScale(scale)

    def rotate(self, angle: float):
        """Rotate the traffic light"""
        self.setRotation(angle)