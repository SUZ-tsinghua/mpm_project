import taichi as ti
from tqdm import tqdm
from MPM.simulate_object import ObjectSimulator
import time

@ti.data_oriented
class SimulationRunner:

    def __init__(self, cfg):
        self.cfg = cfg

        # simulation/discretization constants
        self.dim = self.cfg.dim
        self.quality = self.cfg.quality  # Use a larger value for higher-res simulations
        self.n_particles, self.n_grid_per_length = (
            cfg.base_num_particles * self.quality**self.dim,
            cfg.base_n_grid_per_length * self.quality,
        )
        self.dt = self.cfg.dt
        self.dx = 1.0 / self.n_grid_per_length
        self.inv_dx = float(self.n_grid_per_length)

        total_vol = 0
        for obj in cfg.objects:
            material, geometry = obj
            total_vol += geometry.volume
        
        self.objects = []
        for obj in cfg.objects:
            material, geometry = obj
            par_count = int(geometry.volume / total_vol * self.n_particles)
            self.objects.append(ObjectSimulator(cfg, material, geometry, particle=par_count))
        
        if len(self.objects) == 0:
            print("No objects found!")
            exit(0)

    def set_all_unused(self):
        for object in self.objects:
            object.set_all_unused()

    @ti.func
    def is_normal(self, v):
        return ti.abs(v[0]) < 1 and ti.abs(v[1]) < 1 and ti.abs(v[2]) < 1

    @ti.kernel
    def grid_operation(self):
        for I in ti.grouped(self.objects[0].grid_m):
            for _ in ti.static(range(len(self.objects))):
                obj = self.objects[_]
                if obj.grid_m[I] != 0:
                    obj.grid_v[I] /= obj.grid_m[I]
                    obj.grid_v[I].y += self.dt * obj.gravity
                    for d in ti.static(range(self.dim)):
                        if I[d] < 3 and obj.grid_v[I][d] < 0:
                            obj.grid_v[I][d] = 0
                        if (I[d]
                                > obj.n_grid_per_length * obj.cfg.box_size[d] - 3
                                and obj.grid_v[I][d] > 0):
                            obj.grid_v[I][d] = 0
            # TODO: Do coupling here.

    def substep(self, i):
        for obj in self.objects:
            obj.P2G()

        self.grid_operation()

        for obj in self.objects:
            obj.G2P(i)

    def run(self, run_args):
        self.run_args = run_args

        # initialize visalization settings
        if self.run_args.visualize:
            res = (1080, 720)
            self.window = ti.ui.Window("MPM 3D", res, vsync=True)
            self.canvas = self.window.get_canvas()
            gui = self.window.get_gui()
            self.scene = self.window.get_scene()
            self.camera = ti.ui.Camera()
            self.camera.position(0.5, 1.0, 1.95)
            self.camera.lookat(0.5, 0.3, 0.5)
            self.camera.fov(55)
            self.particles_radius = 0.01 / 2**(self.quality - 1)

        if self.run_args.store_output:
            self.output_dir = f"output/{self.run_args.scenario}"
            import os
            import shutil

            os.makedirs(self.output_dir, exist_ok=True)
            shutil.rmtree(self.output_dir)
            os.makedirs(self.output_dir, exist_ok=True)

        # run simulation
        for i in tqdm(range(self.run_args.simulation_steps)):
            for s in range(100):
                self.substep(i)
            self.render()

            # output .ply files
            if self.run_args.store_output:
                for j, obj in enumerate(self.objects):
                    writer = ti.tools.PLYWriter(num_vertices=obj.n_particles)
                    np_x = obj.x
                    writer.add_vertex_pos(
                        np_x[:, 0],
                        np_x[:, 1],
                        np_x[:, 2],
                    )
                    os.makedirs(self.output_dir + f"/{i:06}", exist_ok=True)
                    writer.export_ascii(self.output_dir +
                                        f"/{i:06}/particle_object_{j}.ply")

    def render(self):
        if self.run_args.visualize:
            self.camera.track_user_inputs(self.window,
                                          movement_speed=0.03,
                                          hold_key=ti.ui.RMB)
            self.scene.set_camera(self.camera)

            self.scene.ambient_light((0, 0, 0))
            for obj in self.objects:
                self.scene.particles(obj.x,
                                    per_vertex_color=obj.colors,
                                    radius=self.particles_radius)

            self.scene.point_light(pos=(0.5, 1.5, 0.5), color=(0.5, 0.5, 0.5))
            self.scene.point_light(pos=(0.5, 1.5, 1.5), color=(0.5, 0.5, 0.5))

            self.canvas.scene(self.scene)
            self.window.show()
