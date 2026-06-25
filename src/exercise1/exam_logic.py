from multiprocessing import Process, Manager
import time
from utils import clear, print_table
from workers import examiner_worker


class ExamLogic:
    def __init__(self, students, examiners, questions):
        self.manager = Manager()

        self.students_state = self.manager.list() # очередь состояний студента, чтобы все экзаменаторы видели
        self.lock = self.manager.Lock()
        
        for s in students:
            self.students_state.append({
                "name": s.name,
                "status": "Очередь",
                "time": 0.0
            })
        
        self.queue = self.manager.list(range(len(students))) # FIFO
        
        self.students = students
        self.examiners = examiners
        self.examiner_state = self.manager.list()
        self.examiner_index = {}
        
        for idx, e in enumerate(examiners):
            self.examiner_state.append({
                "name": e.name,
                "current": "-",
                "total": 0,
                "failed": 0,
                "time": 0.0
            })
            self.examiner_index[e.name] = idx
        
        self.questions = questions
        self.question_stats = self.manager.dict() # для лучшего вопроса (счетчик верных ответов на вопрос)
        for q in questions:
            self.question_stats[q.text] = 0

    def run(self):
        start_time = time.time()
        processes = []

        for examiner in self.examiners:
            p = Process(
                target=examiner_worker,
                args=(
                    examiner,
                    self.queue,
                    self.questions,
                    self.students,
                    self.students_state,
                    self.examiner_state,
                    self.examiner_index,
                    self.lock,
                    self.question_stats
                )
            )
            processes.append(p)
            p.start()

        while any(p.is_alive() for p in processes):
            clear()

            status_order = {"Очередь": 0, "Сдал": 1, "Провалил": 2}
            sorted_students = sorted(self.students_state,
                key=lambda x: status_order.get(x["status"], 99))

            print_table(
                ["Студент", "Статус"],
                [(s["name"], s["status"]) for s in sorted_students])

            print_table(
                ["Экзаменатор", "Текущий студент", "Всего студентов", "Завалил", "Время работы"],
                [(e["name"], e["current"], e["total"], e["failed"], e["time"]) for e in self.examiner_state])
            print()

            in_queue = sum(1 for s in self.students_state if s["status"] == "Очередь")
            total = len(self.students_state)
            print(f"Осталось в очереди: {in_queue} из {total}")
            
            time_now = round(time.time() - start_time, 2)
            print(f"Время с момента начала экзамена: {time_now}")

            time.sleep(0.5)

        for p in processes:
            p.join() # неочевидно, но ждет, пока процессы закончатся
        
        total_time = round(time.time() - start_time, 2)
        
        clear()

        final_students = sorted(self.students_state, 
            key=lambda x: (0 if x["status"] == "Сдал" else 1, x["name"]))
    
        print_table(
            ["Студент", "Статус"],
            [(s["name"], s["status"]) for s in final_students])
        print()
        
        print_table(
            ["Экзаменатор", "Всего студентов", "Завалил", "Время работы"],
            [(e["name"], e["total"], e["failed"], e["time"]) for e in self.examiner_state])
        print()
        
        print(f"Время с момента начала экзамена и до момента его завершения: {total_time}")
        
        passed_students = [s for s in self.students_state if s["status"] == "Сдал"]
        if passed_students:
            min_time = min(s["time"] for s in passed_students)
            best_students = [s["name"] for s in passed_students if s["time"] == min_time]
            print(f"Имена лучших студентов: {', '.join(best_students)}")
        else:
            print("Имена лучших студентов: -")
        
        best_examiners = []
        min_fail_rate = 100
        for e in self.examiner_state:
            if e["total"] > 0:
                rate = e["failed"] / e["total"] * 100
                if rate < min_fail_rate:
                    min_fail_rate = rate
                    best_examiners = [e["name"]]
                elif rate == min_fail_rate:
                    best_examiners.append(e["name"])
        print(f"Имена лучших экзаменаторов: {', '.join(best_examiners)}")
        
        failed_students = [s for s in self.students_state if s["status"] == "Провалил"]
        if failed_students:
            min_fail_time = min(s["time"] for s in failed_students)
            expelled = [s["name"] for s in failed_students if s["time"] == min_fail_time]
            print(f"Имена студентов, которых после экзамена отчислят: {', '.join(expelled)}")
        else:
            print("Имена студентов, которых после экзамена отчислят: -")
        
        max_correct = max(self.question_stats.values()) if self.question_stats else 0
        best_questions = [q for q, count in self.question_stats.items() if count == max_correct]
        print(f"Лучшие вопросы: {', '.join(best_questions)}")
        
        total_students = len(self.students_state)
        passed_count = len(passed_students)
        success_rate = passed_count / total_students * 100 if total_students > 0 else 0
        
        if success_rate > 85:
            print(f"Вывод: экзамен удался ({success_rate:.1f}% сдавших)")
        else:
            print(f"Вывод: экзамен не удался ({success_rate:.1f}% сдавших)")