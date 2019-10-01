import res.ukf
from scipy.io import loadmat
import os
import matplotlib.pyplot as plt
import numpy as np

# %% md
# Load data
x = loadmat('../data/NASA_datasets/'
            'Battery_Uniform_Distribution_Charge_Discharge_DataSet_2Post/'
            'data/Matlab/RW9.mat')

# %% md
# Save to variables and then use them IMPORTANT: [i][j][0] will lead to the content ([0]) of row i, column j
data = x['data']

print('Procedure:\n', x['data']['procedure'][0][0][0])
print('Description:\n', x['data']['description'][0][0][0])

steps = x['data']['step'][0][0][0]

# %% md An example of the low current discharge data
inds = []

for i, commentArr in enumerate(steps['comment']):
    if commentArr[0] == 'low current discharge at 0.04A':
        inds.append(i)

RT = steps['relativeTime'][inds[0]][0] / 3600.0
V = steps['voltage'][inds[0]][0]
I = steps['current'][inds[0]][0]

plt.subplot(121)
plt.plot(RT, V)
plt.title('Voltage for low current discharge')
plt.xlabel('Time (h)')
plt.ylabel('Voltage (V)')

plt.subplot(122)
plt.plot(RT, I)
plt.title('Current for low current discharge')
plt.xlabel('Time (h)')
plt.ylabel('Voltage (V)')

plt.show()

# %% md Next, the constant load profiles that are run after every 50 random walk

for i, commentArr in enumerate(steps['comment']):
    if commentArr[0] == 'reference discharge':
        RT = steps['relativeTime'][i][0] / 3600.0
        V = steps['voltage'][i][0]
        I = steps['current'][i][0]
        plt.plot(RT, V, 'k')

plt.xlim([-.1, 2.5])
plt.ylim([3, 4.25])
plt.xlabel('Time (h)')
plt.ylabel('Voltage (V)')
plt.title('Reference Discharge Profiles')

plt.show()

# %% md We can benchmark the battery’s capacity by integrating current over the
# reference cycles. The next plot shows this capacity measurement vs date.

date = []
capacity = []
for i, commentArr in enumerate(steps['comment']):
    if commentArr[0] == 'reference discharge':
        # date.append(steps['date'][i][0])
        date.append(i)
        capacity.append(np.trapz(steps['current'][i][0],
                        x=steps['relativeTime'][i][0] / 3600.0))

plt.plot(date, capacity, 'o')
plt.xlabel('Date')
plt.ylabel('Capacity (Ah)')
plt.title('Degradation of Measured Capacity')
plt.show()


