from MPM.geometry.base_geometry import BaseGeometry


class CubeGeometry(BaseGeometry):

    def __init__(self,
                 minimum,
                 size,
                 material,
                 p_rho=1.0,
                 E=0.1e4,
                 nu=0.2,
                 color=None):
        super().__init__(material, p_rho, E, nu, color)
        self.minimum = minimum
        self.size = size
        self.volume = self.size.x * self.size.y * self.size.z
        self.start_p_idx = None
        self.end_p_idx = None
