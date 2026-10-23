from bigfive import item_score, predict_traits, full_scores

# Test 1 - a positive question keeps the answer, a reversed question flips the answer
assert item_score("EXT1", 5) == 5
assert item_score("EXT2", 5) == 1

# Test 2 - full test of all answers 3 so the total of every trait should be 10 x 3 = 30
answers = {t + str(n): 3 for t in ["EXT", "EST", "AGR", "CSN", "OPN"] for n in range(1, 11)}
assert full_scores(answers) == {"EXT": 30, "EST": 30, "AGR": 30, "CSN": 30, "OPN": 30}

# Test 3 - full test of all answers 5 so reversed questions count as 1
answers = {t + str(n): 5 for t in ["EXT", "EST", "AGR", "CSN", "OPN"] for n in range(1, 11)}
assert full_scores(answers) == {"EXT": 30, "EST": 42, "AGR": 34, "CSN": 34, "OPN": 38}

# Test 4 - short test of all answers 3, so scores should be near the middle (30)
items = ["EXT4","EXT5","EXT9","EXT7","EST8","EST1","EST6","EST10","AGR4","AGR7","AGR8","AGR3",
         "CSN6","CSN1","CSN9","CSN4","OPN10","OPN1","OPN2","OPN3"]
assert predict_traits({i: 3 for i in items}) == {"EXT": 29.8, "EST": 31.3, "AGR": 30.8, "CSN": 31.7, "OPN": 31.8}

# Test 5 - short test scores always stay between 10 and 50
for value in [1, 5]:
    for score in predict_traits({i: value for i in items}).values():
        assert 10 <= score <= 50

print("All tests passed")

