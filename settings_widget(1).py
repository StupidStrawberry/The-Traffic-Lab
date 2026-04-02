from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt, QSignalBlocker


class SettingsWidget(QGroupBox):
    """Панель управления симуляцией и визуальный редактор объектов."""

    def __init__(self, simulation_widget=None):
        super().__init__("Окно настроек симуляции")
        self.simulation_widget = simulation_widget
        self._editor_sync_in_progress = False
        self.setup_ui()

        if self.simulation_widget is not None:
            self.simulation_widget.set_editor_callback(self.refresh_editor_panel)

        self.refresh_editor_list()
        self.refresh_editor_panel(
            self.simulation_widget.selected_edit_item if self.simulation_widget is not None else None
        )
        self.generate_config_text()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.settings_table = QTableWidget(16, 2)
        self.settings_table.setHorizontalHeaderLabels(["Параметр", "Значение"])

        settings_data = [
            ("Машины вправо - Автомобиль", "Кнопка"),
            ("Машины вправо - Грузовик", "Кнопка"),
            ("Машины вправо - Автобус", "Кнопка"),
            ("Машины влево - Автомобиль", "Кнопка"),
            ("Машины влево - Грузовик", "Кнопка"),
            ("Машины влево - Автобус", "Кнопка"),
            ("Машины вниз - Автомобиль", "Кнопка"),
            ("Машины вниз - Грузовик", "Кнопка"),
            ("Машины вниз - Автобус", "Кнопка"),
            ("Машины вверх - Автомобиль", "Кнопка"),
            ("Машины вверх - Грузовик", "Кнопка"),
            ("Машины вверх - Автобус", "Кнопка"),
            ("Добавить пешехода (вертикальный переход)", "Кнопка"),
            ("Добавить пешехода (горизонтальный переход)", "Кнопка"),
            ("Интервал генерации машин (мс)", "2000"),
            ("Интервал генерации пешеходов (мс)", "5000"),
        ]

        for row, (param, value) in enumerate(settings_data):
            self.settings_table.setItem(row, 0, QTableWidgetItem(param))

            if "Машины вправо - Автомобиль" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_car_to_simulation('horizontal_right'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "Машины вправо - Грузовик" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_truck_to_simulation('horizontal_right'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "Машины вправо - Автобус" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_bus_to_simulation('horizontal_right'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "Машины влево - Автомобиль" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_car_to_simulation('horizontal_left'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "Машины влево - Грузовик" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_truck_to_simulation('horizontal_left'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "Машины влево - Автобус" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_bus_to_simulation('horizontal_left'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "Машины вниз - Автомобиль" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_car_to_simulation('vertical_down'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "Машины вниз - Грузовик" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_truck_to_simulation('vertical_down'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "Машины вниз - Автобус" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_bus_to_simulation('vertical_down'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "Машины вверх - Автомобиль" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_car_to_simulation('vertical_up'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "Машины вверх - Грузовик" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_truck_to_simulation('vertical_up'))
                self.settings_table.setCellWidget(row, 1, button)
            elif "Машины вверх - Автобус" in param:
                button = QPushButton("Добавить")
                button.clicked.connect(lambda: self.add_bus_to_simulation('vertical_up'))
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
            else:
                self.settings_table.setItem(row, 1, QTableWidgetItem(value))

        self.settings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.settings_table.verticalHeader().setVisible(False)
        layout.addWidget(self.settings_table)

        self.editor_group = QGroupBox("Редактор объектов на сцене")
        editor_layout = QVBoxLayout(self.editor_group)

        self.edit_mode_checkbox = QCheckBox("Включить режим редактирования")
        self.edit_mode_checkbox.toggled.connect(self.on_edit_mode_toggled)
        editor_layout.addWidget(self.edit_mode_checkbox)

        editor_hint = QLabel(
            "Можно редактировать светофоры и точки появления машин. "
            "Выбери объект в списке или кликни по нему на сцене, затем перетаскивай мышью "
            "или меняй координаты справа."
        )
        editor_hint.setWordWrap(True)
        editor_layout.addWidget(editor_hint)

        self.object_list = QListWidget()
        self.object_list.currentRowChanged.connect(self.on_editor_list_changed)
        editor_layout.addWidget(self.object_list)

        form_widget = QWidget()
        form_layout = QGridLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)

        self.x_spin = QDoubleSpinBox()
        self.x_spin.setRange(-10000, 10000)
        self.x_spin.setDecimals(1)
        self.x_spin.setSingleStep(1.0)
        self.x_spin.valueChanged.connect(self.apply_selected_item_changes)

        self.y_spin = QDoubleSpinBox()
        self.y_spin.setRange(-10000, 10000)
        self.y_spin.setDecimals(1)
        self.y_spin.setSingleStep(1.0)
        self.y_spin.valueChanged.connect(self.apply_selected_item_changes)

        self.rotation_spin = QDoubleSpinBox()
        self.rotation_spin.setRange(-360, 360)
        self.rotation_spin.setDecimals(1)
        self.rotation_spin.setSingleStep(5.0)
        self.rotation_spin.valueChanged.connect(self.apply_selected_item_changes)

        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.01, 10.0)
        self.scale_spin.setDecimals(3)
        self.scale_spin.setSingleStep(0.01)
        self.scale_spin.valueChanged.connect(self.apply_selected_item_changes)

        form_layout.addWidget(QLabel("X"), 0, 0)
        form_layout.addWidget(self.x_spin, 0, 1)
        form_layout.addWidget(QLabel("Y"), 1, 0)
        form_layout.addWidget(self.y_spin, 1, 1)
        form_layout.addWidget(QLabel("rotation"), 2, 0)
        form_layout.addWidget(self.rotation_spin, 2, 1)
        form_layout.addWidget(QLabel("scale"), 3, 0)
        form_layout.addWidget(self.scale_spin, 3, 1)
        editor_layout.addWidget(form_widget)

        self.generate_button = QPushButton("Сгенерировать строки для config.py")
        self.generate_button.clicked.connect(self.generate_config_text)
        editor_layout.addWidget(self.generate_button)

        self.copy_button = QPushButton("Копировать в буфер")
        self.copy_button.clicked.connect(self.copy_config_text)
        editor_layout.addWidget(self.copy_button)

        self.config_preview = QPlainTextEdit()
        self.config_preview.setPlaceholderText("Здесь появятся готовые строки для вставки в config.py")
        self.config_preview.setMinimumHeight(180)
        editor_layout.addWidget(self.config_preview)

        layout.addWidget(self.editor_group)
        self.setLayout(layout)
        self.set_editor_controls_enabled(False)

    def refresh_editor_list(self):
        current_key = self.get_current_editor_key()
        blocker = QSignalBlocker(self.object_list)
        self.object_list.clear()

        if self.simulation_widget is not None:
            for item_data in self.simulation_widget.get_traffic_light_editor_items():
                item = QListWidgetItem(item_data['label'])
                item.setData(Qt.ItemDataRole.UserRole, item_data['key'])
                self.object_list.addItem(item)

        del blocker

        if current_key is not None:
            self.set_current_editor_key(current_key)
        elif self.object_list.count() > 0:
            self.set_current_editor_key(self.object_list.item(0).data(Qt.ItemDataRole.UserRole))

    def set_editor_controls_enabled(self, enabled: bool, allow_rotation: bool = True, allow_scale: bool = True):
        self.object_list.setEnabled(enabled)
        self.x_spin.setEnabled(enabled)
        self.y_spin.setEnabled(enabled)
        self.rotation_spin.setEnabled(enabled and allow_rotation)
        self.scale_spin.setEnabled(enabled and allow_scale)
        self.generate_button.setEnabled(True)
        self.copy_button.setEnabled(True)

    def get_current_editor_key(self):
        current_item = self.object_list.currentItem()
        if current_item is None:
            return None
        return current_item.data(Qt.ItemDataRole.UserRole)

    def set_current_editor_key(self, key):
        blocker = QSignalBlocker(self.object_list)
        if key is None:
            self.object_list.setCurrentRow(-1)
            del blocker
            return

        for row in range(self.object_list.count()):
            item = self.object_list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == key:
                self.object_list.setCurrentRow(row)
                break
        del blocker

    def on_edit_mode_toggled(self, checked):
        if self.simulation_widget is None:
            return
        self._editor_sync_in_progress = True
        try:
            self.refresh_editor_list()
            self.simulation_widget.set_editor_enabled(checked)
        finally:
            self._editor_sync_in_progress = False

        self.refresh_editor_panel(self.simulation_widget.selected_edit_item)

    def on_editor_list_changed(self, current_row):
        if self._editor_sync_in_progress or self.simulation_widget is None:
            return

        current_item = self.object_list.item(current_row) if current_row >= 0 else None
        if current_item is None:
            self.set_editor_controls_enabled(False)
            return

        key = current_item.data(Qt.ItemDataRole.UserRole)
        self.simulation_widget.select_edit_item_by_name(key)

    def _set_spin_values_from_state(self, state):
        blockers = [
            QSignalBlocker(self.x_spin),
            QSignalBlocker(self.y_spin),
            QSignalBlocker(self.rotation_spin),
            QSignalBlocker(self.scale_spin),
        ]
        self.x_spin.setValue(state['x'])
        self.y_spin.setValue(state['y'])
        self.rotation_spin.setValue(state['rotation'])
        self.scale_spin.setValue(state['scale'])
        del blockers

    def refresh_editor_panel(self, selected_item):
        self._editor_sync_in_progress = True
        try:
            self.refresh_editor_list()

            if selected_item is None:
                self.set_current_editor_key(None)
                self.set_editor_controls_enabled(False)
                self.generate_config_text()
                return

            state = self.simulation_widget.get_editor_item_state(selected_item.name) if self.simulation_widget else None
            if state is None:
                self.set_editor_controls_enabled(False)
                self.generate_config_text()
                return

            self.set_current_editor_key(selected_item.name)
            self._set_spin_values_from_state(state)
            self.set_editor_controls_enabled(
                self.edit_mode_checkbox.isChecked(),
                allow_rotation=state['supports_rotation'],
                allow_scale=state['supports_scale'],
            )
            self.generate_config_text()
        finally:
            self._editor_sync_in_progress = False

    def apply_selected_item_changes(self):
        if self._editor_sync_in_progress or self.simulation_widget is None:
            return

        key = self.get_current_editor_key()
        if not key:
            return

        state = self.simulation_widget.get_editor_item_state(key)
        if state is None:
            return

        rotation_value = self.rotation_spin.value() if state['supports_rotation'] else None
        scale_value = self.scale_spin.value() if state['supports_scale'] else None

        self.simulation_widget.update_selected_item_geometry(
            x=self.x_spin.value(),
            y=self.y_spin.value(),
            rotation=rotation_value,
            scale=scale_value,
        )
        self.generate_config_text()

    def generate_config_text(self):
        if self.simulation_widget is None:
            self.config_preview.clear()
            return
        self.config_preview.setPlainText(self.simulation_widget.get_config_export_text())

    def copy_config_text(self):
        QApplication.clipboard().setText(self.config_preview.toPlainText())

    def add_car_to_simulation(self, direction='horizontal'):
        if self.simulation_widget:
            self.simulation_widget.add_car(direction)

    def add_truck_to_simulation(self, direction='horizontal'):
        if self.simulation_widget:
            self.simulation_widget.add_truck(direction)

    def add_bus_to_simulation(self, direction='horizontal'):
        if self.simulation_widget:
            self.simulation_widget.add_bus(direction)

    def add_pedestrian_to_simulation(self, direction='vertical'):
        if self.simulation_widget:
            self.simulation_widget.add_pedestrian(direction)

    def update_vehicle_interval(self, value):
        if self.simulation_widget:
            self.simulation_widget.vehicle_generator_timer.setInterval(value)

    def update_pedestrian_interval(self, value):
        if self.simulation_widget:
            self.simulation_widget.pedestrian_generator_timer.setInterval(value)

    def update_vehicle_green_time(self, value):
        if self.simulation_widget:
            self.simulation_widget.config.VEHICLE_GREEN_TIME = value
            self.simulation_widget.config.TRAFFIC_LIGHT_CYCLE = (
                self.simulation_widget.config.VEHICLE_GREEN_TIME
                + self.simulation_widget.config.VEHICLE_YELLOW_TIME
                + self.simulation_widget.config.PEDESTRIAN_GREEN_TIME
            )

    def update_pedestrian_green_time(self, value):
        if self.simulation_widget:
            self.simulation_widget.config.PEDESTRIAN_GREEN_TIME = value
            self.simulation_widget.config.TRAFFIC_LIGHT_CYCLE = (
                self.simulation_widget.config.VEHICLE_GREEN_TIME
                + self.simulation_widget.config.VEHICLE_YELLOW_TIME
                + self.simulation_widget.config.PEDESTRIAN_GREEN_TIME
            )
