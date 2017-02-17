from __future__ import division
import sys, os, math, random
from sklearn import datasets
import numpy as np

# Import helper functions
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, dir_path + "/../")
from helper_functions import euclidean_distance, normalize, calculate_covariance_matrix
sys.path.insert(0, dir_path + "/../unsupervised_learning/")
from principal_component_analysis import PCA


class GaussianMixtureModel():
	def __init__(self, k=2, max_iterations=500, tolerance=1e-3):
		self.k = k
		self.parameters = []
		self.max_iterations = max_iterations
		self.tolerance = tolerance
		self.likelihoods = []
		self.sample_assignments = None
		self.responsibility = None

	# Initialize gaussian randomly
	def _init_random_gaussians(self, X):
		n_samples = np.shape(X)[0]
		self.mixing_probs = (1/self.k) * np.ones(self.k)
		for i in range(self.k):
			params = {}
			params["mean"] = X[np.random.choice(range(n_samples))]
			params["covar"] = calculate_covariance_matrix(X)
			self.parameters.append(params)

	# Likelihood 
	def multivariate_gaussian(self, X, params):
		n_features = np.shape(X)[1]
		mean = params["mean"]
		covar = params["covar"]
		determinant = np.linalg.det(covar)
		likelihoods = np.zeros(np.shape(X)[0])
		for i, sample in enumerate(X):
			d = n_features # dimension
			coeff = (1.0 / (math.pow((2.0*math.pi),d/2) * math.sqrt(determinant)))
			exponent = math.exp(-0.5*(sample-mean).reshape((1, n_features)).dot(np.linalg.inv(covar)).dot((sample - mean)))
			likelihoods[i] = coeff*exponent

		return likelihoods

	# Calculate the likelihood over all samples
	def _get_likelihoods(self, X):
		n_samples = np.shape(X)[0]
		likelihoods = np.zeros((n_samples, self.k))
		for i in range(self.k):
			likelihoods[:, i] = self.multivariate_gaussian(X, self.parameters[i])
		return likelihoods

	# Calculate the responsibility
	def _expectation(self, X):
		weighted_likelihoods = self.mixing_probs * self._get_likelihoods(X)
		self.likelihoods.append(weighted_likelihoods.sum()) # Save value for convergence check
		weighted_likelihoods /= weighted_likelihoods.sum(axis=1)[:, np.newaxis] # Normalize
		self.sample_assignments = weighted_likelihoods.argmax(axis=1) # Assign samples to cluster that maximizes likelihood
		self.responsibility = weighted_likelihoods

	# Update the parameters and mixing_probs
	def _maximization(self, X):
		for i in range(self.k):
			resp = self.responsibility[:, i][:, np.newaxis]
			mean = (resp * X).sum(axis=0) / resp.sum()
			covariance = (X - mean).T.dot((X - mean)*resp) / resp.sum()
			self.parameters[i]["mean"], self.parameters[i]["cov"] = mean, covariance

		# Update weights
		mixing_probs = self.responsibility.sum(axis=0)
		self.mixing_probs = np.mean(mixing_probs)

	# Covergence if likehood - last_likelihood < tolerance
	def _converged(self, X):
		if len(self.likelihoods) < 2:
			return False
		diff = math.fabs((self.likelihoods[-1] - self.likelihoods[-2]).sum())
		print "Likelihood update: %s (%s)" %  (diff, self.tolerance)
		return (len(self.likelihoods) >= 2) and (diff <= self.tolerance)

	# Do GMM and return the cluster indices
	def predict(self, X):
		# Initialize the gaussians randomly
		self._init_random_gaussians(X)

		# Run EM until convergence or for max iterations
		for _ in range(self.max_iterations):
			self._expectation(X) 	# E-step
			self._maximization(X) 	# M-step

			# Check convergence
			if self._converged(X):
				break

		# Make new assignments and return them
		self._expectation(X)
		return self.sample_assignments
			


# Demo
def main():
    # Load the dataset
    data = datasets.load_digits()
    X = normalize(data.data)
    y = data.target

    # Reduce dimensionality
    pca = PCA()
    X_transform = pca.transform(X, n_components=10)

    # Cluster the data using K-Means
    clf = GaussianMixtureModel(k=10)
    y_pred = clf.predict(X_transform)
    
    pca.plot_in_2d(X, y_pred)
    pca.plot_in_2d(X, y)


if __name__ == "__main__": main()

