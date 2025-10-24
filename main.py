import sys
import random
from classes import Vehicle
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QGroupBox, QTextEdit, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem
)
from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen


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

    def move(self, vehicles):
        """Двигает транспортное средство по горизонтали с учетом других транспортных средств"""
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

        # Если столкновения нет, двигаем транспортное средство
        if not collision:
            self.setX(new_x)

            # Проверяем границы сцены
            scene_width = self.scene().width() if self.scene() else 800

            # Если транспортное средство вышло за правую границу, помечаем для удаления
            if new_x > scene_width:
                return True  # Помечаем для удаления

        return False  # Не удаляем


class SimulationWidget(QGroupBox):
    """Окно симулирующее - область для визуализации движущихся объектов"""

    def __init__(self):
        super().__init__("Окно симулирующее")
        self.vehicle_items = []  # Список для хранения графических представлений
        self.vehicles = []  # Список для хранения объектов транспортных средств
        self.timer = QTimer()  # Таймер для анимации
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Заголовок или информация о симуляции
        self.info_label = QLabel("Транспортные средства движутся по одной горизонтальной полосе и исчезают в конце")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Создаем графическую сцену и представление для отображения объектов
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 800, 200)  # Уменьшаем высоту сцены для одной полосы

        # Добавляем разметку одной горизонтальной полосы
        self.add_lane_markings()

        self.graphics_view = QGraphicsView(self.scene)
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)  # Сглаживание

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

        # Статистика
        stats_layout = QHBoxLayout()
        self.vehicles_passed_label = QLabel("Проехало машин: 0")
        self.vehicles_current_label = QLabel("Текущее количество: 0")

        stats_layout.addWidget(self.vehicles_passed_label)
        stats_layout.addWidget(self.vehicles_current_label)

        layout.addWidget(self.info_label)
        layout.addWidget(self.graphics_view)
        layout.addLayout(control_layout)
        layout.addLayout(stats_layout)
        self.setLayout(layout)

        # Счетчик для ID транспортных средств
        self.vehicle_count = 0
        self.vehicles_passed = 0  # Счетчик проехавших машин

        # Настраиваем таймер для обновления анимации
        self.timer.timeout.connect(self.update_movement)

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

        # Добавляем отметку о конце полосы
        end_line = QGraphicsRectItem(790, 80, 5, 40)
        #end_line.setBrush(QBrush(QColor(255, 0, 0)))
        #end_line.setPen(QPen(Qt.GlobalColor.red, 2))
        #self.scene.addItem(end_line)

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

    def stop_movement(self):
        """Останавливает движение транспортных средств"""
        if self.timer.isActive():
            self.timer.stop()

    def update_movement(self):
        """Обновляет позиции всех транспортных средств"""
        vehicles_to_remove = []

        for i, vehicle_item in enumerate(self.vehicle_items):
            should_remove = vehicle_item.move(self.vehicle_items)
            if should_remove:
                vehicles_to_remove.append(i)

        # Удаляем транспортные средства, которые достигли конца полосы
        # Удаляем в обратном порядке, чтобы индексы не сдвигались
        for i in sorted(vehicles_to_remove, reverse=True):
            # Удаляем графическое представление
            self.scene.removeItem(self.vehicle_items[i])
            # Удаляем из списков
            self.vehicle_items.pop(i)
            self.vehicles.pop(i)
            # Увеличиваем счетчик проехавших машин
            self.vehicles_passed += 1

        # Обновляем статистику, если были изменения
        if vehicles_to_remove:
            self.update_stats()

    def update_stats(self):
        """Обновляет статистику на экране"""
        self.vehicles_passed_label.setText(f"Проехало машин: {self.vehicles_passed}")
        self.vehicles_current_label.setText(f"Текущее количество: {len(self.vehicles)}")

    def clear_simulation(self):
        """Очищает сцену от всех объектов"""
        self.stop_movement()
        self.scene.clear()
        self.vehicle_count = 0
        self.vehicles = []
        self.vehicle_items = []
        self.vehicles_passed = 0
        # Восстанавливаем разметку полосы
        self.add_lane_markings()
        # Обновляем статистику
        self.update_stats()

    def update_simulation(self, data):
        """Метод для обработки данных симуляции"""
        # Если приходят данные, добавляем транспортное средство
        self.add_vehicle()

    def get_scene(self):
        """Возвращает графическую сцену для манипуляций"""
        return self.scene

    def get_graphics_view(self):
        """Возвращает графическое представление для настройки"""
        return self.graphics_view


class SettingsWidget(QGroupBox):
    """Окно настроек симуляции - панель управления параметрами"""

    def __init__(self, simulation_widget=None):
        super().__init__("Окно настроек симуляции")
        self.simulation_widget = simulation_widget
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Создаем таблицу для настроек
        self.settings_table = QTableWidget(7, 2)  # 7 строк, 2 столбца
        self.settings_table.setHorizontalHeaderLabels(["Параметр", "Значение"])

        # Заполняем таблицу демонстрационными данными
        settings_data = [
            ("Добавить автомобиль", "Кнопка"),
            ("Добавить грузовик", "Кнопка"),
            ("Добавить автобус", "Кнопка")
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

    def get_settings(self):
        """Метод для получения текущих настроек"""
        settings = {}
        for row in range(self.settings_table.rowCount()):
            param = self.settings_table.item(row, 0)
            value_widget = self.settings_table.cellWidget(row, 1)

            if param and not value_widget:  # Обычная ячейка с текстом
                value = self.settings_table.item(row, 1)
                if value:
                    settings[param.text()] = value.text()
            elif param and value_widget and isinstance(value_widget, QPushButton):
                # Для кнопки сохраняем специальное значение
                settings[param.text()] = "button_action"

        return settings


class AnalysisWidget(QGroupBox):
    """Окно анализа симуляции - отображение результатов и статистики"""

    def __init__(self):
        super().__init__("Окно анализа симуляции")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Создаем таблицу для анализа
        self.analysis_table = QTableWidget(4, 2)  # 4 строки, 2 столбца
        self.analysis_table.setHorizontalHeaderLabels(["Показатель", "Значение"])

        # Заполняем таблицу демонстрационными данными
        analysis_data = [
            ("Всего транспортных средств", "0"),
            ("Средняя скорость", "0"),
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

    def update_analysis(self, vehicle_count, average_speed, vehicles_passed):
        """Метод для обновления результатов анализа"""
        self.analysis_table.setItem(0, 1, QTableWidgetItem(str(vehicle_count)))
        self.analysis_table.setItem(1, 1, QTableWidgetItem(f"{average_speed:.2f}"))

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

        self.analysis_table.setItem(2, 1, QTableWidgetItem(congestion))
        self.analysis_table.setItem(3, 1, QTableWidgetItem(f"{status} (Проехало: {vehicles_passed})"))

    def clear_analysis(self):
        """Метод для очистки таблицы анализа"""
        self.analysis_table.clearContents()


class MainWindow(QMainWindow):
    """Главное окно приложения, объединяющее все виджеты"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Симуляционная система - Движение по одной полосе")
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
        vehicles_passed = self.simulation_widget.vehicles_passed

        # Вычисляем среднюю скорость
        if vehicle_count > 0:
            total_speed = sum(item.speed for item in self.simulation_widget.vehicle_items)
            average_speed = total_speed / vehicle_count
        else:
            average_speed = 0

        self.analysis_widget.update_analysis(vehicle_count, average_speed, vehicles_passed)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Устанавливаем стиль для лучшего отображения
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())