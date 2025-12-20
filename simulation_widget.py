from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QBrush, QColor, QPen, QPainter, QPixmap
import random

from config import SimulationConfig
from classes import Vehicle, Pedestrian, Crosswalk
from traffic_light import TrafficLightController, TrafficLightItem
from simulation_objects import VehicleItem, PedestrianItem
from statistics import SimulationStatistics


class SimulationWidget(QGroupBox):
    """Окно симулирующее - область для визуализации движущихся объектов"""

    def __init__(self):
        super().__init__("Окно симулирующее")
        self.config = SimulationConfig()
        self.statistics = SimulationStatistics()
        self.traffic_light = TrafficLightController(self.config)
        self.vehicles = []
        self.vehicle_items = []
        self.pedestrians = []
        self.pedestrian_items = []
        self.crosswalks = []  # Теперь список переходов
        self.traffic_lights = []  # List of all traffic lights
        self.background_pixmap = None

        self.setup_ui()
        self.setup_timers()
        self.load_background_image()

    def load_background_image(self):
        try:
            self.background_pixmap = QPixmap("Bg main.png")
            if not self.background_pixmap.isNull():
                scaled_pixmap = self.background_pixmap.scaled(
                    self.config.SCENE_WIDTH, 
                    self.config.SCENE_HEIGHT,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                # Добавляем фон на сцену
                background_item = self.scene.addPixmap(scaled_pixmap)
                background_item.setZValue(-1) 
                background_x = 20
                background_y = 55
                background_item.setPos(background_x, background_y)
        except Exception as e:
            print(f"Не удалось загрузить фоновое изображение: {e}")

    def setup_ui(self):
        layout = QVBoxLayout()

        self.info_label = QLabel(
            "Транспортные средства движутся по горизонтальной и вертикальной полосам и исчезают в конце. Пешеходы пересекают дорогу.")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, self.config.SCENE_WIDTH, self.config.SCENE_HEIGHT)
        # Убираем сплошной цвет фона, так как используем изображение
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

        # СОЗДАЕМ traffic_light_label ПЕРЕД добавлением его в layout
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

        # ПЕРЕМЕЩАЕМ эти вызовы ПОСЛЕ создания всех элементов интерфейса
        # self.add_intersection_markings()
        self.add_crosswalks()
        self.add_traffic_lights()

    def setup_timers(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_movement)

        self.vehicle_generator_timer = QTimer()
        self.vehicle_generator_timer.timeout.connect(self.generate_vehicle)

        self.pedestrian_generator_timer = QTimer()
        self.pedestrian_generator_timer.timeout.connect(self.generate_pedestrian)

        self.traffic_light_timer = QTimer()
        self.traffic_light_timer.timeout.connect(self.update_traffic_light)

    # def add_intersection_markings(self):
    #     """Добавляет разметку перекрестка"""
    #     # Горизонтальная полоса
    #     line_horizontal = QGraphicsRectItem(0, self.config.HORIZONTAL_LANE_Y, self.config.SCENE_WIDTH, 2)
    #     line_horizontal.setBrush(QBrush(self.config.LANE_COLOR))
    #     line_horizontal.setPen(QPen(Qt.GlobalColor.white, 2))
    #     self.scene.addItem(line_horizontal)

    #     # Вертикальная полоса
    #     line_vertical = QGraphicsRectItem(self.config.VERTICAL_LANE_X, 0, 2, self.config.SCENE_WIDTH)
    #     line_vertical.setBrush(QBrush(self.config.LANE_COLOR))
    #     line_vertical.setPen(QPen(Qt.GlobalColor.white, 2))
    #     self.scene.addItem(line_vertical)

    #     # Добавляем пунктирные линии
    #     for x in range(0, self.config.SCENE_WIDTH, 20):
    #        if abs(x - self.config.VERTICAL_LANE_X) > 30:  # Пропускаем зону перекрестка
    #            dash = QGraphicsRectItem(x, self.config.HORIZONTAL_LANE_Y, 10, 2)
    #            dash.setBrush(QBrush(self.config.LANE_COLOR))
    #            dash.setPen(QPen(Qt.GlobalColor.white, 2))
    #            self.scene.addItem(dash)

    #     for y in range(0, self.config.SCENE_HEIGHT, 20):
    #        if abs(y - self.config.HORIZONTAL_LANE_Y) > 30:  # Пропускаем зону перекрестка
    #            dash = QGraphicsRectItem(self.config.VERTICAL_LANE_X, y, 2, 10)
    #            dash.setBrush(QBrush(self.config.LANE_COLOR))
    #            dash.setPen(QPen(Qt.GlobalColor.white, 2))
    #            self.scene.addItem(dash)

    def add_crosswalks(self):
        """Добавляет пешеходные переходы на сцену"""
        # Горизонтальный переход (для пешеходов, идущих вертикально)
        h_crosswalk = Crosswalk("H_CW",
                                (self.config.HORIZONTAL_CROSSWALK_X, self.config.HORIZONTAL_LANE_Y - 15),
                                self.config.CROSSWALK_WIDTH, 'vertical')
        self.crosswalks.append(h_crosswalk)

        # Вертикальный переход (для пешеходов, идущих горизонтально)
        v_crosswalk = Crosswalk("V_CW",
                                (self.config.VERTICAL_LANE_X - 15, self.config.VERTICAL_CROSSWALK_Y),
                                self.config.CROSSWALK_WIDTH + 30, 'horizontal')
        self.crosswalks.append(v_crosswalk)

        # Добавляем графическое отображение переходов
        # self.add_crosswalk_markings()

    # def add_crosswalk_markings(self):
    #     """Добавляет графическое отображение пешеходных переходов"""
    #     # Горизонтальный переход (зебра для вертикального движения пешеходов)
    #     for i in range(18):
    #         stripe = QGraphicsRectItem(
    #             self.config.HORIZONTAL_CROSSWALK_X - 20,
    #             self.config.HORIZONTAL_LANE_Y - 62 + i * 5,
    #             self.config.CROSSWALK_WIDTH + 15, 3
    #         )
    #         stripe.setBrush(QBrush(self.config.LANE_COLOR))
    #         stripe.setPen(QPen(Qt.GlobalColor.white, 1))
    #         self.scene.addItem(stripe)

    #     # Вертикальный переход (зебра для горизонтального движения пешеходов)
    #     for i in range(18):
    #         stripe = QGraphicsRectItem(
    #             self.config.VERTICAL_LANE_X - 40 + i * 5,
    #             self.config.VERTICAL_CROSSWALK_Y,
    #             3, self.config.CROSSWALK_WIDTH
    #         )
    #         stripe.setBrush(QBrush(self.config.LANE_COLOR))
    #         stripe.setPen(QPen(Qt.GlobalColor.white, 1))
    #         self.scene.addItem(stripe)
    #     pass

    def add_traffic_lights(self):
        """Добавляет светофоры на перекресток"""
        # Remove existing traffic lights
        for light in self.traffic_lights:
            self.scene.removeItem(light)
        self.traffic_lights.clear()
        
        # Vehicle traffic light for horizontal road
        vehicle_light_horizontal = TrafficLightItem(
            self.config.TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_X,
            self.config.TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_Y,
            light_type='vehicle',
            scale=self.config.TRAFFIC_LIGHT_VEHICLE_SCALE,
            rotation=self.config.TRAFFIC_LIGHT_VEHICLE_HORIZONTAL_ROTATION
        )
        vehicle_light_horizontal.setZValue(10)
        self.scene.addItem(vehicle_light_horizontal)
        self.traffic_lights.append(vehicle_light_horizontal)
        
        # Vehicle traffic light for vertical road
        vehicle_light_vertical = TrafficLightItem(
            self.config.TRAFFIC_LIGHT_VEHICLE_VERTICAL_X,
            self.config.TRAFFIC_LIGHT_VEHICLE_VERTICAL_Y,
            light_type='vehicle',
            scale=self.config.TRAFFIC_LIGHT_VEHICLE_SCALE,
            rotation=self.config.TRAFFIC_LIGHT_VEHICLE_VERTICAL_ROTATION
        )
        vehicle_light_vertical.setZValue(10)
        self.scene.addItem(vehicle_light_vertical)
        self.traffic_lights.append(vehicle_light_vertical)
        
        # Pedestrian traffic light for horizontal crossing (vertical pedestrians)
        pedestrian_light_horizontal = TrafficLightItem(
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_X,
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_Y,
            light_type='pedestrian',
            scale=self.config.TRAFFIC_LIGHT_PEDESTRIAN_SCALE,
            rotation=self.config.TRAFFIC_LIGHT_PEDESTRIAN_HORIZONTAL_ROTATION
        )

        self.scene.addItem(pedestrian_light_horizontal)
        self.traffic_lights.append(pedestrian_light_horizontal)
        
        # Pedestrian traffic light for vertical crossing (horizontal pedestrians)
        pedestrian_light_vertical = TrafficLightItem(
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_X,
            self.config.TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_Y,
            light_type='pedestrian',
            scale=self.config.TRAFFIC_LIGHT_PEDESTRIAN_SCALE,
            rotation=self.config.TRAFFIC_LIGHT_PEDESTRIAN_VERTICAL_ROTATION
        )
        pedestrian_light_horizontal.setZValue(10)
        pedestrian_light_vertical.setZValue(10)
        pedestrian_light_vertical.update_state("green")
        self.scene.addItem(pedestrian_light_vertical)
        self.traffic_lights.append(pedestrian_light_vertical)
        
        self.update_traffic_light_display()


    def update_traffic_light_display(self):
        """Обновляет отображение светофоров"""
        # Check if traffic_light_label exists
        if not hasattr(self, 'traffic_light_label') or self.traffic_light_label is None:
            return
        
        print(self.traffic_light.vehicle_yellow, " | ", self.traffic_light.vehicle_green)
        if self.traffic_light.vehicle_yellow:
            # Yellow for all vehicles
            print("SRABOTALO")
            self._update_vehicle_lights('yellow', 'yellow')
            self.traffic_light_label.setText("Светофор: Желтый для всех направлений")
        elif not self.traffic_light.vehicle_green:
            # Green for vertical vehicles
            self._update_vehicle_lights('green', 'red')
            self._update_pedestrian_lights('red', 'green')
            self.traffic_light_label.setText("Светофор: Зеленый для вертикального транспорта")
        else:
            # Green for horizontal vehicles
            self._update_vehicle_lights('red', 'green')
            self._update_pedestrian_lights('green', 'red')
            self.traffic_light_label.setText("Светофор: Зеленый для горизонтального транспорта")
    

    #ТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕДТУТ БРЕД
    def _update_vehicle_lights(self, horizontal_state: str, vertical_state: str):
        """Update vehicle traffic lights"""
        light = self.traffic_lights[0]
        light.update_state(vertical_state)
        light = self.traffic_lights[1]
        light.update_state(horizontal_state)
    
    def _update_pedestrian_lights(self, horizontal_state: str, vertical_state: str):
        """Update pedestrian traffic lights"""
        light = self.traffic_lights[2]
        light.update_state(vertical_state)
        light = self.traffic_lights[3]
        light.update_state(horizontal_state)
    
    def update_traffic_light(self):
        """Обновляет состояние светофора"""
        self.traffic_light.update()
        self.update_traffic_light_display()

    def add_vehicle(self, vehicle_type='car', direction='horizontal_right'):
        """Добавляет транспортное средство на сцену"""
        vehicle_id = f"V{self.statistics.vehicle_count:03d}"
        vehicle = Vehicle(vehicle_id, vehicle_type, direction)

        if direction == 'horizontal_right':
            x = -self.config.VEHICLE_WIDTH
            y = self.config.HORIZONTAL_LANE_Y - self.config.VEHICLE_HEIGHT // 2
        elif direction == 'horizontal_left':
            x = self.config.SCENE_WIDTH
            y = self.config.HORIZONTAL_LANE_Y + self.config.HORIZONTAL_ONCOMING_TRAFFIC_OFFSET - self.config.VEHICLE_HEIGHT // 2
        elif direction == 'vertical_down':
            x = self.config.VERTICAL_LANE_X - self.config.VEHICLE_HEIGHT // 2
            y = -self.config.VEHICLE_WIDTH
        else:  # vertical_up
            x = self.config.VERTICAL_LANE_X + self.config.VERTICAL_ONCOMING_TRAFFIC_OFFSET - self.config.VEHICLE_HEIGHT // 2
            y = self.config.SCENE_HEIGHT

        vehicle_item = VehicleItem(vehicle, x, y, self.config)
        self.scene.addItem(vehicle_item)

        self.vehicles.append(vehicle)
        self.vehicle_items.append(vehicle_item)
        self.statistics.vehicle_added()
        self.update_stats()

        return vehicle

    def add_pedestrian(self, direction='vertical'):
        """Добавляет пешехода на сцену"""
        pedestrian_id = f"P{self.statistics.pedestrian_count:03d}"
        pedestrian = Pedestrian(pedestrian_id, direction)

        if direction == 'vertical':
            x = random.randint(
                self.config.PEDESTRIAN_SPAWN_VERTICAL_X_MIN,
                self.config.HORIZONTAL_CROSSWALK_X + self.config.CROSSWALK_WIDTH - self.config.PEDESTRIAN_WIDTH
            )
            y = self.config.PEDESTRIAN_SPAWN_VERTICAL_Y
        else:
            x = self.config.PEDESTRIAN_SPAWN_HORIZONTAL_X
            y = random.randint(
                self.config.PEDESTRIAN_SPAWN_HORIZONTAL_Y_MIN,
                self.config.VERTICAL_CROSSWALK_Y + self.config.CROSSWALK_WIDTH + self.config.PEDESTRIAN_SPAWN_HORIZONTAL_Y_MAX_OFFSET - self.config.PEDESTRIAN_HEIGHT
            )

        pedestrian_item = PedestrianItem(pedestrian, x, y, self.config)
        self.scene.addItem(pedestrian_item)

        self.pedestrians.append(pedestrian)
        self.pedestrian_items.append(pedestrian_item)

        # Добавляем пешехода на соответствующий переход
        crosswalk = next((cw for cw in self.crosswalks if cw.direction == direction), None)
        if crosswalk:
            crosswalk.add_pedestrian(pedestrian)

        self.statistics.pedestrian_added()
        self.update_stats()

        return pedestrian

    # Обновим методы добавления конкретных типов транспортных средств
    def add_car(self, direction='horizontal_right'):
        self.add_vehicle('car', direction)

    def add_truck(self, direction='horizontal_right'):
        self.add_vehicle('truck', direction)

    def add_bus(self, direction='horizontal_right'):
        self.add_vehicle('bus', direction)

    def start_movement(self):
        """Запускает движение транспортных средств"""
        if not self.timer.isActive():
            self.timer.start(self.config.UPDATE_INTERVAL)

        # Запускаем генераторы, если они не активны
        if not self.vehicle_generator_timer.isActive():
            self.vehicle_generator_timer.start(self.config.VEHICLE_GENERATION_INTERVAL)

        if not self.pedestrian_generator_timer.isActive():
            self.pedestrian_generator_timer.start(self.config.PEDESTRIAN_GENERATION_INTERVAL)

        # Запускаем таймер светофора
        if not self.traffic_light_timer.isActive():
            self.traffic_light_timer.start(self.config.TRAFFIC_LIGHT_UPDATE_INTERVAL)

    def stop_movement(self):
        """Останавливает движение транспортных средств"""
        if self.timer.isActive():
            self.timer.stop()

        if self.vehicle_generator_timer.isActive():
            self.vehicle_generator_timer.stop()

        if self.pedestrian_generator_timer.isActive():
            self.pedestrian_generator_timer.stop()

        if self.traffic_light_timer.isActive():
            self.traffic_light_timer.stop()

    def generate_vehicle(self):
        """Генерирует случайное транспортное средство"""
        vehicle_types = ['car', 'truck', 'bus']
        vehicle_type = random.choice(vehicle_types)
        directions = ['horizontal_right', 'horizontal_left', 'vertical_down', 'vertical_up']
        direction = random.choice(directions)
        self.add_vehicle(vehicle_type, direction)

    def generate_pedestrian(self):
        """Генерирует пешехода"""
        if random.random() < 0.5:  # 50% шанс генерации пешехода
            direction = random.choice(['horizontal', 'vertical'])
            self.add_pedestrian(direction)

    def update_movement(self):
        """Обновляет позиции всех транспортных средств и пешеходов"""
        vehicles_to_remove = []
        pedestrians_to_remove = []

        # Обновляем транспортные средства
        for i, vehicle_item in enumerate(self.vehicle_items):
            should_remove = vehicle_item.move(self.vehicle_items, self.pedestrian_items, self.traffic_light)
            if should_remove:
                vehicles_to_remove.append(i)

        # Обновляем пешеходов
        for i, pedestrian_item in enumerate(self.pedestrian_items):
            should_remove = pedestrian_item.move(self.vehicle_items, self.traffic_light)
            if should_remove:
                pedestrians_to_remove.append(i)

        # Удаляем транспортные средства, которые достигли конца полосы
        for i in sorted(vehicles_to_remove, reverse=True):
            # Удаляем графическое представление
            self.scene.removeItem(self.vehicle_items[i])
            # Удаляем из списков
            self.vehicle_items.pop(i)
            self.vehicles.pop(i)
            # Увеличиваем счетчик проехавших машин
            self.statistics.vehicle_passed()
            self.statistics.vehicle_removed()

        # Удаляем пешеходов, которые перешли дорогу
        for i in sorted(pedestrians_to_remove, reverse=True):
            # Удаляем графическое представление
            self.scene.removeItem(self.pedestrian_items[i])
            # Удаляем из списков
            pedestrian = self.pedestrian_items[i].pedestrian
            for crosswalk in self.crosswalks:
                if pedestrian in crosswalk.pedestrians:
                    crosswalk.remove_pedestrian(pedestrian)
            self.pedestrian_items.pop(i)
            self.pedestrians.pop(i)
            # Увеличиваем счетчик перешедших пешеходов
            self.statistics.pedestrian_passed()
            self.statistics.pedestrian_removed()

        # Обновляем статистику, если были изменения
        if vehicles_to_remove or pedestrians_to_remove:
            self.update_stats()

    def update_stats(self):
        """Обновляет статистику на экране"""
        self.vehicles_passed_label.setText(f"Проехало машин: {self.statistics.vehicles_passed}")
        self.vehicles_current_label.setText(f"Текущее количество: {self.statistics.vehicle_count}")
        self.pedestrians_passed_label.setText(f"Перешло пешеходов: {self.statistics.pedestrians_passed}")

    def clear_simulation(self):
        """Очищает сцену от всех объектов"""
        self.stop_movement()

        # Очищаем списки ПЕРЕД удалением элементов
        # Это предотвращает использование ссылок на удаленные объекты
        self.vehicles = []
        self.vehicle_items = []
        self.pedestrians = []
        self.pedestrian_items = []
        self.traffic_lights = []  # Clear BEFORE scene.clear()
        self.crosswalks = []

        # Очищаем сцену - это удалит все графические элементы
        self.scene.clear()
        
        # Заново загружаем фон
        self.load_background_image()
        
        # self.add_intersection_markings()
        self.add_crosswalks()
        self.add_traffic_lights()  # This will recreate traffic lights

        # Сбрасываем статистику
        self.statistics.reset()
        self.update_stats()

        # Обновляем отображение светофора
        self.update_traffic_light_display()