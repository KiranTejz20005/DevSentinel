"""Reward function registry for Oumi."""

from typing import Callable, Dict

REGISTRY: Dict[str, Callable] = {}


def register(name: str) -> Callable[[Callable], Callable]:
    def decorator(fn: Callable) -> Callable:
        REGISTRY[name] = fn
        return fn

    return decorator


@register("placeholder_reward")
def placeholder_reward(example: dict) -> float:
    # Stub reward: always returns 0.0
    return 0.0


def available_rewards() -> Dict[str, Callable]:
    return REGISTRY


if __name__ == "__main__":
    print({k: v.__name__ for k, v in REGISTRY.items()})
