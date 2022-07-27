import open3d as o3d
import numpy as np

pcl = o3d.geometry.PointCloud()
pcl.points = o3d.utility.Vector3dVector(np.random.randn(500000,3))

o3d.visualization.draw_geometries([pcl])

numpy_points = np.asarray(pcl.points)
pcl.points = numpy_points
