import random
import time

PHI = 1.61803398875


def build_weights(words_count):
    remain = 1.0
    weights = []
    for i in range(words_count - 1):
        weight = remain / PHI
        weights.append(weight)
        remain -= weight
    weights.append(remain)
    return weights


def get_word_weights(words, gender):
    weights = build_weights(len(words))
    if gender == "Ж":
        weights = weights[::-1]
    return weights


def get_student(queue, lock):
    with lock:
        if len(queue) == 0:
            return None
        return queue.pop(0)


def update_examiner_state(state, idx, stats, current=None, total=None, failed=None, time_val=None):
    if current is not None:
        stats["current"] = current
    if total is not None:
        stats["total"] = total
    if failed is not None:
        stats["failed"] = failed
    if time_val is not None:
        stats["time"] = time_val
    state[idx] = stats


def examiner_worker(examiner, queue, questions, students,
                    students_state, examiner_state, examiner_index, lock, question_stats):
    start_time = time.time()
    had_lunch = False
    
    idx_e = examiner_index[examiner.name]
    stats = examiner_state[idx_e]
    
    while True:
        student_idx = get_student(queue, lock)
        if student_idx is None:
            break
        
        student_obj = students[student_idx]
        
        update_examiner_state(examiner_state, idx_e, stats, current=student_obj.name)
        
        exam_time = random.uniform(len(examiner.name) - 1, len(examiner.name) + 1)
        time.sleep(exam_time)
        
        result = process_student(student_obj, examiner, questions, students_state, 
                                 student_idx, start_time, question_stats, lock)
        
        stats["total"] += 1
        if not result:
            stats["failed"] += 1
        
        time_now = round(time.time() - start_time, 2)
        update_examiner_state(examiner_state, idx_e, stats, current="-", time_val=time_now)
        
        if not had_lunch and time.time() - start_time >= 30:
            with lock:
                has_students = len(queue) > 0
            
            if not has_students:
                break
            
            had_lunch = True
            lunch_time = random.uniform(12, 18)
            update_examiner_state(examiner_state, idx_e, stats, current="-")
            time.sleep(lunch_time)
            time_now = round(time.time() - start_time, 2)
            update_examiner_state(examiner_state, idx_e, stats, current="-", time_val=time_now)


def process_student(student, examiner, questions, students_state, student_idx, 
                    start_time, question_stats, lock):
    mood = random.random()
    
    if mood < 1/8:
        passed = False
    elif mood < 1/8 + 1/4:
        passed = True
    else:
        correct = 0
        wrong = 0
        
        exam_questions = random.sample(questions, min(3, len(questions)))
        
        for q in exam_questions:
            student_answer = student.choose_student_word(q)
            correct_answers = examiner.choose_correct_answer(q)
            
            if student_answer in correct_answers:
                correct += 1
                with lock:
                    question_stats[q.text] += 1
            else:
                wrong += 1
        
        passed = correct > wrong
    
    students_state[student_idx] = {
        "name": student.name,
        "status": "Сдал" if passed else "Провалил",
        "time": round(time.time() - start_time, 2)
    }
    
    return passed