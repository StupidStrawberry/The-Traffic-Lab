class SimulationStatistics:
    """Класс для управления статистикой симуляции"""

    def __init__(self):
        self.vehicles_passed = 0
        self.pedestrians_passed = 0
        self.vehicle_count = 0
        self.pedestrian_count = 0

    def vehicle_passed(self) -> None:
        self.vehicles_passed += 1

    def pedestrian_passed(self) -> None:
        self.pedestrians_passed += 1

    def vehicle_added(self) -> None:
        self.vehicle_count += 1

    def pedestrian_added(self) -> None:
        self.pedestrian_count += 1

    def vehicle_removed(self) -> None:
        self.vehicle_count -= 1

    def pedestrian_removed(self) -> None:
        self.pedestrian_count -= 1

    def reset(self) -> None:
        self.vehicles_passed = 0
        self.pedestrians_passed = 0
        self.vehicle_count = 0
        self.pedestrian_count = 0