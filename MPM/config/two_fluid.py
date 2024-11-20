import taichi as ti
from MPM.geometry import BallGeometry, CubeGeometry
from MPM.config.base_cfg import BaseCfg
from MPM import WATER, JELLY, SNOW


class TwoFluidCfg(BaseCfg):
    box_size = [2.0, 2.0, 1.1]

    objects = [
        CubeGeometry(
            material=WATER,
            minimum=ti.Vector([0.05, 0.01, 0.05]),
            size=ti.Vector([0.3, 1.5, 0.9]),
            p_rho=1.0,
            E=0.1e4,
            nu=0.2,
        ),
        BallGeometry(
            material=WATER,
            center=ti.Vector([1.4, 1.0, 0.55]),
            radius=0.5,
            p_rho=2.0,
            E=0.1e4,
            nu=0.2,
        ),
    ]
