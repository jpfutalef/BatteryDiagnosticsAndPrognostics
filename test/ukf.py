import res.ukf
import numpy as np


# A 2-D test for the UKF implementation

def F2D2D_linearModel(x, u):
    return np.vstack([x[0, 0] + u[0, 0],
                      x[1, 0] + u[0, 0]])


def H2D2D_cartesianToPolar(x):
    r = np.sqrt(x[0, 0] ** 2 + x[1, 0] ** 2)
    theta = np.arctan2(x[1, 0], x[0, 0])
    return np.vstack([r, theta])


def H2D1D_distance(x):
    return np.vstack([np.sqrt(np.power(x[0, 0], 2) + np.power(x[1, 0], 2))])


ukf = res.ukf.UnscentedKalmanFilter(F2D2D_linearModel, np.vstack([1, 2]), np.eye(2), h=H2D1D_distance)

x1, P1 = ukf.aPosterioriEstimation(np.vstack([1.0]), np.vstack([1.1]))

print(x1)
