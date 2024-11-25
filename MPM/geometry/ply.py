from MPM.geometry.base_geometry import BaseGeometry


class PlyGeometry(BaseGeometry):

    def __init__(self,
                 ply_path,
                 material,
                 p_rho=1.0,
                 E=0.1e4,
                 nu=0.2,
                 color=None,
                 init_vel=None,
                 translation=[0.0, 0.0, 0.0],
                 rotation=[0.0, 0.0, 0.0],
                 resize_coef=1.0):
        super().__init__(material, p_rho, E, nu, color, init_vel)
        self.ply_path = ply_path
        self.translation = translation
        self.rotation = rotation
        self.resize_coef = resize_coef
        self.start_p_idx = None
        self.end_p_idx = None