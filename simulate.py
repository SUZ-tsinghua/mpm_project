import taichi as ti
import argparse
from MPM.simulation_runner import SimulationRunner
from MPM.config import WaterYellySnowCfg, DifferentDensityCfg, FloodCfg, TwoFluidCfg

# you may want to change the arch to ti.vulkan manually if you are using Apple M1/M2
ti.init(arch=ti.gpu)


def main(args):
    if args.scenario == "WaterYellySnow":
        cfg = WaterYellySnowCfg
    elif args.scenario == "DifferentDensity":
        cfg = DifferentDensityCfg
    elif args.scenario == "Flood":
        cfg = FloodCfg
    elif args.scenario == "TwoFluid":
        cfg = TwoFluidCfg
    else:
        raise Exception("Undefined scenario")

    runner = SimulationRunner(cfg)
    runner.run(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario",
                        type=str,
                        default="WaterYellySnow",
                        help="scenario")
    parser.add_argument(
        "--visualize",
        action="store_true",
        default=False,
        help="Visualize the simulation steps",
    )
    parser.add_argument(
        "--store_output",
        action="store_true",
        default=False,
        help="Store the output .ply files",
    )
    parser.add_argument("--simulation_steps",
                        type=int,
                        default=200,
                        help="Simulation steps")
    args = parser.parse_args()
    main(args)
