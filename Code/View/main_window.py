"""Головне вікно TravelSystem (шар представлення, PyQt6).

Двоетапний flow:
  1. сторінка профілю туриста — ім'я, бюджет, тривалість поїздки та теги
     інтересів (чипси у 4 категоріях); у код/JSON передаються точні
     англійські ключі тегів для обрахунку відповідності з об'єктами каталогу;
  2. лише після застосування профілю — сторінка планувальника: вибір міста,
     стартової точки маршруту зі списку готелів обраного міста (ComboBox),
     каталог об'єктів міста (QTableWidget), запити та згенерований план по днях.

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
    QGridLayout,
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
    QStackedWidget,
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

# Теги інтересів профілю, згруповані за 4 категоріями.
# Ключ (перший елемент пари) — точний англійський ідентифікатор, який іде
# у ядро/JSON і зіставляється з тегами об'єктів каталогу; підпис — для UI.
InterestCategories = [
    ("Thematic interests", [
        ("history", "History"),
        ("architecture", "Architecture"),
        ("art", "Art"),
        ("science_tech", "Science and Technology"),
        ("nature", "Nature"),
        ("religion", "Religion and Temples"),
        ("entertainment", "Entertainment"),
        ("gastronomy", "Gastronomy"),
        ("shopping", "Shopping"),
        ("panoramic", "Panoramas"),
    ]),
    ("Space and location format", [
        ("outdoor", "Outdoor"),
        ("indoor", "Indoor"),
        ("scenic_route", "Scenic pedestrian routes"),
    ]),
    ("Pace and duration", [
        ("quick_visit", "Quick visit (15–45 min)"),
        ("deep_dive", "Deep dive (1.5–3+ h)"),
        ("relaxing", "Relaxing"),
        ("active", "Active leisure"),
    ]),
    ("Budget and audience", [
        ("free_entry", "Free entry"),
        ("budget_friendly", "Budget friendly"),
        ("premium", "Premium / Exclusive"),
        ("family_friendly", "Family friendly"),
        ("nightlife", "Nightlife"),
        ("accessible", "Accessible"),
    ]),
]
AllInterestKeys = [key for _, items in InterestCategories for key, _ in items]
DefaultInterests = {"history", "architecture"}

# Об'єкт каталогу вважається готелем (кандидат на стартову точку маршруту),
# якщо його type/name/теги містять один із маркерів.
HotelMarkers = {"hotel", "hotels", "hostel", "accommodation", "lodging"}

# Колонки каталогу без службових полів (без ID, Relevance, Visit h).
CatalogColumns = [
    "Type", "Name", "Price, EUR", "Rating", "Opens", "Closes", "Tags", "Details",
]
# індекси числових колонок для сортування
CatalogNumeric = {2, 3, 4, 5}
# колонки, за якими працює пошук (type, name, tags, details)
CatalogSearchColumns = (0, 1, 6, 7)

SortOptions = ["No sorting", "Relevance ↓", "Price ↑", "Price ↓", "Rating ↓"]
SortColumnMap = {2: 2, 3: 2, 4: 3}          # індекс comboSort -> колонка таблиці
SortAscending = {2: True, 3: False, 4: False}

PlanColumns = ["Step", "Time, h", "Cost, EUR", "Details"]

TagChipStyle = (
    "QPushButton { border: 1px solid #b8b8b8; border-radius: 10px;"
    " padding: 3px 10px; background: #f4f4f4; }"
    "QPushButton:hover { border-color: #2d6cdf; }"
    "QPushButton:checked { background: #2d6cdf; color: #ffffff;"
    " border-color: #2d6cdf; }"
)


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
        self.resize(1920, 1080)

        self.client = None
        self.cities = []
        self.lastPlan = None
        self._searchText = ""
        self.tagButtons = {}  # ключ тега -> чип (QPushButton)
        # Шлях до бази фіксований за кулісами; аргумент CLI може його лише перевизначити
        self.dbPath = os.path.normpath(dbPath) if dbPath else os.path.normpath(DefaultDb)

        self._buildUi()
        self._connectClient()
        self._autoLoadDb()

    # ---------------- побудова інтерфейсу ----------------
    def _buildUi(self):
        # Центральний QStackedWidget: сторінка 0 — профіль, сторінка 1 — планувальник
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)
        self.stack.addWidget(self._buildProfilePage())
        self.stack.addWidget(self._buildPlannerPage())
        self.stack.setCurrentIndex(0)

    def _buildProfilePage(self):
        """Сторінка 1: профіль туриста (заповнюється перед вибором міста)."""
        page = QWidget()
        pageLayout = QVBoxLayout(page)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        inner = QWidget()
        inner.setMaximumWidth(1000)
        innerLayout = QVBoxLayout(inner)
        scroll.setWidget(inner)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(scroll, 1)
        row.addStretch(1)
        pageLayout.addLayout(row, 1)

        gbProf = QGroupBox("Tourist Profile")
        form = QFormLayout(gbProf)
        self.editName = QLineEdit("Турист")
        form.addRow("Name:", self.editName)
        self.spinBudget = QDoubleSpinBox()
        self.spinBudget.setRange(0, 10_000_000)
        self.spinBudget.setValue(20)
        self.spinBudget.setSuffix(" €")
        form.addRow("Budget:", self.spinBudget)
        self.comboBudgetMode = QComboBox()
        self.comboBudgetMode.addItems(["на день", "на всю подорож"])
        form.addRow("Budget mode:", self.comboBudgetMode)
        self.spinDays = QSpinBox()
        self.spinDays.setRange(1, 30)
        self.spinDays.setValue(2)
        form.addRow("Trip duration (days):", self.spinDays)
        self.spinTime = QDoubleSpinBox()
        self.spinTime.setRange(1, 24)
        self.spinTime.setValue(8)
        self.spinTime.setSuffix(" год")
        form.addRow("Hours per day:", self.spinTime)
        innerLayout.addWidget(gbProf)

        # Теги інтересів: клікабельні чипси, згруповані за 4 категоріями
        gbTags = QGroupBox("Interests (tags)")
        tagsLayout = QVBoxLayout(gbTags)
        for catTitle, items in InterestCategories:
            catBox = QGroupBox(catTitle)
            grid = QGridLayout(catBox)
            for i, (key, label) in enumerate(items):
                chip = QPushButton(label)
                chip.setCheckable(True)
                chip.setChecked(key in DefaultInterests)
                chip.setStyleSheet(TagChipStyle)
                chip.setToolTip(key)  # точний англійський ключ тега
                chip.toggled.connect(self.onTagToggled)
                self.tagButtons[key] = chip
                grid.addWidget(chip, i // 3, i % 3)
            tagsLayout.addWidget(catBox)
        tagsLayout.addWidget(QLabel("Selected tag keys:"))
        self.lblSelectedTags = QLabel("")
        self.lblSelectedTags.setWordWrap(True)
        self.lblSelectedTags.setStyleSheet("color: gray;")
        tagsLayout.addWidget(self.lblSelectedTags)
        self._updateSelectedTagsLabel()
        innerLayout.addWidget(gbTags)

        btnRow = QHBoxLayout()
        btnRow.addStretch(1)
        self.btnContinue = QPushButton("Apply profile and proceed to city selection →")
        self.btnContinue.clicked.connect(self.onContinueProfile)
        btnRow.addWidget(self.btnContinue)
        innerLayout.addLayout(btnRow)
        innerLayout.addStretch(1)
        return page

    def _buildPlannerPage(self):
        """Сторінка 2: вибір міста, стартової точки (готель) та меню плану."""
        page = QWidget()
        pageLayout = QHBoxLayout(page)
        self.splitter = QSplitter(Qt.Orientation.Horizontal, page)
        pageLayout.addWidget(self.splitter)

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

        self.btnBack = QPushButton("← Edit tourist profile")
        self.btnBack.clicked.connect(self.onBackToProfile)
        leftLayout.addWidget(self.btnBack)

        # Місто / агломерація
        gbCity = QGroupBox("1. City")
        cityLayout = QVBoxLayout(gbCity)
        self.comboCity = QComboBox()
        self.comboCity.currentIndexChanged.connect(self.onCityChanged)
        cityLayout.addWidget(self.comboCity)
        self.lblCityDesc = QLabel("")
        self.lblCityDesc.setWordWrap(True)
        cityLayout.addWidget(self.lblCityDesc)
        leftLayout.addWidget(gbCity)

        # Стартова точка маршруту — готель обраного міста (ComboBox, не ручний ID)
        gbStart = QGroupBox("2. Starting point of the route (city hotel)")
        startLayout = QVBoxLayout(gbStart)
        startRow = QHBoxLayout()
        startRow.addWidget(QLabel("Hotel:"))
        self.comboStart = QComboBox()
        self.comboStart.currentIndexChanged.connect(self.onStartChanged)
        startRow.addWidget(self.comboStart, 1)
        startLayout.addLayout(startRow)
        self.lblStartHint = QLabel("")
        self.lblStartHint.setWordWrap(True)
        self.lblStartHint.setStyleSheet("color: gray;")
        startLayout.addWidget(self.lblStartHint)
        leftLayout.addWidget(gbStart)

        # Запити
        gbActions = QGroupBox("3. Actions")
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
        self.btnPath = QPushButton("Find shortest path from the hotel (Dijkstra)")
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

        return page

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

    def _currentStartId(self):
        data = self.comboStart.currentData()
        return int(data) if data is not None else -1

    def _selectedTags(self):
        """Точні англійські ключі обраних тегів (у канонічному порядку категорій)."""
        return [k for k in AllInterestKeys if k in self.tagButtons and self.tagButtons[k].isChecked()]

    def _updateSelectedTagsLabel(self):
        tags = self._selectedTags()
        self.lblSelectedTags.setText(", ".join(tags) if tags else "—")

    @staticmethod
    def _isHotel(dest):
        text = f"{dest.get('type', '')} {dest.get('name', '')}".lower()
        tags = {str(t).lower() for t in dest.get("tags", [])}
        return bool(tags & HotelMarkers) or any(m in text for m in ("hotel", "hostel", "готель"))

    def _applyProfile(self):
        """Передати профіль туриста у ядро разом із обраним містом (якщо є)."""
        self.client.setTourist(
            self.editName.text().strip() or "Турист",
            self.spinBudget.value(),
            self.comboBudgetMode.currentIndex() == 1,  # "на всю подорож"
            self.spinDays.value(),
            self.spinTime.value(),
            self._selectedTags(),
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

    def _fillStartPoints(self):
        """Список готелів обраного міста для старту маршруту (ComboBox)."""
        self.comboStart.blockSignals(True)
        self.comboStart.clear()
        hotels = []
        cityId = self._currentCityId()
        if cityId >= 0 and self.client is not None:
            for d in self.client.getCatalog(cityId):
                if self._isHotel(d):
                    hotels.append(d)
        hotels.sort(key=lambda d: str(d.get("name", "")))
        for h in hotels:
            self.comboStart.addItem(f"{h['name']} (id={h['id']})", h["id"])
        self.comboStart.blockSignals(False)
        if hotels:
            self.lblStartHint.setText(
                f"Готелів у місті: {len(hotels)} — старт маршруту обирається зі списку."
            )
        else:
            self.lblStartHint.setText(
                "У базі немає готелів обраного міста (потрібен об'єкт із тегом "
                "hotel/accommodation) — шлях від готелю недоступний."
            )

    def _fillCatalogTable(self, rows):
        self.tableCatalog.setSortingEnabled(False)
        self.tableCatalog.setRowCount(0)
        for d in rows:
            r = self.tableCatalog.rowCount()
            self.tableCatalog.insertRow(r)
            values = [
                (d["type"], None), (d["name"], None),
                (d["cost"], None), (d["rating"], None),
                (d["openHour"], f"{d['openHour']:g}"), (d["closeHour"], f"{d['closeHour']:g}"),
                (", ".join(d.get("tags", [])), None),
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
                self.tableCatalog.item(r, c).text() for c in CatalogSearchColumns
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
        nObj = self.client.catalogSize()
        nRoutes = self.client.routesCount()
        self.lblDbInfo.setText(
            f"Database (auto-loaded): {os.path.basename(self.dbPath)} — "
            f"{len(self.cities)} cities, {nObj} destinations, {nRoutes} graph edges"
        )
        self.statusBar().showMessage(
            f"Database loaded automatically: {self.dbPath} — заповніть профіль туриста"
        )
        # Залишаємось на сторінці профілю: місто та план — лише після профілю
        self.stack.setCurrentIndex(0)

    def onTagToggled(self, _checked):
        self._updateSelectedTagsLabel()

    def onContinueProfile(self):
        """Застосувати профіль і перейти до вибору міста та меню плану."""
        if not self._requireClient():
            return
        if not self.editName.text().strip():
            self._showError("Профіль не заповнено", "Input your name")
            return
        if not self._selectedTags():
            self._showError("Профіль не заповнено", "Chose tags, min one required")
            return
        try:
            self._applyProfile()  # місто ще не обрано → cityId=-1
        except Exception as e:
            self._showError("Profile error", str(e))
            return
        self.stack.setCurrentIndex(1)
        if self.cities:
            self.comboCity.setCurrentIndex(0)
            self.onCityChanged(0)
        profile = self.client.getProfile()
        self.statusBar().showMessage(
            f"Профіль застосовано: {profile.get('name')}, "
            f"теги: {', '.join(profile.get('interests', []))}. Chosen city: {self.comboCity.currentText()}."
        )

    def onBackToProfile(self):
        self.stack.setCurrentIndex(0)
        self.statusBar().showMessage("Редагування профілю туриста")

    def onCityChanged(self, _index):
        self._updateCityDesc()
        if not self._requireClient():
            return
        cityId = self._currentCityId()
        if cityId >= 0:
            # профіль туриста вже застосовано — оновлюємо лише місто
            try:
                self._applyProfile()
            except Exception:
                pass
        self._fillStartPoints()
        self.statusBar().showMessage(f"Selected city id={cityId}")
        self.onShowCatalog()

    def onStartChanged(self, _index):
        startId = self._currentStartId()
        if startId >= 0:
            self.statusBar().showMessage(f"Start point (hotel) id={startId}")

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
        elif index in SortColumnMap:
            col = SortColumnMap[index]
            order = Qt.SortOrder.AscendingOrder if SortAscending[index] else Qt.SortOrder.DescendingOrder
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
        a = self._currentStartId()  # старт — обраний готель, а не ручний ID
        if a < 0:
            self._showError(
                "Стартова точка не обрана",
                "Оберіть готель зі списку стартових точок обраного міста.",
            )
            return
        b = self.spinTo.value()
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
