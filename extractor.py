import json
import re
from typing import Dict, List, Any


# Mock SNOMED CT dictionary for common women's health symptoms.
# Codes are 9-digit strings (some are fictional but structurally similar to real SNOMED CT codes).
SNOMED_SYMPTOM_MAP: Dict[str, str] = {
    "pelvic pain": "21522001",       # Pelvic pain (finding)
    "lower back pain": "279039007",  # Low back pain (finding)
    "cramps": "84387000",            # Cramp in lower limb (finding) - reused generically here
    "dysmenorrhea": "266599000",     # Painful menstruation
    "fatigue": "84229001",           # Fatigue (finding)
    "nausea": "422587007",           # Nausea (finding)
    "migraine": "37796009",          # Migraine (disorder)
    "bloating": "116289008",         # Abdominal bloating (finding)
    "headache": "25064002",          # Headache (finding)
    "abdominal pain": "21522001",    # Using same as pelvic for simplicity
}


SYMPTOM_KEYWORDS: List[str] = sorted(SNOMED_SYMPTOM_MAP.keys(), key=len, reverse=True)


def _extract_severity(text: str) -> int | None:
    """
    Extract a severity value on a 0–10 scale from free text.
    Examples it should catch:
      - 'pain is 7'
      - '7/10'
      - '7 out of 10'
      - 'about a 3 today'
    """
    lowered = text.lower()

    # Patterns like "7/10" or "7 out of 10"
    patterns = [
        r"\b([0-9]|10)\s*/\s*10\b",
        r"\b([0-9]|10)\s+out of\s+10\b",
        r"\b(?:about|around|roughly)?\s*([0-9]|10)\b",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, lowered):
            # The capturing group should correspond to the numeric part
            groups = [g for g in match.groups() if g is not None]
            if groups:
                try:
                    value = int(groups[0])
                    if 0 <= value <= 10:
                        return value
                except ValueError:
                    continue

    return None


def _extract_symptoms(text: str) -> List[str]:
    """
    Perform very simple keyword-based matching for symptoms.
    Returns the list of matched symptom keys from SNOMED_SYMPTOM_MAP.
    """
    lowered = text.lower()
    found: List[str] = []

    for keyword in SYMPTOM_KEYWORDS:
        # Use a loose containment check; in a more advanced extractor, you would use
        # tokenization + span detection and avoid substring collisions.
        if keyword in lowered:
            found.append(keyword)

    # Deduplicate while preserving order
    deduped: List[str] = []
    for s in found:
        if s not in deduped:
            deduped.append(s)
    return deduped


def _compute_confidence(num_symptoms: int, has_severity: bool) -> float:
    """
    Produce a mock confidence score based on what we've extracted.
    """
    base = 0.5
    if num_symptoms > 0:
        base += 0.25
    if has_severity:
        base += 0.15
    # Clamp between 0 and 0.99 for realism
    return round(min(max(base, 0.0), 0.99), 2)


def extract_clinical_data(user_text: str) -> Dict[str, Any]:
    """
    Naive rule-based extractor for clinical concepts in Alexandria-style narratives.

    It searches for:
      - Symptom keywords based on SNOMED_SYMPTOM_MAP
      - Severity values expressed on a 0–10 scale
    and returns a structured JSON-serializable dictionary.
    """
    if not isinstance(user_text, str):
        raise TypeError("user_text must be a string")

    symptoms = _extract_symptoms(user_text)
    snomed_codes = [SNOMED_SYMPTOM_MAP[s] for s in symptoms]
    severity = _extract_severity(user_text)
    confidence = _compute_confidence(len(symptoms), severity is not None)

    return {
        "original_text": user_text,
        "extracted_symptoms": symptoms,
        "snomed_codes": snomed_codes,
        "severity": severity,
        "confidence_score": confidence,
    }


if __name__ == "__main__":
    test_inputs = [
        "I have awful pelvic pain today, maybe a 7 out of 10, and I feel really fatigued.",
        "Lower back pain is killing me, it's like 9/10 right now.",
        "Just mild cramps and a bit of nausea, maybe a 3 today.",
        "Terrible headache and fatigue, couldn't sleep at all.",
        "Almost no pain today, maybe 1 out of 10, just a bit of bloating.",
    ]

    for i, text in enumerate(test_inputs, start=1):
        result = extract_clinical_data(text)
        print(f"\n=== Test case {i} ===")
        print(json.dumps(result, indent=2))

