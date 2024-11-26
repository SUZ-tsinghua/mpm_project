import taichi as ti
from MPM.geometry import *

@ti.data_oriented
class ObjectSimulator:

    def __init__(self, cfg, material, geometry, particle):
        self.cfg = cfg

        # preprocess configuration
        if len(material.color) == 3:
            r, g, b = material.color
            material.color = (r, g, b, 1.0)
        if not hasattr(material, "dim"):
            material.dim = self.cfg.dim
        elif material.dim != self.cfg.dim:
            raise TypeError(f"Configuration dimension {self.cfg.dim} does not match material {material.dim}")
        if not hasattr(geometry, "dim"):
            geometry.dim = self.cfg.dim
        elif geometry.dim != self.cfg.dim:
            raise TypeError(f"Configuration dimension {self.cfg.dim} does not match geometry {geometry.dim}")

        # simulation/discretization constants
        self.dim = self.cfg.dim
        self.quality = self.cfg.quality  # Use a larger value for higher-res simulations
        self.n_particles, self.n_grid_per_length = (
            particle * self.quality**self.dim,
            cfg.base_n_grid_per_length * self.quality,
        )
        self.dt = self.cfg.dt
        self.dx = 1.0 / self.n_grid_per_length
        self.inv_dx = float(self.n_grid_per_length)

        # physics related constants
        self.gravity = cfg.gravity

        self.material = material
        self.geometry = geometry

        # for simulation
        self.p_vol = (self.dx * 0.5)**(self.dim)
        self.p_mass = ti.field(float, self.n_particles)
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
            tuple(int(self.n_grid_per_length * self.cfg.box_size[_]) for _ in range(self.dim))
        )
        self.grid_m = ti.field(
            float,
            tuple(int(self.n_grid_per_length * self.cfg.box_size[_]) for _ in range(self.dim))
        )
        self.p_is_used = ti.field(
            int, self.n_particles)  # should be a boolean field
        self.p_is_used.fill(1)

        # for visualization
        self.colors = ti.Vector.field(4, float, self.n_particles)
        self.set_all_unused()
        self.init_vol()

    @ti.kernel
    def set_all_unused(self):
        # set all to unused
        for p in self.p_is_used:
            # particles are intialized as unused
            self.p_is_used[p] = 0
            # unused particles are thrown away to the abyss (where your camera can not see)
            self.x[p] = ti.Vector([533799.0 for _ in range(self.dim)])
            self.Jp[p] = 1
            self.F[p] = ti.Matrix.identity(float, self.dim)
            self.C[p] = ti.Matrix.zero(float, self.dim, self.dim)
            self.v[p] = ti.Vector.zero(float, self.dim)

    @ti.kernel
    def init_vol(self):
        for i in range(self.n_particles):
            self.x[i] = self.geometry.uniform_sample()
            self.Jp[i] = 1
            self.F[i] = ti.Matrix.identity(float, self.dim)
            self.v[i] = ti.Vector(self.geometry.init_vel)
            self.p_mass[i] = self.material.p_rho * self.p_vol
            self.colors[i] = ti.Vector(self.material.color)
            self.p_is_used[i] = 1

    @ti.kernel
    def P2G(self):
        for i, j, k in self.grid_m:
            self.grid_v[i, j, k] = [0 for i in range(self.dim)]
            self.grid_m[i, j, k] = 0

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
                self.F[p] = (ti.Matrix.identity(float, self.dim) +
                                self.dt * self.C[p]) @ self.F[p]
                stress_param = self.material.get_stress_param(self.Jp[p])
                U, sig, V = ti.svd(self.F[p])
                J = 1.0
                for d in ti.static(range(3)):
                    new_sig = self.material.clamp_sig(sig[d, d])
                    self.Jp[p] *= sig[d, d] / new_sig
                    sig[d, d] = new_sig
                    J *= new_sig
                self.F[p] = self.material.update_transformation(self.F[p], U, sig, V, J)
                stress = self.material.evaluate_stress(self.F[p], U, V, J, stress_param)
                stress = (-self.dt * self.p_vol * 4 * self.inv_dx *
                            self.inv_dx) * stress
                affine = stress + self.p_mass[p] * self.C[p]

                for i, j, k in ti.static(ti.ndrange(3, 3, 3)):
                    offset = ti.Vector([i, j, k])
                    dpos = (offset.cast(float) - fx) * self.dx
                    weight = w[i].x * w[j].y * w[k].z
                    self.grid_v[base + offset] += weight * (
                        self.p_mass[p] * self.v[p] + affine @ dpos)
                    self.grid_m[base + offset] += weight * self.p_mass[p]


    @ti.kernel
    def G2P(self, id: int):
        for p in self.x:
            if self.p_is_used[p]:
                base = (self.x[p] * self.inv_dx - 0.5).cast(int)
                fx = self.x[p] * self.inv_dx - base.cast(float)
                w = [
                    0.5 * (1.5 - fx)**2,
                    0.75 - (fx - 1.0)**2,
                    0.5 * (fx - 0.5)**2,
                ]
                new_v = ti.Vector.zero(float, self.dim)
                new_C = ti.Matrix.zero(float, self.dim, self.dim)
                for i, j, k in ti.static(ti.ndrange(3, 3, 3)):
                    dpos = ti.Vector([i, j, k]).cast(float) - fx
                    g_v = self.grid_v[base + ti.Vector([i, j, k])]
                    weight = w[i].x * w[j].y * w[k].z
                    new_v += weight * g_v
                    new_C += 4 * self.inv_dx * weight * g_v.outer_product(dpos)
                self.v[p], self.C[p] = new_v, new_C
                self.x[p] += self.dt * self.v[p]  # advection
                self.Jp[p] *= 1 + self.dt * self.C[p].trace()