import taichi as ti
from MPM.geometry import BallGeometry, CubeGeometry
from MPM.config.base_cfg import BaseCfg
from MPM import WATER, JELLY, SNOW


class WaterYellySnowCfg(BaseCfg):
    objects = [
        CubeGeometry(
            material=WATER,
            minimum=ti.Vector([0.6, 0.05, 0.6]),
            size=ti.Vector([0.25, 0.25, 0.25]),
            p_rho=1.0,
            E=400,
            nu=0.2,
        ),
        CubeGeometry(
            material=SNOW,
            minimum=ti.Vector([0.35, 0.35, 0.35]),
            size=ti.Vector([0.25, 0.25, 0.25]),
            p_rho=1.0,
            E=0.1e4,
            nu=0.2,
        ),
        CubeGeometry(
            material=JELLY,
            minimum=ti.Vector([0.05, 0.6, 0.05]),
            size=ti.Vector([0.25, 0.25, 0.25]),
            p_rho=1.0,
            E=0.1e4,
            nu=0.2,
        ),
    ]
