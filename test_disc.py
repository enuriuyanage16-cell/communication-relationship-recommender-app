from disc import color_scores, classify

# Test 1 - all answers are 3, so the total of every colour should be 8 x 3 = 24
scores = color_scores([3] * 32)
assert scores == {"Green": 24, "Yellow": 24, "Blue": 24, "Red": 24}

# Test 2 - all answers are 5, so the total of every colour should be 8 x 5 = 40
scores = color_scores([5] * 32)
assert scores == {"Green": 40, "Yellow": 40, "Blue": 40, "Red": 40}

# Test 3 - real pilot respondent
row = [2,4,3,2,4,3,5,5,4,2,2,4,4,5,4,5,2,2,3,1,3,4,2,3,5,1,3,4,5,2,4,1]
assert color_scores(row) == {"Green": 29, "Yellow": 23, "Blue": 26, "Red": 25}
assert classify(color_scores(row)) == "Unclear"

# Test 4 - gap between Green (35) and Yellow (20) is above the threshold
assert classify({"Green": 35, "Yellow": 20, "Blue": 18, "Red": 15}) == "Pure Green"

# Test 5 - top two colours (Green and Red) are opposites
assert classify({"Green": 30, "Yellow": 28, "Blue": 15, "Red": 29}) == "Inconsistent"

# Test 6 - the gap between top two colours (Green and Blue) is below the threshold
assert classify({"Green": 32, "Yellow": 20, "Blue": 30, "Red": 18}) == "Two-way blend"

# Test 7 - the gaps between top three colours (Green, Blue and Yellow) are below the threshold
assert classify({"Green": 34, "Yellow": 28, "Blue": 31, "Red": 20}) == "Three-way blend"

print("All tests passed")
