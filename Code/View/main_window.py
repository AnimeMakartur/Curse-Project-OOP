"""Головне вікно TravelSystem (PyQt6). Двоетапний flow: профіль туриста → планувальник.
БД travel_db.json автозавантажується при старті — за кулісами, без кнопок вибору файлу."""

import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtWidgets import *
from travel_client import TravelClient

DefaultDb = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "DataBase", "travel_db.json")
)

# Задник сторінки створення профілю туриста — фото з Code/View/images
_ViewDir = os.path.dirname(os.path.abspath(__file__))
ProfileBgImage = os.path.normpath(
    os.path.join(_ViewDir, "images", "istockphoto-1477997501-1024x1024.jpg")
)
if not os.path.exists(ProfileBgImage):
    # фолбек на колишнє розміщення в корені репозиторію
    _legacy = os.path.normpath(
        os.path.join(_ViewDir, "..", "..", "istockphoto-1477997501-1024x1024.jpg")
    )
    if os.path.exists(_legacy):
        ProfileBgImage = _legacy

# Основна кольорова тема застосунку: синій + білий.
# Базове правило QWidget — щоб ЛЮБИЙ віджет (у т.ч. при темній системній палітрі)
# мав білий фон і темний текст: без нього лишки теми та "білий текст на білому".
AppStyleSheet = """
QWidget {
    background: #ffffff;
    color: #1a2b4a;
}
QMainWindow, QStackedWidget, QDialog {
    background: #ffffff;
}
QLabel {
    color: #1a2b4a;
}
QGroupBox {
    background: #ffffff;
    border: 1px solid #c9d9f5;
    border-radius: 8px;
    margin-top: 14px;
    padding: 10px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #1a4fb0;
    background: #ffffff;
}
QPushButton {
    background: #2d6cdf;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background: #1a4fb0;
}
QPushButton:pressed {
    background: #143c8a;
}
QPushButton:disabled {
    background: #b9cff2;
    color: #f0f5ff;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
    background: #ffffff;
    border: 1px solid #c9d9f5;
    border-radius: 6px;
    padding: 5px 8px;
    color: #1a2b4a;
    selection-background-color: #2d6cdf;
    selection-color: #ffffff;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #2d6cdf;
}
QTextEdit:focus {
    border: 1px solid #2d6cdf;
}
QComboBox QAbstractItemView {
    background: #ffffff;
    color: #1a2b4a;
    border: 1px solid #c9d9f5;
    selection-background-color: #e8f0fd;
    selection-color: #1a4fb0;
}
QMenu {
    background: #ffffff;
    color: #1a2b4a;
    border: 1px solid #c9d9f5;
}
QMenu::item:selected {
    background: #2d6cdf;
    color: #ffffff;
}
QToolTip {
    background: #ffffff;
    color: #1a2b4a;
    border: 1px solid #c9d9f5;
}
QScrollBar:vertical, QScrollBar:horizontal {
    background: #f2f7ff;
    border: none;
}
QScrollBar:vertical {
    width: 12px;
}
QScrollBar:horizontal {
    height: 12px;
}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #c9d9f5;
    border-radius: 6px;
    min-height: 24px;
    min-width: 24px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background: #2d6cdf;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    height: 0;
    width: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}
QCheckBox {
    color: #1a2b4a;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #c9d9f5;
    border-radius: 4px;
    background: #ffffff;
}
QCheckBox::indicator:checked {
    background: #2d6cdf;
    border-color: #2d6cdf;
}
QTableWidget, QTreeWidget {
    background: #ffffff;
    alternate-background-color: #f2f7ff;
    gridline-color: #d7e4fa;
    border: 1px solid #c9d9f5;
    selection-background-color: #2d6cdf;
    selection-color: #ffffff;
    color: #1a2b4a;
}
QHeaderView::section {
    background: #2d6cdf;
    color: #ffffff;
    border: none;
    padding: 6px;
    font-weight: bold;
}
QTabWidget::pane {
    border: 1px solid #c9d9f5;
    background: #ffffff;
    border-radius: 6px;
}
QTabBar::tab {
    background: #e8f0fd;
    color: #1a4fb0;
    padding: 8px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: #2d6cdf;
    color: #ffffff;
}
QStatusBar {
    background: #1a4fb0;
    color: #ffffff;
}
QSplitter::handle {
    background: #c9d9f5;
}
"""

# Теги інтересів: (категорія, [(ключ_для_ядра, підпис_UI), ...])
InterestCategories = [
    (
        "Thematic interests",
        [
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
        ],
    ),
    (
        "Space and location format",
        [
            ("outdoor", "Outdoor"),
            ("indoor", "Indoor"),
            ("scenic_route", "Scenic pedestrian routes"),
        ],
    ),
    (
        "Pace and duration",
        [
            ("quick_visit", "Quick visit (15–45 min)"),
            ("deep_dive", "Deep dive (1.5–3+ h)"),
            ("relaxing", "Relaxing"),
            ("active", "Active leisure"),
        ],
    ),
    (
        "Budget and audience",
        [
            ("free_entry", "Free entry"),
            ("budget_friendly", "Budget friendly"),
            ("premium", "Premium / Exclusive"),
            ("family_friendly", "Family friendly"),
            ("nightlife", "Nightlife"),
            ("accessible", "Accessible"),
        ],
    ),
]
AllInterestKeys = [k for _, items in InterestCategories for k, _ in items]
DefaultInterests = {"history", "architecture"}
HotelMarkers = {"hotel", "hotels", "hostel", "accommodation", "lodging"}
CatalogColumns = ["Type", "Name", "Price, EUR", "Rating", "Opens", "Closes", "Tags", "Details"]
CatalogNumeric = {2, 3, 4, 5}
CatalogSearchColumns = (0, 1, 6, 7)
SortOptions = ["No sorting", "Relevance ↓", "Price ↑", "Price ↓", "Rating ↓"]
SortColumnMap = {2: 2, 3: 2, 4: 3}
SortAscending = {2: True, 3: False, 4: False}
PlanColumns = ["Step", "Time, h", "Cost, EUR", "Details"]
PathColumns = ["Transfer", "Distance, km", "Time, h", "Cost, EUR", "Chosen transport / line"]
TagChipStyle = (
    "QPushButton { border: 1px solid #c9d9f5; border-radius: 10px; padding: 3px 10px;"
    " background: #ffffff; color: #1a4fb0; }"
    "QPushButton:hover { border-color: #2d6cdf; background: #e8f0fd; }"
    "QPushButton:checked { background: #2d6cdf; color: #ffffff; border-color: #2d6cdf; }"
)


def _item(value, text=None, numeric=False):
    t = text if text is not None else (f"{value:g}" if numeric else str(value))
    it = QTableWidgetItem(t)
    it.setData(Qt.ItemDataRole.EditRole, float(value) if numeric else str(value))
    return it


def _fmtTransport(lane):
    t = lane.get("transportUkr") or lane.get("description") or lane.get("type", "")
    rn = lane.get("routeName", "")
    return f"{t} «{rn}»" if rn else t


class _BackgroundPage(QWidget):
    """Сторінка з фоновим фото: картинка розтягується на весь віджет (cover)."""

    def __init__(self, imagePath, parent=None):
        super().__init__(parent)
        self._bg = QPixmap(imagePath)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._bg.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        scaled = self._bg.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.drawPixmap(
            (self.width() - scaled.width()) // 2,
            (self.height() - scaled.height()) // 2,
            scaled,
        )
        # легке синє тонування поверх фото — під колірну тему застосунку
        painter.fillRect(self.rect(), QColor(26, 79, 176, 28))


class MainWindow(QMainWindow):
    def __init__(self, dbPath=None):
        super().__init__()
        self.setWindowTitle("TravelSystem — Personalized Travel Planner")
        self.resize(1920, 1080)
        self.setStyleSheet(AppStyleSheet)
        self.client = None
        self.cities = []
        self.lastPlan = None
        self._searchText = ""
        self.tagButtons = {}
        self.dbPath = os.path.normpath(dbPath) if dbPath else DefaultDb
        self._buildUi()
        self._connectClient()
        self._autoLoadDb()

    # ---------- хелпери UI ----------
    @staticmethod
    def _spin(cls, mn, mx, val, suffix=""):
        s = cls()
        s.setRange(mn, mx)
        s.setValue(val)
        if suffix:
            s.setSuffix(suffix)
        return s

    @staticmethod
    def _btn(text, slot):
        b = QPushButton(text)
        b.clicked.connect(slot)
        return b

    @staticmethod
    def _combo(items, slot=None):
        c = QComboBox()
        c.addItems(items)
        if slot:
            c.currentIndexChanged.connect(slot)
        return c

    @staticmethod
    def _label(text="", wrap=False, gray=False):
        l = QLabel(text)
        if wrap:
            l.setWordWrap(True)
        if gray:
            l.setStyleSheet("color: #5b6b8c;")
        return l

    @staticmethod
    def _group(title, layout_cls=QVBoxLayout):
        g = QGroupBox(title)
        layout_cls(g)
        return g

    def _buildUi(self):
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)
        self.stack.addWidget(self._buildProfilePage())
        self.stack.addWidget(self._buildPlannerPage())
        self.stack.setCurrentIndex(0)

    def _buildProfilePage(self):
        page = _BackgroundPage(ProfileBgImage)
        outer = QVBoxLayout(page)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea, QScrollArea > QWidget { background: transparent; border: none; }"
        )
        inner = QWidget()
        inner.setObjectName("profileCard")
        inner.setMaximumWidth(1000)
        inner.setStyleSheet(
            "#profileCard { background-color: rgba(255, 255, 255, 0.92); border-radius: 14px; }"
        )
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(20, 20, 20, 20)
        scroll.setWidget(inner)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(scroll, 3)
        row.addStretch(1)
        outer.addLayout(row, 1)

        gb = self._group("Tourist Profile", QFormLayout)
        form = gb.layout()
        self.editName = QLineEdit("Tourist")
        form.addRow("Name:", self.editName)
        self.spinBudget = self._spin(QDoubleSpinBox, 0, 10_000_000, 20, " €")
        form.addRow("Budget:", self.spinBudget)
        self.comboBudgetMode = self._combo(["on day", "for the whole trip"])
        form.addRow("Budget mode:", self.comboBudgetMode)
        self.spinDays = self._spin(QSpinBox, 1, 30, 2)
        form.addRow("Trip duration (days):", self.spinDays)
        self.spinTime = self._spin(QDoubleSpinBox, 1, 24, 8, " h")
        form.addRow("Hours per day:", self.spinTime)
        lay.addWidget(gb)

        gbTags = self._group("Interests (tags)")
        tagsLay = gbTags.layout()
        for catTitle, items in InterestCategories:
            catBox = self._group(catTitle, QGridLayout)
            grid = catBox.layout()
            for i, (key, label) in enumerate(items):
                chip = QPushButton(label)
                chip.setCheckable(True)
                chip.setChecked(key in DefaultInterests)
                chip.setStyleSheet(TagChipStyle)
                chip.setToolTip(key)
                chip.toggled.connect(self.onTagToggled)
                self.tagButtons[key] = chip
                grid.addWidget(chip, i // 3, i % 3)
            tagsLay.addWidget(catBox)
        tagsLay.addWidget(self._label("Selected tag keys:"))
        self.lblSelectedTags = self._label("", wrap=True, gray=True)
        tagsLay.addWidget(self.lblSelectedTags)
        self._updateSelectedTagsLabel()
        lay.addWidget(gbTags)

        btnRow = QHBoxLayout()
        btnRow.addStretch(1)
        self.btnContinue = self._btn(
            "Apply profile and proceed to city selection →", self.onContinueProfile
        )
        btnRow.addWidget(self.btnContinue)
        lay.addLayout(btnRow)
        lay.addStretch(1)
        return page

    def _buildPlannerPage(self):
        page = QWidget()
        QHBoxLayout(page)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        page.layout().addWidget(self.splitter)
        self.splitter.addWidget(self._buildLeftPanel())
        self.tabs = QTabWidget()
        self.splitter.addWidget(self.tabs)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        return page

    def _buildLeftPanel(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(600)
        scroll.setStyleSheet(
            "QScrollArea, QScrollArea > QWidget { background: #ffffff; border: none; }"
        )
        left = QWidget()
        lay = QVBoxLayout(left)
        scroll.setWidget(left)

        self.lblDbInfo = self._label("Database: loading automatically...", wrap=True, gray=True)
        lay.addWidget(self.lblDbInfo)
        lay.addWidget(self._btn("← Edit tourist profile", self.onBackToProfile))

        gbCity = self._group("1. City")
        self.comboCity = self._combo([], self.onCityChanged)
        gbCity.layout().addWidget(self.comboCity)
        self.lblCityDesc = self._label("", wrap=True)
        gbCity.layout().addWidget(self.lblCityDesc)
        lay.addWidget(gbCity)

        gbStart = self._group("2. Starting point of the route (city hotel)")
        sRow = QHBoxLayout()
        sRow.addWidget(QLabel("Hotel:"))
        self.comboStart = self._combo([], self.onStartChanged)
        sRow.addWidget(self.comboStart, 1)
        gbStart.layout().addLayout(sRow)
        self.lblStartHint = self._label("", wrap=True, gray=True)
        gbStart.layout().addWidget(self.lblStartHint)
        lay.addWidget(gbStart)

        gbAct = self._group("3. Actions")
        act = gbAct.layout()
        act.addWidget(self._btn("Catalog of the selected city", self.onShowCatalog))
        act.addWidget(self._btn("Filter by tourist parameters", self.onFilter))
        act.addWidget(self._btn("Sort by relevance", self.onSorted))
        act.addWidget(self._btn("Generate personalized plan", self.onGenerate))
        pRow = QHBoxLayout()
        pRow.addWidget(QLabel("To:"))
        self.comboTo = self._combo([])
        pRow.addWidget(self.comboTo, 1)
        act.addLayout(pRow)
        bRow = QHBoxLayout()
        self.chkBudget = QCheckBox("Custom path budget:")
        bRow.addWidget(self.chkBudget)
        self.spinPathBudget = self._spin(QDoubleSpinBox, 0, 1_000_000, 10, " €")
        bRow.addWidget(self.spinPathBudget)
        act.addLayout(bRow)
        act.addWidget(self._btn("Find shortest path from the hotel (Dijkstra)", self.onFindPath))
        lay.addWidget(gbAct)
        lay.addStretch(1)
        return scroll

    def _buildTabs(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        tools = QHBoxLayout()
        self.editSearch = QLineEdit()
        self.editSearch.setPlaceholderText("Search by name / tags / details...")
        self.editSearch.textChanged.connect(self.onSearchChanged)
        tools.addWidget(self.editSearch)
        tools.addWidget(QLabel("Sort:"))
        self.comboSort = self._combo(SortOptions, self.onSortChanged)
        tools.addWidget(self.comboSort)
        tools.addWidget(self._btn("Refresh", self.onShowCatalog))
        lay.addLayout(tools)
        self.tableCatalog = QTableWidget(0, len(CatalogColumns))
        self.tableCatalog.setHorizontalHeaderLabels(CatalogColumns)
        self.tableCatalog.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableCatalog.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableCatalog.setSortingEnabled(True)
        hdr = self.tableCatalog.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hdr.setStretchLastSection(True)
        lay.addWidget(self.tableCatalog)
        self.lblCatalogInfo = QLabel("")
        lay.addWidget(self.lblCatalogInfo)
        self.tabs.addTab(tab, "City Catalog")

        tab = QWidget()
        lay = QVBoxLayout(tab)
        self.treePlan = QTreeWidget()
        self.treePlan.setHeaderLabels(PlanColumns)
        h = self.treePlan.header()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self.treePlan)
        self.tabs.addTab(tab, "Travel Plan")

        tab = QWidget()
        lay = QVBoxLayout(tab)
        self.treePath = QTreeWidget()
        self.treePath.setHeaderLabels(PathColumns)
        self.treePath.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self.treePath)
        self.lblPathTotal = QLabel("")
        lay.addWidget(self.lblPathTotal)
        self.tabs.addTab(tab, "Path (Dijkstra)")

        tab = QWidget()
        lay = QVBoxLayout(tab)
        self.lblMetrics = self._label("Plan not generated yet", wrap=True)
        lay.addWidget(self.lblMetrics)
        self.txtSummary = QTextEdit()
        self.txtSummary.setReadOnly(True)
        lay.addWidget(self.txtSummary)
        self.tabs.addTab(tab, "Metrics & Summary")

    # ---------- клієнт ----------
    def _connectClient(self):
        try:
            self.client = TravelClient()
        except FileNotFoundError as e:
            self.client = None
            QMessageBox.critical(self, "Core library missing", str(e))
            self.statusBar().showMessage(str(e))
            return False
        return True

    def _requireClient(self):
        return self.client is not None or self._connectClient()

    # ---------- допоміжні ----------
    @staticmethod
    def _comboId(combo):
        d = combo.currentData()
        return int(d) if d is not None else -1

    def _currentCityId(self):
        return self._comboId(self.comboCity)

    def _currentStartId(self):
        return self._comboId(self.comboStart)

    def _selectedTags(self):
        return [
            k for k in AllInterestKeys if k in self.tagButtons and self.tagButtons[k].isChecked()
        ]

    def _updateSelectedTagsLabel(self):
        tags = self._selectedTags()
        self.lblSelectedTags.setText(", ".join(tags) if tags else "—")

    @staticmethod
    def _isHotel(dest):
        text = f"{dest.get('type', '')} {dest.get('name', '')}".lower()
        tags = {str(t).lower() for t in dest.get("tags", [])}
        return bool(tags & HotelMarkers) or any(m in text for m in ("hotel", "hostel", "готель"))

    def _applyProfile(self):
        self.client.setTourist(
            self.editName.text().strip() or "Tourist",
            self.spinBudget.value(),
            self.comboBudgetMode.currentIndex() == 1,
            self.spinDays.value(),
            self.spinTime.value(),
            self._selectedTags(),
            cityId=self._currentCityId(),
        )

    def _fillCities(self):
        self.comboCity.blockSignals(True)
        self.comboCity.clear()
        for c in self.cities:
            label = (
                f"{c['name']} (id={c['id']}" + (f", {c['region']}" if c.get("region") else "") + ")"
            )
            self.comboCity.addItem(label, c["id"])
        self.comboCity.blockSignals(False)
        if self.cities:
            self.comboCity.setCurrentIndex(0)
            self._updateCityDesc()

    def _updateCityDesc(self):
        idx = self.comboCity.currentIndex()
        self.lblCityDesc.setText(
            self.cities[idx].get("description", "") if 0 <= idx < len(self.cities) else ""
        )

    def _fillStartPoints(self):
        self.comboStart.blockSignals(True)
        self.comboStart.clear()
        cityId = self._currentCityId()
        hotels = sorted(
            (
                d
                for d in (self.client.getCatalog(cityId) if cityId >= 0 and self.client else [])
                if self._isHotel(d)
            ),
            key=lambda d: str(d.get("name", "")),
        )
        for h in hotels:
            self.comboStart.addItem(f"{h['name']} (id={h['id']})", h["id"])
        self.comboStart.blockSignals(False)
        self.lblStartHint.setText(
            f"Готелів у місті: {len(hotels)} — старт маршруту обирається зі списку."
            if hotels
            else "У базі немає готелів обраного міста (потрібен об'єкт із тегом hotel/accommodation) — шлях від готелю недоступний."
        )
        self._fillEndPoints()

    def _fillEndPoints(self):
        """Список усіх об'єктів обраного міста для вибору кінцевої точки маршруту (за назвами)."""
        self.comboTo.blockSignals(True)
        self.comboTo.clear()
        cityId = self._currentCityId()
        dests = sorted(
            (self.client.getCatalog(cityId) if cityId >= 0 and self.client else []),
            key=lambda d: str(d.get("name", "")),
        )
        for d in dests:
            self.comboTo.addItem(f"{d['name']} (id={d['id']})", d["id"])
        self.comboTo.blockSignals(False)

    def _fillCatalogTable(self, rows):
        self.tableCatalog.setSortingEnabled(False)
        self.tableCatalog.setRowCount(0)
        for d in rows:
            r = self.tableCatalog.rowCount()
            self.tableCatalog.insertRow(r)
            vals = [
                d["type"],
                d["name"],
                d["cost"],
                d["rating"],
                d["openHour"],
                d["closeHour"],
                ", ".join(d.get("tags", [])),
                d.get("details", ""),
            ]
            for col, v in enumerate(vals):
                self.tableCatalog.setItem(r, col, _item(v, numeric=col in CatalogNumeric))
        self.tableCatalog.setSortingEnabled(True)
        self._applySearchFilter()
        self.lblCatalogInfo.setText(f"Showing destinations: {self.tableCatalog.rowCount()}")

    def _applySearchFilter(self):
        text = self._searchText.lower()
        for r in range(self.tableCatalog.rowCount()):
            if not text:
                self.tableCatalog.setRowHidden(r, False)
            else:
                hay = " ".join(
                    self.tableCatalog.item(r, c).text() for c in CatalogSearchColumns
                ).lower()
                self.tableCatalog.setRowHidden(r, text not in hay)

    def _showError(self, title, message):
        QMessageBox.warning(self, title, message)
        self.statusBar().showMessage(message)

    # ---------- обробники ----------
    def _autoLoadDb(self):
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
        self._buildTabs()
        self.lblDbInfo.setText(
            f"Database (auto-loaded): {os.path.basename(self.dbPath)} — "
            f"{len(self.cities)} cities, {self.client.catalogSize()} destinations, {self.client.routesCount()} graph edges"
        )
        self.statusBar().showMessage(
            f"Database loaded automatically: {self.dbPath} — fill in the tourist profile"
        )
        self.stack.setCurrentIndex(0)

    def onTagToggled(self, _checked):
        self._updateSelectedTagsLabel()

    def onContinueProfile(self):
        if not self._requireClient():
            return
        if not self.editName.text().strip():
            self._showError("Profile not filled", "Input your name")
            return
        if not self._selectedTags():
            self._showError("Profile not filled", "Chose tags, min one required")
            return
        try:
            self._applyProfile()
        except Exception as e:
            self._showError("Profile error", str(e))
            return
        self.stack.setCurrentIndex(1)
        if self.cities:
            self.comboCity.setCurrentIndex(0)
            self.onCityChanged(0)
        p = self.client.getProfile()
        self.statusBar().showMessage(
            f"Profile applied: {p.get('name')}, tags: {', '.join(p.get('interests', []))}. Chosen city: {self.comboCity.currentText()}."
        )

    def onBackToProfile(self):
        self.stack.setCurrentIndex(0)
        self.statusBar().showMessage("Changed to profile editing")

    def onCityChanged(self, _index):
        self._updateCityDesc()
        if not self._requireClient():
            return
        cityId = self._currentCityId()
        if cityId >= 0:
            try:
                self._applyProfile()
            except Exception:
                pass
        self._fillStartPoints()
        self.statusBar().showMessage(f"Selected city id={cityId}")
        self.onShowCatalog()

    def onStartChanged(self, _index):
        sid = self._currentStartId()
        if sid >= 0 and self.client:
            self.statusBar().showMessage(f"Start point: {self.client.destinationName(sid)}")

    def onShowCatalog(self):
        if not self._requireClient():
            return
        self._fillCatalogTable(self.client.getCatalog(self._currentCityId()))
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
        self.comboSort.setCurrentIndex(1)
        self.comboSort.blockSignals(False)
        self.statusBar().showMessage(f"Sorted by relevance: {len(rows)} destinations")
        self.tabs.setCurrentIndex(0)

    def onSearchChanged(self, text):
        self._searchText = text
        self._applySearchFilter()

    def onSortChanged(self, index):
        if index == 1:
            self.onSorted()
        elif index in SortColumnMap:
            order = (
                Qt.SortOrder.AscendingOrder
                if SortAscending[index]
                else Qt.SortOrder.DescendingOrder
            )
            self.tableCatalog.sortItems(SortColumnMap[index], order)

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
            f"Plan generated: cost {plan.get('totalCost', 0):g} EUR, remaining {plan.get('remainingBudget', 0):g} EUR"
        )
        self.tabs.setCurrentIndex(1)

    def _fillPlanTree(self, plan):
        self.treePlan.clear()
        for day in plan.get("days", []):
            tTime = tCost = 0.0
            node = QTreeWidgetItem(self.treePlan, [f"Day {day['day']}", "", "", ""])
            node.setFirstColumnSpanned(True)
            f = node.font(0)
            f.setBold(True)
            node.setFont(0, f)
            for it in day.get("items", []):
                dest = it.get("destination") or {}
                for t in it.get("transfers", []):
                    QTreeWidgetItem(
                        node,
                        [
                            f"→ transfer {t.get('fromName', t['fromId'])} → {t.get('toName', t['toId'])}",
                            f"{t['timeHours']:.3f}",
                            f"{t['cost']:g}",
                            f"{t['distanceKm']:g} km — {_fmtTransport(t.get('lane', {}))}",
                        ],
                    )
                    tTime += t["timeHours"]
                    tCost += t["cost"]
                if dest:
                    QTreeWidgetItem(
                        node,
                        [
                            f"• {dest['name']}",
                            f"{dest.get('visitDuration', 0):g}",
                            f"{dest.get('cost', 0):g}",
                            f"{dest.get('type', '')}, rating {dest.get('rating', 0):g}, "
                            f"hours {dest.get('openHour', 0):g}–{dest.get('closeHour', 0):g}, tags: {', '.join(dest.get('tags', []))}",
                        ],
                    )
                    tTime += dest.get("visitDuration", 0)
                    tCost += dest.get("cost", 0)
            node.setText(1, f"{tTime:.2f}")
            node.setText(2, f"{tCost:g}")
        self.treePlan.expandAll()

    def _fillMetrics(self, plan):
        self.lblMetrics.setText(
            f"Total cost: {plan.get('totalCost', 0):g} EUR\nRemaining budget: {plan.get('remainingBudget', 0):g} EUR\n"
            f"Travel time: {plan.get('totalTravelTime', 0):.2f} h\nTime on site: {plan.get('totalVisitTime', 0):.2f} h\n"
            f"Total plan time: {plan.get('totalDuration', 0):.2f} h\nSelected city: id={plan.get('targetCityId', -1)}"
        )
        self.txtSummary.setPlainText(plan.get("summary", ""))

    def onFindPath(self):
        if not self._requireClient():
            return
        try:
            self._applyProfile()
        except Exception:
            pass
        a = self._currentStartId()
        if a < 0:
            self._showError(
                "Стартова точка не обрана",
                "Оберіть готель зі списку стартових точок обраного міста.",
            )
            return
        b = self._comboId(self.comboTo)
        if b < 0:
            self._showError(
                "Кінцева точка не обрана",
                "Оберіть об'єкт зі списку «To» обраного міста.",
            )
            return
        budget = self.spinPathBudget.value() if self.chkBudget.isChecked() else None
        steps = self.client.findShortestPath(a, b, budget=budget)
        nameA = self.client.destinationName(a)
        nameB = self.client.destinationName(b)
        self.treePath.clear()
        tTime = tCost = 0.0
        if not steps:
            QTreeWidgetItem(
                self.treePath,
                [f"No path {nameA} → {nameB} within the selected city", "", "", "", ""],
            )
        for s in steps:
            QTreeWidgetItem(
                self.treePath,
                [
                    f"{s.get('fromName', s['fromId'])} → {s.get('toName', s['toId'])}",
                    f"{s['distanceKm']:g}",
                    f"{s['timeHours']:.3f}",
                    f"{s['cost']:g}",
                    _fmtTransport(s.get("lane", {})),
                ],
            )
            tTime += s["timeHours"]
            tCost += s["cost"]
        self.lblPathTotal.setText(
            f"Total: {len(steps)} transfers, {tTime:.3f} h travel, {tCost:g} EUR"
            + (f" (path budget: {budget:g} EUR)" if budget is not None else " (profile budget)")
        )
        self.tabs.setCurrentIndex(2)
