class Vehicle:
    def __init__(self, id, type):
        self.id = id
        self.type = type

class Pedestrian:
    def __init__(self, id):
        self.id = id

class Crosswalk:
    def __init__(self, id, position, width):
        self.id = id
        self.position = position
        self.width = width
        self.pedestrians = []

    def add_pedestrian(self, pedestrian):
        self.pedestrians.append(pedestrian)

    def remove_pedestrian(self, pedestrian):
        if pedestrian in self.pedestrians:
            self.pedestrians.remove(pedestrian)