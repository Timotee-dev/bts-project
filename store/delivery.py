"""
BTS Project — Delivery fee calculator
Flat-rate per state (NGN). Update these as your logistics costs change.
"""

DELIVERY_FEES = {
    # Lagos
    'lagos': 1500,
    # South West
    'ogun': 2000, 'oyo': 2500, 'osun': 2500, 'ondo': 2800, 'ekiti': 3000,
    # South South
    'rivers': 3500, 'delta': 3500, 'edo': 3000, 'akwa ibom': 3800,
    'cross river': 4000, 'bayelsa': 4500,
    # South East
    'anambra': 3000, 'imo': 3200, 'enugu': 3200, 'abia': 3500, 'ebonyi': 3800,
    # North Central
    'abuja': 2500, 'fct': 2500, 'kwara': 2800, 'kogi': 3000, 'benue': 3500,
    'nassarawa': 3000, 'niger': 3200, 'plateau': 3500,
    # North West
    'kano': 3500, 'kaduna': 3500, 'katsina': 4000, 'sokoto': 4500,
    'zamfara': 4500, 'kebbi': 4500, 'jigawa': 4000,
    # North East
    'borno': 5000, 'yobe': 5000, 'gombe': 4500, 'bauchi': 4500,
    'adamawa': 5000, 'taraba': 5000,
}

DEFAULT_FEE = 3500  # fallback for unlisted states


def get_delivery_fee(state: str) -> int:
    """Return delivery fee in NGN for a given state."""
    if not state:
        return DEFAULT_FEE
    return DELIVERY_FEES.get(state.lower().strip(), DEFAULT_FEE)


def get_all_states_with_fees():
    """Return sorted list of (state_name, fee) tuples for display."""
    return sorted(DELIVERY_FEES.items(), key=lambda x: x[0])
