import res.ukf
from scipy.io import loadmat
import os
import matplotlib.pyplot as plt
import numpy as np


# %%md define state transition function

def stateTransition(x0, u):
    q_sp = x0[0, 0]
    q_bp = x0[0, 1]
    q_bn = x0[0, 1]
    q_sn = x0[0, 1]
    V_o = x0[0, 1]
    V_np = x0[0, 1]
    V_nn = x0[0, 1]
    return np.vstack([q_sp, q_bp, q_bn, q_sn, V_o, V_np, V_nn])


def observationModel(x0):
    V = 0
    return V


# %% md
# Load data
x = loadmat('../data/NASA_datasets/'
            'Battery_Uniform_Distribution_Charge_Discharge_DataSet_2Post/'
            'data/Matlab/RW9.mat')

# %% md
# Save to variables and then use them IMPORTANT: [i][j][0] will lead to the content
# ([0]) of row i, column j
data = x['data']

print('Procedure:\n', x['data']['procedure'][0][0][0])
print('Description:\n', x['data']['description'][0][0][0])

steps = x['data']['step'][0][0][0]
