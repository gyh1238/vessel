"""VESSEL_MOE_SHARE_BACKBONE: fc2(+gate) shared, heads distinct, expert0 head copied at init."""
import os
import sys
import importlib
import torch

os.environ['VESSEL_USE_MOE'] = '1'
os.environ['VESSEL_MOE_SHARED'] = '1'
os.environ['VESSEL_MOE_SHARE_BACKBONE'] = '1'
os.environ['VESSEL_MOE_WIDTH'] = '1.0'
os.environ['VESSEL_USE_COMM'] = '1'
os.environ['VESSEL_MSG_LN'] = '1'
os.environ['VESSEL_CENTRAL_CRITIC'] = '0'

import config
importlib.reload(config)
import networks
importlib.reload(networks)


def main():
    assert config.MOE_SHARE_BACKBONE and config.MOE_SHARED
    p = networks.CNNPolicy(config.MSG_DIM, config.CONTINUOUS_ACTION_SIZE, config.FRAMES)
    ctr = p.ctr_actor
    msg = p.msg_actor
    cri = p.critic

    assert ctr.experts[1].fc2 is ctr.experts[0].fc2
    assert ctr.experts[1].radar_encoder is ctr.experts[0].radar_encoder
    assert ctr.experts[1].msg_gate is ctr.experts[0].msg_gate
    assert ctr.experts[1].fc3 is not ctr.experts[0].fc3
    assert ctr.experts[1].action_mean is not ctr.experts[0].action_mean
    assert torch.equal(ctr.experts[1].action_mean.weight, ctr.experts[0].action_mean.weight)
    assert torch.equal(ctr.experts[1].fc3.weight, ctr.experts[0].fc3.weight)

    assert msg.experts[1].fc2 is msg.experts[0].fc2
    assert msg.experts[1].msg_out is not msg.experts[0].msg_out
    assert torch.equal(msg.experts[1].msg_out.weight, msg.experts[0].msg_out.weight)

    assert cri.experts[1].fc2 is cri.experts[0].fc2
    assert cri.experts[1].value_out is not cri.experts[0].value_out

    B, N, F, S = 2, 4, config.FRAMES, config.STATE_SIZE
    x = torch.randn(B, N, F * S)
    goal = torch.randn(B, N, 2)
    self_s = torch.randn(B, N, 4)
    om = torch.randn(B, N, config.MSG_DIM)
    sit = torch.full((B, N), 3, dtype=torch.long)

    _act, _lp, mean, _raw = ctr.forward(x, goal, self_s, om, sit)
    loss = mean.pow(2).mean()
    loss.backward()

    g0 = ctr.experts[0].fc3.weight.grad
    g3 = ctr.experts[3].fc3.weight.grad
    g1 = ctr.experts[1].fc3.weight.grad
    assert g3 is not None and g3.abs().sum() > 0, 'sit3 head must get grad'
    assert g1 is None or g1.abs().sum() == 0, 'other heads must not get grad'
    assert g0 is None or g0.abs().sum() == 0, 'sit0 head unused'
    assert ctr.experts[0].fc2.weight.grad is not None
    assert ctr.experts[0].fc2.weight.grad.abs().sum() > 0, 'shared fc2 must get grad from sit3'

    # default flag off: v11 radar-only share, fc2 distinct
    os.environ['VESSEL_MOE_SHARE_BACKBONE'] = '0'
    importlib.reload(config)
    importlib.reload(networks)
    p2 = networks.CNNPolicy(config.MSG_DIM, config.CONTINUOUS_ACTION_SIZE, config.FRAMES)
    assert p2.ctr_actor.experts[1].radar_encoder is p2.ctr_actor.experts[0].radar_encoder
    assert p2.ctr_actor.experts[1].fc2 is not p2.ctr_actor.experts[0].fc2
    print('SHARE_BACKBONE tests passed')
    return 0


if __name__ == '__main__':
    # get_logprob_entropy signature — use forward instead if needed
    sys.exit(main())
