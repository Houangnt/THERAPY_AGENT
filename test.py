import time
import numpy as np
import cv2
import PIL.Image
from scipy.interpolate import CubicSpline
from scipy.integrate import quad
from numpy.polynomial.legendre import leggauss
import os
import json

# ==================== 3D PROCESSING ====================
def read_ply_file(file_path):
    with open(file_path, "r") as f:
        for line in f:
            if line.strip() == "end_header":
                break
        points = np.loadtxt(f, dtype=np.float32)
    return points

def extract_mask_points(mask):
    ys, xs = np.where(mask > 0)
    points = np.column_stack((xs, ys))
    return points

#def _2d_to_3d(points_2d, points_3d, width=1920):
#    x = points_2d[:, 0]
#    y = points_2d[:, 1]
#    idx = y * width + x
#    surface_points = points_3d[idx]
#    nonzero_mask = np.any(surface_points != 0, axis=1)
#    surface_points = surface_points[nonzero_mask]
#    idx = idx[nonzero_mask]
#    return surface_points, idx

def _2d_to_3d(points_2d, points_3d, width=1920):
    x = points_2d[:, 0].astype(int)
    y = points_2d[:, 1].astype(int)
    idx = y * width + x
    surface_points = points_3d[idx]
    
    nonzero_mask = surface_points[:, 2] != 0
    surface_points = surface_points[nonzero_mask]
    idx = idx[nonzero_mask]
    
    return surface_points, idx

def get_3d_from_2d(points_3d, point_2d, width=1920):
    x, y = int(point_2d[0]), int(point_2d[1])
    idx = y * width + x
    if idx < 0 or idx >= len(points_3d):
        raise ValueError(f"Index {idx} out of range")
    return points_3d[idx]

def find_curve(surface_points, surface_idx, left_3d, center_3d, right_3d, threshold=0.2):
    p1 = np.array(left_3d)
    p2 = np.array(center_3d)
    p3 = np.array(right_3d)
    
    n = np.cross(p2 - p1, p3 - p1)
    n_norm = np.linalg.norm(n)
    if n_norm < 1e-8:
        raise ValueError("Points are collinear")
    n = n / n_norm
    
    distances = np.dot(surface_points - p1, n)
    mask = np.abs(distances) < threshold
    curve = surface_points[mask]
    index = surface_idx[mask]
    
    # print(f"  Found {len(curve)} curve points within {threshold}mm")
    return curve, index

def idx_to_xy(indices, width=1920):
    indices = np.asarray(indices, dtype=np.int64)
    x = indices % width
    y = indices // width
    return np.stack((x, y), axis=1)

def sort_unique_x_mean_y(curve_2d_points, round_y=False):
    pts = np.asarray(curve_2d_points)
    x_vals = pts[:, 0]
    y_vals = pts[:, 1]
    uniq_x, inv, counts = np.unique(x_vals, return_inverse=True, return_counts=True)
    sum_y = np.bincount(inv, weights=y_vals)
    mean_y = sum_y / counts
    if round_y:
        mean_y = np.rint(mean_y).astype(int)
    result = np.column_stack([uniq_x.astype(int), mean_y])
    return result

def sort_unique_y_mean_x(curve_2d_points, round_x=False):
    pts = np.asarray(curve_2d_points)
    x_vals = pts[:, 0]
    y_vals = pts[:, 1]
    uniq_y, inv, counts = np.unique(y_vals, return_inverse=True, return_counts=True)
    sum_x = np.bincount(inv, weights=x_vals)
    mean_x = sum_x / counts
    if round_x:
        mean_x = np.rint(mean_x).astype(int)
    result = np.column_stack([mean_x, uniq_y.astype(int)])
    return result

def curve_length_spline(points_3d, n_gauss=16, dedup_eps=1e-12, bc_type='natural'):
    """
    Tính độ dài đường cong 3D từ các điểm bằng spline bậc 3 (CubicSpline)
    và tích phân Gauss-Legendre (nhanh hơn nhiều so với quad).

    - n_gauss: số điểm Gauss mỗi đoạn (8, 16, 32 đều được)
    - dedup_eps: loại bỏ đoạn có chiều dài ~0
    - bc_type: điều kiện biên ('natural' hoặc 'clamped')
    """
    pts = np.asarray(points_3d, dtype=float)
    if pts.shape[0] < 2:
        return 0.0

    # Tham số s theo chiều dài dây cung
    diffs = np.diff(pts, axis=0)
    seg_len = np.linalg.norm(diffs, axis=1)
    s = np.insert(np.cumsum(seg_len), 0, 0.0)

    # Loại bỏ các điểm trùng (s không tăng)
    keep = np.insert(seg_len > dedup_eps, 0, True)
    s = s[keep]
    pts = pts[keep]

    if pts.shape[0] < 2:
        return 0.0

    # Tạo spline 3 chiều
    sx = CubicSpline(s, pts[:, 0], bc_type=bc_type)
    sy = CubicSpline(s, pts[:, 1], bc_type=bc_type)
    sz = CubicSpline(s, pts[:, 2], bc_type=bc_type)

    # Đạo hàm spline (chỉ làm 1 lần)
    sx1 = sx.derivative()
    sy1 = sy.derivative()
    sz1 = sz.derivative()

    # Lấy điểm và trọng số Gauss-Legendre trên [-1, 1]
    xg, wg = leggauss(n_gauss)

    # Tích phân theo từng đoạn spline
    total = 0.0
    for a, b in zip(s[:-1], s[1:]):
        mid = 0.5 * (a + b)
        half = 0.5 * (b - a)
        u = mid + half * xg  # ánh xạ về [a, b]

        # Tính tốc độ (đạo hàm vector)
        dx = sx1(u)
        dy = sy1(u)
        dz = sz1(u)
        speed = np.sqrt(dx*dx + dy*dy + dz*dz)

        # Cộng kết quả Gauss-Legendre
        total += half * np.dot(wg, speed)

    return float(total)

def _curve_length_spline(points_3d):
    start = time.time()
    pts = np.asarray(points_3d, dtype=float)
    if len(pts) < 2:
        return 0.0
    
    diffs = np.diff(pts, axis=0)
    seg_len = np.linalg.norm(diffs, axis=1)
    s = np.insert(np.cumsum(seg_len), 0, 0)
    print("TIME 1 ", time.time() - start)
    
    start = time.time()
    uniq_mask = np.insert(np.diff(s) > 1e-8, 0, True)
    s = s[uniq_mask]
    pts = pts[uniq_mask]
    print("TIME 2 ", time.time() - start)
    
    if len(pts) < 2:
        return 0.0
    
    start = time.time()
    sx = CubicSpline(s, pts[:, 0])
    sy = CubicSpline(s, pts[:, 1])
    sz = CubicSpline(s, pts[:, 2])
    print("TIME 3 ", time.time() - start)
    
    start = time.time()
    def speed(u):
        dx = sx.derivative()(u)
        dy = sy.derivative()(u)
        dz = sz.derivative()(u)
        return np.sqrt(dx**2 + dy**2 + dz**2)
    
    length, _ = quad(speed, s[0], s[-1], limit=500)
    print("TIME 4 ", time.time() - start)
    return float(length)

def save_points_to_ply(points, filename):
    header = (
        "ply\n"
        "format ascii 1.0\n"
        f"element vertex {len(points)}\n"
        "property float x\n"
        "property float y\n"
        "property float z\n"
        "end_header\n"
    )
    with open(filename, "w") as f:
        f.write(header)
        np.savetxt(f, points, fmt="%.6f %.6f %.6f")

def find_valid_3d_point(points_3d, start_x, start_y, direction, width, height):
    
    x, y = start_x, start_y
    max_steps = max(width, height)
    step = 0

    while 0 <= x < width and 0 <= y < height and step < max_steps:
        point_3d = get_3d_from_2d(points_3d, (x, y), width)
        # print(f"{direction} get point point_3d ", point_3d)
        # print(f"{direction} x y 2D ",  x, y)
        if sum(point_3d) != 0:  
            return (x, y), point_3d

        if direction == "left":
            x += 1
        elif direction == "right":
            x -= 1
        elif direction == "up":
            y += 1
        elif direction == "down":
            y -= 1
        step += 1
    
    # fallback_point_3d = get_3d_from_2d(points_3d, (start_x, start_y), width)
    # return (start_x, start_y), fallback_point_3d
    raise ValueError(f"Cannot find valid 3D point edges valid from ({start_x},{start_y})")

def find_valid_center(points_3d, center_2d, width, height, horizontal=True, max_steps=5):
    x, y = center_2d
    directions = ["left", "right"] if horizontal else ["up", "down"]

    for dir in directions:
        for _ in range(max_steps):
            pt_2d, pt_3d = find_valid_3d_point(points_3d, x, y, dir, width, height)
            if sum(pt_3d) != 0:  
                return pt_2d, pt_3d
            if dir == "left":
                x -= 1
            elif dir == "right":
                x += 1
            elif dir == "up":
                y -= 1
            elif dir == "down":
                y += 1

    # return center_2d, get_3d_from_2d(points_3d, center_2d, width)
    raise ValueError(f"Cannot find valid 3D point center valid from ({x},{y})")

def find_longest_horizontal_and_vertical(mask, trim_box=None):
    # Apply trim if needed
    if trim_box is not None:
        mask = mask[int(trim_box[1]):int(trim_box[3]), 
                    int(trim_box[0]):int(trim_box[2])]

    # Force to signed int to avoid wrap-around in np.diff
    bin_mask = (mask > 0).astype(np.int8)

    h, w = bin_mask.shape

    # ---------- Horizontal ----------
    padded_h = np.pad(bin_mask, ((0,0),(1,1)), constant_values=0).astype(np.int8)
    diff_h = np.diff(padded_h, axis=1)

    max_len_x = 0
    max_row = -1
    max_x_start = max_x_end = -1

    for r in range(h):
        starts = np.where(diff_h[r] == 1)[0]
        ends   = np.where(diff_h[r] == -1)[0]
        if len(starts) != len(ends):
            continue  # skip if mismatch
        if starts.size > 0:
            lengths = ends - starts
            idx = np.argmax(lengths)
            if lengths[idx] > max_len_x:
                max_len_x = lengths[idx]
                max_row = r
                max_x_start, max_x_end = starts[idx], ends[idx]

    # ---------- Vertical ----------
    padded_v = np.pad(bin_mask, ((1,1),(0,0)), constant_values=0).astype(np.int8)
    diff_v = np.diff(padded_v, axis=0)

    max_len_y = 0
    max_col = -1
    max_y_start = max_y_end = -1

    for c in range(w):
        starts = np.where(diff_v[:, c] == 1)[0]
        ends   = np.where(diff_v[:, c] == -1)[0]
        if len(starts) != len(ends):
            continue
        if starts.size > 0:
            lengths = ends - starts
            idx = np.argmax(lengths)
            if lengths[idx] > max_len_y:
                max_len_y = lengths[idx]
                max_col = c
                max_y_start, max_y_end = starts[idx], ends[idx]

    # ---------- Adjust for trim ----------
    if trim_box is not None and max_len_x > 0 and max_len_y > 0:
        max_row += int(trim_box[1])
        max_y_start += int(trim_box[1])
        max_y_end += int(trim_box[1])

        max_col += int(trim_box[0])
        max_x_start += int(trim_box[0])
        max_x_end += int(trim_box[0])

    return {
        "length": max_len_x,
        "row": max_row,
        "start_col": max_x_start,
        "end_col": max_x_end
    }, {
        "length": max_len_y,
        "col": max_col,
        "start_row": max_y_start,
        "end_row": max_y_end
    }

def plane_perpendicular_to_AB(A, B, C):
    print("A ", A, " B ", B, " C ", C)
    A = np.array(A, dtype=float)
    B = np.array(B, dtype=float)
    C = np.array(C, dtype=float)
    
    n = B - A
    nx, ny, nz = n

    D = - (nx * C[0] + ny * C[1] + nz * C[2])
    
    plane_str = f"{nx:.3f}x + {ny:.3f}y + {nz:.3f}z + ({D:.3f}) = 0"
    print("plane_str ", plane_str)
    return (nx, ny, nz, D), plane_str

import numpy as np

def distance_point_to_plane(point, plane):
    x, y, z = point
    a, b, c, d = plane

    numerator = abs(a * x + b * y + c * z + d)
    denominator = np.sqrt(a**2 + b**2 + c**2)

    distance = numerator / denominator
    return distance


def intersect_multi_planes(*planes):
    if len(planes) < 2:
        raise ValueError("At least two planes are required.")

    A = np.array([plane[:3] for plane in planes])
    d = np.array([plane[3] for plane in planes])

    print("A ", A)
    print("d ", d)

    rank_A = np.linalg.matrix_rank(A)
    augmented_rank = np.linalg.matrix_rank(np.column_stack((A, d)))

    if rank_A == 3 and augmented_rank == 3:
        intersection = np.linalg.solve(A, d)
        return {
            'type': 'intersection',
            'point': intersection
        }
    else:
        nearest_point = np.linalg.lstsq(A, d, rcond=None)[0]
        for plane in planes:
            d = distance_point_to_plane(nearest_point, plane)
            print("D ", d, " for plane ", plane)
        return {
            'type': 'approximate',
            'point': nearest_point
        }



def line_intersection_of_planes(plane1, plane2):
   
    A1, B1, C1, D1 = plane1
    A2, B2, C2, D2 = plane2

    n1 = np.array([A1, B1, C1])
    n2 = np.array([A2, B2, C2])
    

    direction = np.cross(n1, n2)
    

    A = np.array([[A1, B1],
                  [A2, B2]], dtype=float)
    b = -np.array([D1, D2], dtype=float)
    
    try:
        xy = np.linalg.solve(A, b)
        point = np.array([xy[0], xy[1], 0.0])
    except np.linalg.LinAlgError:
        A = np.array([[A1, B1],
                      [A2, B2]], dtype=float)
        b = -np.array([D1 + C1, D2 + C2], dtype=float)
        xy = np.linalg.solve(A, b)
        point = np.array([xy[0], xy[1], 1.0])
    
    return point, direction

def point_to_line_distance(P, point_on_line, direction):

    P = np.array(P, dtype=float)
    A = np.array(point_on_line, dtype=float)
    u = np.array(direction, dtype=float)
    
    AP = P - A
    cross = np.cross(AP, u)
    d = np.linalg.norm(cross) / np.linalg.norm(u)
    return d

def process_single_apple(apple_id, box, mask, img_bgr, points_3d, output_dir):
    # try:
        x0, y0, x1, y1 = [int(v) for v in box]
        height, width = mask.shape[:2]


        bbox_width  = (x1 - x0) // 2
        bbox_height = (y1 - y0) // 2
        
        # Find edge points
        start = time.time()
        h_info, v_info = find_longest_horizontal_and_vertical(mask, trim_box=box)
        # print("TIME find_longest_horizontal_and_vertical ", time.time() - start)
        # Horizontal points

        start = time.time()
        left_point = (h_info["start_col"], h_info["row"])
        right_point = (h_info["end_col"], h_info["row"])
        center_h_point = (
            int((left_point[0] + right_point[0]) / 2),
            int((left_point[1] + right_point[1]) / 2)
        )
        
        # Vertical points 
        up_point = (v_info["col"], v_info["start_row"])
        down_point = (v_info["col"], v_info["end_row"])
        center_v_point = (
            int((up_point[0] + down_point[0]) / 2),
            int((up_point[1] + down_point[1]) / 2)
        )
        # print("TIME 2d point ", time.time() - start)
        
        # print(f"  H: Left={left_point}, Right={right_point}, Center={center_h_point}")
        # print(f"  V: Up={up_point}, Down={down_point}, Center={center_v_point}")
        
        start = time.time()
        left_point, left_3d = find_valid_3d_point(points_3d, *left_point, "left", width, height)
        right_point, right_3d = find_valid_3d_point(points_3d, *right_point, "right", width, height)
        up_point, up_3d = find_valid_3d_point(points_3d, *up_point, "up", width, height)
        down_point, down_3d = find_valid_3d_point(points_3d, *down_point, "down", width, height)
        # print("TIME find_valid_up_down_left_right ", time.time() - start)
        
        start = time.time()
        center_h_point, center_h_3d = find_valid_center(points_3d, center_h_point, width, height, horizontal=True, max_steps=bbox_width)
        center_v_point, center_v_3d = find_valid_center(points_3d, center_v_point, width, height, horizontal=False, max_steps=bbox_height)

        print("left_point_3d ", left_3d, " right_point_3d ", right_3d, " center_h_3d ", center_h_3d)
        print("up_point_3d ", up_3d, " down_point_3d ", down_3d, " center_v_3d ", center_v_3d)

        # print("TIME find_valid_center ", time.time() - start)
        camera = (0.0, 0.0, 0.0) 
        center_left_right_3d = [(left_3d[0] + right_3d[0]) / 2, 
                                (left_3d[1] + right_3d[1]) / 2, 
                                (left_3d[2] + right_3d[2]) / 2]
        print('center_left_right_3d ', center_left_right_3d)
        plane1, _  = plane_perpendicular_to_AB(right_3d, left_3d, center_left_right_3d)
        plane2, _  = plane_perpendicular_to_AB(left_3d, camera, left_3d)
        plane3, _ = plane_perpendicular_to_AB(right_3d, camera, right_3d)

        result = intersect_multi_planes(plane1, plane2, plane3)
        print("result ", result)

        left_right_distance = np.linalg.norm(np.array(right_3d) - np.array(left_3d))

        if result['type'] == 'intersection':
            print("Case 1: Point intersection (ideal sphere)")
            
            center = result['point']
            
            radius = np.linalg.norm(np.array(right_3d) - center)
            
            print(f"Radius: {radius:.3f} mm")

        elif result['type'] == 'approximate':
            center = result['point']
            
            A = np.array([plane1[:3], plane2[:3], plane3[:3]])
            rank_A = np.linalg.matrix_rank(A)
            
            if rank_A == 2:
                print("Case 2: Line intersection")
                
                point_on_line, direction = line_intersection_of_planes(plane2, plane3)
                
                h = point_to_line_distance(left_3d, point_on_line, direction)
                
                half_chord = left_right_distance / 2
                radius = np.sqrt(h**2 + half_chord**2)
                
                print(f"Radius (Pythagorean) = {radius:.3f} mm")
            
            else:
                print("Case 3: No clear intersection")
                
                print(f"Approx center: {center}")
                
                r_left = np.linalg.norm(np.array(left_3d) - center)
                r_right = np.linalg.norm(np.array(right_3d) - center)
                radius = (r_left + r_right) / 2
                
                print(f"Radius left: {r_left:.3f}, right: {r_right:.3f}")
                print(f"Radius (average) = {radius:.3f} mm")
        
        # Map 2D to 3D
        start = time.time()
        points_2d = extract_mask_points(mask)
        surface_points, surface_idx = _2d_to_3d(points_2d, points_3d, width=img_bgr.shape[1])
        # print("TIME extract_mask_points ", time.time() - start)
        
        # Horizontal 3D points
        # left_3d = get_3d_from_2d(points_3d, left_point)
        #center_h_3d = get_3d_from_2d(points_3d, center_h_point)
        # right_3d = get_3d_from_2d(points_3d, right_point)
        
        # Vertical 3D points
        # up_3d = get_3d_from_2d(points_3d, up_point)
        #center_v_3d = get_3d_from_2d(points_3d, center_v_point)
        # down_3d = get_3d_from_2d(points_3d, down_point)
        
        # ===== HORIZONTAL CURVE =====
        # print("  Processing horizontal curve...")
        # print('====================================================')
        start = time.time()
        _, curve_h_idx = find_curve(surface_points, surface_idx, left_3d, center_h_3d, right_3d)
        # print("TIME find_curve horizontal ", time.time() - start)
        start = time.time()
        curve_h_2d = idx_to_xy(curve_h_idx, width=img_bgr.shape[1])
        # print("TIME idx_to_xy horizontal ", time.time() - start)
        start = time.time()
        curve_h_2d = sort_unique_x_mean_y(curve_h_2d, round_y=True)
        # print("TIME sort_unique_x_mean_y horizontal ", time.time() - start)

        start = time.time()
        curve_h_3d, _ = _2d_to_3d(curve_h_2d, points_3d, width=img_bgr.shape[1])
        # print("TIME _2d_to_3d horizontal ", time.time() - start)

        start = time.time()
        diffs_h = np.diff(curve_h_3d, axis=0)
        seg_lengths_h = np.linalg.norm(diffs_h, axis=1)
        length_h_direct = float(seg_lengths_h.sum())
        # print("TIME curve_length_sum_direct horizontal ", time.time() - start)
        

        start = time.time()
        length_h_spline = curve_length_spline(curve_h_3d)
        # print("TIME curve_length_spline horizontal ", time.time() - start)
        
        diameter_h = np.linalg.norm(np.array(right_3d) - np.array(left_3d))

        print("length_h_spline ", length_h_spline , " length_h_direct ", length_h_direct)
        # print('====================================================')
        

        # print(f"  H Length: {length_h_spline:.2f}mm (spline), {len(curve_h_3d)} points")
        print(f"H diameter_h : {diameter_h}")

        # ===== VERTICAL CURVE =====
        # print("  Processing vertical curve...")
        start = time.time()
        _, curve_v_idx = find_curve(surface_points, surface_idx, up_3d, center_v_3d, down_3d)
        curve_v_2d = idx_to_xy(curve_v_idx, width=img_bgr.shape[1])
        curve_v_2d = sort_unique_y_mean_x(curve_v_2d, round_x=True)
        
   
                
        curve_v_3d, _ = _2d_to_3d(curve_v_2d, points_3d, width=img_bgr.shape[1])
        
        diffs_v = np.diff(curve_v_3d, axis=0)
        seg_lengths_v = np.linalg.norm(diffs_v, axis=1)
        length_v_direct = float(seg_lengths_v.sum())
        length_v_spline = curve_length_spline(curve_v_3d)
        diameter_v = np.linalg.norm(np.array(down_3d) - np.array(up_3d))
        # print("TIME curve_vertical ", time.time() - start)
        print("length_v_spline ", length_v_spline , " length_v_direct ", length_v_direct)

        # print(f"  V Length: {length_v_spline:.2f}mm (spline), {len(curve_v_3d)} points")
        print(f"V diameter_v : {diameter_v}")
        # print("Vertical curve visualization saved with diameter and length")  
        return {
            "id": apple_id,
            "bbox": box,
            # Horizontal
            "left_2d": left_point,
            "right_2d": right_point,
            "center_h_2d": center_h_point,
            "left_3d": left_3d.tolist(),
            "center_h_3d": center_h_3d.tolist(),
            "right_3d": right_3d.tolist(),
            "length_h_direct": length_h_direct,
            "length_h_spline": length_h_spline,
            "curve_h_points": len(curve_h_3d),
            "curve_h_2d": curve_h_2d,
            "diameter_h": diameter_h,
            # Vertical
            "up_2d": up_point,
            "down_2d": down_point,
            "center_v_2d": center_v_point,
            "up_3d": up_3d.tolist(),
            "center_v_3d": center_v_3d.tolist(),
            "down_3d": down_3d.tolist(),
            "length_v_direct": length_v_direct,
            "length_v_spline": length_v_spline,
            "curve_v_points": len(curve_v_3d),
            "curve_v_2d": curve_v_2d,
            "diameter_v": diameter_v,
            "success": True
        }
        
    # except Exception as e:
    #     print(f"  ERROR: {str(e)}")
    #     return {
    #         "id": apple_id,
    #         "bbox": box,
    #         "success": False,
    #         "error": str(e)
    #     }