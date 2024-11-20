import taichi as ti
from MPM.geometry import BallGeometry, CubeGeometry
from MPM.config.base_cfg import BaseCfg
from MPM import WATER, JELLY, SNOW


class TwoBallCfg(BaseCfg):
    base_num_particles = 8192
    box_size = [2.0, 2.0, 1.0]

    objects = [
        BallGeometry(
            material=JELLY,
            center=ti.Vector([0.5, 1.0, 0.5]),
            radius=0.2,
            p_rho=1.0,
            E=0.1e4,
            nu=0.2,
            init_vel=[2.0, 0.0, 0.0]
        ),
        BallGeometry(
            material=JELLY,
            center=ti.Vector([1.5, 1.0, 0.5]),
            radius=0.2,
            p_rho=1.0,
            E=1e4,
            nu=0.2,
            init_vel=[-2.0, 0.0, 0.0]
        ),
    ]
