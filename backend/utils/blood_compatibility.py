# backend\utils\blood_compatibility.py
# Blood type compatibility matrix
# Key: Donor blood type, Value: List of recipient blood types that can receive from this donor
COMPATIBILITY_MATRIX = {
    "O-": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],  # Universal donor
    "O+": ["O+", "A+", "B+", "AB+"],
    "A-": ["A-", "A+", "AB-", "AB+"],
    "A+": ["A+", "AB+"],
    "B-": ["B-", "B+", "AB-", "AB+"],
    "B+": ["B+", "AB+"],
    "AB-": ["AB-", "AB+"],
    "AB+": ["AB+"]  # Universal recipient
}

# Reverse: Which donors can donate to a given blood type
def get_compatible_donors_for_blood_type(recipient_blood_type: str) -> list:
    """Get list of donor blood types that can donate to the recipient"""
    compatible_donors = []
    for donor_type, recipients in COMPATIBILITY_MATRIX.items():
        if recipient_blood_type in recipients:
            compatible_donors.append(donor_type)
    return compatible_donors

def is_blood_compatible(donor_blood_type: str, recipient_blood_type: str) -> bool:
    """Check if donor can donate to recipient"""
    return recipient_blood_type in COMPATIBILITY_MATRIX.get(donor_blood_type, [])

# Priority score weights
SCORING_WEIGHTS = {
    "distance": 0.35,          # Closer is better (inverse)
    "reliability": 0.25,       # Higher reliability score is better
    "transport": 0.15,         # Has transport is better
    "response_time": 0.15,     # Quick responders get priority
    "donation_frequency": 0.10  # Regular donors get priority
}