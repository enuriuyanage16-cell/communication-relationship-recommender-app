from attachment import item_score, attachment_scores, attachment_style, to_percent

# Test 1 - a normal item keeps the answer and a reversed item becomes 8 minus the answer
assert item_score(1, 6) == 6
assert item_score(9, 6) == 2

# Test 2 - all answers are 4 (the middle), so both scores should be 4.0
assert attachment_scores([4] * 36) == {"Anxiety": 4.0, "Avoidance": 4.0}

# Test 3 - all answers 7 so 2 of 18 anxiety items and 12 of 18 avoidance items are reversed
assert attachment_scores([7] * 36) == {"Anxiety": round((16 * 7 + 2 * 1) / 18, 2), "Avoidance": round((6 * 7 + 12 * 1) / 18, 2)}

# Test 4 - one example for each style
assert attachment_style({"Anxiety": 2.0, "Avoidance": 2.0}) == "Secure"
assert attachment_style({"Anxiety": 5.0, "Avoidance": 2.0}) == "Anxious (preoccupied)"
assert attachment_style({"Anxiety": 2.0, "Avoidance": 5.0}) == "Avoidant (dismissive)"
assert attachment_style({"Anxiety": 5.0, "Avoidance": 5.0}) == "Fearful-avoidant"

# Test 5 - 1 is 0% and 4 (the middle) is 50% and 7 is 100%
assert to_percent(1) == 0.0
assert to_percent(4) == 50.0
assert to_percent(7) == 100.0

# Test 6 - a score of exactly 4 is the middle, so it is not "high"
assert attachment_style({"Anxiety": 4.0, "Avoidance": 4.0}) == "Secure"

print("All tests passed")
