import numpy as np
import taichi as ti
import os

ti.init(
    arch=ti.gpu
)  # you may want to change the arch to ti.vulkan manually if you are using Apple M1/M2

# simulation/discretization constants
dim = 3
quality = 2  # Use a larger value for higher-res simulations
n_particles, n_grid = 8192 * quality**3, 32 * quality
dt = 2e-4
dx = 1.0 / n_grid
inv_dx = float(n_grid)
p_vol, p_rho = (dx * 0.5)**3, 1
p_mass = p_vol * p_rho
E, nu = 0.1e4, 0.2  # Young's modulus and Poisson's ratio
mu_0, lambda_0 = E / (2 * (1 + nu)), E * nu / (
    (1 + nu) * (1 - 2 * nu))  # Lame parameters

# physics related constants
gravity = -9.8

# for simulation
x = ti.Vector.field(dim, float, n_particles)  # position
v = ti.Vector.field(dim, float, n_particles)  # velocity
C = ti.Matrix.field(dim, dim, float, n_particles)  # The APIC-related matrix
F = ti.Matrix.field(3, 3, dtype=float,
                    shape=n_particles)  # deformation gradient
Jp = ti.field(float, n_particles)
grid_v = ti.Vector.field(dim, float, (n_grid, ) * dim)
grid_m = ti.field(float, (n_grid, ) * dim)
materials = ti.field(int, n_particles)
is_used = ti.field(int, n_particles)  # should be a boolean field

# for visualization
colors = ti.Vector.field(4, float, n_particles)
colors_random = ti.Vector.field(4, float, n_particles)

# enumerations for materials
WATER = 0
JELLY = 1
SNOW = 2


@ti.kernel
def substep(gravity: float):
    # TODO: fill the p2g, gridop, and g2p steps to form a substep of MPM
    for i, j, k in grid_m:
        grid_v[i, j, k] = [0, 0, 0]
        grid_m[i, j, k] = 0

    # P2G step
    for p in x:
        if is_used[
                p]:  # LOOKATME: do not swap the branch stmt with the for-loop, because ONLY the outermost loop stmt can be parallized.
            base = (x[p] * inv_dx - 0.5).cast(int)
            fx = x[p] * inv_dx - base.cast(float)
            w = [0.5 * (1.5 - fx)**2, 0.75 - (fx - 1)**2, 0.5 * (fx - 0.5)**2]
            affine = ti.Matrix.zero(float, dim, dim)
            if materials[p] != WATER:
                F[p] = (ti.Matrix.identity(float, 3) + dt * C[p]) @ F[p]
                h = ti.exp(10 * (1.0 - Jp[p]))
                if materials[p] == JELLY:
                    h = 0.3
                mu, la = mu_0 * h, lambda_0 * h
                U, sig, V = ti.svd(F[p])
                J = 1.0
                for d in ti.static(range(3)):
                    new_sig = sig[d, d]
                    if materials[p] == SNOW:
                        new_sig = ti.min(ti.max(sig[d, d], 1 - 2.5e-2),
                                         1 + 4.5e-3)
                    Jp[p] *= sig[d, d] / new_sig
                    sig[d, d] = new_sig
                    J *= new_sig
                if materials[p] == SNOW:
                    F[p] = U @ sig @ V.transpose()
                stress = 2 * mu * (F[p] - U @ V.transpose()) @ F[p].transpose(
                ) + ti.Matrix.identity(float, 3) * la * J * (J - 1)
                stress = (-dt * p_vol * 4 * inv_dx * inv_dx) * stress
                affine = stress + p_mass * C[p]
            else:
                stress = -dt * 4 * E * p_vol * (Jp[p] - 1) * inv_dx * inv_dx
                affine = ti.Matrix.identity(float,
                                            dim) * stress + p_mass * C[p]
            for i, j, k in ti.static(ti.ndrange(3, 3, 3)):
                offset = ti.Vector([i, j, k])
                dpos = (offset.cast(float) - fx) * dx
                weight = w[i].x * w[j].y * w[k].z
                grid_v[base +
                       offset] += weight * (p_mass * v[p] + affine @ dpos)
                grid_m[base + offset] += weight * p_mass

    # Grid operation
    for I in ti.grouped(grid_m):
        if grid_m[I] > 0:
            grid_v[I] /= grid_m[I]
            grid_v[I].y += dt * gravity
            for d in ti.static(range(dim)):
                if I[d] < 3 and grid_v[I][d] < 0:
                    grid_v[I][d] = 0
                if I[d] > n_grid - 3 and grid_v[I][d] > 0:
                    grid_v[I][d] = 0

    # G2P step
    for p in x:
        if is_used[p]:
            base = (x[p] * inv_dx - 0.5).cast(int)
            fx = x[p] * inv_dx - base.cast(float)
            w = [
                0.5 * (1.5 - fx)**2, 0.75 - (fx - 1.0)**2, 0.5 * (fx - 0.5)**2
            ]
            new_v = ti.Vector.zero(float, 3)
            new_C = ti.Matrix.zero(float, 3, 3)
            for i, j, k in ti.static(ti.ndrange(3, 3, 3)):
                dpos = ti.Vector([i, j, k]).cast(float) - fx
                g_v = grid_v[base + ti.Vector([i, j, k])]
                weight = w[i].x * w[j].y * w[k].z
                new_v += weight * g_v
                new_C += 4 * inv_dx * weight * g_v.outer_product(dpos)
            v[p], C[p] = new_v, new_C
            x[p] += dt * v[p]  # advection
            Jp[p] *= 1 + dt * C[p].trace()


# region is recognizable in vscode and pycharm at least...
#region initialization_and_visualization
class CubeVolume:

    def __init__(self, minimum, size, material):
        self.minimum = minimum
        self.size = size
        self.volume = self.size.x * self.size.y * self.size.z
        self.material = material
        mat_color = np.array(material_colors, dtype=np.float32)
        self.color = ti.Vector([
            mat_color[self.material, 0], mat_color[self.material, 1],
            mat_color[self.material, 2], 1.0
        ])
        self.start_p_idx = None
        self.end_p_idx = None


@ti.kernel
def init_cube_vol(first_par: int, last_par: int, x_begin: float,
                  y_begin: float, z_begin: float, x_size: float, y_size: float,
                  z_size: float, material: int):
    for i in range(first_par, last_par):
        x[i] = ti.Vector([ti.random() for i in range(dim)]) * ti.Vector(
            [x_size, y_size, z_size]) + ti.Vector([x_begin, y_begin, z_begin])
        Jp[i] = 1
        F[i] = ti.Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        v[i] = ti.Vector([0.0, 0.0, 0.0])
        materials[i] = material
        colors_random[i] = ti.Vector(
            [ti.random(), ti.random(),
             ti.random(), ti.random()])
        is_used[i] = 1


@ti.kernel
def set_all_unused():
    for p in is_used:
        # particles are intialized as unused
        is_used[p] = 0
        # unused particles are thrown away to the abyss (where your camera can not see)
        x[p] = ti.Vector([533799.0, 533799.0, 533799.0])
        Jp[p] = 1
        F[p] = ti.Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        C[p] = ti.Matrix([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
        v[p] = ti.Vector([0.0, 0.0, 0.0])


def init_vols(vols):
    set_all_unused()
    total_vol = 0
    for v in vols:
        total_vol += v.volume

    next_p = 0
    for i, v in enumerate(vols):
        v = vols[i]
        if isinstance(v, CubeVolume):
            par_count = int(v.volume / total_vol * n_particles)
            if i == len(
                    vols
            ) - 1:  # this is the last volume, so use all remaining particles
                par_count = n_particles - next_p
            init_cube_vol(next_p, next_p + par_count, *v.minimum, *v.size,
                          v.material)
            v.start_p_idx = next_p
            v.end_p_idx = next_p + par_count
            next_p += par_count      
        else:
            raise Exception("???")


@ti.kernel
def set_color_by_material(mat_color: ti.types.ndarray()):
    for i in range(n_particles):
        mat = materials[i]
        colors[i] = ti.Vector(
            [mat_color[mat, 0], mat_color[mat, 1], mat_color[mat, 2], 1.0])


#endregion

#region GUI
print("Loading presets...this might take some time")
material_colors = [(0.1, 0.6, 0.9), (0.93, 0.33, 0.23), (1.0, 1.0, 1.0)]

presets = [[
    CubeVolume(ti.Vector([0.55, 0.05, 0.55]), ti.Vector([0.4, 0.4, 0.4]),
               WATER),
],
           [
               CubeVolume(ti.Vector([0.05, 0.05, 0.05]),
                          ti.Vector([0.3, 0.4, 0.3]), WATER),
               CubeVolume(ti.Vector([0.65, 0.05, 0.65]),
                          ti.Vector([0.3, 0.4, 0.3]), WATER),
           ],
           [
               CubeVolume(ti.Vector([0.6, 0.05, 0.6]),
                          ti.Vector([0.25, 0.25, 0.25]), WATER),
               CubeVolume(ti.Vector([0.35, 0.35, 0.35]),
                          ti.Vector([0.25, 0.25, 0.25]), SNOW),
               CubeVolume(ti.Vector([0.05, 0.6, 0.05]),
                          ti.Vector([0.25, 0.25, 0.25]), JELLY),
           ]]
preset_names = [
    "Single Dam Break",
    "Double Dam Break",
    "Water/Snow/Jelly",
]

curr_preset_id = 2
paused = False
use_random_colors = False
particles_radius = 0.01 / 2**(quality - 1)


def show_options():
    global use_random_colors
    global paused
    global particles_radius
    global gravity
    global curr_preset_id

    with gui.sub_window("Presets", 0.05, 0.1, 0.2, 0.15) as w:
        old_preset = curr_preset_id
        for i in range(len(presets)):
            if w.checkbox(preset_names[i], curr_preset_id == i):
                curr_preset_id = i
        if curr_preset_id != old_preset:
            init()
            paused = True

    with gui.sub_window("Gravity", 0.05, 0.3, 0.2, 0.1) as w:
        gravity = w.slider_float("y", gravity, -50, 50)

    with gui.sub_window("Options", 0.05, 0.45, 0.2, 0.4) as w:
        use_random_colors = w.checkbox("use_random_colors", use_random_colors)
        if not use_random_colors:
            material_colors[WATER] = w.color_edit_3("water color",
                                                    material_colors[WATER])
            material_colors[SNOW] = w.color_edit_3("snow color",
                                                   material_colors[SNOW])
            material_colors[JELLY] = w.color_edit_3("jelly color",
                                                    material_colors[JELLY])
            set_color_by_material(np.array(material_colors, dtype=np.float32))
        particles_radius = w.slider_float("particles radius ",
                                          particles_radius, 0, 0.05)
        if w.button("restart"):
            init()
        if paused:
            if w.button("Continue"):
                paused = False
        else:
            if w.button("Pause"):
                paused = True


#endregion


def init():
    global paused
    init_vols(presets[curr_preset_id])


init()

res = (1080, 720)
window = ti.ui.Window("MPM 3D", res, vsync=True)


def render():
    camera.track_user_inputs(window, movement_speed=0.03, hold_key=ti.ui.RMB)
    scene.set_camera(camera)

    scene.ambient_light((0, 0, 0))

    colors_used = colors_random if use_random_colors else colors
    scene.particles(x, per_vertex_color=colors_used, radius=particles_radius)

    scene.point_light(pos=(0.5, 1.5, 0.5), color=(0.5, 0.5, 0.5))
    scene.point_light(pos=(0.5, 1.5, 1.5), color=(0.5, 0.5, 0.5))

    canvas.scene(scene)


canvas = window.get_canvas()
gui = window.get_gui()
scene = ti.ui.Scene()
camera = ti.ui.Camera()
camera.position(0.5, 1.0, 1.95)
camera.lookat(0.5, 0.3, 0.5)
camera.fov(55)


def main():
    frame_id = 0
    import shutil
    shutil.rmtree('output_ply')
    while window.running:
        #print("heyyy ",frame_id)
        frame_id += 1
        # frame_id = frame_id % 256

        if not paused:
            for s in range(30):
                substep(gravity)

        render()
        show_options()
        np_x = x.to_numpy()
        os.makedirs(f"output_ply/{frame_id:06}", exist_ok=True)
        for i in range(len(presets[curr_preset_id])):
            obj = presets[curr_preset_id][i]
            writer = ti.tools.PLYWriter(num_vertices=obj.end_p_idx -
                                        obj.start_p_idx)
            writer.add_vertex_pos(np_x[obj.start_p_idx:obj.end_p_idx, 0],
                                  np_x[obj.start_p_idx:obj.end_p_idx, 1],
                                  np_x[obj.start_p_idx:obj.end_p_idx, 2])
            np_color = obj.color.to_numpy()
            np_colors = np.expand_dims(np_color, 0).repeat(
                obj.end_p_idx - obj.start_p_idx, 0)
            writer.add_vertex_rgba(np_colors[:, 0], np_colors[:, 1],
                                   np_colors[:, 2], np_colors[:, 3])
            
            writer.export_ascii(
                f"./output_ply/{frame_id:06}/particle_object_{i}.ply")

        window.show()


if __name__ == '__main__':
    main()
