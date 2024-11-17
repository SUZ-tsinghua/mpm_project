import taichi as ti
from MPM.geometry import BallGeometry, CubeGeometry
from MPM.config.base_cfg import BaseCfg
from MPM import WATER, JELLY, SNOW

class DifferentDensityCfg(BaseCfg):
    objects = [
        CubeGeometry(material=WATER,
                     minimum=ti.Vector([0.05, 0.01, 0.05]),
                     size=ti.Vector([0.9, 0.5, 0.9]),
                     p_rho=1.0,
                     E=0.1e4,
                     nu=0.2),
        CubeGeometry(material=JELLY,
                     minimum=ti.Vector([0.05, 0.6, 0.05]),
                     size=ti.Vector([0.1, 0.1, 0.1]),
                     p_rho=1.0,
                     E=0.1e4,
                     nu=0.2),
        CubeGeometry(material=JELLY,
                     minimum=ti.Vector([0.35, 0.6, 0.35]),
                     size=ti.Vector([0.1, 0.1, 0.1]),
                     p_rho=2.0,
                     E=0.1e4,
                     nu=0.2),
        CubeGeometry(material=JELLY,
                     minimum=ti.Vector([0.55, 0.6, 0.55]),
                     size=ti.Vector([0.1, 0.1, 0.1]),
                     p_rho=3.0,
                     E=0.1e4,
                     nu=0.2),
    ]
