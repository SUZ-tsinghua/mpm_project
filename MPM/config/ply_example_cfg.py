import taichi as ti
from MPM.geometry import BallGeometry, CubeGeometry, PlyGeometry
from MPM.config.base_cfg import BaseCfg
from MPM import WATER, JELLY, SNOW

class PlyExampleCfg(BaseCfg):
    box_size = [2.2, 1.0, 1.0]

    objects = [
        CubeGeometry(
            material=JELLY,
            minimum=ti.Vector([0.05, 0.5, 0.2]),
            size=ti.Vector([0.3, 0.3, 0.3]),
            p_rho=1.0,
            E=0.1e4,
            nu=0.2,
        ),
        PlyGeometry(
            material=SNOW,
            ply_path='data/ply/stanford-bunny.ply',
            resize_coef=3,
            translation=[0.75, 0.4, 0.5],
            rotation=[0, 0, 0],
            p_rho=1.0,
            E=0.1e4,
            nu=0.2,
        ),
        PlyGeometry(
            material=WATER,
            ply_path='data/ply/cow.ply',
            resize_coef=0.08,
            translation=[1.25, 0.6, 0.5],
            rotation=[0, 3.1415 / 2, 0],
            p_rho=1.0,
            E=0.1e4,
            nu=0.2,
        ),
    ]