import taichi as ti
from MPM.material.base_material import BaseMaterial

@ti.data_oriented
class SnowMaterial(BaseMaterial):
    def __init__(self, p_rho, E, nu, color=None):
        if color == None:
            color = (1.0, 1.0, 1.0)
        super().__init__(color)
        self.p_rho = p_rho
        self.p_mu_0 = E / (2 * (1 + nu))
        self.p_lambda_0 = E * nu / ((1 + nu) * (1 - 2 * nu))
        self.p_mu = ti.float64
        self.p_lambda = ti.float64

    @ti.func
    def get_stress_param(self, Jp=None):
        h = ti.exp(10 * (1.0 - Jp))
        return self.p_mu_0 * h, self.p_lambda_0 * h
    
    @ti.func
    def clamp_sig(self, sig):
        return ti.min(ti.max(sig, 1 - 2.5e-2), 1 + 4.5e-3)
    
    @ti.func
    def update_transformation(self, F, U, sig, V, J):
        # Reconstruct elastic deformation gradient after plasticity
        return U @ sig @ V.transpose()

    @ti.func
    def evaluate_stress(self, F, U, V, J, params):
        p_mu, p_lambda = params
        return 2 * p_mu * (F - U @ V.transpose()) @ F.transpose(
                ) + ti.Matrix.identity(float, self.dim) * p_lambda * J * (J - 1)