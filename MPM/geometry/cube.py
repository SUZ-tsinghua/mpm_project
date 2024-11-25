import taichi as ti
from MPM.geometry.base_geometry import BaseGeometry


class CubeGeometry(BaseGeometry):

    def __init__(self,
                 minimum,
                 size,
                 init_vel=None):
        super().__init__(init_vel)
        self.minimum = minimum
        self.size = size
        self.volume = self.size.x * self.size.y * self.size.z

    @ti.func
    def uniform_sample(self):
        return ti.Vector([ti.random() for _ in range(self.dim)]) * ti.Vector(
                        self.size) + ti.Vector(self.minimum)