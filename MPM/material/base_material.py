import taichi as ti

class BaseMaterial:

    def __init__(self, color=None):
        self.color = color

    @ti.func
    def set_stress_param(self, Jp=None):
        raise NotImplementedError

    @ti.func
    def clamp_sig(self, sig):
        return sig
    
    @ti.func
    def update_transformation(self, F, U, sig, V, J):
        return NotImplementedError

    @ti.func
    def evaluate_stress(self, F, U, V, J, params):
        raise NotImplementedError