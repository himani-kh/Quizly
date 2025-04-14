import csv

def calculate_score(student_answers, answer_file):
    correct_answers = []
    with open(answer_file, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            correct_answers.append(row[0])

    print("Student Answers:", student_answers)
    print("Correct Answers:", correct_answers)

    # Compare one by one and print result of each
    score = 0
    for i, (sa, ca) in enumerate(zip(student_answers, correct_answers)):
        match = sa.strip() == ca.strip()
        print(f"Q{i+1}: Student='{sa.strip()}', Correct='{ca.strip()}', Match={match}")
        if match:
            score += 1

    print("Final Score:", score)
    return score
