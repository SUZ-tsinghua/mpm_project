import taichi as ti

class BaseGeometry:

    def __init__(self, init_vel=None):
        self.volume = None
        
        if init_vel == None:
            self.init_vel = [0.0, 0.0, 0.0]
        else:
            self.init_vel = init_vel

    @ti.func
    def uniform_sample(self):
        raise NotImplementedError