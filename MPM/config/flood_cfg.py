import taichi as ti
from MPM.geometry import *
from MPM.material import *
from MPM.config.base_cfg import BaseCfg


class FloodCfg(BaseCfg):
    box_size = [2.0, 2.0, 1.0]

    objects = [
        (WaterMaterial(
            p_rho=1.0,
            E=277.777777778,
        ),
        CubeGeometry(
            minimum=ti.Vector([0.05, 0.01, 0.05]),
            size=ti.Vector([0.3, 1.5, 0.9]),
        )),
        (JellyMaterial(
            p_rho=1.0,
            E=300.0,
            nu=0.2,
        ),
        CubeGeometry(
            minimum=ti.Vector([1.0, 0.01, 0.05]),
            size=ti.Vector([0.2, 0.2, 0.2]),
        )),
        (JellyMaterial(
            p_rho=2.0,
            E=300.0,
            nu=0.2,
        ),
        CubeGeometry(
            minimum=ti.Vector([1.0, 0.01, 0.35]),
            size=ti.Vector([0.2, 0.2, 0.2]),
        )),
        (JellyMaterial(
            p_rho=3.0,
            E=300.0,
            nu=0.2,
        ),
        CubeGeometry(
            minimum=ti.Vector([1.0, 0.01, 0.35]),
            size=ti.Vector([0.2, 0.2, 0.2]),
        )),
    ]
