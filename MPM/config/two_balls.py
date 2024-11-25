import taichi as ti
from MPM.geometry import *
from MPM.material import *
from MPM.config.base_cfg import BaseCfg


class TwoBallCfg(BaseCfg):
    base_num_particles = 8192
    box_size = [2.0, 2.0, 1.0]

    objects = [
        (JellyMaterial(
            p_rho=1.0,
            E=300,
            nu=0.2,
        ),
        BallGeometry(
            center=ti.Vector([0.5, 1.0, 0.5]),
            radius=0.2,
            init_vel=[2.0, 0.0, 0.0]
        )),
        (JellyMaterial(
            p_rho=1.0,
            E=3e3,
            nu=0.2,
        ),
        BallGeometry(
            center=ti.Vector([1.5, 1.0, 0.5]),
            radius=0.2,
            init_vel=[-2.0, 0.0, 0.0]
        )),
    ]
