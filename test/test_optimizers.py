# Copyright Contributors to the Pyro project.
# SPDX-License-Identifier: Apache-2.0

import pytest

from jax import grad, jit, partial
import jax.numpy as jnp

from numpyro import optim;import numpy as np


def loss(params):
    return jnp.sum(params['x'] ** 2 + params['y'] ** 2)


@partial(jit, static_argnums=(1,))
def step(opt_state, optim):
    params = optim.get_params(opt_state)
    g = grad(loss)(params)
    return optim.update(g, opt_state)


@pytest.mark.parametrize('optim_class, args', [
    (optim.Adam, (1e-2,)),
    (optim.ClippedAdam, (1e-2,)),
    (optim.Adagrad, (1e-1,)),
    (optim.Momentum, (1e-2, 0.5,)),
    (optim.RMSProp, (1e-2, 0.95)),
    (optim.RMSPropMomentum, (1e-4,)),
    (optim.SGD, (1e-2,))
])
def test_optim_multi_params(optim_class, args):
    params = {'x': jnp.array([1., 1., 1.]), 'y': jnp.array([-1, -1., -1.])}
    opt = optim_class(*args)
    opt_state = opt.init(params)
    for i in range(2000):
        opt_state = step(opt_state, opt)
    for _, param in opt.get_params(opt_state).items():
        np.testing.assert_allclose(param, jnp.zeros(3), atol=1e-08, rtol=1e-05)


# note: this is somewhat of a bruteforce test. testing directly from
# _NumpyroOptim would probably be better
@pytest.mark.parametrize('optim_class, args', [
    (optim.Adam, (1e-2,)),
    (optim.ClippedAdam, (1e-2,)),
    (optim.Adagrad, (1e-1,)),
    (optim.Momentum, (1e-2, 0.5,)),
    (optim.RMSProp, (1e-2, 0.95)),
    (optim.RMSPropMomentum, (1e-4,)),
    (optim.SGD, (1e-2,))
])
def test_numpyrooptim_no_double_jit(optim_class, args):

    opt = optim_class(*args)
    state = opt.init(jnp.zeros(10))

    my_fn_calls = 0

    @jit
    def my_fn(state, g):
        nonlocal my_fn_calls
        my_fn_calls += 1

        state = opt.update(g, state)
        return state

    state = my_fn(state, jnp.ones(10)*1.)
    state = my_fn(state, jnp.ones(10)*2.)
    state = my_fn(state, jnp.ones(10)*3.)

    assert my_fn_calls == 1
