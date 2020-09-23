from PySide2.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QTableView,
    QDialogButtonBox,
    QAbstractItemView,
    QHeaderView,
)
from PySide2.QtCore import Qt, QAbstractTableModel, QModelIndex
from cutevariant.gui.plugin import PluginDialog

from cutevariant.core import sql

import sqlite3


#  Metrics
def get_variant_count(conn: sqlite3.Connection):
    return conn.execute(
        "SELECT `count` FROM selections WHERE name = 'variants'"
    ).fetchone()["count"]


def get_variant_transition(conn: sqlite3.Connection):
    return conn.execute(
        "SELECT COUNT(*) as `count` FROM variants WHERE (ref == 'A' AND alt == 'G') OR (ref == 'G' AND alt == 'A') OR (ref == 'C' AND alt == 'T') OR (ref == 'T' AND alt == 'C') "
    ).fetchone()["count"]


def get_variant_transversion(conn: sqlite3.Connection):
    return conn.execute(
        "SELECT COUNT(*) as `count` FROM variants WHERE (ref == 'A' AND alt == 'C') OR (ref == 'C' AND alt == 'A') OR (ref == 'G' AND alt == 'T') OR (ref == 'T' AND alt == 'G') OR (ref == 'G' AND alt == 'C') OR (ref == 'C' AND alt == 'G') OR (ref == 'A' AND alt == 'T')OR (ref == 'T' AND alt == 'A')      "
    ).fetchone()["count"]


def get_sample_count(conn: sqlite3.Connection):
    return conn.execute("SELECT COUNT(*)  as `count` FROM samples").fetchone()["count"]


def get_snp_count(conn: sqlite3.Connection):
    return conn.execute(
        "SELECT COUNT(*)  as `count` FROM variants WHERE is_snp = 1"
    ).fetchone()["count"]


class MetricModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.items = []

    def columnCount(self, parent=QModelIndex()) -> int:
        """ override """
        if parent == QModelIndex():
            return 2
        else:
            return None

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.items)

    def data(self, index, role):

        if role == Qt.DisplayRole:
            return self.items[index.row()][index.column()]
        return None

    def clear(self):
        self.beginResetModel()
        self.items.clear()
        self.endResetModel()

    def add_metrics(self, name, value):

        self.beginInsertRows(QModelIndex(), len(self.items), len(self.items))
        self.items.append((name, value))
        self.endInsertRows()


class MetricDialog(PluginDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # self.conn = self.mainwindow.conn
        self.view = QTableView()
        self.model = MetricModel()
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok)

        self.view.setModel(self.model)
        self.view.setAlternatingRowColors(True)
        self.view.horizontalHeader().hide()
        self.view.verticalHeader().hide()
        self.view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.buttons.accepted.connect(self.accept)

        self.setWindowTitle("Metrics Plugin")

        v_layout = QVBoxLayout()
        v_layout.addWidget(self.view)
        v_layout.addWidget(self.buttons)
        self.setLayout(v_layout)

    def on_refresh(self):
        """ override """
        self.populate()

    def populate(self):
        self.model.clear()

        self.model.add_metrics("Variant count", get_variant_count(self.conn))
        self.model.add_metrics("Snp count", get_snp_count(self.conn))

        transition = get_variant_transition(self.conn)
        transversion = get_variant_transversion(self.conn)
        ratio = transition / transversion

        self.model.add_metrics("Transition count", transition)
        self.model.add_metrics("Transversion count", transversion)
        self.model.add_metrics("Tr/tv ratio", ratio)
        self.model.add_metrics("Samples count", get_sample_count(self.conn))

        self.view.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)


if __name__ == "__main__":
    from PySide2.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    conn = sql.get_sql_connexion("test.db")

    dialog = MetricDialog()
    dialog.conn = conn
    dialog.populate()

    dialog.show()

    app.exec_()