import taichi as ti
from MPM.material.base_material import BaseMaterial

@ti.data_oriented
class JellyMaterial(BaseMaterial):
    def __init__(self, p_rho, E, nu, color=None):
        if color == None:
            color = (0.93, 0.33, 0.23)
        super().__init__(color)
        self.p_rho = p_rho
        self.p_mu_0 = E / (2 * (1 + nu))
        self.p_lambda_0 = E * nu / ((1 + nu) * (1 - 2 * nu))

    @ti.func
    def get_stress_param(self, Jp=None):
        return None
    
    @ti.func
    def update_transformation(self, F, U, sig, V, J):
        return F

    @ti.func
    def evaluate_stress(self, F, U, V, J, params):
        return 2 * self.p_mu_0 * (F - U @ V.transpose()) @ F.transpose(
                ) + ti.Matrix.identity(float, self.dim) * self.p_lambda_0 * J * (J - 1)