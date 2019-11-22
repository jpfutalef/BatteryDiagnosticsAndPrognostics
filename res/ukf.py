import numpy as np
from scipy.linalg import sqrtm as msqrt


class UnscentedKalmanFilter:
    def __init__(self, f, x0, p0, h=None, process_noise=None, observation_noise=None, uk0=None,
                 recycle_sigma_points=True, kappa=1.0, input_at_output=False):
        # TODO add doc. h=None returns the state (identity)
        self.processFunction = f
        self.x0 = x0
        self.p0 = p0

        if h is None:
            self.observationFunction = lambda x: x

        else:
            self.observationFunction = h

        self.recycleSigmaPoints = recycle_sigma_points
        self.kappa = kappa

        # Covariance matrices
        if process_noise is None:
            self.processNoise = np.eye(self.stateDimension)
        else:
            self.processNoise = process_noise

        if observation_noise is None:
            self.observationNoise = np.eye(self.outputDimension)
        else:
            self.observationNoise = observation_noise

        # Initial input
        if uk0 is None:
            self.uk0 = np.vstack([.0])
        else:
            self.uk0 = np.vstack([uk0])

        # If observation model requires the input, the following must be true
        if input_at_output:
            self.inputAtOutput = True
        else:
            self.inputAtOutput = False

        # Calculated from inputs
        self.stateDimension = np.size(x0)
        if input_at_output:
            self.outputDimension = np.size(self.observationFunction(x0, uk0))
        else:
            self.outputDimension = np.size(self.observationFunction(x0))

        # Create sigma points matrices
        self.X = np.zeros([self.stateDimension, 2 * self.stateDimension + 1])  # stores sigma points
        self.priorX = np.zeros([self.stateDimension, 2 * self.stateDimension + 1])  # stores evaluated sigma points
        self.priorX_extended = np.zeros(
            [self.stateDimension, 4 * self.stateDimension + 1])  # stores extended evaluated sigma points
        self.priorY = np.zeros(
            [self.outputDimension, 2 * self.stateDimension + 1])  # stores not extended evaluated sigma points
        self.priorY_extended = np.zeros(
            [self.outputDimension, 4 * self.stateDimension + 1])  # stores extended evaluated sigma points

        # Sigma points weights
        self.weights = np.zeros([1, 2 * self.stateDimension + 1])  # stores weights
        self.gamma = self.stateDimension + kappa  # L+kappa
        self.sqrtGamma = np.sqrt(self.gamma)  # sqrt(L+kappa)

        self.weights_extended = np.zeros([1, 4 * self.stateDimension + 1])  # stores weights
        self.gamma_extended = self.stateDimension + kappa  # L+kappa
        self.sqrtGamma_extended = np.sqrt(self.gamma)  # sqrt(L+kappa)

        self.updateWeights(kappa)

        # prior vectors
        self.x1_prior = x0
        self.p1_prior = p0

        if input_at_output:
            self.y_prior = self.observationFunction(x0, uk0)
        else:
            self.y_prior = self.observationFunction(x0)

        # Matrices
        self.pyy = np.zeros_like(self.observationNoise)
        self.pxy = np.zeros((self.stateDimension, self.outputDimension))
        self.kalmanGain = np.zeros((self.stateDimension, self.outputDimension))

    def updateWeights(self, kappa):
        # Non-extended
        self.kappa = kappa
        self.gamma = self.stateDimension + kappa  # L+kappa
        self.sqrtGamma = np.sqrt(self.gamma)

        self.weights[0, 0] = kappa / self.gamma

        for i in range(0, self.stateDimension):
            self.weights[:, i + 1] = 1 / (2.0 * self.gamma)
            self.weights[:, i + self.stateDimension + 1] = 1 / (2.0 * self.gamma)

        # Extended
        self.gamma_extended = 2 * self.stateDimension + kappa  # L+kappa
        self.sqrtGamma_extended = np.sqrt(self.gamma_extended)

        self.weights_extended[0, 0] = kappa / self.gamma_extended

        for i in range(0, self.stateDimension):
            self.weights_extended[:, i + 1] = 1 / (2.0 * self.gamma_extended)
            self.weights_extended[:, i + self.stateDimension + 1] = 1 / (2.0 * self.gamma_extended)
            self.weights_extended[:, i + 2 * self.stateDimension + 1] = 1 / (2.0 * self.gamma_extended)
            self.weights_extended[:, i + 3 * self.stateDimension + 1] = 1 / (2.0 * self.gamma_extended)

    def unscentedTransform(self, x, p, x_matrix):
        sP = msqrt(p)
        x_matrix[:, 0] = x[:, 0]

        for i in range(0, self.stateDimension):
            x_matrix[:, i + 1] = x[:, 0] + self.sqrtGamma * sP[:, i]
            x_matrix[:, i + 1 + self.stateDimension] = x[:, 0] - self.sqrtGamma * sP[:, i]

        return x_matrix

    def unscentedTransformExtended(self, x_matrix_old, x_matrix_new, p):
        sP = msqrt(p)
        x_matrix_new[:, 0] = x_matrix_old[:, 0]

        for i in range(0, 2 * self.stateDimension):
            if i < self.stateDimension:
                x_matrix_new[:, i + 1] = x_matrix_old[:, i + 1]
                x_matrix_new[:, i + 1 + self.stateDimension] = x_matrix_old[:, i + 1 + self.stateDimension]
            else:
                x_matrix_new[:, i + 1 + self.stateDimension] = x_matrix_new[:, 0] + \
                                                               self.sqrtGamma_extended * sP[:, i - self.stateDimension]
                x_matrix_new[:, i + 1 + 2 * self.stateDimension] = \
                    x_matrix_new[:, 0] - self.sqrtGamma_extended * sP[:, i - self.stateDimension]
        return x_matrix_new

    def aPosterioriEstimation(self, uk0, yk1, internal=False, process_noise=None, observation_noise=None):
        # Update process and observation noises
        if process_noise is not None:
            self.processNoise = process_noise

        if observation_noise is not None:
            self.observationNoise = observation_noise

        # Update input
        self.uk0 = uk0

        # Obtain sigma points from previous a posteriori estimation
        self.unscentedTransform(self.x0, self.p0, self.X)

        # Evaluate sigma points
        for i in range(0, np.size(self.X, 1)):
            self.priorX[:, i] = self.processFunction(np.vstack(self.X[:, i]), self.uk0)[:, 0]

        # Obtain prior values
        self.x1_prior = weightedSum(self.priorX, self.weights)
        self.p1_prior = np.copy(self.processNoise)
        for i in range(0, np.size(self.priorX, 1)):
            v = np.vstack(self.priorX[:, i]) - self.x1_prior
            self.p1_prior += self.weights[:, i] * np.outer(v, v)

        # Propagate prediction
        if self.recycleSigmaPoints:
            self.unscentedTransformExtended(self.priorX, self.priorX_extended, self.processNoise)
            if self.inputAtOutput:
                for i in range(0, np.size(self.priorX_extended, 1)):
                    self.priorY_extended[:, i] = self.observationFunction(np.vstack(self.priorX_extended[:, i]),
                                                                          uk0)[:, 0]
            else:
                for i in range(0, np.size(self.priorX_extended, 1)):
                    self.priorY_extended[:, i] = self.observationFunction(np.vstack(self.priorX_extended[:, i]))[:, 0]

            self.y_prior = weightedSum(self.priorY_extended, self.weights_extended)

        else:
            if self.inputAtOutput:
                for i in range(0, np.size(self.priorX, 1)):
                    self.priorY[:, i] = self.observationFunction(np.vstack(self.priorX[:, i]), uk0)[:, 0]
            else:
                for i in range(0, np.size(self.priorX, 1)):
                    self.priorY[:, i] = self.observationFunction(np.vstack(self.priorX[:, i]))[:, 0]

            self.y_prior = weightedSum(self.priorY, self.weights)

        # Update equations
        self.pyy = np.copy(self.observationNoise)
        self.pxy = np.zeros((self.stateDimension, self.outputDimension))

        if self.recycleSigmaPoints:
            for i in range(0, np.size(self.priorY_extended, 1)):
                v = np.vstack(self.priorY_extended[:, i]) - self.y_prior
                self.pyy += self.weights_extended[0, i] * np.outer(v, v)

                w = np.vstack(self.priorX_extended[:, i]) - self.x1_prior
                ww = np.vstack(self.priorY_extended[:, i]) - self.y_prior
                self.pxy = self.weights_extended[0, i] * np.outer(w, ww)

        else:
            for i in range(0, np.size(self.priorY, 1)):
                v = np.vstack(self.priorY[:, i]) - self.y_prior
                self.pyy += self.weights[0, i] * np.outer(v, v)

                w = np.vstack(self.priorX[:, i]) - self.x1_prior
                ww = np.vstack(self.priorY[:, i]) - self.y_prior
                self.pxy = self.weights[0, i] * np.outer(w, ww)

        self.kalmanGain = np.matmul(self.pxy, np.linalg.inv(self.pyy))
        xk1 = self.x1_prior + np.matmul(self.kalmanGain, yk1 - self.y_prior)
        Pk1 = self.p1_prior - np.matmul(np.matmul(self.kalmanGain, self.pyy), self.kalmanGain.T)

        if internal:
            self.x0 = xk1
            self.p0 = Pk1

        return xk1, Pk1


def weightedSum(X, W):
    return np.vstack(np.average(X, axis=1, weights=W[0, :]))
