import taichi as ti
from MPM.geometry import *
from MPM.material import *
from MPM.config.base_cfg import BaseCfg


class TwoFluidCfg(BaseCfg):
    box_size = [2.0, 2.0, 1.1]

    objects = [
        (WaterMaterial(
            p_rho=1.0,
            E=277.777777778,
        ),
        CubeGeometry(
            minimum=ti.Vector([0.05, 0.01, 0.05]),
            size=ti.Vector([0.3, 1.5, 0.9]),
        )),
        (WaterMaterial(
            p_rho=2.0,
            E=277.777777778,
        ),
        BallGeometry(
            center=ti.Vector([1.4, 1.0, 0.55]),
            radius=0.5,
        )),
    ]
