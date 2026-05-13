from PyQt6.QtCore import Qt, QSignalBlocker
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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class SettingsWidget(QGroupBox):
    """Панель управления: быстрые действия, визуальный редактор и runtime-параметры."""

    def __init__(self, simulation_widget=None):
        super().__init__('Окно настроек симуляции')
        self.simulation_widget = simulation_widget
        self._editor_sync_in_progress = False
        self._config_sync_in_progress = False
        self._known_editor_revision = -1
        self._config_widgets = {}

        self.setup_ui()

        if self.simulation_widget is not None:
            self.simulation_widget.set_editor_callback(self.refresh_editor_panel)

        self.refresh_editor_list(force=True)
        self.build_runtime_config_table(force=True)
        self.refresh_runtime_config_controls()
        initial_item = self.simulation_widget.selected_edit_item if self.simulation_widget is not None else None
        self.refresh_editor_panel(initial_item)
        self.generate_config_text()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.tabs.addTab(self._build_actions_tab(), 'Быстрые действия')
        self.tabs.addTab(self._build_editor_tab(), 'Редактор сцены')
        self.tabs.addTab(self._build_params_tab(), 'Параметры')

        layout.addWidget(self.tabs)
        self.setLayout(layout)
        self.set_editor_controls_enabled(False, has_selection=False)

    def _build_actions_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.actions_table = QTableWidget(14, 2)
        self.actions_table.setHorizontalHeaderLabels(['Параметр', 'Действие'])
        rows = [
            ('Машины вправо - Автомобиль', lambda: self.add_car_to_simulation('horizontal_right')),
            ('Машины вправо - Грузовик', lambda: self.add_truck_to_simulation('horizontal_right')),
            ('Машины вправо - Автобус', lambda: self.add_bus_to_simulation('horizontal_right')),
            ('Машины влево - Автомобиль', lambda: self.add_car_to_simulation('horizontal_left')),
            ('Машины влево - Грузовик', lambda: self.add_truck_to_simulation('horizontal_left')),
            ('Машины влево - Автобус', lambda: self.add_bus_to_simulation('horizontal_left')),
            ('Машины вниз - Автомобиль', lambda: self.add_car_to_simulation('vertical_down')),
            ('Машины вниз - Грузовик', lambda: self.add_truck_to_simulation('vertical_down')),
            ('Машины вниз - Автобус', lambda: self.add_bus_to_simulation('vertical_down')),
            ('Машины вверх - Автомобиль', lambda: self.add_car_to_simulation('vertical_up')),
            ('Машины вверх - Грузовик', lambda: self.add_truck_to_simulation('vertical_up')),
            ('Машины вверх - Автобус', lambda: self.add_bus_to_simulation('vertical_up')),
            ('Добавить пешехода (вертикальный переход)', lambda: self.add_pedestrian_to_simulation('vertical')),
            ('Добавить пешехода (горизонтальный переход)', lambda: self.add_pedestrian_to_simulation('horizontal')),
        ]

        for row, (label, handler) in enumerate(rows):
            self.actions_table.setItem(row, 0, QTableWidgetItem(label))
            button = QPushButton('Добавить')
            button.clicked.connect(handler)
            self.actions_table.setCellWidget(row, 1, button)

        self.actions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.actions_table.verticalHeader().setVisible(False)
        layout.addWidget(self.actions_table)

        hint = QLabel(
            'Скорости, интервалы, размеры, тайминги светофоров и прочие параметры теперь меняются на вкладке “Параметры”.'
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        return tab

    def _build_editor_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.edit_mode_checkbox = QCheckBox('Включить режим редактирования')
        self.edit_mode_checkbox.toggled.connect(self.on_edit_mode_toggled)
        layout.addWidget(self.edit_mode_checkbox)

        hint = QLabel(
            'Здесь можно выбирать светофоры, точки старта машин, точки поворота, пешеходные переходы '
            'и точки появления пешеходов. Перетаскивай объект мышью по сцене или точно правь координаты. '
            'Кнопка “Сохранить в config.py” записывает текущие изменения в файл даже во время работы симуляции.'
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.object_list = QListWidget()
        self.object_list.currentRowChanged.connect(self.on_editor_list_changed)
        layout.addWidget(self.object_list)

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

        form_layout.addWidget(QLabel('X'), 0, 0)
        form_layout.addWidget(self.x_spin, 0, 1)
        form_layout.addWidget(QLabel('Y'), 1, 0)
        form_layout.addWidget(self.y_spin, 1, 1)
        form_layout.addWidget(QLabel('rotation'), 2, 0)
        form_layout.addWidget(self.rotation_spin, 2, 1)
        form_layout.addWidget(QLabel('scale'), 3, 0)
        form_layout.addWidget(self.scale_spin, 3, 1)
        layout.addWidget(form_widget)

        self.generate_button = QPushButton('Сгенерировать строки для config.py')
        self.generate_button.clicked.connect(self.generate_config_text)
        layout.addWidget(self.generate_button)

        self.copy_button = QPushButton('Копировать в буфер')
        self.copy_button.clicked.connect(self.copy_config_text)
        layout.addWidget(self.copy_button)

        self.save_button = QPushButton('Сохранить в config.py')
        self.save_button.clicked.connect(self.save_config_file)
        layout.addWidget(self.save_button)

        self.save_status_label = QLabel('')
        self.save_status_label.setWordWrap(True)
        layout.addWidget(self.save_status_label)

        self.config_preview = QPlainTextEdit()
        self.config_preview.setPlaceholderText('Здесь появятся готовые строки для вставки в config.py')
        self.config_preview.setMinimumHeight(220)
        layout.addWidget(self.config_preview)

        return tab

    def _build_params_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        hint = QLabel(
            'Можно менять почти все числовые и логические параметры, которые уже используются в симуляции: '
            'скорости, интервалы, размеры, стоп-линии, спавн пешеходов, повороты, геометрию и т.п. '
            'Часть изменений начинает действовать сразу и для уже существующих объектов.'
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.config_table = QTableWidget(0, 2)
        self.config_table.setHorizontalHeaderLabels(['Параметр', 'Значение'])
        self.config_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.config_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.config_table.verticalHeader().setVisible(False)
        layout.addWidget(self.config_table)

        return tab

    def build_runtime_config_table(self, force=False):
        if self.simulation_widget is None:
            return
        if self._config_widgets and not force:
            return

        specs = self.simulation_widget.get_runtime_config_specs()
        self._config_widgets = {}
        self.config_table.setRowCount(len(specs))

        for row, spec in enumerate(specs):
            self.config_table.setItem(row, 0, QTableWidgetItem(spec['label']))

            if spec['kind'] == 'bool':
                widget = QCheckBox()
                widget.toggled.connect(lambda checked, key=spec['name']: self.on_runtime_config_value_changed(key, checked))
            elif spec['kind'] == 'float':
                widget = QDoubleSpinBox()
                widget.setDecimals(spec.get('decimals', 3))
                widget.setRange(spec.get('min', -100000.0), spec.get('max', 100000.0))
                widget.setSingleStep(spec.get('step', 0.1))
                widget.valueChanged.connect(lambda value, key=spec['name']: self.on_runtime_config_value_changed(key, value))
            else:
                widget = QSpinBox()
                widget.setRange(spec.get('min', -100000), spec.get('max', 100000))
                widget.setSingleStep(spec.get('step', 1))
                widget.valueChanged.connect(lambda value, key=spec['name']: self.on_runtime_config_value_changed(key, value))

            self.config_table.setCellWidget(row, 1, widget)
            self._config_widgets[spec['name']] = widget

    def refresh_runtime_config_controls(self):
        if self.simulation_widget is None:
            return
        if not self._config_widgets:
            self.build_runtime_config_table(force=True)

        self._config_sync_in_progress = True
        try:
            for name, widget in self._config_widgets.items():
                value = getattr(self.simulation_widget.config, name)
                blocker = QSignalBlocker(widget)
                if isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
                else:
                    widget.setValue(value)
                del blocker
        finally:
            self._config_sync_in_progress = False

    def refresh_editor_list(self, force=False):
        if self.simulation_widget is None:
            self.object_list.clear()
            self._known_editor_revision = -1
            return

        current_revision = self.simulation_widget.get_editor_revision()
        if not force and current_revision == self._known_editor_revision:
            return

        current_key = self.get_current_editor_key()
        descriptors = self.simulation_widget.get_editor_item_descriptors()
        blocker = QSignalBlocker(self.object_list)
        self.object_list.clear()
        for descriptor in descriptors:
            item = QListWidgetItem(descriptor['label'])
            item.setData(Qt.ItemDataRole.UserRole, descriptor['key'])
            self.object_list.addItem(item)
        del blocker

        self._known_editor_revision = current_revision
        if current_key is not None:
            self.set_current_editor_key(current_key)
        elif self.simulation_widget.selected_edit_item is not None:
            self.set_current_editor_key(self.simulation_widget.selected_edit_item.name)
        elif self.object_list.count() > 0:
            self.set_current_editor_key(self.object_list.item(0).data(Qt.ItemDataRole.UserRole))

    def set_editor_controls_enabled(self, enabled: bool, allow_rotation: bool = True, allow_scale: bool = True, has_selection: bool = True):
        self.object_list.setEnabled(enabled)
        self.x_spin.setEnabled(enabled and has_selection)
        self.y_spin.setEnabled(enabled and has_selection)
        self.rotation_spin.setEnabled(enabled and has_selection and allow_rotation)
        self.scale_spin.setEnabled(enabled and has_selection and allow_scale)
        self.generate_button.setEnabled(True)
        self.copy_button.setEnabled(True)
        if hasattr(self, 'save_button'):
            self.save_button.setEnabled(True)

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
            self.refresh_editor_list(force=True)
            self.simulation_widget.set_editor_enabled(checked)
        finally:
            self._editor_sync_in_progress = False

        self.refresh_editor_panel(self.simulation_widget.selected_edit_item)

    def on_editor_list_changed(self, current_row):
        if self._editor_sync_in_progress or self.simulation_widget is None:
            return

        current_item = self.object_list.item(current_row) if current_row >= 0 else None
        if current_item is None:
            self.set_editor_controls_enabled(self.edit_mode_checkbox.isChecked(), has_selection=False)
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
        self.refresh_editor_list()

        self._editor_sync_in_progress = True
        try:
            if self.simulation_widget is None:
                self.set_editor_controls_enabled(False, has_selection=False)
                self.generate_config_text()
                return

            if selected_item is None:
                self.set_current_editor_key(None)
                self.set_editor_controls_enabled(self.edit_mode_checkbox.isChecked(), has_selection=False)
                self.generate_config_text()
                return

            state = self.simulation_widget.get_editor_item_state(selected_item.name)
            if state is None:
                self.set_current_editor_key(None)
                self.set_editor_controls_enabled(self.edit_mode_checkbox.isChecked(), has_selection=False)
                self.generate_config_text()
                return

            self.set_current_editor_key(selected_item.name)
            self._set_spin_values_from_state(state)
            self.set_editor_controls_enabled(
                self.edit_mode_checkbox.isChecked(),
                allow_rotation=state['supports_rotation'],
                allow_scale=state['supports_scale'],
                has_selection=True,
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

        self.simulation_widget.select_edit_item_by_name(key)
        self.simulation_widget.update_selected_item_geometry(
            x=self.x_spin.value(),
            y=self.y_spin.value(),
            rotation=rotation_value,
            scale=scale_value,
        )
        self.generate_config_text()

    def on_runtime_config_value_changed(self, key, value):
        if self._config_sync_in_progress or self.simulation_widget is None:
            return

        self.simulation_widget.apply_config_value(key, value)
        self.generate_config_text()
        self.refresh_editor_panel(self.simulation_widget.selected_edit_item)

    def generate_config_text(self):
        if self.simulation_widget is None:
            self.config_preview.clear()
            return
        self.config_preview.setPlainText(self.simulation_widget.get_config_export_text())

    def copy_config_text(self):
        QApplication.clipboard().setText(self.config_preview.toPlainText())

    def save_config_file(self):
        if self.simulation_widget is None:
            return
        try:
            changed, path = self.simulation_widget.save_config_to_file()
            self.generate_config_text()
            self.save_status_label.setText(f'Сохранено в {path}. Обновлено строк: {changed}')
        except Exception as exc:
            self.save_status_label.setText(f'Не удалось сохранить config.py: {exc}')

    def add_car_to_simulation(self, direction='horizontal_right'):
        if self.simulation_widget:
            self.simulation_widget.add_car(direction)

    def add_truck_to_simulation(self, direction='horizontal_right'):
        if self.simulation_widget:
            self.simulation_widget.add_truck(direction)

    def add_bus_to_simulation(self, direction='horizontal_right'):
        if self.simulation_widget:
            self.simulation_widget.add_bus(direction)

    def add_pedestrian_to_simulation(self, direction='vertical'):
        if self.simulation_widget:
            self.simulation_widget.add_pedestrian(direction)
