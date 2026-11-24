"""Головне вікно TravelSystem (шар представлення, PyQt6).

Ліва панель: обране місто/агломерація, профіль туриста, запити.
Права частина (вкладки): каталог об'єктів обраного міста (QTableWidget),
згенерований план по днях із деталями переходів, метрики, шлях Дейкстри.

База даних (travel_db.json) завантажується автоматично при старті —
користувач не натискає кнопок і не обирає файл, БД працює за кулісами.
"""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
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

DefaultDb = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "DataBase", "travel_db.json"
)

InterestHint = "e.g.: history, architecture, nature, food, museums"

CatalogColumns = [
    "ID", "Type", "Name", "Price, EUR", "Rating", "Visit, h",
    "Opens", "Closes", "Tags", "Relevance", "Details",
]
# індекси числових колонок для сортування
CatalogNumeric = {0, 3, 4, 5, 6, 7, 9}

SortOptions = ["No sorting", "Relevance ↓", "Price ↑", "Price ↓", "Rating ↓"]

PlanColumns = ["Step", "Time, h", "Cost, EUR", "Details"]


def _numItem(value, text=None):
    """Числова комірка таблиці: сортується за числом, відображає text."""
    item = QTableWidgetItem(text if text is not None else f"{value:g}")
    item.setData(Qt.ItemDataRole.EditRole, float(value))
    return item


def _textItem(text):
    item = QTableWidgetItem(str(text))
    item.setData(Qt.ItemDataRole.EditRole, str(text))
    return item


class MainWindow(QMainWindow):
    def __init__(self, dbPath=None):
        super().__init__()
        self.setWindowTitle("TravelSystem — Personalized Travel Planner")
        self.resize(1280, 760)

        self.client = None
        self.cities = []
        self.lastPlan = None
        self._searchText = ""
        # Шлях до бази фіксований за кулісами; аргумент CLI може його лише перевизначити
        self.dbPath = os.path.normpath(dbPath) if dbPath else os.path.normpath(DefaultDb)

        self._buildUi()
        self._connectClient()
        self._autoLoadDb()

    # ---------------- побудова інтерфейсу ----------------
    def _buildUi(self):
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.setCentralWidget(self.splitter)

        # --- ліва панель ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(600)
        left = QWidget()
        leftLayout = QVBoxLayout(left)
        scroll.setWidget(left)
        self.splitter.addWidget(scroll)

        # Статус бази даних (автозавантаження, без елементів керування — за кулісами)
        self.lblDbInfo = QLabel("Database: loading automatically...")
        self.lblDbInfo.setWordWrap(True)
        self.lblDbInfo.setStyleSheet("color: gray;")
        leftLayout.addWidget(self.lblDbInfo)

        # Місто / агломерація
        gbCity = QGroupBox("1. City / agglomeration")
        cityLayout = QVBoxLayout(gbCity)
        self.comboCity = QComboBox()
        self.comboCity.currentIndexChanged.connect(self.onCityChanged)
        cityLayout.addWidget(self.comboCity)
        self.lblCityDesc = QLabel("")
        self.lblCityDesc.setWordWrap(True)
        cityLayout.addWidget(self.lblCityDesc)
        leftLayout.addWidget(gbCity)

        # Профіль туриста
        gbProf = QGroupBox("2. Tourist profile")
        form = QFormLayout(gbProf)
        self.editName = QLineEdit("Tourist")
        form.addRow("Name:", self.editName)
        self.spinBudget = QDoubleSpinBox()
        self.spinBudget.setRange(0, 10_000_000)
        self.spinBudget.setValue(20)
        self.spinBudget.setSuffix(" €")
        form.addRow("Budget:", self.spinBudget)
        self.comboBudgetMode = QComboBox()
        self.comboBudgetMode.addItems(["per day", "for the whole trip"])
        form.addRow("Budget is set:", self.comboBudgetMode)
        self.spinDays = QSpinBox()
        self.spinDays.setRange(1, 30)
        self.spinDays.setValue(2)
        form.addRow("Trip days:", self.spinDays)
        self.spinTime = QDoubleSpinBox()
        self.spinTime.setRange(1, 24)
        self.spinTime.setValue(8)
        self.spinTime.setSuffix(" h")
        form.addRow("Hours per day:", self.spinTime)
        self.editInterests = QLineEdit("history, architecture")
        form.addRow("Interests (comma-separated):", self.editInterests)
        hint = QLabel(InterestHint)
        hint.setStyleSheet("color: gray;")
        form.addRow("", hint)
        self.btnProfile = QPushButton("Apply profile")
        self.btnProfile.clicked.connect(self.onApplyProfile)
        form.addRow(self.btnProfile)
        leftLayout.addWidget(gbProf)

        # Запити
        gbActions = QGroupBox("3. Queries")
        act = QVBoxLayout(gbActions)
        self.btnCatalog = QPushButton("Catalog of the selected city")
        self.btnCatalog.clicked.connect(self.onShowCatalog)
        act.addWidget(self.btnCatalog)
        self.btnFilter = QPushButton("Filter by tourist parameters")
        self.btnFilter.clicked.connect(self.onFilter)
        act.addWidget(self.btnFilter)
        self.btnSorted = QPushButton("Sort by relevance")
        self.btnSorted.clicked.connect(self.onSorted)
        act.addWidget(self.btnSorted)
        self.btnPlan = QPushButton("Generate personalized plan")
        self.btnPlan.clicked.connect(self.onGenerate)
        act.addWidget(self.btnPlan)
        pathRow = QHBoxLayout()
        pathRow.addWidget(QLabel("Path from id:"))
        self.spinFrom = QSpinBox()
        self.spinFrom.setRange(0, 100000)
        self.spinFrom.setValue(1)
        pathRow.addWidget(self.spinFrom)
        pathRow.addWidget(QLabel("to id:"))
        self.spinTo = QSpinBox()
        self.spinTo.setRange(0, 100000)
        self.spinTo.setValue(3)
        pathRow.addWidget(self.spinTo)
        act.addLayout(pathRow)
        budgetRow = QHBoxLayout()
        self.chkBudget = QCheckBox("Custom path budget:")
        budgetRow.addWidget(self.chkBudget)
        self.spinPathBudget = QDoubleSpinBox()
        self.spinPathBudget.setRange(0, 1_000_000)
        self.spinPathBudget.setValue(10)
        self.spinPathBudget.setSuffix(" €")
        budgetRow.addWidget(self.spinPathBudget)
        act.addLayout(budgetRow)
        self.btnPath = QPushButton("Find shortest path (Dijkstra)")
        self.btnPath.clicked.connect(self.onFindPath)
        act.addWidget(self.btnPath)
        leftLayout.addWidget(gbActions)
        leftLayout.addStretch(1)

        # --- права частина: вкладки ---
        self.tabs = QTabWidget()
        self.splitter.addWidget(self.tabs)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        # Вкладка каталогу
        tabCatalog = QWidget()
        catLayout = QVBoxLayout(tabCatalog)
        tools = QHBoxLayout()
        self.editSearch = QLineEdit()
        self.editSearch.setPlaceholderText("Search by name / tags / details...")
        self.editSearch.textChanged.connect(self.onSearchChanged)
        tools.addWidget(self.editSearch)
        tools.addWidget(QLabel("Sort:"))
        self.comboSort = QComboBox()
        self.comboSort.addItems(SortOptions)
        self.comboSort.currentIndexChanged.connect(self.onSortChanged)
        tools.addWidget(self.comboSort)
        btnRefresh = QPushButton("Refresh")
        btnRefresh.clicked.connect(self.onShowCatalog)
        tools.addWidget(btnRefresh)
        catLayout.addLayout(tools)
        self.tableCatalog = QTableWidget(0, len(CatalogColumns))
        self.tableCatalog.setHorizontalHeaderLabels(CatalogColumns)
        self.tableCatalog.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableCatalog.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableCatalog.setSortingEnabled(True)
        self.tableCatalog.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.tableCatalog.horizontalHeader().setStretchLastSection(True)
        catLayout.addWidget(self.tableCatalog)
        self.lblCatalogInfo = QLabel("")
        catLayout.addWidget(self.lblCatalogInfo)
        self.tabs.addTab(tabCatalog, "City Catalog")

        # Вкладка плану
        tabPlan = QWidget()
        planLayout = QVBoxLayout(tabPlan)
        self.treePlan = QTreeWidget()
        self.treePlan.setHeaderLabels(PlanColumns)
        self.treePlan.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in (1, 2):
            self.treePlan.header().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.treePlan.header().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        planLayout.addWidget(self.treePlan)
        self.tabs.addTab(tabPlan, "Travel Plan")

        # Вкладка шляху (Дейкстра)
        tabPath = QWidget()
        pathLayout = QVBoxLayout(tabPath)
        self.treePath = QTreeWidget()
        self.treePath.setHeaderLabels(
            ["Transfer", "Distance, km", "Time, h", "Cost, EUR", "Chosen transport / line"]
        )
        self.treePath.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        pathLayout.addWidget(self.treePath)
        self.lblPathTotal = QLabel("")
        pathLayout.addWidget(self.lblPathTotal)
        self.tabs.addTab(tabPath, "Path (Dijkstra)")

        # Вкладка метрик
        tabMetrics = QWidget()
        metLayout = QVBoxLayout(tabMetrics)
        self.lblMetrics = QLabel("Plan not generated yet")
        self.lblMetrics.setWordWrap(True)
        metLayout.addWidget(self.lblMetrics)
        self.txtSummary = QTextEdit()
        self.txtSummary.setReadOnly(True)
        metLayout.addWidget(self.txtSummary)
        self.tabs.addTab(tabMetrics, "Metrics & Summary")

        self.statusBar().showMessage("Ready — loading the database automatically...")

    def _connectClient(self):
        try:
            self.client = TravelClient()
        except FileNotFoundError as e:
            self.client = None
            QMessageBox.critical(self, "Core library missing", str(e))
            self.statusBar().showMessage(str(e))
            return False
        return True

    # ---------------- допоміжні ----------------
    def _requireClient(self):
        if self.client is None and not self._connectClient():
            return False
        return True

    def _currentCityId(self):
        data = self.comboCity.currentData()
        return int(data) if data is not None else -1

    def _parseInterests(self):
        return [s.strip() for s in self.editInterests.text().split(",") if s.strip()]

    def _applyProfile(self):
        """Передати профіль туриста у ядро разом із обраним містом."""
        self.client.setTourist(
            self.editName.text().strip() or "Tourist",
            self.spinBudget.value(),
            self.comboBudgetMode.currentIndex() == 1,  # "for the whole trip"
            self.spinDays.value(),
            self.spinTime.value(),
            self._parseInterests(),
            cityId=self._currentCityId(),
        )

    def _fillCities(self):
        self.comboCity.blockSignals(True)
        self.comboCity.clear()
        for c in self.cities:
            label = f"{c['name']} (id={c['id']}"
            if c.get("region"):
                label += f", {c['region']}"
            label += ")"
            self.comboCity.addItem(label, c["id"])
        self.comboCity.blockSignals(False)
        if self.cities:
            self.comboCity.setCurrentIndex(0)
            self._updateCityDesc()

    def _updateCityDesc(self):
        idx = self.comboCity.currentIndex()
        if 0 <= idx < len(self.cities):
            c = self.cities[idx]
            self.lblCityDesc.setText(c.get("description", ""))
        else:
            self.lblCityDesc.setText("")

    def _fillCatalogTable(self, rows):
        self.tableCatalog.setSortingEnabled(False)
        self.tableCatalog.setRowCount(0)
        for d in rows:
            r = self.tableCatalog.rowCount()
            self.tableCatalog.insertRow(r)
            values = [
                (d["id"], None), (d["type"], None), (d["name"], None),
                (d["cost"], None), (d["rating"], None), (d["visitDuration"], None),
                (d["openHour"], f"{d['openHour']:g}"), (d["closeHour"], f"{d['closeHour']:g}"),
                (", ".join(d.get("tags", [])), None),
                (d.get("relevance", 0.0), f"{d.get('relevance', 0.0):.3f}"),
                (d.get("details", ""), None),
            ]
            for col, (val, text) in enumerate(values):
                if col in CatalogNumeric:
                    self.tableCatalog.setItem(r, col, _numItem(val, text))
                else:
                    self.tableCatalog.setItem(r, col, _textItem(text if text is not None else val))
        self.tableCatalog.setSortingEnabled(True)
        self._applySearchFilter()
        self.lblCatalogInfo.setText(f"Showing destinations: {self.tableCatalog.rowCount()}")

    def _applySearchFilter(self):
        text = self._searchText.lower()
        for r in range(self.tableCatalog.rowCount()):
            if not text:
                self.tableCatalog.setRowHidden(r, False)
                continue
            hay = " ".join(
                self.tableCatalog.item(r, c).text() for c in (1, 2, 8, 10)
            ).lower()
            self.tableCatalog.setRowHidden(r, text not in hay)

    def _showError(self, title, message):
        QMessageBox.warning(self, title, message)
        self.statusBar().showMessage(message)

    # ---------------- обробники ----------------
    def _autoLoadDb(self):
        """Автоматично завантажити базу даних при старті — без дій користувача."""
        if not self._requireClient():
            return
        try:
            self.client.loadData(self.dbPath)
        except RuntimeError as e:
            self.lblDbInfo.setText(f"Database: failed to load ({e})")
            self._showError("Database load error", str(e))
            return
        self.cities = self.client.getCities()
        self._fillCities()
        if self.cities:
            try:
                self._applyProfile()
            except Exception:
                pass
        nObj = self.client.catalogSize()
        nRoutes = self.client.routesCount()
        self.lblDbInfo.setText(
            f"Database (auto-loaded): {os.path.basename(self.dbPath)} — "
            f"{len(self.cities)} cities, {nObj} destinations, {nRoutes} graph edges"
        )
        self.statusBar().showMessage(f"Database loaded automatically: {self.dbPath}")
        self.onShowCatalog()

    def onCityChanged(self, _index):
        self._updateCityDesc()
        if not self._requireClient():
            return
        cityId = self._currentCityId()
        if cityId >= 0:
            # профіль tourist міг уже існувати — оновлюємо лише місто
            try:
                self._applyProfile()
            except Exception:
                pass
        self.statusBar().showMessage(f"Selected city id={cityId}")
        self.onShowCatalog()

    def onApplyProfile(self):
        if not self._requireClient():
            return
        try:
            self._applyProfile()
        except Exception as e:
            self._showError("Profile error", str(e))
            return
        profile = self.client.getProfile()
        self.statusBar().showMessage(
            f"Profile applied: city id={profile.get('targetCityId')}, "
            f"daily budget {profile.get('dailyBudget'):g} EUR"
        )

    def onShowCatalog(self):
        if not self._requireClient():
            return
        cityId = self._currentCityId()
        rows = self.client.getCatalog(cityId)
        self._fillCatalogTable(rows)
        self.tabs.setCurrentIndex(0)

    def onFilter(self):
        if not self._requireClient():
            return
        self._applyProfile()
        rows = self.client.filterDestinations()
        self._fillCatalogTable(rows)
        self.statusBar().showMessage(f"Filter (linear search) found destinations: {len(rows)}")
        self.tabs.setCurrentIndex(0)

    def onSorted(self):
        if not self._requireClient():
            return
        self._applyProfile()
        rows = self.client.sortedDestinations()
        self._fillCatalogTable(rows)
        self.comboSort.blockSignals(True)
        self.comboSort.setCurrentIndex(1)  # "Relevance ↓"
        self.comboSort.blockSignals(False)
        self.statusBar().showMessage(f"Sorted by relevance: {len(rows)} destinations")
        self.tabs.setCurrentIndex(0)

    def onSearchChanged(self, text):
        self._searchText = text
        self._applySearchFilter()

    def onSortChanged(self, index):
        # comboSort — перемикач сортування; фактичне сортування — через QTableWidget
        if index == 1:
            self.onSorted()
        elif index in (2, 3, 4):
            col = {2: 3, 3: 3, 4: 4}[index]
            order = Qt.SortOrder.AscendingOrder if index == 2 else Qt.SortOrder.DescendingOrder
            self.tableCatalog.sortItems(col, order)

    def onGenerate(self):
        if not self._requireClient():
            return
        try:
            self._applyProfile()
            plan = self.client.generatePlan()
        except Exception as e:
            self._showError("Plan generation error", str(e))
            return
        self.lastPlan = plan
        self._fillPlanTree(plan)
        self._fillMetrics(plan)
        self.statusBar().showMessage(
            f"Plan generated: cost {plan.get('totalCost', 0):g} EUR, "
            f"remaining {plan.get('remainingBudget', 0):g} EUR"
        )
        self.tabs.setCurrentIndex(1)

    def _fillPlanTree(self, plan):
        self.treePlan.clear()
        for day in plan.get("days", []):
            dayTotalTime = 0.0
            dayTotalCost = 0.0
            dayNode = QTreeWidgetItem(self.treePlan, [f"Day {day['day']}", "", "", ""])
            dayNode.setFirstColumnSpanned(True)
            font = dayNode.font(0)
            font.setBold(True)
            dayNode.setFont(0, font)
            for item in day.get("items", []):
                dest = item.get("destination") or {}
                for t in item.get("transfers", []):
                    lane = t.get("lane", {})
                    routeName = lane.get("routeName", "")
                    transport = lane.get("transportUkr") or lane.get("description") or lane.get("type", "")
                    if routeName:
                        transport = f"{transport} «{routeName}»"
                    label = f"→ transfer {t['fromId']} → {t['toId']}"
                    detail = f"{t['distanceKm']:g} km — {transport}"
                    row = QTreeWidgetItem(dayNode, [label, f"{t['timeHours']:.3f}", f"{t['cost']:g}", detail])
                    dayTotalTime += t["timeHours"]
                    dayTotalCost += t["cost"]
                if dest:
                    label = f"• {dest['name']}"
                    detail = (
                        f"{dest.get('type', '')}, rating {dest.get('rating', 0):g}, "
                        f"hours {dest.get('openHour', 0):g}–{dest.get('closeHour', 0):g}, "
                        f"tags: {', '.join(dest.get('tags', []))}"
                    )
                    QTreeWidgetItem(
                        dayNode,
                        [label, f"{dest.get('visitDuration', 0):g}", f"{dest.get('cost', 0):g}", detail],
                    )
                    dayTotalTime += dest.get("visitDuration", 0)
                    dayTotalCost += dest.get("cost", 0)
            dayNode.setText(1, f"{dayTotalTime:.2f}")
            dayNode.setText(2, f"{dayTotalCost:g}")
        self.treePlan.expandAll()

    def _fillMetrics(self, plan):
        self.lblMetrics.setText(
            "Total cost: {cost:g} EUR\n"
            "Remaining budget: {rem:g} EUR\n"
            "Travel time: {trav:.2f} h\n"
            "Time on site: {visit:.2f} h\n"
            "Total plan time: {dur:.2f} h\n"
            "Selected city: id={city}".format(
                cost=plan.get("totalCost", 0),
                rem=plan.get("remainingBudget", 0),
                trav=plan.get("totalTravelTime", 0),
                visit=plan.get("totalVisitTime", 0),
                dur=plan.get("totalDuration", 0),
                city=plan.get("targetCityId", -1),
            )
        )
        self.txtSummary.setPlainText(plan.get("summary", ""))

    def onFindPath(self):
        if not self._requireClient():
            return
        try:
            self._applyProfile()
        except Exception:
            pass
        a, b = self.spinFrom.value(), self.spinTo.value()
        budget = self.spinPathBudget.value() if self.chkBudget.isChecked() else None
        steps = self.client.findShortestPath(a, b, budget=budget)
        self.treePath.clear()
        totalTime = 0.0
        totalCost = 0.0
        if not steps:
            QTreeWidgetItem(self.treePath, [f"No path {a} → {b} within the selected city", "", "", "", ""])
        for s in steps:
            lane = s.get("lane", {})
            routeName = lane.get("routeName", "")
            transport = lane.get("transportUkr") or lane.get("type", "")
            if routeName:
                transport = f"{transport} «{routeName}»"
            QTreeWidgetItem(
                self.treePath,
                [
                    f"{s['fromId']} → {s['toId']}",
                    f"{s['distanceKm']:g}",
                    f"{s['timeHours']:.3f}",
                    f"{s['cost']:g}",
                    transport,
                ],
            )
            totalTime += s["timeHours"]
            totalCost += s["cost"]
        self.lblPathTotal.setText(
            f"Total: {len(steps)} transfers, {totalTime:.3f} h travel, {totalCost:g} EUR"
            + (f" (path budget: {budget:g} EUR)" if budget is not None else " (profile budget)")
        )
        self.tabs.setCurrentIndex(2)
