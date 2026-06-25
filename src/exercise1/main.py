from pathlib import Path
from models import Student, Examiner, Question
from exam_logic import ExamLogic

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "files_to_read"
        

def load_people(file_name, cls):
    path = DATA_DIR / file_name
    people = []

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            name, gender = line.split()
            people.append(cls(name, gender))

    return people

def load_questions(file_name):
    path = DATA_DIR / file_name
    questions = []
    
    with open(path, encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if not line:
                continue
            questions.append(Question(text))
    
    return questions


def main():
    students = load_people("students.txt", Student)
    examiners = load_people("examiners.txt", Examiner)
    questions = load_questions("questions.txt")

    engine = ExamLogic(students, examiners, questions)
    engine.run()



if __name__ == "__main__":
    main()
