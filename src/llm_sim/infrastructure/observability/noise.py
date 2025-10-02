import random


def apply_noise(
    value: float,
    noise_factor: float,
    seed_components: tuple[int, str, str],  # (turn, observer_id, variable_name)
) -> float:
    """Apply deterministic multiplicative noise to a value.

    Args:
        value: The true value
        noise_factor: Noise magnitude (0.0 = no noise, 0.2 = ±20%)
        seed_components: (turn, observer_id, variable_name) for deterministic seeding

    Returns:
        Noisy value = value * (1.0 + random_factor)
        where random_factor in [-noise_factor, +noise_factor]
    """
    if noise_factor == 0.0:
        return value

    seed = hash(seed_components)
    rng = random.Random(seed)
    noise = rng.uniform(-noise_factor, noise_factor)
    return value * (1.0 + noise)
