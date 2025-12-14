"""
Reward function registry for Oumi RL training.

This module provides custom reward functions for training the DevSentinel AI
to perform better incident management and code repairs via reinforcement learning.

Each reward function takes an example/episode and returns a scalar reward value.
Positive rewards encourage the behavior, negative rewards discourage it.
"""

from typing import Callable, Dict, Any, Optional
import re


# Global registry of all reward functions
REGISTRY: Dict[str, Callable] = {}


def register(name: str) -> Callable[[Callable], Callable]:
    """
    Decorator to register a reward function.
    
    Usage:
        @register("my_reward")
        def my_reward(example: dict) -> float:
            return 1.0
    """
    def decorator(fn: Callable) -> Callable:
        REGISTRY[name] = fn
        return fn
    return decorator


@register("incident_success_reward")
def incident_success_reward(example: dict) -> float:
    """
    Primary reward: +1 if incident is resolved, -1 otherwise.
    
    Expected example format:
    {
        "status": "resolved" | "pending" | "failed",
        "incident_id": "...",
        ...
    }
    """
    status = (example or {}).get("status", "").lower()
    return 1.0 if status == "resolved" else -1.0


@register("fix_quality_reward")
def fix_quality_reward(example: dict) -> float:
    """
    Reward based on fix quality indicators.
    
    Factors:
    - Was a proper diff generated? (+0.5)
    - Was code review positive? (+0.5)
    - Did tests pass? (+0.5)
    - Was fix applied successfully? (+0.5)
    
    Returns: 0.0 to 2.0
    """
    reward = 0.0
    
    # Check if diff was generated
    if example.get("diff") and len(example.get("diff", "")) > 50:
        reward += 0.5
    
    # Check code review sentiment
    review = example.get("code_review", {})
    if review.get("approved", False):
        reward += 0.5
    
    # Check test results
    tests = example.get("tests", {})
    if tests.get("passed", False):
        reward += 0.5
    
    # Check if fix was applied
    if example.get("applied", False):
        reward += 0.5
    
    return reward


@register("response_time_reward")
def response_time_reward(example: dict) -> float:
    """
    Reward faster incident resolution.
    
    Expected format:
    {
        "resolution_time_seconds": <float>,
        ...
    }
    
    Returns:
    - 1.0 for < 60 seconds (excellent)
    - 0.5 for < 300 seconds (good)
    - 0.0 for < 600 seconds (acceptable)
    - -0.5 for >= 600 seconds (too slow)
    """
    resolution_time = example.get("resolution_time_seconds", float('inf'))
    
    if resolution_time < 60:
        return 1.0
    elif resolution_time < 300:
        return 0.5
    elif resolution_time < 600:
        return 0.0
    else:
        return -0.5


@register("false_positive_penalty")
def false_positive_penalty(example: dict) -> float:
    """
    Penalize false positive detections.
    
    Expected format:
    {
        "is_false_positive": <bool>,
        ...
    }
    
    Returns: -2.0 for false positives, 0.0 otherwise
    """
    if example.get("is_false_positive", False):
        return -2.0
    return 0.0


@register("severity_alignment_reward")
def severity_alignment_reward(example: dict) -> float:
    """
    Reward accurate severity classification.
    
    Expected format:
    {
        "predicted_severity": "low" | "medium" | "high" | "critical",
        "actual_severity": "low" | "medium" | "high" | "critical",
        ...
    }
    
    Returns:
    - 1.0 for exact match
    - 0.5 for one level off
    - -1.0 for two+ levels off
    """
    severity_levels = ["low", "medium", "high", "critical"]
    
    predicted = example.get("predicted_severity", "").lower()
    actual = example.get("actual_severity", "").lower()
    
    if predicted == actual:
        return 1.0
    
    try:
        pred_idx = severity_levels.index(predicted)
        actual_idx = severity_levels.index(actual)
        diff = abs(pred_idx - actual_idx)
        
        if diff == 1:
            return 0.5
        else:
            return -1.0
    except ValueError:
        return -0.5  # Invalid severity level


@register("code_quality_reward")
def code_quality_reward(example: dict) -> float:
    """
    Reward good code quality in fixes.
    
    Checks:
    - No syntax errors (+0.5)
    - Follows style guidelines (+0.3)
    - Has proper comments (+0.2)
    - No security issues (+0.5)
    
    Returns: 0.0 to 1.5
    """
    reward = 0.0
    
    # Check for syntax errors
    if not example.get("syntax_errors", False):
        reward += 0.5
    
    # Check style compliance
    style_score = example.get("style_score", 0.0)
    if style_score > 0.8:
        reward += 0.3
    
    # Check for comments
    diff = example.get("diff", "")
    if diff and ("# " in diff or "\"\"\"" in diff):
        reward += 0.2
    
    # Check for security issues
    if not example.get("security_issues", False):
        reward += 0.5
    
    return reward


@register("user_satisfaction_reward")
def user_satisfaction_reward(example: dict) -> float:
    """
    Reward based on user feedback/satisfaction.
    
    Expected format:
    {
        "user_feedback": "positive" | "neutral" | "negative",
        "user_rating": 1-5,
        ...
    }
    
    Returns: -1.0 to 1.0
    """
    feedback = example.get("user_feedback", "").lower()
    rating = example.get("user_rating", 3)
    
    # Map feedback to reward
    feedback_reward = {
        "positive": 1.0,
        "neutral": 0.0,
        "negative": -1.0
    }.get(feedback, 0.0)
    
    # Map rating (1-5) to reward (-1 to 1)
    rating_reward = (rating - 3) / 2.0
    
    # Average the two signals
    return (feedback_reward + rating_reward) / 2.0


@register("composite_reward")
def composite_reward(example: dict) -> float:
    """
    Composite reward combining multiple factors.
    
    This is the main reward function used for training.
    It combines multiple reward signals with appropriate weights.
    
    Weights:
    - incident_success: 2.0 (primary goal)
    - fix_quality: 1.0
    - response_time: 0.5
    - false_positive_penalty: 1.0
    - severity_alignment: 0.5
    - code_quality: 0.5
    """
    weights = {
        "incident_success": 2.0,
        "fix_quality": 1.0,
        "response_time": 0.5,
        "false_positive_penalty": 1.0,
        "severity_alignment": 0.5,
        "code_quality": 0.5,
    }
    
    total_reward = 0.0
    
    # Compute each reward component
    total_reward += weights["incident_success"] * incident_success_reward(example)
    total_reward += weights["fix_quality"] * fix_quality_reward(example)
    total_reward += weights["response_time"] * response_time_reward(example)
    total_reward += weights["false_positive_penalty"] * false_positive_penalty(example)
    total_reward += weights["severity_alignment"] * severity_alignment_reward(example)
    total_reward += weights["code_quality"] * code_quality_reward(example)
    
    return total_reward


def available_rewards() -> Dict[str, Callable]:
    """Get all registered reward functions."""
    return REGISTRY


def get_reward(name: str) -> Optional[Callable]:
    """Get a specific reward function by name."""
    return REGISTRY.get(name)


def compute_reward(example: dict, reward_name: str = "composite_reward") -> float:
    """
    Compute reward for an example using the specified reward function.
    
    Args:
        example: Dictionary containing episode/example data
        reward_name: Name of the reward function to use
    
    Returns:
        Scalar reward value
    """
    reward_fn = get_reward(reward_name)
    if reward_fn is None:
        raise ValueError(f"Unknown reward function: {reward_name}")
    
    return reward_fn(example)


if __name__ == "__main__":
    print("Available Reward Functions:")
    print("=" * 50)
    for name, fn in REGISTRY.items():
        doc = fn.__doc__.strip().split('\n')[0] if fn.__doc__ else "No description"
        print(f"  {name}: {doc}")
    print("=" * 50)
    print(f"\nTotal: {len(REGISTRY)} reward functions registered")
