import numpy as np
import taichi as ti
from taichi import math
import os
from MPM.geometry import CubeGeometry, BallGeometry
from MPM import WATER, JELLY, SNOW


@ti.data_oriented
class SimulationRunner:

    def __init__(self, cfg):
        self.cfg = cfg

        # simulation/discretization constants
        self.dim = self.cfg.dim
        self.quality = self.cfg.quality  # Use a larger value for higher-res simulations
        self.n_particles, self.n_grid_per_length = (
            65536 * self.quality**self.dim,
            32 * self.quality,
        )
        self.dt = self.cfg.dt
        self.dx = 1.0 / self.n_grid_per_length
        self.inv_dx = float(self.n_grid_per_length)

        # physics related constants
        self.gravity = -9.8

        # for simulation
        self.p_vol = (self.dx * 0.5)**(self.dim)
        self.p_rho = ti.field(float, self.n_particles)
        self.p_mass = ti.field(float, self.n_particles)
        self.p_E = ti.field(float, self.n_particles)
        self.p_nu = ti.field(float, self.n_particles)
        self.p_mu_0 = ti.field(float, self.n_particles)
        self.p_lambda_0 = ti.field(float, self.n_particles)
        self.x = ti.Vector.field(self.dim, float, self.n_particles)  # position
        self.v = ti.Vector.field(self.dim, float, self.n_particles)  # velocity
        self.C = ti.Matrix.field(self.dim, self.dim, float,
                                 self.n_particles)  # The APIC-related matrix
        self.F = ti.Matrix.field(
            self.dim, self.dim, dtype=float,
            shape=self.n_particles)  # deformation gradient
        self.Jp = ti.field(float, self.n_particles)
        self.grid_v = ti.Vector.field(
            self.dim,
            float,
            (
                int(self.n_grid_per_length * self.cfg.box_size[0]),
                int(self.n_grid_per_length * self.cfg.box_size[1]),
                int(self.n_grid_per_length * self.cfg.box_size[2]),
            ),
        )
        self.grid_m = ti.field(
            float,
            (
                int(self.n_grid_per_length * self.cfg.box_size[0]),
                int(self.n_grid_per_length * self.cfg.box_size[1]),
                int(self.n_grid_per_length * self.cfg.box_size[2]),
            ),
        )
        self.materials = ti.field(int, self.n_particles)
        self.p_is_used = ti.field(
            int, self.n_particles)  # should be a boolean field
        self.p_is_used.fill(1)

        # for visualization
        self.colors = ti.Vector.field(4, float, self.n_particles)

        self.objects = cfg.objects
        self.create_objects()

    def create_objects(self):
        self.set_all_unused()
        total_vol = 0
        for obj in self.objects:
            total_vol += obj.volume

        next_p = 0
        for i, obj in enumerate(self.objects):
            par_count = int(obj.volume / total_vol * self.n_particles)

            # this is the last volume, so use all remaining particles
            if i == len(self.objects) - 1:
                par_count = self.n_particles - next_p
            if isinstance(obj, CubeGeometry):
                self.init_cube_vol(
                    next_p,
                    next_p + par_count,
                    *obj.minimum,
                    *obj.size,
                    obj.material,
                    *obj.color,
                    obj.p_rho,
                    obj.E,
                    obj.nu,
                )
            elif isinstance(obj, BallGeometry):
                self.init_ball_vol(
                    next_p,
                    next_p + par_count,
                    *obj.center,
                    obj.radius,
                    obj.material,
                    *obj.color,
                    obj.p_rho,
                    obj.E,
                    obj.nu,
                )
            else:
                raise Exception("Undefined object geometry")

            obj.start_p_idx = next_p
            obj.end_p_idx = next_p + par_count
            next_p += par_count

    @ti.kernel
    def set_all_unused(self):
        # set all to unused
        for p in self.p_is_used:
            # particles are intialized as unused
            self.p_is_used[p] = 0
            # unused particles are thrown away to the abyss (where your camera can not see)
            self.x[p] = ti.Vector([533799.0, 533799.0, 533799.0])
            self.Jp[p] = 1
            self.F[p] = ti.Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
            self.C[p] = ti.Matrix([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
            self.v[p] = ti.Vector([0.0, 0.0, 0.0])

    @ti.kernel
    def init_cube_vol(
        self,
        first_par: int,
        last_par: int,
        x_begin: float,
        y_begin: float,
        z_begin: float,
        x_size: float,
        y_size: float,
        z_size: float,
        material: int,
        color_r: float,
        color_g: float,
        color_b: float,
        p_rho: float,
        E: float,
        nu: float,
    ):
        for i in range(first_par, last_par):
            self.x[i] = ti.Vector([ti.random()
                                   for j in range(self.dim)]) * ti.Vector(
                                       [x_size, y_size, z_size]) + ti.Vector(
                                           [x_begin, y_begin, z_begin])
            self.Jp[i] = 1
            self.F[i] = ti.Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
            self.v[i] = ti.Vector([0.0, 0.0, 0.0])
            self.p_rho[i] = p_rho
            self.p_mass[i] = p_rho * self.p_vol
            self.p_E[i] = E
            self.p_nu[i] = nu
            self.p_mu_0[i] = E / (2 * (1 + nu))
            self.p_lambda_0[i] = E * nu / ((1 + nu) * (1 - 2 * nu))
            self.materials[i] = material
            self.colors[i] = ti.Vector([color_r, color_g, color_b, 1.0])
            self.p_is_used[i] = 1

    @ti.kernel
    def init_ball_vol(
        self,
        first_par: int,
        last_par: int,
        center_x: float,
        center_y: float,
        center_z: float,
        radius: float,
        material: int,
        color_r: float,
        color_g: float,
        color_b: float,
        p_rho: float,
        E: float,
        nu: float,
    ):
        for i in range(first_par, last_par):
            theta = 2 * math.pi * ti.random()
            phi = math.acos(1 - 2 * ti.random())
            r = radius * (ti.random())**(1 / 3)
            self.x[i] = ti.Vector([
                center_x + r * math.sin(phi) * math.cos(theta),
                center_y + r * math.sin(phi) * math.sin(theta),
                center_z + r * math.cos(phi),
            ])
            self.Jp[i] = 1
            self.F[i] = ti.Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
            self.v[i] = ti.Vector([0.0, 0.0, 0.0])
            self.p_rho[i] = p_rho
            self.p_mass[i] = p_rho * self.p_vol
            self.p_E[i] = E
            self.p_nu[i] = nu
            self.p_mu_0[i] = E / (2 * (1 + nu))
            self.p_lambda_0[i] = E * nu / ((1 + nu) * (1 - 2 * nu))
            self.materials[i] = material
            self.colors[i] = ti.Vector([color_r, color_g, color_b, 1.0])
            self.p_is_used[i] = 1

    @ti.kernel
    def substep(self):
        for i, j, k in self.grid_m:
            self.grid_v[i, j, k] = [0, 0, 0]
            self.grid_m[i, j, k] = 0

        # P2G step
        for p in self.x:
            # LOOKATME: do not swap the branch stmt with the for-loop, because ONLY the outermost loop stmt can be parallized.
            if self.p_is_used[p]:
                base = (self.x[p] * self.inv_dx - 0.5).cast(int)
                fx = self.x[p] * self.inv_dx - base.cast(float)
                w = [
                    0.5 * (1.5 - fx)**2, 0.75 - (fx - 1)**2,
                    0.5 * (fx - 0.5)**2
                ]
                affine = ti.Matrix.zero(float, self.dim, self.dim)
                if self.materials[p] != WATER:
                    self.F[p] = (ti.Matrix.identity(float, 3) +
                                 self.dt * self.C[p]) @ self.F[p]
                    h = ti.exp(10 * (1.0 - self.Jp[p]))
                    if self.materials[p] == JELLY:
                        h = 0.3
                    mu, la = self.p_mu_0[p] * h, self.p_lambda_0[p] * h
                    U, sig, V = ti.svd(self.F[p])
                    J = 1.0
                    for d in ti.static(range(3)):
                        new_sig = sig[d, d]
                        if self.materials[p] == SNOW:
                            new_sig = ti.min(ti.max(sig[d, d], 1 - 2.5e-2),
                                             1 + 4.5e-3)
                        self.Jp[p] *= sig[d, d] / new_sig
                        sig[d, d] = new_sig
                        J *= new_sig
                    if self.materials[p] == SNOW:
                        self.F[p] = U @ sig @ V.transpose()
                    stress = 2 * mu * (
                        self.F[p] - U @ V.transpose()) @ self.F[p].transpose(
                        ) + ti.Matrix.identity(float, 3) * la * J * (J - 1)
                    stress = (-self.dt * self.p_vol * 4 * self.inv_dx *
                              self.inv_dx) * stress
                    affine = stress + self.p_mass[p] * self.C[p]
                else:
                    stress = (-self.dt * 4 * self.p_E[p] * self.p_vol *
                              (self.Jp[p] - 1) * self.inv_dx * self.inv_dx)
                    affine = (ti.Matrix.identity(float, self.dim) * stress +
                              self.p_mass[p] * self.C[p])

                for i, j, k in ti.static(ti.ndrange(3, 3, 3)):
                    offset = ti.Vector([i, j, k])
                    dpos = (offset.cast(float) - fx) * self.dx
                    weight = w[i].x * w[j].y * w[k].z
                    self.grid_v[base + offset] += weight * (
                        self.p_mass[p] * self.v[p] + affine @ dpos)
                    self.grid_m[base + offset] += weight * self.p_mass[p]

        # Grid operation
        for I in ti.grouped(self.grid_m):
            if self.grid_m[I] > 0:
                self.grid_v[I] /= self.grid_m[I]
                self.grid_v[I].y += self.dt * self.gravity
                for d in ti.static(range(self.dim)):
                    if I[d] < 3 and self.grid_v[I][d] < 0:
                        self.grid_v[I][d] = 0
                    if (I[d]
                            > self.n_grid_per_length * self.cfg.box_size[d] - 3
                            and self.grid_v[I][d] > 0):
                        self.grid_v[I][d] = 0

        # G2P step
        for p in self.x:
            if self.p_is_used[p]:
                base = (self.x[p] * self.inv_dx - 0.5).cast(int)
                fx = self.x[p] * self.inv_dx - base.cast(float)
                w = [
                    0.5 * (1.5 - fx)**2,
                    0.75 - (fx - 1.0)**2,
                    0.5 * (fx - 0.5)**2,
                ]
                new_v = ti.Vector.zero(float, 3)
                new_C = ti.Matrix.zero(float, 3, 3)
                for i, j, k in ti.static(ti.ndrange(3, 3, 3)):
                    dpos = ti.Vector([i, j, k]).cast(float) - fx
                    g_v = self.grid_v[base + ti.Vector([i, j, k])]
                    weight = w[i].x * w[j].y * w[k].z
                    new_v += weight * g_v
                    new_C += 4 * self.inv_dx * weight * g_v.outer_product(dpos)
                self.v[p], self.C[p] = new_v, new_C
                self.x[p] += self.dt * self.v[p]  # advection
                self.Jp[p] *= 1 + self.dt * self.C[p].trace()

    def run(self, run_args):
        self.run_args = run_args

        # initialize visalization settings
        if self.run_args.visualize:
            res = (1080, 720)
            self.window = ti.ui.Window("MPM 3D", res, vsync=True)
            self.canvas = self.window.get_canvas()
            gui = self.window.get_gui()
            self.scene = ti.ui.Scene()
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
        for i in range(self.run_args.simulation_steps):
            for s in range(300):
                self.substep()
            self.render()

            # output .ply files
            if self.run_args.store_output:
                np_x = self.x.to_numpy()
                for j, obj in enumerate(self.objects):
                    writer = ti.tools.PLYWriter(num_vertices=obj.end_p_idx -
                                                obj.start_p_idx)
                    writer.add_vertex_pos(
                        np_x[obj.start_p_idx:obj.end_p_idx, 0],
                        np_x[obj.start_p_idx:obj.end_p_idx, 1],
                        np_x[obj.start_p_idx:obj.end_p_idx, 2],
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
            self.scene.particles(self.x,
                                 per_vertex_color=self.colors,
                                 radius=self.particles_radius)

            self.scene.point_light(pos=(0.5, 1.5, 0.5), color=(0.5, 0.5, 0.5))
            self.scene.point_light(pos=(0.5, 1.5, 1.5), color=(0.5, 0.5, 0.5))

            self.canvas.scene(self.scene)
            self.window.show()
