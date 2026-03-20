#!/usr/bin/env python3
"""
ReviewSentinel detector — score_review copied verbatim from fake-review-detector experiment (100.0 F1).
explain_review runs the same signal checks and accumulates human-readable reasons.
"""


def score_review(review: dict) -> float:
    """
    Returns a fakeness score in [0.0, 1.0].
    1.0 = very likely fake, 0.0 = very likely genuine.

    review keys:
      text         (str)  - review body
      rating       (int)  - star rating 1-5
      verified     (bool) - verified purchase
      helpful_votes(int)  - number of helpful votes
      review_length(int)  - character count
    """
    score = 0.0

    # Metadata signals
    verified = review.get("verified", True)
    helpful_votes = review.get("helpful_votes", 0)
    rating = review.get("rating", 3)

    if not verified:
        score += 0.3
    if helpful_votes == 0:
        score += 0.1
    if rating == 5 or rating == 1:
        score += 0.2

    # Combined signal: extreme rating + zero helpful votes = strong fake indicator
    if (rating == 5 or rating == 1) and helpful_votes == 0 and not verified:
        score += 0.1

    # Length signal: short reviews are suspicious, but less so for verified buyers
    length = review.get("review_length", 200)
    if not verified and length < 80:
        score += 0.25
    elif verified and length < 50:
        score += 0.1

    # Text signals
    text = review.get("text", "")
    text_lower = text.lower()

    # Exclamation marks
    exclamations = text.count("!")
    if exclamations >= 2:
        score += 0.1

    # ALL CAPS words: fakes often shout (DO NOT BUY, AMAZING, BUY NOW)
    words_raw = text.split()
    caps_words = [w for w in words_raw if len(w) >= 3 and w.isupper() and w.isalpha()]
    if len(caps_words) >= 2:
        score += 0.15

    # Generic superlatives and vague praise phrases
    generic = ["amazing", "perfect", "love it", "great product", "highly recommend",
               "best ever", "excellent", "fantastic", "awesome", "wonderful",
               "outstanding", "superb", "incredible", "best purchase", "will buy again",
               "recommend to", "so happy", "love this", "love the quality"]
    generic_count = sum(1 for g in generic if g in text_lower)
    if generic_count >= 2:
        score += 0.15
    if generic_count >= 4:
        score += 0.1

    # Word repetition: fakes repeat the same words (low lexical diversity)
    stop_words = {"the", "a", "an", "and", "or", "it", "is", "for", "of", "to",
                  "i", "my", "this", "that", "was", "with", "in", "at", "so", "very"}
    words = [w.strip("!.,?") for w in text_lower.split() if w.strip("!.,?") not in stop_words and len(w) > 2]
    if words:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.65:
            score += 0.15

    return min(1.0, score)


def explain_review(review: dict) -> dict:
    """
    Runs the same signal checks as score_review, but returns a structured
    explanation with human-readable reasons.

    Returns:
      {
        "score": float,
        "verdict": str,
        "reasons": list[str],
        "color": str  -- "green" | "yellow" | "red"
      }
    """
    score = 0.0
    reasons = []

    verified = review.get("verified", True)
    helpful_votes = review.get("helpful_votes", 0)
    rating = review.get("rating", 3)

    if not verified:
        score += 0.3
        reasons.append("Unverified purchase (+30%)")
    if helpful_votes == 0:
        score += 0.1
        reasons.append("No helpful votes (+10%)")
    if rating == 5 or rating == 1:
        score += 0.2
        reasons.append("Extreme star rating — 1 or 5 stars (+20%)")

    if (rating == 5 or rating == 1) and helpful_votes == 0 and not verified:
        score += 0.1
        reasons.append("Suspicious combination: extreme rating + no votes + unverified (+10%)")

    length = review.get("review_length", 200)
    if not verified and length < 80:
        score += 0.25
        reasons.append("Very short unverified review (+25%)")
    elif verified and length < 50:
        score += 0.1
        reasons.append("Very short review (+10%)")

    text = review.get("text", "")
    text_lower = text.lower()

    exclamations = text.count("!")
    if exclamations >= 2:
        score += 0.1
        reasons.append("Excessive exclamation marks (+10%)")

    words_raw = text.split()
    caps_words = [w for w in words_raw if len(w) >= 3 and w.isupper() and w.isalpha()]
    if len(caps_words) >= 2:
        score += 0.15
        reasons.append("Multiple ALL-CAPS words — common in fake reviews (+15%)")

    generic = ["amazing", "perfect", "love it", "great product", "highly recommend",
               "best ever", "excellent", "fantastic", "awesome", "wonderful",
               "outstanding", "superb", "incredible", "best purchase", "will buy again",
               "recommend to", "so happy", "love this", "love the quality"]
    generic_count = sum(1 for g in generic if g in text_lower)
    if generic_count >= 2:
        score += 0.15
        reasons.append("Generic praise language — vague superlatives (+15%)")
    if generic_count >= 4:
        score += 0.1
        reasons.append("Heavy use of generic phrases — 4+ matches (+10%)")

    stop_words = {"the", "a", "an", "and", "or", "it", "is", "for", "of", "to",
                  "i", "my", "this", "that", "was", "with", "in", "at", "so", "very"}
    words = [w.strip("!.,?") for w in text_lower.split() if w.strip("!.,?") not in stop_words and len(w) > 2]
    if words:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.65:
            score += 0.15
            reasons.append("Low lexical diversity — repetitive language (+15%)")

    score = min(1.0, score)

    if score < 0.3:
        verdict = "Likely genuine"
        color = "green"
    elif score <= 0.6:
        verdict = "Possibly suspicious"
        color = "yellow"
    else:
        verdict = "Likely fake"
        color = "red"

    return {
        "score": round(score, 4),
        "verdict": verdict,
        "reasons": reasons,
        "color": color,
    }
