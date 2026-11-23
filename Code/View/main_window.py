"""Головне вікно TravelSystem (шар представлення, PyQt6).

Ліва панель: завантаження БД, вибір міста/агломерації, профіль туриста, запити.
Права частина (вкладки): каталог об'єктів обраного міста (QTableWidget),
згенерований план по днях із деталями переходів, метрики, шлях Дейкстри.
"""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from travel_client import TravelClient

INTEREST_HINT = "наприклад: історія, архітектура, природа, їжа, музеї"

CATALOG_COLUMNS = [
    "ID", "Тип", "Назва", "Ціна, грн", "Рейтинг", "Огляд, год",
    "Відкрито", "Закрито", "Теги", "Релевантність", "Деталі",
]
# індекси числових колонок для сортування
CATALOG_NUMERIC = {0, 3, 4, 5, 6, 7, 9}

SORT_OPTIONS = ["Без сортування", "Релевантність ↓", "Ціна ↑", "Ціна ↓", "Рейтинг ↓"]

PLAN_COLUMNS = ["Крок", "Час, год", "Вартість, грн", "Деталі"]


def _num_item(value, text=None):
    """Числова комірка таблиці: сортується за числом, відображає text."""
    item = QTableWidgetItem(text if text is not None else f"{value:g}")
    item.setData(Qt.ItemDataRole.EditRole, float(value))
    return item


def _text_item(text):
    item = QTableWidgetItem(str(text))
    item.setData(Qt.ItemDataRole.EditRole, str(text))
    return item


class MainWindow(QMainWindow):
    def __init__(self, db_path=None):
        super().__init__()
        self.setWindowTitle("TravelSystem — персоналізований підбір туристичного плану")
        self.resize(1280, 760)

        self.client = None
        self.cities = []
        self.last_plan = None
        self._search_text = ""

        self._build_ui(db_path or "")
        self._connect_client()
        if db_path:
            self.edit_db.setText(os.path.normpath(db_path))

    # ---------------- побудова інтерфейсу ----------------
    def _build_ui(self, db_path):
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.setCentralWidget(splitter)

        # --- ліва панель ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        scroll.setWidget(left)
        splitter.addWidget(scroll)

        # База даних
        gb_db = QGroupBox("1. База даних (travel_db.json)")
        db_layout = QVBoxLayout(gb_db)
        row = QHBoxLayout()
        self.edit_db = QLineEdit(db_path)
        self.edit_db.setPlaceholderText("Шлях до JSON бази даних")
        row.addWidget(self.edit_db)
        btn_browse = QPushButton("Огляд...")
        btn_browse.clicked.connect(self.on_browse_db)
        row.addWidget(btn_browse)
        db_layout.addLayout(row)
        self.btn_load = QPushButton("Завантажити базу даних")
        self.btn_load.clicked.connect(self.on_load_db)
        db_layout.addWidget(self.btn_load)
        self.lbl_db_status = QLabel("Базу не завантажено")
        self.lbl_db_status.setWordWrap(True)
        db_layout.addWidget(self.lbl_db_status)
        left_layout.addWidget(gb_db)

        # Місто / агломерація
        gb_city = QGroupBox("2. Місто / агломерація")
        city_layout = QVBoxLayout(gb_city)
        self.combo_city = QComboBox()
        self.combo_city.currentIndexChanged.connect(self.on_city_changed)
        city_layout.addWidget(self.combo_city)
        self.lbl_city_desc = QLabel("")
        self.lbl_city_desc.setWordWrap(True)
        city_layout.addWidget(self.lbl_city_desc)
        left_layout.addWidget(gb_city)

        # Профіль туриста
        gb_prof = QGroupBox("3. Профіль туриста")
        form = QFormLayout(gb_prof)
        self.edit_name = QLineEdit("Турист")
        form.addRow("Ім'я:", self.edit_name)
        self.spin_budget = QDoubleSpinBox()
        self.spin_budget.setRange(0, 10_000_000)
        self.spin_budget.setValue(1000)
        self.spin_budget.setSuffix(" грн")
        form.addRow("Бюджет:", self.spin_budget)
        self.combo_budget_mode = QComboBox()
        self.combo_budget_mode.addItems(["на один день", "на всю подорож"])
        form.addRow("Бюджет задано:", self.combo_budget_mode)
        self.spin_days = QSpinBox()
        self.spin_days.setRange(1, 30)
        self.spin_days.setValue(2)
        form.addRow("Днів у подорожі:", self.spin_days)
        self.spin_time = QDoubleSpinBox()
        self.spin_time.setRange(1, 24)
        self.spin_time.setValue(8)
        self.spin_time.setSuffix(" год")
        form.addRow("Час на день:", self.spin_time)
        self.edit_interests = QLineEdit("історія, архітектура")
        form.addRow("Інтереси (через кому):", self.edit_interests)
        hint = QLabel(INTEREST_HINT)
        hint.setStyleSheet("color: gray;")
        form.addRow("", hint)
        self.btn_profile = QPushButton("Застосувати профіль")
        self.btn_profile.clicked.connect(self.on_apply_profile)
        form.addRow(self.btn_profile)
        left_layout.addWidget(gb_prof)

        # Запити
        gb_actions = QGroupBox("4. Запити до системи")
        act = QVBoxLayout(gb_actions)
        self.btn_catalog = QPushButton("Каталог обраного міста")
        self.btn_catalog.clicked.connect(self.on_show_catalog)
        act.addWidget(self.btn_catalog)
        self.btn_filter = QPushButton("Фільтр за параметрами туриста")
        self.btn_filter.clicked.connect(self.on_filter)
        act.addWidget(self.btn_filter)
        self.btn_sorted = QPushButton("Сортувати за релевантністю")
        self.btn_sorted.clicked.connect(self.on_sorted)
        act.addWidget(self.btn_sorted)
        self.btn_plan = QPushButton("Згенерувати персоналізований план")
        self.btn_plan.clicked.connect(self.on_generate)
        act.addWidget(self.btn_plan)
        path_row = QHBoxLayout()
        path_row.addWidget(QLabel("Шлях від id:"))
        self.spin_from = QSpinBox()
        self.spin_from.setRange(0, 100000)
        self.spin_from.setValue(1)
        path_row.addWidget(self.spin_from)
        path_row.addWidget(QLabel("до id:"))
        self.spin_to = QSpinBox()
        self.spin_to.setRange(0, 100000)
        self.spin_to.setValue(3)
        path_row.addWidget(self.spin_to)
        act.addLayout(path_row)
        budget_row = QHBoxLayout()
        self.chk_budget = QCheckBox("Власний бюджет на шлях:")
        budget_row.addWidget(self.chk_budget)
        self.spin_path_budget = QDoubleSpinBox()
        self.spin_path_budget.setRange(0, 1_000_000)
        self.spin_path_budget.setValue(500)
        self.spin_path_budget.setSuffix(" грн")
        budget_row.addWidget(self.spin_path_budget)
        act.addLayout(budget_row)
        self.btn_path = QPushButton("Знайти найкоротший шлях (Дейкстра)")
        self.btn_path.clicked.connect(self.on_find_path)
        act.addWidget(self.btn_path)
        left_layout.addWidget(gb_actions)
        left_layout.addStretch(1)

        # --- права частина: вкладки ---
        self.tabs = QTabWidget()
        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # Вкладка каталогу
        tab_catalog = QWidget()
        cat_layout = QVBoxLayout(tab_catalog)
        tools = QHBoxLayout()
        self.edit_search = QLineEdit()
        self.edit_search.setPlaceholderText("Пошук за назвою / тегами / деталями...")
        self.edit_search.textChanged.connect(self.on_search_changed)
        tools.addWidget(self.edit_search)
        tools.addWidget(QLabel("Сортування:"))
        self.combo_sort = QComboBox()
        self.combo_sort.addItems(SORT_OPTIONS)
        self.combo_sort.currentIndexChanged.connect(self.on_sort_changed)
        tools.addWidget(self.combo_sort)
        btn_refresh = QPushButton("Оновити")
        btn_refresh.clicked.connect(self.on_show_catalog)
        tools.addWidget(btn_refresh)
        cat_layout.addLayout(tools)
        self.table_catalog = QTableWidget(0, len(CATALOG_COLUMNS))
        self.table_catalog.setHorizontalHeaderLabels(CATALOG_COLUMNS)
        self.table_catalog.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_catalog.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_catalog.setSortingEnabled(True)
        self.table_catalog.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.table_catalog.horizontalHeader().setStretchLastSection(True)
        cat_layout.addWidget(self.table_catalog)
        self.lbl_catalog_info = QLabel("")
        cat_layout.addWidget(self.lbl_catalog_info)
        self.tabs.addTab(tab_catalog, "Каталог міста")

        # Вкладка плану
        tab_plan = QWidget()
        plan_layout = QVBoxLayout(tab_plan)
        self.tree_plan = QTreeWidget()
        self.tree_plan.setHeaderLabels(PLAN_COLUMNS)
        self.tree_plan.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in (1, 2):
            self.tree_plan.header().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.tree_plan.header().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        plan_layout.addWidget(self.tree_plan)
        self.tabs.addTab(tab_plan, "Туристичний план")

        # Вкладка шляху (Дейкстра)
        tab_path = QWidget()
        path_layout = QVBoxLayout(tab_path)
        self.tree_path = QTreeWidget()
        self.tree_path.setHeaderLabels(
            ["Перехід", "Відстань, км", "Час, год", "Вартість, грн", "Обраний транспорт / лінія"]
        )
        self.tree_path.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        path_layout.addWidget(self.tree_path)
        self.lbl_path_total = QLabel("")
        path_layout.addWidget(self.lbl_path_total)
        self.tabs.addTab(tab_path, "Шлях (Дейкстра)")

        # Вкладка метрик
        tab_metrics = QWidget()
        met_layout = QVBoxLayout(tab_metrics)
        self.lbl_metrics = QLabel("План ще не згенеровано")
        self.lbl_metrics.setWordWrap(True)
        met_layout.addWidget(self.lbl_metrics)
        self.txt_summary = QTextEdit()
        self.txt_summary.setReadOnly(True)
        met_layout.addWidget(self.txt_summary)
        self.tabs.addTab(tab_metrics, "Метрики та підсумок")

        self.statusBar().showMessage("Готово. Завантажте базу даних (travel_db.json).")

    def _connect_client(self):
        try:
            self.client = TravelClient()
        except FileNotFoundError as e:
            self.client = None
            QMessageBox.critical(self, "Немає бібліотеки ядра", str(e))
            self.statusBar().showMessage(str(e))
            return False
        return True

    # ---------------- допоміжні ----------------
    def _require_client(self):
        if self.client is None and not self._connect_client():
            return False
        return True

    def _current_city_id(self):
        data = self.combo_city.currentData()
        return int(data) if data is not None else -1

    def _parse_interests(self):
        return [s.strip() for s in self.edit_interests.text().split(",") if s.strip()]

    def _apply_profile(self):
        """Передати профіль туриста у ядро разом із обраним містом."""
        self.client.set_tourist(
            self.edit_name.text().strip() or "Турист",
            self.spin_budget.value(),
            self.combo_budget_mode.currentIndex() == 1,  # "на всю подорож"
            self.spin_days.value(),
            self.spin_time.value(),
            self._parse_interests(),
            city_id=self._current_city_id(),
        )

    def _fill_cities(self):
        self.combo_city.blockSignals(True)
        self.combo_city.clear()
        for c in self.cities:
            label = f"{c['name']} (id={c['id']}"
            if c.get("region"):
                label += f", {c['region']}"
            label += ")"
            self.combo_city.addItem(label, c["id"])
        self.combo_city.blockSignals(False)
        if self.cities:
            self.combo_city.setCurrentIndex(0)
            self._update_city_desc()

    def _update_city_desc(self):
        idx = self.combo_city.currentIndex()
        if 0 <= idx < len(self.cities):
            c = self.cities[idx]
            self.lbl_city_desc.setText(c.get("description", ""))
        else:
            self.lbl_city_desc.setText("")

    def _fill_catalog_table(self, rows):
        self.table_catalog.setSortingEnabled(False)
        self.table_catalog.setRowCount(0)
        for d in rows:
            r = self.table_catalog.rowCount()
            self.table_catalog.insertRow(r)
            values = [
                (d["id"], None), (d["type"], None), (d["name"], None),
                (d["cost"], None), (d["rating"], None), (d["visitDuration"], None),
                (d["openHour"], f"{d['openHour']:g}"), (d["closeHour"], f"{d['closeHour']:g}"),
                (", ".join(d.get("tags", [])), None),
                (d.get("relevance", 0.0), f"{d.get('relevance', 0.0):.3f}"),
                (d.get("details", ""), None),
            ]
            for col, (val, text) in enumerate(values):
                if col in CATALOG_NUMERIC:
                    self.table_catalog.setItem(r, col, _num_item(val, text))
                else:
                    self.table_catalog.setItem(r, col, _text_item(text if text is not None else val))
        self.table_catalog.setSortingEnabled(True)
        self._apply_search_filter()
        self.lbl_catalog_info.setText(f"Показано об'єктів: {self.table_catalog.rowCount()}")

    def _apply_search_filter(self):
        text = self._search_text.lower()
        for r in range(self.table_catalog.rowCount()):
            if not text:
                self.table_catalog.setRowHidden(r, False)
                continue
            hay = " ".join(
                self.table_catalog.item(r, c).text() for c in (1, 2, 8, 10)
            ).lower()
            self.table_catalog.setRowHidden(r, text not in hay)

    def _show_error(self, title, message):
        QMessageBox.warning(self, title, message)
        self.statusBar().showMessage(message)

    # ---------------- обробники ----------------
    def on_browse_db(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Оберіть файл бази даних JSON", os.path.dirname(self.edit_db.text()) or ".",
            "JSON (*.json);;Усі файли (*.*)",
        )
        if path:
            self.edit_db.setText(path)

    def on_load_db(self):
        if not self._require_client():
            return
        path = self.edit_db.text().strip()
        try:
            self.client.load_data(path)
        except RuntimeError as e:
            self._show_error("Помилка завантаження", str(e))
            return
        self.cities = self.client.get_cities()
        self._fill_cities()
        n_obj = self.client.catalog_size()
        n_routes = self.client.routes_count()
        self.lbl_db_status.setText(
            f"Завантажено: міст {len(self.cities)}, об'єктів {n_obj}, ребер графів {n_routes}"
        )
        self.statusBar().showMessage(f"Базу завантажено: {path}")
        self.on_show_catalog()

    def on_city_changed(self, _index):
        self._update_city_desc()
        if not self._require_client():
            return
        city_id = self._current_city_id()
        if city_id >= 0:
            # профіль tourist міг уже існувати — оновлюємо лише місто
            try:
                self._apply_profile()
            except Exception:
                pass
        self.statusBar().showMessage(f"Обрано місто id={city_id}")
        self.on_show_catalog()

    def on_apply_profile(self):
        if not self._require_client():
            return
        try:
            self._apply_profile()
        except Exception as e:
            self._show_error("Помилка профілю", str(e))
            return
        profile = self.client.get_profile()
        self.statusBar().showMessage(
            f"Профіль застосовано: місто id={profile.get('targetCityId')}, "
            f"денний бюджет {profile.get('dailyBudget'):g} грн"
        )

    def on_show_catalog(self):
        if not self._require_client():
            return
        city_id = self._current_city_id()
        rows = self.client.get_catalog(city_id)
        self._fill_catalog_table(rows)
        self.tabs.setCurrentIndex(0)

    def on_filter(self):
        if not self._require_client():
            return
        self._apply_profile()
        rows = self.client.filter_destinations()
        self._fill_catalog_table(rows)
        self.statusBar().showMessage(f"Фільтр (лінійний пошук) знайшов об'єктів: {len(rows)}")
        self.tabs.setCurrentIndex(0)

    def on_sorted(self):
        if not self._require_client():
            return
        self._apply_profile()
        rows = self.client.sorted_destinations()
        self._fill_catalog_table(rows)
        self.combo_sort.blockSignals(True)
        self.combo_sort.setCurrentIndex(1)  # "Релевантність ↓"
        self.combo_sort.blockSignals(False)
        self.statusBar().showMessage(f"Відсортовано за релевантністю: {len(rows)} об'єктів")
        self.tabs.setCurrentIndex(0)

    def on_search_changed(self, text):
        self._search_text = text
        self._apply_search_filter()

    def on_sort_changed(self, index):
        # combo_sort — перемикач сортування; фактичне сортування — через QTableWidget
        if index == 1:
            self.on_sorted()
        elif index in (2, 3, 4):
            col = {2: 3, 3: 3, 4: 4}[index]
            order = Qt.SortOrder.AscendingOrder if index == 2 else Qt.SortOrder.DescendingOrder
            self.table_catalog.sortItems(col, order)

    def on_generate(self):
        if not self._require_client():
            return
        try:
            self._apply_profile()
            plan = self.client.generate_plan()
        except Exception as e:
            self._show_error("Помилка генерації плану", str(e))
            return
        self.last_plan = plan
        self._fill_plan_tree(plan)
        self._fill_metrics(plan)
        self.statusBar().showMessage(
            f"План згенеровано: витрати {plan.get('totalCost', 0):g} грн, "
            f"залишок {plan.get('remainingBudget', 0):g} грн"
        )
        self.tabs.setCurrentIndex(1)

    def _fill_plan_tree(self, plan):
        self.tree_plan.clear()
        for day in plan.get("days", []):
            day_total_time = 0.0
            day_total_cost = 0.0
            day_node = QTreeWidgetItem(self.tree_plan, [f"День {day['day']}", "", "", ""])
            day_node.setFirstColumnSpanned(True)
            font = day_node.font(0)
            font.setBold(True)
            day_node.setFont(0, font)
            for item in day.get("items", []):
                dest = item.get("destination") or {}
                for t in item.get("transfers", []):
                    lane = t.get("lane", {})
                    route_name = lane.get("routeName", "")
                    transport = lane.get("transportUkr") or lane.get("description") or lane.get("type", "")
                    if route_name:
                        transport = f"{transport} «{route_name}»"
                    label = f"→ перехід {t['fromId']} → {t['toId']}"
                    detail = f"{t['distanceKm']:g} км — {transport}"
                    row = QTreeWidgetItem(day_node, [label, f"{t['timeHours']:.3f}", f"{t['cost']:g}", detail])
                    day_total_time += t["timeHours"]
                    day_total_cost += t["cost"]
                if dest:
                    label = f"• {dest['name']}"
                    detail = (
                        f"{dest.get('type', '')}, рейтинг {dest.get('rating', 0):g}, "
                        f"години {dest.get('openHour', 0):g}–{dest.get('closeHour', 0):g}, "
                        f"теги: {', '.join(dest.get('tags', []))}"
                    )
                    QTreeWidgetItem(
                        day_node,
                        [label, f"{dest.get('visitDuration', 0):g}", f"{dest.get('cost', 0):g}", detail],
                    )
                    day_total_time += dest.get("visitDuration", 0)
                    day_total_cost += dest.get("cost", 0)
            day_node.setText(1, f"{day_total_time:.2f}")
            day_node.setText(2, f"{day_total_cost:g}")
        self.tree_plan.expandAll()

    def _fill_metrics(self, plan):
        self.lbl_metrics.setText(
            "Загальні витрати: {cost:g} грн\n"
            "Залишок бюджету: {rem:g} грн\n"
            "Час у дорозі: {trav:.2f} год\n"
            "Час на локаціях: {visit:.2f} год\n"
            "Загальний час плану: {dur:.2f} год\n"
            "Обране місто: id={city}".format(
                cost=plan.get("totalCost", 0),
                rem=plan.get("remainingBudget", 0),
                trav=plan.get("totalTravelTime", 0),
                visit=plan.get("totalVisitTime", 0),
                dur=plan.get("totalDuration", 0),
                city=plan.get("targetCityId", -1),
            )
        )
        self.txt_summary.setPlainText(plan.get("summary", ""))

    def on_find_path(self):
        if not self._require_client():
            return
        try:
            self._apply_profile()
        except Exception:
            pass
        a, b = self.spin_from.value(), self.spin_to.value()
        budget = self.spin_path_budget.value() if self.chk_budget.isChecked() else None
        steps = self.client.find_shortest_path(a, b, budget=budget)
        self.tree_path.clear()
        total_time = 0.0
        total_cost = 0.0
        if not steps:
            QTreeWidgetItem(self.tree_path, [f"Шляху {a} → {b} у межах обраного міста немає", "", "", "", ""])
        for s in steps:
            lane = s.get("lane", {})
            route_name = lane.get("routeName", "")
            transport = lane.get("transportUkr") or lane.get("type", "")
            if route_name:
                transport = f"{transport} «{route_name}»"
            QTreeWidgetItem(
                self.tree_path,
                [
                    f"{s['fromId']} → {s['toId']}",
                    f"{s['distanceKm']:g}",
                    f"{s['timeHours']:.3f}",
                    f"{s['cost']:g}",
                    transport,
                ],
            )
            total_time += s["timeHours"]
            total_cost += s["cost"]
        self.lbl_path_total.setText(
            f"Разом: {len(steps)} переходів, {total_time:.3f} год у дорозі, {total_cost:g} грн"
            + (f" (бюджет на шлях: {budget:g} грн)" if budget is not None else " (бюджет профілю)")
        )
        self.tabs.setCurrentIndex(2)
