"""Графічний інтерфейс користувача (шар представлення, Python + tkinter).

Запуск:  python app.py            — GUI
         python app.py --console [шлях_до_db] — консольна демонстрація без вікна
"""

import json
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from travel_client import TravelClient

DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "DataBase", "travel_db.json")

INTEREST_HINT = "наприклад: історія, архітектура, природа, їжа, музеї"


class TravelApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TravelSystem — персоналізований підбору туристичного плану")
        self.geometry("980x640")
        self.client = None
        self._build_widgets()

    # ---------- побудова вікна ----------
    def _build_widgets(self):
        main = ttk.Frame(self, padding=8)
        main.pack(fill=tk.BOTH, expand=True)

        left = ttk.LabelFrame(main, text="Профіль туриста та запити", padding=8)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        self.var_name = tk.StringVar(value="Турист")
        self.var_budget = tk.StringVar(value="1000")
        self.var_budget_mode = tk.IntVar(value=0)  # 0 — на день, 1 — на всю подорож
        self.var_days = tk.IntVar(value=2)
        self.var_time = tk.StringVar(value="8")
        self.var_interests = tk.StringVar(value="історія, архітектура")
        self.var_db = tk.StringVar(value=os.path.normpath(DEFAULT_DB))
        self.var_from = tk.StringVar(value="1")
        self.var_to = tk.StringVar(value="3")

        row = 0
        ttk.Label(left, text="Ім'я:").grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(left, textvariable=self.var_name, width=26).grid(row=row, column=1, sticky=tk.W)
        row += 1
        ttk.Label(left, text="Бюджет, грн:").grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(left, textvariable=self.var_budget, width=26).grid(row=row, column=1, sticky=tk.W)
        row += 1
        ttk.Label(left, text="Бюджет задано:").grid(row=row, column=0, sticky=tk.W)
        mode = ttk.Frame(left)
        ttk.Radiobutton(mode, text="на один день", variable=self.var_budget_mode, value=0).pack(side=tk.LEFT)
        ttk.Radiobutton(mode, text="на всю подорож", variable=self.var_budget_mode, value=1).pack(side=tk.LEFT)
        mode.grid(row=row, column=1, sticky=tk.W)
        row += 1
        ttk.Label(left, text="Днів у подорожі:").grid(row=row, column=0, sticky=tk.W)
        ttk.Spinbox(left, from_=1, to=30, textvariable=self.var_days, width=6).grid(row=row, column=1, sticky=tk.W)
        row += 1
        ttk.Label(left, text="Час на день, год:").grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(left, textvariable=self.var_time, width=26).grid(row=row, column=1, sticky=tk.W)
        row += 1
        ttk.Label(left, text="Інтереси (через кому):").grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(left, textvariable=self.var_interests, width=26).grid(row=row, column=1, sticky=tk.W)
        ttk.Label(left, text=INTEREST_HINT, foreground="gray").grid(row=row + 1, column=0, columnspan=2, sticky=tk.W)
        row += 2

        ttk.Label(left, text="Файл бази даних (JSON):").grid(row=row, column=0, sticky=tk.W)
        db_row = ttk.Frame(left)
        ttk.Entry(db_row, textvariable=self.var_db, width=26).pack(side=tk.LEFT)
        ttk.Button(db_row, text="Огляд...", command=self._browse_db).pack(side=tk.LEFT, padx=4)
        db_row.grid(row=row, column=1, sticky=tk.W)
        row += 2

        ttk.Button(left, text="1. Завантажити базу даних", command=self.on_load_db).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=2)
        row += 1
        ttk.Button(left, text="2. Застосувати профіль", command=self.on_set_profile).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=2)
        row += 1
        ttk.Button(left, text="3. Фільтр каталогу (лінійний пошук)", command=self.on_filter).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=2)
        row += 1
        ttk.Button(left, text="4. Сортувати за релевантністю", command=self.on_sorted).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=2)
        row += 1
        ttk.Button(left, text="5. Згенерувати персоналізований план", command=self.on_generate).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=2)
        row += 1

        path_frame = ttk.LabelFrame(left, text="Найкоротший шлях (Дейкстра)", padding=4)
        path_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=4)
        ttk.Label(path_frame, text="від id:").pack(side=tk.LEFT)
        ttk.Entry(path_frame, textvariable=self.var_from, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(path_frame, text="до id:").pack(side=tk.LEFT)
        ttk.Entry(path_frame, textvariable=self.var_to, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Button(path_frame, text="Знайти", command=self.on_shortest_path).pack(side=tk.LEFT, padx=4)

        right = ttk.Frame(main)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.output = tk.Text(right, wrap=tk.WORD, font=("Consolas", 10))
        scroll = ttk.Scrollbar(right, command=self.output.yview)
        self.output.configure(yscrollcommand=scroll.set)
        self.output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._ensure_client()
        self._print("Готово. Завантажте базу даних кнопкою зліва (за замовчуванням Code/DataBase/travel_db.json).")

    # ---------- допоміжні ----------
    def _ensure_client(self):
        if self.client is None:
            try:
                self.client = TravelClient()
            except FileNotFoundError as e:
                messagebox.showerror("Немає бібліотеки ядра", str(e))
                self._print(str(e))
                return False
        return True

    def _browse_db(self):
        path = filedialog.askopenfilename(
            title="Оберіть файл бази даних JSON",
            filetypes=[("JSON", "*.json"), ("Усі файли", "*.*")],
            initialdir=os.path.dirname(self.var_db.get()),
        )
        if path:
            self.var_db.set(path)

    def _print(self, text):
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)

    def _print_json(self, title, data):
        self._print("=== " + title + " ===")
        self._print(json.dumps(data, ensure_ascii=False, indent=2))
        self._print("")

    def _apply_profile(self):
        interests = [s.strip() for s in self.var_interests.get().split(",") if s.strip()]
        self.client.set_tourist(
            self.var_name.get().strip() or "Турист",
            float(self.var_budget.get() or 0),
            self.var_budget_mode.get() == 1,
            int(self.var_days.get()),
            float(self.var_time.get() or 8),
            interests,
        )

    # ---------- обробники кнопок ----------
    def on_load_db(self):
        if not self._ensure_client():
            return
        path = self.var_db.get()
        ok = self.client.load_data(path)
        if ok:
            self._print(f"Базу даних завантажено: {path}")
            self._print(f"Об'єктів у каталозі: {self.client.catalog_size()}, "
                        f"ребер графа: {self.client.routes_count()}")
        else:
            messagebox.showerror("Помилка", f"Не вдалося завантажити файл: {path}")
            self._print(f"Помилка завантаження: {path}")

    def on_set_profile(self):
        if not self._ensure_client():
            return
        self._apply_profile()
        self._print_json("Профіль туриста", self.client.get_profile())

    def on_filter(self):
        if not self._ensure_client():
            return
        self._apply_profile()
        self._print_json("Фільтр каталогу (лінійний пошук)", self.client.filter_destinations())

    def on_sorted(self):
        if not self._ensure_client():
            return
        self._apply_profile()
        self._print_json("Відсортовано за релевантністю", self.client.sorted_destinations())

    def on_generate(self):
        if not self._ensure_client():
            return
        self._apply_profile()
        plan = self.client.generate_plan()
        self._print(plan.get("summary", ""))
        self._print_json("План (JSON)", plan)

    def on_shortest_path(self):
        if not self._ensure_client():
            return
        try:
            a, b = int(self.var_from.get()), int(self.var_to.get())
        except ValueError:
            messagebox.showerror("Помилка", "id мають бути цілими числами")
            return
        path = self.client.find_shortest_path(a, b)
        self._print_json(f"Найкоротший шлях {a} -> {b} (Дейкстра)", path)


def run_console(db_path):
    """Консольна демонстрація роботи без GUI (для перевірки після збірки)."""
    with TravelClient() as client:
        if not client.load_data(db_path):
            print(f"Не вдалося завантажити базу: {db_path}")
            return 1
        print(f"Завантажено об'єктів: {client.catalog_size()}, ребер графа: {client.routes_count()}")
        client.set_tourist("Єгор", 1000, True, 2, 8.0, ["історія", "архітектура", "природа"])
        print("\nПрофіль:", json.dumps(client.get_profile(), ensure_ascii=False, indent=2))
        print("\nФільтр:", json.dumps(client.filter_destinations(), ensure_ascii=False, indent=2))
        print("\nСортовано:", json.dumps(client.sorted_destinations(), ensure_ascii=False, indent=2))
        plan = client.generate_plan()
        print("\n" + plan.get("summary", ""))
        print("\nПлан JSON:", json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


def main():
    if "--console" in sys.argv:
        idx = sys.argv.index("--console")
        db = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else os.path.normpath(DEFAULT_DB)
        sys.exit(run_console(db))
    app = TravelApp()
    app.mainloop()


if __name__ == "__main__":
    main()
