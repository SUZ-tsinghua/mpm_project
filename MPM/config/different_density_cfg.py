import taichi as ti
from MPM.geometry import *
from MPM.material import *
from MPM.config.base_cfg import BaseCfg


class DifferentDensityCfg(BaseCfg):
    objects = [
        (WaterMaterial(
            p_rho=1.0,
            E=2777.77777778,
        ),
        CubeGeometry(
            minimum=ti.Vector([0.1, 0.1, 0.1]),
            size=ti.Vector([0.8, 0.5, 0.8]),
        )),
        (JellyMaterial(
            p_rho=1.0,
            E=300.0,
            nu=0.2,
        ),
        BallGeometry(
            center=ti.Vector([0.25, 0.7, 0.5]),
            radius=0.05,
        )),
        (JellyMaterial(
            p_rho=2.0,
            E=300.0,
            nu=0.2,
        ),
        BallGeometry(
            center=ti.Vector([0.5, 0.7, 0.5]),
            radius=0.05,
        )),
        (JellyMaterial(
            p_rho=3.0,
            E=300.0,
            nu=0.2,
        ),
        BallGeometry(
            center=ti.Vector([0.75, 0.7, 0.5]),
            radius=0.05,
        )),
    ]
