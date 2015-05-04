from scipy.optimize import minimize
import math
import random
import autograd.numpy as np
from autograd.numpy import sum
from autograd import grad, hessian_vector_product

from sum_product import compute_sfs
from demography import make_demography
from likelihood_surface import CompositeLogLikelihood as LogLik


def test_regularization():
    num_runs = 1000
    def get_demo(t0,t1):
        return make_demography("-I 3 5 5 5 -ej $0 1 2 -ej $1 2 3", np.exp(t0),np.exp(t0) + np.exp(t1))
    true_x = np.array([np.log(.5),np.log(.2)])
    true_demo = get_demo(*true_x)
    sfs_list = true_demo.simulate_sfs(num_runs, theta=None)    

    #log_lik = LogLik(sfs_list, lambda x: get_demo(*x), theta=1.0, eps=1e-100)
    #log_lik = LogLik(sfs_list, lambda x: get_demo(*x), theta=1.0, eps=1e-10)
    log_lik = LogLik(sfs_list, lambda x: get_demo(*x), theta=1.0, eps=1e-6)
    #log_lik = LogLik(sfs_list, lambda x: get_demo(*x), theta=1.0, eps=0)

    f = lambda x: -log_lik.log_likelihood(x)
    g, hp = grad(f), hessian_vector_product(f)
    def f_verbose(x):
        # for verbose output during the gradient descent
        print (x - true_x) / true_x
        return f(x)

    optimize_res = minimize(f_verbose, np.array([np.log(.1),np.log(100.)]), jac=g, hessp=hp, method='newton-cg')
    print optimize_res
    inferred_x = optimize_res.x
    error = (true_x - inferred_x) / true_x
    print "# Truth:\n", true_x
    print "# Inferred:\n", inferred_x
    print "# Max Relative Error: %f" % max(abs(error))
    print "# Relative Error:","\n", error

    assert max(abs(error)) < .1

if __name__=="__main__":
    test_regularization()