from workers import get_word_weights
import random

class Student:
    def __init__(self, name, gender):
        self.name = name
        self.gender = gender
    
    def choose_student_word(self, question):
        weights = get_word_weights(question.words, self.gender)
        return random.choices(question.words, weights)[0]

class Examiner:
    def __init__(self, name, gender):
        self.name = name
        self.gender = gender
    
    def choose_correct_answer(self, question):
        words = question.words
        weights = get_word_weights(words, self.gender)
        first = random.choices(words, weights)[0]
        
        correct = {first}
        remain = [w for w in words if w not in correct]
        
        while remain:
            if random.random() < 1/3:
                weights = get_word_weights(remain, self.gender)
                next_word = random.choices(remain, weights)[0]
                correct.add(next_word)
                remain = [w for w in remain if w != next_word]
            else:
                break
        
        return correct

class Question:
    def __init__(self, text):
        self.text = text
        self.words = text.split()        

