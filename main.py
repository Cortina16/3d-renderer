import sys

import numpy as np
import pygame

WIDTH = 800
HEIGHT = 400
FPS = 60

# CUBE_VERTICIES = np.array([
#     [-1, -1, -1, 1],
#     [ 1, -1, -1, 1],
#     [ 1,  1, -1, 1],
#     [-1,  1, -1, 1],
#     [-1,  1,  1, 1],
#     [-1, -1,  1, 1],
#     [ 1, -1,  1, 1],
#     [ 1,  1,  1, 1],
# ], dtype=np.float32).T
#
# EDGES = [
#     (0, 1), (1, 2), (2, 3), (3, 0),  # Back face
#     (4, 5), (5, 6), (6, 7), (7, 4),  # Front face
#     (0, 5), (1, 6), (2, 7), (3, 4)  # Lateral connectors
#
# ]
def load_obj(filename):
    verticies = []
    edges = set()
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            prefix = parts[0]
            if prefix == 'v':
                x, y, z = map(float, parts[1:4])
                verticies.append([x, y, z, 1.0])
            elif prefix == 'f':
                face_indecies = []
                for tokens in parts[1:]:
                    v_idx = int(tokens.split('/')[0])
                    if v_idx < 0:
                        v_idx = len(verticies) + v_idx
                    else:
                        v_idx -= 1
                    face_indecies.append(v_idx)

                num_verts = len(face_indecies)
                for i in range(num_verts):
                    u = face_indecies[i]
                    v = face_indecies[(i+1) % num_verts]
                    edges.add(tuple(sorted((u,v))))
    verts_arr = np.array(verticies, dtype=np.float32)
    xyz = verts_arr[:, :3]
    min_bound = xyz.min(axis=0)
    max_bound = xyz.max(axis=0)
    center = (min_bound + max_bound) / 2.0
    scale = (max_bound - min_bound).max() / 2.0
    if scale > 0:
        verts_arr[:, :3] = (xyz - center) / scale
    return verts_arr.T, list(edges)


VERTICIES, EDGES = load_obj('teapot.obj')
def translate_matrix(x,y,z):
    return np.array([
        [1, 0, 0, x],
        [0, 1, 0, y],
        [0, 0, 1, z],
        [0, 0, 0, 1]
    ])

def rotate_x(theta):
    return np.array([
        [1, 0, 0, 0],
        [0, np.cos(theta), -np.sin(theta), 0],
        [0, np.sin(theta), np.cos(theta), 0],
        [0, 0, 0, 1]
    ])

def rotate_y(theta):
    return np.array([
        [np.cos(theta), 0, np.sin(theta), 0],
        [0, 1, 0 , 0],
        [-np.sin(theta), 0, np.cos(theta), 0],
        [0, 0, 0, 1],
    ])

def rotate_z(theta):
    return np.array([
        [np.cos(theta), -np.sin(theta), 0, 0],
        [np.sin(theta), np.cos(theta), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ])

def scaling_matrix(fov, aspect_ratio):
    f = 1/np.tan(np.radians(fov)/2)
    return np.array([
        [f/aspect_ratio, 0, 0, 0],
        [0, f, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 1, 0],
    ])


def main():
    pygame.init()
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("3D Matrix Wireframe Engine")
    clock = pygame.time.Clock()

    aspect_ratio = WIDTH / HEIGHT
    proj_matrix = scaling_matrix(65.0, aspect_ratio)

    angle_x = 0.0
    angle_y = 0.0
    distance = 3.5 #distance from cube cneter to cam
    is_dragging = False

    SENSITIVITY = 0.005


    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    is_dragging = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    is_dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if is_dragging:
                    dx, dy = event.rel
                    angle_y += dx * SENSITIVITY
                    angle_x += dy * SENSITIVITY
            elif event.type == pygame.MOUSEWHEEL:
                distance -= event.y * 0.3
                distance = max(1.5, min(distance, 15.0))
        # angle_x += 0.015
        # angle_y += 0.02

        rot_x = rotate_x(angle_x)
        rot_y = rotate_y(angle_y)

        rot_mat = rot_y @ rot_x

        move_t = translate_matrix(0.0, 0.0, distance)
        m_view = move_t @ rot_mat

        M_composite = proj_matrix @ m_view

        projected = M_composite @ VERTICIES

        w = projected[3, :]
        valid_mask = w > 0.1
        screen_coords = {}
        for i in range(projected.shape[1]):
            if valid_mask[i]:
                ndc_x = projected[0, i] / w[i]
                ndc_y = projected[1, i] / w[i]
                px = int((ndc_x + 1.0) * 0.5 * WIDTH)
                py = int((1.0 - (ndc_y + 1.0) * 0.5) * HEIGHT)
                screen_coords[i] = (px, py)

        screen.fill((0, 0, 0))
        for u, v in EDGES:
            if u in screen_coords and v in screen_coords:
                if (u, v) == (0, 4):
                    pygame.draw.line(screen, (255, 0, 255), screen_coords[u], screen_coords[v], 2)
                else:
                    pygame.draw.line(screen, (0, 220, 255), screen_coords[u], screen_coords[v], 2)

        # for idx, pt in screen_coords.items():
            # pygame.draw.circle(screen, (255, 100, 150), pt, 5)

        pygame.display.flip()
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
