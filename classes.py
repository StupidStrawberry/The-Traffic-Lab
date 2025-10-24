class TrafficLight:
    """Класс светофора"""

    def __init__(self, id, position, direction):
        self.id = id
        self.position = position  # (x, y) координаты
        self.direction = direction  # 'north', 'south', 'east', 'west'
        self.current_color = 'red'  # 'red', 'yellow', 'green'
        self.timer = 0
        self.phase_duration = {'red': 30, 'yellow': 3, 'green': 30}

    def change_color(self, color):
        self.current_color = color
        self.timer = 0

    def update(self, delta_time):
        self.timer += delta_time
        # Логика автоматической смены цвета по таймеру


class Lane:
    """Класс полосы движения"""

    def __init__(self, id, direction, capacity):
        self.id = id
        self.direction = direction
        self.capacity = capacity  # максимальное количество машин
        self.vehicles = []  # список машин на полосе
        self.traffic_light = None  # связанный светофор

    def add_vehicle(self, vehicle):
        if len(self.vehicles) < self.capacity:
            self.vehicles.append(vehicle)
            return True
        return False

    def remove_vehicle(self, vehicle):
        if vehicle in self.vehicles:
            self.vehicles.remove(vehicle)

    def get_queue_length(self):
        return len(self.vehicles)


class Vehicle:
    """Класс транспортного средства"""

    def __init__(self, id, vehicle_type='car'):
        self.id = id
        self.type = vehicle_type  # 'car', 'truck', 'bus'
        self.speed = 0
        self.position = (0, 0)
        self.current_lane = None
        self.waiting_time = 0
        self.max_speed = self.get_max_speed()

    def get_max_speed(self):
        speeds = {'car': 60, 'truck': 40, 'bus': 50}
        return speeds.get(self.type, 50)

    def move(self):
        # Логика движения вперед
        if self.can_move():
            self.speed = self.max_speed
        else:
            self.speed = 0
            self.waiting_time += 1

    def can_move(self):
        # Проверка, может ли машина двигаться (светофор зеленый, впереди нет пробки)
        if (self.current_lane and
                self.current_lane.traffic_light and
                self.current_lane.traffic_light.current_color == 'green'):
            return True
        return False



class Intersection:
    """Класс перекрестка"""

    def __init__(self, name):
        self.name = name
        self.lanes = []  # все полосы перекрестка
        self.traffic_lights = []  # все светофоры
        self.simulation_time = 0
        self.is_running = False

    def add_lane(self, lane):
        self.lanes.append(lane)

    def add_traffic_light(self, traffic_light):
        self.traffic_lights.append(traffic_light)

    def start_simulation(self):
        self.is_running = True
        self.simulation_time = 0

    def stop_simulation(self):
        self.is_running = False

    def update(self, delta_time):
        if self.is_running:
            self.simulation_time += delta_time
            # Обновление всех светофоров
            for traffic_light in self.traffic_lights:
                traffic_light.update(delta_time)

            # Обновление всех машин на всех полосах
            for lane in self.lanes:
                for vehicle in lane.vehicles:
                    vehicle.move()