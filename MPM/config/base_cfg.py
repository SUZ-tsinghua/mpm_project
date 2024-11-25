class BaseCfg:
    dim = 3
    quality = 2
    dt = 2e-4 / quality
    box_size = [1.0, 1.0, 1.0]
    base_max_num_particles = 2**20
    base_n_grid_per_length = 32
    particles_per_unit_volume = 2**19
