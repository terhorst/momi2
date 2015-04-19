from demography import Demography
from scipy.optimize import basinhopping, minimize
from adarray.ad.admath import log,exp
import numpy as np
from adarray.ad import adnumber
from adarray import array

def simple_human_demo(n,
                      t_bottleneck_to_africa_split,
                      t_africa_split_to_eurasia_split,
                      t_eurasia_split_to_present,
                      ancestral_size,
                      africa_size, eurasia_size,
                      eur_present_size, asia_present_size):
    demo_cmd = " ".join(["-I 3 %s" % (" ".join(map(str,n))),
                         "-n 1 $0", # present pop size of africa
                         "-n 2 $1", # present pop size of europe
                         "-n 3 $2", # present pop size of asia
                         "-ej $3 3 2 -en $3 2 $4", # eurasia merge and bottleneck
                         "-ej $5 2 1", # eurasia,africa merge
                         "-en $6 1 $7", # ancestral pop size
                         ])

    eurasia_split = array(t_eurasia_split_to_present)
    africa_split = eurasia_split + t_africa_split_to_eurasia_split
    bottleneck = africa_split + t_bottleneck_to_africa_split

    return Demography.from_ms(demo_cmd,
                              africa_size,
                              eur_present_size,
                              asia_present_size,
                              eurasia_split, eurasia_size,
                              africa_split,
                              bottleneck, ancestral_size)

def test_simple_human_demo():
    #n = [10] * 3
    n = [5] * 3
    theta = 2.0
    num_sims = 10000
    true_params = np.exp(np.random.normal(size=8))
                                 
    true_demo = simple_human_demo(n, *true_params)
    #sfs,_,_ = true_demo.simulate_sfs(num_sims, theta)
    sfs,_,_ = true_demo.simulate_sfs(num_sims)

    true_lik = true_demo.log_likelihood_prf(theta * num_sims, sfs)

    p = len(true_params)

    def objective(x):
        x = np.ravel(x)
        params = list(true_params)
        x = map(adnumber,x)

        params[:p] = x
        ret = -simple_human_demo(n, *params).log_likelihood_prf(theta * num_sims, sfs)
        #return float(ret)
        #print x, ret.x, ret.gradient(x)
        return np.asarray(ret.x), np.asarray(ret.gradient(x))

    true_x = true_params[:p]
    init_x = np.exp(np.random.normal(size=p))

    print true_x, init_x

    def accept_test(x_new,**kwargs):
        return bool(np.all(x_new >= 1e-16))

    def print_fun(x, f, accepted):
        print x
        print("at minimum %.4f accepted %d" % (f, int(accepted)))

    inferred_x = basinhopping(objective, init_x, minimizer_kwargs = {'bounds':[(1e-16,None)] * len(init_x),'jac':True}, niter=10, accept_test=accept_test, callback=print_fun)
    #inferred_x = minimize(objective, init_x, jac=True, bounds=[(0,None)] * len(init_x))
    #inferred_x = minimize(objective, init_x, jac=False)

    print inferred_x
    error = max(abs(true_x - inferred_x.x) / true_x)
    print true_x, "\n", inferred_x.x
    print error
    assert error < .05

if __name__ == "__main__":
    test_simple_human_demo()