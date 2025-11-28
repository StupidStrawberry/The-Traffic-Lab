# settings_widget.py
from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QHeaderView, QSpinBox, QComboBox
)
from PyQt6.QtCore import Qt

class SettingsWidget(QGroupBox):
    """Окно настроек симуляции - панель управления параметрами"""

    def __init__(self, simulation_widget=None):
        super().__init__("Окно настроек симуляции")
        self.simulation_widget = simulation_widget
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Создаем таблицу для настроек
        self.settings_table = QTableWidget(12, 2)  # Увеличили количество строк
        self.settings_table.setHorizontalHeaderLabels(["Параметр", "Значение"])

        # Заполняем таблицу данными
        settings_data = [
            ("Добавить автомобиль (горизонтальный)", "Кнопка"),
            ("Добавить автомобиль (вертикальный)", "Кнопка"),
            ("Добавить грузовик (горизонтальный)", "Кнопка"),
            ("Добавить грузовик (вертикальный)", "Кнопка"),
            ("Добавить автобус (горизонтальный)", "Кнопка"),
            ("Добавить автобус (вертикальный)", "Кнопка"),
            ("Добавить пешехода (вертикальный переход)", "Кнопка"),
            ("Добавить пешехода (горизонтальный переход)", "Кнопка"),
            ("Интервал генерации машин (мс)", "2000"),
            ("Интервал генерации пешеходов (мс)", "5000"),
            ("Время зеленого для транспорта", "60"),
            ("Время зеленого для пешеходов", "30")
        ]

        for row, (param, value) in enumerate(settings_data):
            self.settings_table.setItem(row, 0, QTableWidgetItem(param))

            if "автомобиль (горизонтальный)" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_car_to_simulation('horizontal'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "автомобиль (вертикальный)" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_car_to_simulation('vertical'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "грузовик (горизонтальный)" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_truck_to_simulation('horizontal'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "грузовик (вертикальный)" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_truck_to_simulation('vertical'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "автобус (горизонтальный)" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_bus_to_simulation('horizontal'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "автобус (вертикальный)" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_bus_to_simulation('vertical'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "пешехода (вертикальный переход)" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_pedestrian_to_simulation('vertical'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "пешехода (горизонтальный переход)" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_pedestrian_to_simulation('horizontal'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "Интервал генерации машин" in param:
                spinbox = QSpinBox()
                spinbox.setRange(500, 10000)
                spinbox.setValue(2000)
                spinbox.valueChanged.connect(self.update_vehicle_interval)
                self.settings_table.setCellWidget(row, 1, spinbox)
            elif "Интервал генерации пешеходов" in param:
                spinbox = QSpinBox()
                spinbox.setRange(1000, 15000)
                spinbox.setValue(5000)
                spinbox.valueChanged.connect(self.update_pedestrian_interval)
                self.settings_table.setCellWidget(row, 1, spinbox)
            elif "Время зеленого для транспорта" in param:
                spinbox = QSpinBox()
                spinbox.setRange(10, 200)
                spinbox.setValue(60)
                spinbox.valueChanged.connect(self.update_vehicle_green_time)
                self.settings_table.setCellWidget(row, 1, spinbox)
            elif "Время зеленого для пешеходов" in param:
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

    def add_car_to_simulation(self, direction='horizontal'):
        """Метод для добавления легкового автомобиля в симуляцию"""
        if self.simulation_widget:
            self.simulation_widget.add_car(direction)

    def add_truck_to_simulation(self, direction='horizontal'):
        """Метод для добавления грузовика в симуляцию"""
        if self.simulation_widget:
            self.simulation_widget.add_truck(direction)

    def add_bus_to_simulation(self, direction='horizontal'):
        """Метод для добавления автобуса в симуляцию"""
        if self.simulation_widget:
            self.simulation_widget.add_bus(direction)

    def add_pedestrian_to_simulation(self, direction='vertical'):
        """Метод для добавления пешехода в симуляцию"""
        if self.simulation_widget:
            self.simulation_widget.add_pedestrian(direction)

    def update_vehicle_interval(self, value):
        """Обновляет интервал генерации машин"""
        if self.simulation_widget:
            self.simulation_widget.vehicle_generator_timer.setInterval(value)

    def update_pedestrian_interval(self, value):
        """Обновляет интервал генерации пешеходов"""
        if self.simulation_widget:
            self.simulation_widget.pedestrian_generator_timer.setInterval(value)

    def update_vehicle_green_time(self, value):
        """Обновляет время зеленого для транспорта"""
        if self.simulation_widget:
            self.simulation_widget.config.VEHICLE_GREEN_TIME = value
            self.simulation_widget.config.TRAFFIC_LIGHT_CYCLE = (
                self.simulation_widget.config.VEHICLE_GREEN_TIME +
                self.simulation_widget.config.VEHICLE_YELLOW_TIME +
                self.simulation_widget.config.PEDESTRIAN_GREEN_TIME
            )

    def update_pedestrian_green_time(self, value):
        """Обновляет время зеленого для пешеходов"""
        if self.simulation_widget:
            self.simulation_widget.config.PEDESTRIAN_GREEN_TIME = value
            self.simulation_widget.config.TRAFFIC_LIGHT_CYCLE = (
                self.simulation_widget.config.VEHICLE_GREEN_TIME +
                self.simulation_widget.config.VEHICLE_YELLOW_TIME +
                self.simulation_widget.config.PEDESTRIAN_GREEN_TIME
            )