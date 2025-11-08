import sys
import random
from classes import Vehicle, Pedestrian, Crosswalk
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QGroupBox, QTextEdit, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
    QSpinBox, QDoubleSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen


class TrafficLight:
    """Класс для управления светофором"""

    def __init__(self):
        self.vehicle_green = True  # Зеленый для транспорта
        self.pedestrian_green = False  # Зеленый для пешеходов
        self.vehicle_yellow = False  # Желтый для транспорта
        self.timer = 0
        self.cycle_time = 100  # Время цикла в условных единицах
        self.green_time = 60  # Время зеленого для транспорта
        self.yellow_time = 10  # Время желтого для транспорта
        self.pedestrian_time = 30  # Время зеленого для пешеходов

    def update(self):
        """Обновляет состояние светофора"""
        self.timer += 1

        if self.timer >= self.cycle_time:
            self.timer = 0

        if self.timer < self.green_time:
            self.vehicle_green = True
            self.vehicle_yellow = False
            self.pedestrian_green = False
        elif self.timer < self.green_time + self.yellow_time:
            self.vehicle_green = False
            self.vehicle_yellow = True
            self.pedestrian_green = False
        else:
            self.vehicle_green = False
            self.vehicle_yellow = False
            self.pedestrian_green = True


class VehicleItem(QGraphicsRectItem):
    """Графическое представление транспортного средства"""

    def __init__(self, vehicle, x, y):
        super().__init__(QRectF(0, 0, 40, 20))
        self.vehicle = vehicle
        self.speed = random.uniform(0.5, 2.0)  # Случайная скорость
        self.waiting = False  # Ожидает ли транспортное средство
        self.wait_time = 0  # Время ожидания

        colors = {
            'car': QColor(65, 105, 225),
            'truck': QColor(139, 0, 0),
            'bus': QColor(255, 140, 0)
        }

        color = colors.get(vehicle.type, QColor(65, 105, 225))
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.GlobalColor.black, 1))

        self.setPos(x, y)

    def move(self, vehicles, crosswalk_items, traffic_light):
        """Двигает транспортное средство по горизонтали с учетом других транспортных средств, пешеходов и светофора"""
        if self.waiting:
            self.wait_time -= 1
            if self.wait_time <= 0:
                self.waiting = False
            return

        # Определяем следующую позицию
        new_x = self.x() + self.speed
        new_y = self.y()

        # Проверяем столкновение с другими транспортными средствами
        collision = False
        min_distance = 60  # Минимальное расстояние между транспортными средствами

        for other_vehicle in vehicles:
            if other_vehicle != self:
                # Проверяем, находится ли другое транспортное средство впереди на той же полосе
                if (other_vehicle.x() > self.x() and  # Впереди
                        abs(other_vehicle.x() - new_x) < min_distance and  # Слишком близко
                        abs(other_vehicle.y() - self.y()) < 10):  # На той же полосе
                    collision = True
                    break

        # Проверяем наличие пешеходов на переходе и состояние светофора
        crosswalk_x = 350  # Позиция пешеходного перехода
        crosswalk_width = 20  # Ширина перехода

        # Если транспортное средство приближается к переходу
        approaching_crosswalk = (new_x < crosswalk_x + crosswalk_width and new_x + 40 > crosswalk_x)

        # Останавливаемся на красный свет или если есть пешеходы на переходе
        if approaching_crosswalk:
            if not traffic_light.vehicle_green:
                # Красный или желтый для транспорта
                collision = True
            elif any(not p.crossed for p in crosswalk_items):
                # Есть пешеходы на переходе
                collision = True

        # Если столкновения нет, двигаем транспортное средство
        if not collision:
            self.setX(new_x)

            # Проверяем границы сцены
            scene_width = self.scene().width() if self.scene() else 800

            # Если транспортное средство вышло за правую границу, помечаем для удаления
            if new_x > scene_width:
                return True  # Помечаем для удаления

        return False  # Не удаляем


class PedestrianItem(QGraphicsRectItem):
    """Графическое представление пешехода"""

    def __init__(self, pedestrian, x, y):
        super().__init__(QRectF(0, 0, 10, 20))
        self.pedestrian = pedestrian
        self.speed = random.uniform(0.3, 0.8)  # Скорость пешехода
        self.waiting = False
        self.crossing = False
        self.crossed = False

        self.setBrush(QBrush(QColor(50, 205, 50)))  # Зеленый цвет для пешеходов
        self.setPen(QPen(Qt.GlobalColor.black, 1))

        self.setPos(x, y)

    def move(self, vehicles, traffic_light):
        """Двигает пешехода через дорогу с учетом светофора"""
        if self.waiting:
            return False

        if not self.crossing and not self.crossed:
            # Начинаем переход только на зеленый свет для пешеходов
            if traffic_light.pedestrian_green:
                self.crossing = True
            else:
                return False

        if self.crossing and not self.crossed:
            # Двигаем пешехода вверх
            new_y = self.y() - self.speed
            self.setY(new_y)

            # Проверяем, перешел ли пешеход дорогу
            if new_y < 50:  # Достиг другой стороны
                self.crossed = True
                self.crossing = False
                return True  # Помечаем для удаления

        return False


class TrafficLightItem(QGraphicsRectItem):
    """Графическое представление светофора"""

    def __init__(self, x, y):
        super().__init__(QRectF(0, 0, 20, 60))
        self.setPos(x, y)
        self.setPen(QPen(Qt.GlobalColor.black, 2))

        # Создаем огни светофора
        self.vehicle_red = QGraphicsRectItem(5, 5, 10, 10, self)
        self.vehicle_yellow = QGraphicsRectItem(5, 25, 10, 10, self)
        self.vehicle_green = QGraphicsRectItem(5, 45, 10, 10, self)

        self.pedestrian_red = QGraphicsRectItem(25, 5, 10, 10, self)
        self.pedestrian_green = QGraphicsRectItem(25, 25, 10, 10, self)

        # Изначально выключаем все огни
        self.set_vehicle_light('red')
        self.set_pedestrian_light('red')

    def set_vehicle_light(self, color):
        """Устанавливает цвет для транспортного светофора"""
        self.vehicle_red.setBrush(QBrush(QColor(100, 0, 0)))  # Темно-красный
        self.vehicle_yellow.setBrush(QBrush(QColor(100, 100, 0)))  # Темно-желтый
        self.vehicle_green.setBrush(QBrush(QColor(0, 100, 0)))  # Темно-зеленый

        if color == 'red':
            self.vehicle_red.setBrush(QBrush(QColor(255, 0, 0)))  # Ярко-красный
        elif color == 'yellow':
            self.vehicle_yellow.setBrush(QBrush(QColor(255, 255, 0)))  # Ярко-желтый
        elif color == 'green':
            self.vehicle_green.setBrush(QBrush(QColor(0, 255, 0)))  # Ярко-зеленый

    def set_pedestrian_light(self, color):
        """Устанавливает цвет для пешеходного светофора"""
        self.pedestrian_red.setBrush(QBrush(QColor(100, 0, 0)))  # Темно-красный
        self.pedestrian_green.setBrush(QBrush(QColor(0, 100, 0)))  # Темно-зеленый

        if color == 'red':
            self.pedestrian_red.setBrush(QBrush(QColor(255, 0, 0)))  # Ярко-красный
        elif color == 'green':
            self.pedestrian_green.setBrush(QBrush(QColor(0, 255, 0)))  # Ярко-зеленый


class SimulationWidget(QGroupBox):
    """Окно симулирующее - область для визуализации движущихся объектов"""

    def __init__(self):
        super().__init__("Окно симулирующее")
        self.vehicle_items = []  # Список для хранения графических представлений
        self.vehicles = []  # Список для хранения объектов транспортных средств
        self.pedestrian_items = []  # Список для хранения графических представлений пешеходов
        self.pedestrians = []  # Список для хранения объектов пешеходов
        self.crosswalk = None  # Пешеходный переход
        self.traffic_light = TrafficLight()  # Светофор
        self.timer = QTimer()  # Таймер для анимации
        self.vehicle_generator_timer = QTimer()  # Таймер для генерации машин
        self.pedestrian_generator_timer = QTimer()  # Таймер для генерации пешеходов
        self.traffic_light_timer = QTimer()  # Таймер для переключения светофора
        self.traffic_light_item = None  # Графическое представление светофора
        self.setup_ui()

    # В методе setup_ui класса SimulationWidget добавьте инициализацию traffic_light_label:
    def setup_ui(self):
        layout = QVBoxLayout()

        # Заголовок или информация о симуляции
        self.info_label = QLabel(
            "Транспортные средства движутся по одной горизонтальной полосе и исчезают в конце. Пешеходы пересекают дорогу.")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Создаем графическую сцену и представление для отображения объектов
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 800, 200)

        # Добавляем разметку одной горизонтальной полосы
        self.add_lane_markings()

        # Добавляем пешеходный переход
        self.add_crosswalk()

        # Добавляем светофор
        self.add_traffic_light()

        self.graphics_view = QGraphicsView(self.scene)
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Устанавливаем минимальный размер для области просмотра
        self.graphics_view.setMinimumSize(400, 200)

        # Кнопки управления
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

        # Статистика - ИНИЦИАЛИЗИРУЕМ traffic_light_label ПЕРЕД ИСПОЛЬЗОВАНИЕМ
        stats_layout = QHBoxLayout()
        self.vehicles_passed_label = QLabel("Проехало машин: 0")
        self.vehicles_current_label = QLabel("Текущее количество: 0")
        self.pedestrians_passed_label = QLabel("Перешло пешеходов: 0")
        self.traffic_light_label = QLabel("Светофор: Зеленый для транспорта")  # ДОБАВЛЕНО

        stats_layout.addWidget(self.vehicles_passed_label)
        stats_layout.addWidget(self.vehicles_current_label)
        stats_layout.addWidget(self.pedestrians_passed_label)
        stats_layout.addWidget(self.traffic_light_label)  # ДОБАВЛЕНО

        layout.addWidget(self.info_label)
        layout.addWidget(self.graphics_view)
        layout.addLayout(control_layout)
        layout.addLayout(stats_layout)
        self.setLayout(layout)
        # Счетчики для ID
        self.vehicle_count = 0
        self.pedestrian_count = 0
        self.vehicles_passed = 0  # Счетчик проехавших машин
        self.pedestrians_passed = 0  # Счетчик перешедших пешеходов

        # Настраиваем таймер для обновления анимации
        self.timer.timeout.connect(self.update_movement)

        # Настраиваем таймеры для генерации
        self.vehicle_generator_timer.timeout.connect(self.generate_vehicle)
        self.pedestrian_generator_timer.timeout.connect(self.generate_pedestrian)

        # Настраиваем таймер для светофора
        self.traffic_light_timer.timeout.connect(self.update_traffic_light)

    def add_lane_markings(self):
        """Добавляет разметку одной горизонтальной полосы на сцену"""
        # Центральная линия полосы
        lane_y = 100
        line = QGraphicsRectItem(0, lane_y, 800, 2)
        line.setBrush(QBrush(QColor(255, 255, 255)))
        line.setPen(QPen(Qt.GlobalColor.white, 2))
        self.scene.addItem(line)

        # Добавляем пунктирную разделительную линию
        for x in range(0, 800, 20):
            dash = QGraphicsRectItem(x, lane_y, 10, 2)
            dash.setBrush(QBrush(QColor(255, 255, 255)))
            dash.setPen(QPen(Qt.GlobalColor.white, 2))
            self.scene.addItem(dash)

    def add_crosswalk(self):
        """Добавляет пешеходный переход на сцену"""
        crosswalk_x = 350
        crosswalk_width = 20
        crosswalk_y = 85

        # Создаем объект пешеходного перехода
        self.crosswalk = Crosswalk("CW1", (crosswalk_x, crosswalk_y), crosswalk_width)

        # Добавляем зебру
        for i in range(6):
            stripe = QGraphicsRectItem(crosswalk_x, crosswalk_y - 10 + i * 10, 30, 3)
            stripe.setBrush(QBrush(QColor(255, 255, 255)))
            stripe.setPen(QPen(Qt.GlobalColor.white, 1))
            self.scene.addItem(stripe)

    def add_traffic_light(self):
        """Добавляет светофор на сцену"""
        # Светофор для транспорта располагаем перед переходом
        self.traffic_light_item = TrafficLightItem(320, 40)
        self.scene.addItem(self.traffic_light_item)
        self.update_traffic_light_display()

    def update_traffic_light_display(self):
        """Обновляет отображение светофора"""
        if not hasattr(self, 'traffic_light_label') or self.traffic_light_label is None:
            return

        if not hasattr(self, 'traffic_light_item') or self.traffic_light_item is None:
            return

        if self.traffic_light.vehicle_green:
            self.traffic_light_item.set_vehicle_light('green')
            self.traffic_light_item.set_pedestrian_light('red')
            self.traffic_light_label.setText("Светофор: Зеленый для транспорта")
        elif self.traffic_light.vehicle_yellow:
            self.traffic_light_item.set_vehicle_light('yellow')
            self.traffic_light_item.set_pedestrian_light('red')
            self.traffic_light_label.setText("Светофор: Желтый для транспорта")
        else:
            self.traffic_light_item.set_vehicle_light('red')
            self.traffic_light_item.set_pedestrian_light('green')
            self.traffic_light_label.setText("Светофор: Зеленый для пешеходов")

    def update_traffic_light(self):
        """Обновляет состояние светофора"""
        self.traffic_light.update()
        self.update_traffic_light_display()

    def add_vehicle(self, vehicle_type='car'):
        """Добавляет транспортное средство на сцену"""
        # Создаем объект транспортного средства
        vehicle_id = f"V{self.vehicle_count:03d}"
        vehicle = Vehicle(vehicle_id, vehicle_type)

        # Размещаем на горизонтальной полосе
        x = -40  # Начинаем за пределами видимости слева
        y = 90  # Фиксированная позиция по вертикали (центр полосы)

        # Создаем графическое представление
        vehicle_item = VehicleItem(vehicle, x, y)

        # Добавляем на сцену
        self.scene.addItem(vehicle_item)

        # Сохраняем объекты
        self.vehicles.append(vehicle)
        self.vehicle_items.append(vehicle_item)

        # Увеличиваем счетчик
        self.vehicle_count += 1

        # Обновляем статистику
        self.update_stats()

        return vehicle

    def add_pedestrian(self):
        """Добавляет пешехода на сцену"""
        # Создаем объект пешехода
        pedestrian_id = f"P{self.pedestrian_count:03d}"
        pedestrian = Pedestrian(pedestrian_id)

        # Размещаем пешехода в начале перехода (снизу)
        x = random.randint(350, 370)  # Случайная позиция на переходе
        y = 120  # Начинаем снизу дороги

        # Создаем графическое представление
        pedestrian_item = PedestrianItem(pedestrian, x, y)

        # Добавляем на сцену
        self.scene.addItem(pedestrian_item)

        # Сохраняем объекты
        self.pedestrians.append(pedestrian)
        self.pedestrian_items.append(pedestrian_item)

        # Добавляем пешехода на переход
        if self.crosswalk:
            self.crosswalk.add_pedestrian(pedestrian)

        # Увеличиваем счетчик
        self.pedestrian_count += 1

        # Обновляем статистику
        self.update_stats()

        return pedestrian

    def add_car(self):
        """Добавляет легковой автомобиль"""
        self.add_vehicle('car')

    def add_truck(self):
        """Добавляет грузовик"""
        self.add_vehicle('truck')

    def add_bus(self):
        """Добавляет автобус"""
        self.add_vehicle('bus')

    def start_movement(self):
        """Запускает движение транспортных средств"""
        if not self.timer.isActive():
            self.timer.start(30)  # Обновление каждые 30 мс

        # Запускаем генераторы, если они не активны
        if not self.vehicle_generator_timer.isActive():
            self.vehicle_generator_timer.start(5000)  # Генерация машин каждые 5 секунды

        if not self.pedestrian_generator_timer.isActive():
            self.pedestrian_generator_timer.start(5000)  # Генерация пешеходов каждые 5 секунд

        # Запускаем таймер светофора
        if not self.traffic_light_timer.isActive():
            self.traffic_light_timer.start(500)  # Обновление светофора каждые 500 мс

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
        self.add_vehicle(vehicle_type)

    def generate_pedestrian(self):
        """Генерирует пешехода"""
        if random.random() < 0.7:  # 70% шанс генерации пешехода
            self.add_pedestrian()

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
            self.vehicles_passed += 1

        # Удаляем пешеходов, которые перешли дорогу
        for i in sorted(pedestrians_to_remove, reverse=True):
            # Удаляем графическое представление
            self.scene.removeItem(self.pedestrian_items[i])
            # Удаляем из списков
            if self.pedestrian_items[i].pedestrian in self.crosswalk.pedestrians:
                self.crosswalk.remove_pedestrian(self.pedestrian_items[i].pedestrian)
            self.pedestrian_items.pop(i)
            self.pedestrians.pop(i)
            # Увеличиваем счетчик перешедших пешеходов
            self.pedestrians_passed += 1

        # Обновляем статистику, если были изменения
        if vehicles_to_remove or pedestrians_to_remove:
            self.update_stats()

    def update_stats(self):
        """Обновляет статистику на экране"""
        self.vehicles_passed_label.setText(f"Проехало машин: {self.vehicles_passed}")
        self.vehicles_current_label.setText(f"Текущее количество: {len(self.vehicles)}")
        self.pedestrians_passed_label.setText(f"Перешло пешеходов: {self.pedestrians_passed}")

    def clear_simulation(self):
        """Очищает сцену от всех объектов"""
        self.stop_movement()

        # Выборочно удаляем элементы сцены вместо полной очистки
        for item in self.vehicle_items[:]:
            self.scene.removeItem(item)
        for item in self.pedestrian_items[:]:
            self.scene.removeItem(item)

        if hasattr(self, 'traffic_light_item') and self.traffic_light_item:
            self.scene.removeItem(self.traffic_light_item)

        # Удаляем элементы разметки (можно добавить, если храните ссылки на них)
        # Восстанавливаем разметку
        self.add_lane_markings()
        self.add_crosswalk()
        self.add_traffic_light()

        # Очищаем списки
        self.vehicle_count = 0
        self.pedestrian_count = 0
        self.vehicles = []
        self.vehicle_items = []
        self.pedestrians = []
        self.pedestrian_items = []
        self.vehicles_passed = 0
        self.pedestrians_passed = 0

        # Обновляем статистику
        self.update_stats()


class SettingsWidget(QGroupBox):
    """Окно настроек симуляции - панель управления параметрами"""

    def __init__(self, simulation_widget=None):
        super().__init__("Окно настроек симуляции")
        self.simulation_widget = simulation_widget
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Создаем таблицу для настроек
        self.settings_table = QTableWidget(10, 2)  # 10 строк, 2 столбца
        self.settings_table.setHorizontalHeaderLabels(["Параметр", "Значение"])

        # Заполняем таблицу демонстрационными данными
        settings_data = [
            ("Добавить автомобиль", "Кнопка"),
            ("Добавить грузовик", "Кнопка"),
            ("Добавить автобус", "Кнопка"),
            ("Добавить пешехода", "Кнопка"),
            ("Интервал генерации машин (мс)", "2000"),
            ("Интервал генерации пешеходов (мс)", "5000"),
            ("Включить генерацию машин", "Да"),
            ("Включить генерацию пешеходов", "Да"),
            ("Время зеленого для транспорта", "60"),
            ("Время зеленого для пешеходов", "30")
        ]

        for row, (param, value) in enumerate(settings_data):
            self.settings_table.setItem(row, 0, QTableWidgetItem(param))

            if param == "Добавить автомобиль":
                # Добавляем кнопку для легкового автомобиля
                button = QPushButton("Добавить")
                button.clicked.connect(self.add_car_to_simulation)
                self.settings_table.setCellWidget(row, 1, button)
            elif param == "Добавить грузовик":
                # Добавляем кнопку для грузовика
                button = QPushButton("Добавить")
                button.clicked.connect(self.add_truck_to_simulation)
                self.settings_table.setCellWidget(row, 1, button)
            elif param == "Добавить автобус":
                # Добавляем кнопку для автобуса
                button = QPushButton("Добавить")
                button.clicked.connect(self.add_bus_to_simulation)
                self.settings_table.setCellWidget(row, 1, button)
            elif param == "Добавить пешехода":
                # Добавляем кнопку для пешехода
                button = QPushButton("Добавить")
                button.clicked.connect(self.add_pedestrian_to_simulation)
                self.settings_table.setCellWidget(row, 1, button)
            elif param == "Интервал генерации машин (мс)":
                spinbox = QSpinBox()
                spinbox.setRange(500, 10000)
                spinbox.setValue(2000)
                spinbox.valueChanged.connect(self.update_vehicle_interval)
                self.settings_table.setCellWidget(row, 1, spinbox)
            elif param == "Интервал генерации пешеходов (мс)":
                spinbox = QSpinBox()
                spinbox.setRange(1000, 15000)
                spinbox.setValue(5000)
                spinbox.valueChanged.connect(self.update_pedestrian_interval)
                self.settings_table.setCellWidget(row, 1, spinbox)
            elif param == "Включить генерацию машин":
                button = QPushButton("Выключить")
                button.setCheckable(True)
                button.setChecked(True)
                button.clicked.connect(self.toggle_vehicle_generation)
                self.settings_table.setCellWidget(row, 1, button)
            elif param == "Включить генерацию пешеходов":
                button = QPushButton("Выключить")
                button.setCheckable(True)
                button.setChecked(True)
                button.clicked.connect(self.toggle_pedestrian_generation)
                self.settings_table.setCellWidget(row, 1, button)
            elif param == "Время зеленого для транспорта":
                spinbox = QSpinBox()
                spinbox.setRange(10, 200)
                spinbox.setValue(60)
                spinbox.valueChanged.connect(self.update_vehicle_green_time)
                self.settings_table.setCellWidget(row, 1, spinbox)
            elif param == "Время зеленого для пешеходов":
                spinbox = QSpinBox()
                spinbox.setRange(10, 200)
                spinbox.setValue(30)
                spinbox.valueChanged.connect(self.update_pedestrian_green_time)
                self.settings_table.setCellWidget(row, 1, spinbox)
            else:
                self.settings_table.setItem(row, 1, QTableWidgetItem(value))

        # Настраиваем внешний вид таблицы
        self.settings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.settings_table.verticalHeader().setVisible(False)

        layout.addWidget(self.settings_table)
        self.setLayout(layout)

    def add_car_to_simulation(self):
        """Метод для добавления легкового автомобиля в симуляцию"""
        if self.simulation_widget:
            self.simulation_widget.add_car()

    def add_truck_to_simulation(self):
        """Метод для добавления грузовика в симуляцию"""
        if self.simulation_widget:
            self.simulation_widget.add_truck()

    def add_bus_to_simulation(self):
        """Метод для добавления автобуса в симуляцию"""
        if self.simulation_widget:
            self.simulation_widget.add_bus()

    def add_pedestrian_to_simulation(self):
        """Метод для добавления пешехода в симуляцию"""
        if self.simulation_widget:
            self.simulation_widget.add_pedestrian()

    def update_vehicle_interval(self, value):
        """Обновляет интервал генерации машин"""
        if self.simulation_widget:
            self.simulation_widget.vehicle_generator_timer.setInterval(value)

    def update_pedestrian_interval(self, value):
        """Обновляет интервал генерации пешеходов"""
        if self.simulation_widget:
            self.simulation_widget.pedestrian_generator_timer.setInterval(value)

    def toggle_vehicle_generation(self):
        """Включает/выключает генерацию машин"""
        button = self.sender()
        if self.simulation_widget:
            if button.isChecked():
                self.simulation_widget.vehicle_generator_timer.start()
                button.setText("Выключить")
            else:
                self.simulation_widget.vehicle_generator_timer.stop()
                button.setText("Включить")

    def toggle_pedestrian_generation(self):
        """Включает/выключает генерацию пешеходов"""
        button = self.sender()
        if self.simulation_widget:
            if button.isChecked():
                self.simulation_widget.pedestrian_generator_timer.start()
                button.setText("Выключить")
            else:
                self.simulation_widget.pedestrian_generator_timer.stop()
                button.setText("Включить")

    def update_vehicle_green_time(self, value):
        """Обновляет время зеленого для транспорта"""
        if self.simulation_widget:
            self.simulation_widget.traffic_light.green_time = value
            self.simulation_widget.traffic_light.cycle_time = value + self.simulation_widget.traffic_light.yellow_time + self.simulation_widget.traffic_light.pedestrian_time

    def update_pedestrian_green_time(self, value):
        """Обновляет время зеленого для пешеходов"""
        if self.simulation_widget:
            self.simulation_widget.traffic_light.pedestrian_time = value
            self.simulation_widget.traffic_light.cycle_time = self.simulation_widget.traffic_light.green_time + self.simulation_widget.traffic_light.yellow_time + value


class AnalysisWidget(QGroupBox):
    """Окно анализа симуляции - отображение результатов и статистики"""

    def __init__(self):
        super().__init__("Окно анализа симуляции")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Создаем таблицу для анализа
        self.analysis_table = QTableWidget(5, 2)  # 5 строк, 2 столбца
        self.analysis_table.setHorizontalHeaderLabels(["Показатель", "Значение"])

        # Заполняем таблицу демонстрационными данными
        analysis_data = [
            ("Всего транспортных средств", "0"),
            ("Всего пешеходов", "0"),
            ("Средняя скорость ТС", "0"),
            ("Загруженность", "Низкая"),
            ("Статус", "Ожидание")
        ]

        for row, (indicator, value) in enumerate(analysis_data):
            self.analysis_table.setItem(row, 0, QTableWidgetItem(indicator))
            self.analysis_table.setItem(row, 1, QTableWidgetItem(value))

        # Настраиваем внешний вид таблицы
        self.analysis_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.analysis_table.verticalHeader().setVisible(False)

        layout.addWidget(self.analysis_table)
        self.setLayout(layout)

    def update_analysis(self, vehicle_count, pedestrian_count, average_speed, vehicles_passed, pedestrians_passed):
        """Метод для обновления результатов анализа"""
        self.analysis_table.setItem(0, 1, QTableWidgetItem(str(vehicle_count)))
        self.analysis_table.setItem(1, 1, QTableWidgetItem(str(pedestrian_count)))
        self.analysis_table.setItem(2, 1, QTableWidgetItem(f"{average_speed:.2f}"))

        # Обновляем загруженность на основе количества транспортных средств
        if vehicle_count == 0:
            congestion = "Низкая"
            status = "Ожидание"
        elif vehicle_count < 5:
            congestion = "Умеренная"
            status = "Активна"
        else:
            congestion = "Высокая"
            status = "Высокая нагрузка"

        self.analysis_table.setItem(3, 1, QTableWidgetItem(congestion))
        self.analysis_table.setItem(4, 1, QTableWidgetItem(
            f"{status} (Машин: {vehicles_passed}, Пешеходов: {pedestrians_passed})"))

    def clear_analysis(self):
        """Метод для очистки таблицы анализа"""
        self.analysis_table.clearContents()


class MainWindow(QMainWindow):
    """Главное окно приложения, объединяющее все виджеты"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Симуляционная система - Движение по одной полосе с пешеходным переходом")
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        self.setGeometry(screen_geometry)
        self.showMaximized()
        self.setup_ui()

        # Таймер для обновления анализа
        self.analysis_timer = QTimer()
        self.analysis_timer.timeout.connect(self.update_analysis)
        self.analysis_timer.start(1000)  # Обновление каждую секунду

    def setup_ui(self):
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной горизонтальный layout
        main_layout = QHBoxLayout(central_widget)

        # Создаем экземпляры виджетов
        self.simulation_widget = SimulationWidget()
        self.settings_widget = SettingsWidget(self.simulation_widget)  # Передаем ссылку на симуляцию
        self.analysis_widget = AnalysisWidget()

        # Правая колонка (настройки + анализ)
        right_column = QVBoxLayout()
        right_column.addWidget(self.settings_widget)
        right_column.addWidget(self.analysis_widget)

        # Добавляем все в основной layout
        main_layout.addWidget(self.simulation_widget, 2)  # Больший коэффициент растяжения
        main_layout.addLayout(right_column, 1)  # Меньший коэффициент

        # Настройка пропорций
        main_layout.setStretchFactor(self.simulation_widget, 2)
        main_layout.setStretchFactor(right_column, 1)

    def update_analysis(self):
        """Обновляет анализ на основе текущего состояния симуляции"""
        vehicle_count = len(self.simulation_widget.vehicles)
        pedestrian_count = len(self.simulation_widget.pedestrians)
        vehicles_passed = self.simulation_widget.vehicles_passed
        pedestrians_passed = self.simulation_widget.pedestrians_passed

        # Вычисляем среднюю скорость
        if vehicle_count > 0:
            total_speed = sum(item.speed for item in self.simulation_widget.vehicle_items)
            average_speed = total_speed / vehicle_count
        else:
            average_speed = 0

        self.analysis_widget.update_analysis(vehicle_count, pedestrian_count, average_speed, vehicles_passed,
                                             pedestrians_passed)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Устанавливаем стиль для лучшего отображения
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())