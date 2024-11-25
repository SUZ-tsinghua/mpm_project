import taichi as ti
from MPM.geometry.base_geometry import BaseGeometry
from math import pi


class BallGeometry(BaseGeometry):

    def __init__(self,
                 center,
                 radius,
                 init_vel=None):
        super().__init__(init_vel)
        self.center = center
        self.radius = radius
        self.volume = 4 / 3 * pi * radius**3

    @ti.func
    def uniform_sample(self):
        r = self.radius * (ti.random())**(1 / self.dim)
        return ti.Vector(self.center) + ti.Vector([ti.randn() for _ in range(self.dim)]).normalized() * r
        