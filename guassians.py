import math

import numpy as np
import pygame


def scale_matrix(sx,sy,sz):
    return np.array([
        [sx, 0, 0],
        [0, sy, 0],
        [0, 0, sz]
    ])


#IMPORTANT:  make fucking sure its in radians

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

center = np.array([0.0, 0.0, 0.0])
scale = np.array([1.5, 0.4, 0.4])
S = np.diag(scale)
R = np.eye(3)
Sigma = R @ (S @ S.T) @ R.T

def compute_2d_covariance(center_cam, Sigma_3d, fx, fy):
    """

    :param center_cam: (x,y,z) position of the splat center relative to the camera
    :param Sigma_3d: (3, 3)( world covariance
    :param fx: camera focal length x
    :param fy: camera focal length y
    :return:
    """

    tx, ty, tz = center_cam
    J = np.array([
        [fx/tz, 0.0, -(fx*tx)/(tz * tz)],
        [0.0, fy/tz, -(fy*ty)/(tz * tz)],
    ], dtype=np.float32)

    Sigma_2d = J @ Sigma_3d @ J.T
    Sigma_2d[0, 0] += 0.3
    Sigma_2d[1, 1] += 0.3

def extract_ellipse_params(Sigma_2d):
    a = float(Sigma_2d[0, 0])
    b = float(Sigma_2d[0, 1])
    c = float(Sigma_2d[1, 1])

    trace = a + c
    diff = a-c
    discriminate = math.sqrt(max(0.0, diff * diff + 4.0 * b * b))

    lambda_a = (trace + discriminate)/2
    lambda_b = (trace - discriminate)/2

    r_major = 3*math.sqrt(max(0.0, lambda_a))
    r_minor = 3*math.sqrt(max(0.0, lambda_b))

    theta = 0.5*np.atan2(2.0 * b, diff)
    theta_deg = math.degrees(theta)

    return r_major, r_minor, theta_deg

def draw_gaussian_splat(target_surface, center_plx, r_major, r_minor, angle_deg, base_color=(0, 220, 255)):
    int_w = max(4, int(r_major * 2) + 10)
    int_h = max(4, int(r_minor * 2) + 10)
    ellipse_surf = pygame.Surface((int_w, int_h), pygame.SRCALPHA)
    surf_center = (int_w // 2, int_h // 2)

    rings = 8
    for i in range(rings, 0, -1):
        fraction = i / rings
        alpha = int(255 * (1.0 - fraction) ** 1.8)
        color = (*base_color, max(10, alpha))

        curr_w = max(2, int(r_major * 2 * fraction))
        curr_h = max(2, int(r_minor * 2 * fraction))

        rect = pygame.Rect(0, 0, curr_w, curr_h)
        rect.center = surf_center
        pygame.draw.ellipse(ellipse_surf, color, rect)

    rotated_surf = pygame.transform.rotozoom(ellipse_surf, -angle_deg, 1.0)

    dest_rect = rotated_surf.get_rect(center=center_plx)
    target_surface.blit(rotated_surf, dest_rect)