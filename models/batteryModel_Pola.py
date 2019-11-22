from res.ukf import UnscentedKalmanFilter
import numpy as np
from scipy.io import loadmat
from scipy.integrate import cumtrapz
import matplotlib.pyplot as plt

from functools import partial


def F1D1D_withParameters(x, u, val=10.0):
    return np.vstack([x[0, 0] + val])


def F2D2D_linearModel(x, u):
    return np.vstack([x[0, 0] + u[0, 0],
                      x[1, 0] + u[0, 0]])


def F2D2D_PolaModel_process(x, u, dt=1.0, Ecrit=1389900.0):
    vk = u[0, 0]
    ik = u[1, 0]
    return np.vstack([x[0, 0],
                      x[1, 0] - vk * ik * dt * np.power(Ecrit, -1)])


def H2D2D_cartesianToPolar(x):
    r = np.sqrt(x[0, 0] ** 2 + x[1, 0] ** 2)
    theta = np.arctan2(x[1, 0], x[0, 0])
    return np.vstack([r, theta])


def H2D1D_distance(x):
    return np.vstack([np.sqrt(np.power(x[0, 0], 2) + np.power(x[1, 0], 2))])


def H2D1D_PolaModel_observation(x, u, alpha=0.0053193, beta=11.505, gamma=1.5538, vo=41.405, vl=33.481):
    return np.vstack([vl + (vo - vl) * np.exp(gamma * (x[1, 0] - 1)) + alpha * vl * (x[1, 0] - 1)
                      + (1 - alpha) * vl * (np.exp(-beta) - np.exp(-beta * np.sqrt(x[1, 0]))) - u[1, 0] * x[0, 0]])


# %% Import data
DB = 1

if DB == 1:
    x = loadmat('../data/Filtering_Algorithm/Ground_truth/PO2016.mat')
elif DB == 2:
    x = loadmat('../data/Filtering_Algorithm/Ground_truth/SANCRIS.mat')
elif DB == 3:
    x = loadmat('../data/Filtering_Algorithm/Ground_truth/POU.mat')

I = x['I']
V = x['V']

# SOC from data
P = np.multiply(V, I)
P_cum = cumtrapz(P, axis=0)
SOC = 1 - P_cum / P_cum[-1, 0]

# plot
fig = plt.figure(figsize=(19, 6))

plt.subplot(131)
plt.plot(I)
plt.xlabel('Time')
plt.ylabel('Current [A]')
plt.title('Current profile')

plt.subplot(132)
plt.plot(V)
plt.xlabel('Time')
plt.ylabel('Voltage [V]')
plt.title('Voltage profile')

plt.subplot(133)
plt.plot(SOC)
plt.xlabel('Time')
plt.ylabel('SOC')
plt.title('SOC profile')

# %% Model and filter parameters
alpha = 0.0053193
beta = 11.505
gamma = 1.5538
vo = 41.405
vl = 33.481
Ecrit = 1389900.0

w1 = 5e-8
w2 = 1e-6
eta = .9
dt = 1.0

# Process and observation noises
Q = np.array([[w1, 0.0], [0.0, w2]])
R = np.array([[eta]])

# Filter initial conditions
x0 = np.vstack([0.26, 0.85])
p0 = np.array([[2e-4**2.0, .0], [.0, 1e-3**2.0]])
uk0 = np.vstack([V[0, 0], I[0, 0]])

# Adjust default model parameters
F2D2D_PolaModel_process = partial(F2D2D_PolaModel_process, dt=dt, Ecrit=Ecrit)
H2D1D_PolaModel_observation = partial(H2D1D_PolaModel_observation, alpha=alpha, beta=beta, gamma=gamma,
                                      vo=vo, vl=vl)

ukf = UnscentedKalmanFilter(F2D2D_PolaModel_process, x0, p0, h=H2D1D_PolaModel_observation, process_noise=Q,
                            observation_noise=R, input_at_output=True, uk0=uk0, recycle_sigma_points=False,
                            kappa=1.0)

# %% Do the thing TODO there is an issue, a NaN appears at k=6323

xPosteriori = list()
socEstimate = list()

for k, (Vk1, Ik1) in enumerate(zip(V[1:], I[1:])):
    print("Iteration", k)
    Vk0 = V[k - 1, 0]
    Ik0 = I[k - 1, 0]
    try:
        xP, P = ukf.aPosterioriEstimation(np.vstack([Vk0, Ik0]), np.vstack([Vk1]), internal=True)
        print("A posteriori estimation:\n", xP)
        print("A posteriori process covariance:\n", P, "\n")
        xPosteriori.append(xP)
        socEstimate.append(xP[1, 0])
    except Exception:
        break


plt.plot(socEstimate)
plt.show()
