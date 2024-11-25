import trimesh
import numpy as np
import open3d as o3d
import os

files = os.listdir("./obj")
obj_list = [f for f in files if f.endswith(".obj")]

for obj_file in obj_list:
    name = obj_file.split(".")[0]
    mesh = trimesh.load(f'./obj/{name}.obj')

    bounding_box = mesh.bounding_box.bounds
    min_bound, max_bound = bounding_box[0], bounding_box[1]
    num_samples = 100000
    candidates = np.random.uniform(low=min_bound, high=max_bound, size=(num_samples, 3))

    inside_points = candidates[mesh.contains(candidates)]

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(inside_points)

    o3d.io.write_point_cloud(f'./ply/{name}.ply', pcd)

    print(f"Sampled {inside_points.shape[0]} points inside the {name} mesh.")