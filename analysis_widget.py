# analysis_widget.py
from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView

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