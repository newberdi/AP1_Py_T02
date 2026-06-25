import os

def print_table(headers, rows):
    col_widths = [len(h) for h in headers]

    # считаем ширину колонок
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    def line():
        return "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    def format_row(row):
        return "| " + " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)) + " |"

    print(line())
    print(format_row(headers))
    print(line())

    for row in rows:
        print(format_row(row))

    print(line())

def clear():
    os.system("cls" if os.name == "nt" else "clear")