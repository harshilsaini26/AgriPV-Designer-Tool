"""One spelling per state or union territory, whatever the source writes."""

import re

_ALIASES = {
    "ORISSA": "ODISHA",
    "NCT OF DELHI": "DELHI",
    "CHATTISGARH": "CHHATTISGARH",
    "UTTARANCHAL": "UTTARAKHAND",
    "PONDICHERRY": "PUDUCHERRY",
}


def canonical_state(name: str) -> str:
    """'ODISHA', 'Orissa' -> 'Odisha'; 'DADRA,NAGAR HAVELI,DAMAN & DIU' -> 'Dadra, Nagar Haveli, Daman & Diu'."""
    upper = re.sub(r"\s+", " ", name.replace(",", ", ")).strip().upper()
    upper = _ALIASES.get(upper, upper)
    return " ".join(word if word == "&" else word.capitalize() for word in upper.split(" "))
