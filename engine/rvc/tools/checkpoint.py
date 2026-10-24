"""Portable checkpoint tensors for backends without a serialization tag."""

import torch


def portable_state(value):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu() if value.device.type == "privateuseone" else value
    if isinstance(value, dict):
        return {key: portable_state(item) for key, item in value.items()}
    if isinstance(value, list):
        return [portable_state(item) for item in value]
    if isinstance(value, tuple):
        return tuple(portable_state(item) for item in value)
    return value
