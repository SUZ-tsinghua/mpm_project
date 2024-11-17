from MPM.geometry.base_geometry import BaseGeometry
import numpy as np


class BallGeometry(BaseGeometry):

    def __init__(self,
                 center,
                 radius,
                 material,
                 p_rho=1.0,
                 E=0.1e4,
                 nu=0.2,
                 color=None):
        super().__init__(material, p_rho, E, nu, color)
        self.center = center
        self.radius = radius
        self.volume = 4 / 3 * np.pi * radius**3
        self.start_p_idx = None
        self.end_p_idx = None
