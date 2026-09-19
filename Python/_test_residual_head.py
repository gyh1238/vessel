"""VESSEL_MOE_RESIDUAL_HEAD: shared μ + per-situation zero Δμ."""
import os
import importlib
import torch

os.environ['VESSEL_USE_MOE'] = '1'
os.environ['VESSEL_MOE_SHARED'] = '1'
os.environ['VESSEL_MOE_SHARE_BACKBONE'] = '1'
os.environ['VESSEL_MOE_RESIDUAL_HEAD'] = '1'
os.environ['VESSEL_MOE_WIDTH'] = '1.0'
os.environ['VESSEL_USE_COMM'] = '1'
os.environ['VESSEL_MSG_LN'] = '1'
os.environ['VESSEL_CENTRAL_CRITIC'] = '0'

import config
importlib.reload(config)
import networks
importlib.reload(networks)

assert config.MOE_RESIDUAL_HEAD
p = networks.CNNPolicy(config.MSG_DIM, config.CONTINUOUS_ACTION_SIZE, config.FRAMES)
ctr = p.ctr_actor
assert ctr.experts[1].fc3 is ctr.experts[0].fc3
assert ctr.experts[1].action_mean is ctr.experts[0].action_mean
assert ctr.experts[1].action_delta is not ctr.experts[0].action_delta
assert torch.equal(ctr.experts[1].action_delta.weight, torch.zeros_like(ctr.experts[1].action_delta.weight))
assert p.msg_actor.experts[1].msg_out is p.msg_actor.experts[0].msg_out
assert p.critic.experts[1].value_out is p.critic.experts[0].value_out

B, N, F, S = 2, 4, config.FRAMES, config.STATE_SIZE
x = torch.randn(B, N, F * S)
goal = torch.randn(B, N, 2)
self_s = torch.randn(B, N, 4)
om = torch.randn(B, N, config.MSG_DIM)
sit = torch.full((B, N), 3, dtype=torch.long)
_act, _lp, mean, _raw = ctr.forward(x, goal, self_s, om, sit)
mean.pow(2).mean().backward()
assert ctr.experts[3].action_delta.weight.grad is not None
assert ctr.experts[3].action_delta.weight.grad.abs().sum() > 0
g1 = ctr.experts[1].action_delta.weight.grad
assert g1 is None or g1.abs().sum() == 0
assert ctr.experts[0].action_mean.weight.grad is not None
assert float(ctr.delta_l2().detach()) == 0.0
print('RESIDUAL_HEAD tests passed')
