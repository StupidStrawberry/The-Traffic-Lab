class Vehicle:
    def __init__(self, id, type, direction):
        self.id = id
        self.type = type
        self.direction = direction  # 'horizontal_right', 'horizontal_left', 'vertical_down', 'vertical_up'

class Pedestrian:
    def __init__(self, id, direction):
        self.id = id
        self.direction = direction  # 'vertical' or 'horizontal'

class Crosswalk:
    def __init__(self, id, position, width, direction):
        self.id = id
        self.position = position
        self.width = width
        self.direction = direction
        self.pedestrians = []

    def add_pedestrian(self, pedestrian):
        self.pedestrians.append(pedestrian)

    def remove_pedestrian(self, pedestrian):
        if pedestrian in self.pedestrians:
            self.pedestrians.remove(pedestrian)