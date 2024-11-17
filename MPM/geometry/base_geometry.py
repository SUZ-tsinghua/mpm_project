material_colors = [(0.1, 0.6, 0.9), (0.93, 0.33, 0.23), (1.0, 1.0, 1.0)]


class BaseGeometry:

    def __init__(self, material, p_rho=1.0, E=0.1e4, nu=0.2, color=None):
        self.material = material
        self.volume = None
        self.p_rho = p_rho
        self.E = E
        self.nu = nu
        self.start_p_idx = None
        self.end_p_idx = None
        if color == None:
            self.color = material_colors[self.material]
        else:
            self.color = color
