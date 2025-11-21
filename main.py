import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import QTimer

from simulation_widget import SimulationWidget
from settings_widget import SettingsWidget
from analysis_widget import AnalysisWidget


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

        self.analysis_timer = QTimer()
        self.analysis_timer.timeout.connect(self.update_analysis)
        self.analysis_timer.start(1000)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        self.simulation_widget = SimulationWidget()
        self.settings_widget = SettingsWidget(self.simulation_widget)
        self.analysis_widget = AnalysisWidget()

        right_column = QVBoxLayout()
        right_column.addWidget(self.settings_widget)
        right_column.addWidget(self.analysis_widget)

        main_layout.addWidget(self.simulation_widget, 2)
        main_layout.addLayout(right_column, 1)

        main_layout.setStretchFactor(self.simulation_widget, 2)
        main_layout.setStretchFactor(right_column, 1)

    def update_analysis(self):
        """Обновляет анализ на основе текущего состояния симуляции"""
        vehicle_count = self.simulation_widget.statistics.vehicle_count
        pedestrian_count = self.simulation_widget.statistics.pedestrian_count
        vehicles_passed = self.simulation_widget.statistics.vehicles_passed
        pedestrians_passed = self.simulation_widget.statistics.pedestrians_passed

        if vehicle_count > 0:
            total_speed = sum(item.speed for item in self.simulation_widget.vehicle_items)
            average_speed = total_speed / vehicle_count
        else:
            average_speed = 0

        self.analysis_widget.update_analysis(vehicle_count, pedestrian_count, average_speed,
                                           vehicles_passed, pedestrians_passed)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())