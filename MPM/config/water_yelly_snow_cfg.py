import taichi as ti
from MPM.geometry import *
from MPM.material import *
from MPM.config.base_cfg import BaseCfg


class WaterYellySnowCfg(BaseCfg):
    objects = [
        (WaterMaterial(
            p_rho=1.0,
            E=277.777777778,
        ),
        CubeGeometry(
            minimum=ti.Vector([0.6, 0.05, 0.6]),
            size=ti.Vector([0.25, 0.25, 0.25]),
        )),
        (SnowMaterial(
            p_rho=1.0,
            E=0.1e4,
            nu=0.2,
        ),
        CubeGeometry(
            minimum=ti.Vector([0.35, 0.35, 0.35]),
            size=ti.Vector([0.25, 0.25, 0.25]),
        )),
        (JellyMaterial(
            p_rho=1.0,
            E=300.0,
            nu=0.2,
        ),
        CubeGeometry(
            minimum=ti.Vector([0.05, 0.6, 0.05]),
            size=ti.Vector([0.25, 0.25, 0.25]),
        )),
    ]
