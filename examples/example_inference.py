from __future__ import division
import sys

## TODO: import momi
from likelihood_surface import CompositeLogLikelihood
from demography import make_demography
from util import check_symmetric, default_ms_path

import scipy
from scipy.stats import norm,chi2
from scipy.optimize import minimize

## Thinly-wrapped numpy that supports automatic differentiation
import autograd.numpy as anp
## Methods for computing derivatives
from autograd import grad, hessian_vector_product

def main():
    if len(sys.argv) > 2:
        raise Exception("Too many command-line arguments.")

    if len(sys.argv) == 2:
        ms_path = sys.argv[1]
    else:
        ms_path = default_ms_path()

    fit_log_likelihood_example(example_pulse_demo,
                               ms_path=ms_path,
                               num_loci=1000,
                               theta=10.0,
                               true_params = anp.array([1.0, -1.0, -1.0, 1.0]),
                               init_params = anp.random.normal(size=4))

def example_pulse_demo(x):
    '''
    Function that returns an example pulse demography, parametrized by x.
    
    Parametrization is chosen so that the parameter space is all of \mathbb{R}^4,
    thus allowing the convenience of using unconstrained optimization.

    Note also that only math functions from autograd.numpy used, to allow for
    automatic differentiation. 
    
    autograd.numpy supports nearly all functions from numpy, and also 
    makes it easy to define your own differentiable functions as necessary.
    '''
    growth, logit_pulse_prob, log_pulse_time, log_join_wait_time = x

    pulse_prob = anp.exp(logit_pulse_prob) / (anp.exp(logit_pulse_prob)+1)
    pulse_time = anp.exp(log_pulse_time)
    join_time = pulse_time + anp.exp(log_join_wait_time)

    return make_demography("-I 2 10 10 -g 1 $growth"
                           + " -es $pulse_time 1 $pulse_prob -ej $pulse_time 3 2"
                           + " -ej $join_time 2 1 -eG $join_time 0.0",
                           growth = growth,
                           pulse_time = pulse_time,
                           pulse_prob = pulse_prob,
                           join_time = join_time)

def fit_log_likelihood_example(demo_func, ms_path, num_loci, theta, true_params, init_params):
    '''
    Simulate a SFS, then estimate the demography via maximum composite
    likelihood, using first and second-order derivatives to search 
    over log-likelihood surface.

    demo_func: a function that takes a numpy array and returns a demography
    num_loci: number of unlinked loci to simulate
    true_params: true parameters
    init_params: parameters to start gradient descent
    theta: mutation rate per locus.
    '''
    true_demo = demo_func(true_params)

    print "# Simulating %d trees" % num_loci
    sfs_list = true_demo.simulate_sfs(num_loci, ms_path=ms_path, theta=theta)
    surface = CompositeLogLikelihood(sfs_list, demo_func, theta=theta)

    # construct the function to minimize, and its derivatives
    f = lambda params: -surface.log_likelihood(params)
    g, hp = grad(f), hessian_vector_product(f)
    def f_verbose(params):
        # for verbose output during the gradient descent
        print "Evaluating objective. Current relative error:"
        print (params - true_params) / true_params
        return f(params)
    def g_verbose(params):
        print "Evaluating gradient"
        return g(params)
    def hp_verbose(params, v):
        print "Evaluating hessian-vector product"
        return hp(params, v)

    print "# Start point:"
    print init_params
    print "# Performing optimization. Printing relative error."
    optimize_res = minimize(f_verbose, init_params, jac=g_verbose, hessp=hp_verbose, method='newton-cg')
    print optimize_res
    
    inferred_params = optimize_res.x
    error = (true_params - inferred_params) / true_params
    print "# Max Relative Error: %f" % max(abs(error))
    print "# Relative Error:","\n", error
    print "# True params:", "\n", true_params
    print "# Inferred params:", "\n", inferred_params   

    for params,param_name in ((true_params,"TRUTH"), (inferred_params,"PLUGIN")):
        print "\n\n**** Estimating Sigma_hat at %s" % param_name
        sigma = surface.max_covariance(params)

        # recommend to call check_symmetric on matrix inverse and square root
        # linear algebra routines may not preserve symmetry due to numerical errors
        sigma_inv = check_symmetric(anp.linalg.inv(sigma))
        sigma_inv_root = check_symmetric(scipy.linalg.sqrtm(sigma_inv))

        print "# Estimated standard deviation of inferred[i] - truth[i]"
        sd = anp.sqrt(anp.diag(sigma))
        print sd
        ## TODO: use t-test instead
        print "# p-value of Z-test that params[i]=true_params[i]"
        z = (inferred_params - true_params) / sd
        print (1.0 - norm.cdf(anp.abs(z))) * 2.0
        print "# Transformed residuals EPS_hat = Sigma_hat^{-1/2} * (inferred - truth)"
        eps_hat = anp.dot(sigma_inv_root, inferred_params - true_params )
        print eps_hat
        ## TODO: use correct degrees of freedom
        print "# Chi2 test for params=true_params, using transformed residuals"
        print "# <EPS_hat,EPS_hat>, 1-Chi2_cdf(<EPS_hat,EPS_hat>,df=%d)" % len(eps_hat)
        eps_norm = anp.sum(eps_hat**2)
        print eps_norm, 1.0 - chi2.cdf(eps_norm, df=len(eps_hat))


if __name__=="__main__":
    main()
