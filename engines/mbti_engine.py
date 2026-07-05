def axis_position(left_score, right_score):
    total = left_score + right_score
    if total == 0:
        return 50.0
    return round(100 * right_score / total, 1)


def calculate_mbti(answers, questions):
    scores = {
        "E": 0, "I": 0,
        "S": 0, "N": 0,
        "T": 0, "F": 0,
        "J": 0, "P": 0
    }

    for question in questions:
        answer = answers.get(question["id"])

        if answer == "A":
            scores[question["A_score"]] += 1
        elif answer == "B":
            scores[question["B_score"]] += 1

    mbti_type = ""
    mbti_type += "E" if scores["E"] >= scores["I"] else "I"
    mbti_type += "S" if scores["S"] >= scores["N"] else "N"
    mbti_type += "T" if scores["T"] >= scores["F"] else "F"
    mbti_type += "J" if scores["J"] >= scores["P"] else "P"

    axis_positions = {
        "I_E": axis_position(scores["I"], scores["E"]),
        "S_N": axis_position(scores["S"], scores["N"]),
        "T_F": axis_position(scores["T"], scores["F"]),
        "J_P": axis_position(scores["J"], scores["P"])
    }

    return {
        "type": mbti_type,
        "scores": scores,
        "axis_positions": axis_positions
    }