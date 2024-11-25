import taichi as ti
from MPM.material.base_material import BaseMaterial

@ti.data_oriented
class WaterMaterial(BaseMaterial):
    def __init__(self, p_rho, E, color=None):
        if color == None:
            color = (0.1, 0.6, 0.9)
        super().__init__(color)
        self.p_rho = p_rho
        self.p_E_0 = E
        
    @ti.func
    def get_stress_param(self, Jp=None):
        h = ti.exp(10 * (1.0 - Jp))
        return self.p_E_0 * h
    
    @ti.func
    def update_transformation(self, F, U, sig, V, J):
        # Reset deformation gradient to avoid numerical instability
        return ti.Matrix.identity(float, self.dim) * ti.pow(J, 1/self.dim)

    @ti.func
    def evaluate_stress(self, F, U, V, J, params):
        p_E = params
        return ti.Matrix.identity(float, self.dim) * p_E * J * (J - 1)