import re
import sys

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QLabel,
    QDateEdit, QTimeEdit, QCheckBox, QHeaderView
)
from PyQt5.QtCore import Qt, QTime, QDate
from datetime import datetime

from export import export_to_pdf

# CONFIG
MAX_INFO = 30
MAX_TABLE_ENTRIES = 22
iban_re = re.compile(r'\b[A-Z]{2}[0-9]{2}(?:[ ]?[0-9]{4}){4}(?!(?:[ ]?[0-9]){3})(?:[ ]?[0-9]{1,2})?\b')


class TimeTrackingApp(QWidget):
    def __init__(self, default_iban="", default_name="", default_use_template=True, locations_list=None):
        super().__init__()
        self.setWindowTitle("EXPLORHINO TIME TRACKER")
        self.resize(950, 600)

        self.default_iban = default_iban
        self.default_name = default_name
        self.default_use_template = default_use_template
        self.locations_list = locations_list or ["Office", "Remote", "Client Site"]

        self.layout = QVBoxLayout(self)
        self.init_extra_fields()
        self.init_table()
        self.add_row()  # Add an initial row

    def init_extra_fields(self):
        """Initialize extra fields layout."""
        self.extra_fields_layout = QHBoxLayout()
        self.layout.addLayout(self.extra_fields_layout)

        # Name
        self.extra_fields_layout.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit(self.default_name)
        self.extra_fields_layout.addWidget(self.name_input)

        # Month
        self.extra_fields_layout.addWidget(QLabel("Month:"))
        self.month_combo = QComboBox()
        self.months = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        self.month_combo.addItems(self.months)
        prev_month = (datetime.now().month - 2) % 12
        self.month_combo.setCurrentIndex(prev_month)
        self.month_combo.currentIndexChanged.connect(self.update_all_row_months)
        self.extra_fields_layout.addWidget(self.month_combo)

        # Year
        self.extra_fields_layout.addWidget(QLabel("Year:"))
        self.year_combo = QComboBox()
        current_year = datetime.now().year
        years = [str(current_year), str(current_year - 1), str(current_year - 2)]
        self.year_combo.addItems(years)
        self.year_combo.setCurrentIndex(datetime.now().month == 1)
        self.extra_fields_layout.addWidget(self.year_combo)

        # IBAN
        self.extra_fields_layout.addWidget(QLabel("IBAN:"))
        self.iban_input = QLineEdit(self.default_iban)
        self.iban_input.textChanged.connect(self.check_iban)
        self.extra_fields_layout.addWidget(self.iban_input)

        # Use PDF Template
        self.use_pdf_checkbox = QCheckBox("Use PDF Template")
        self.use_pdf_checkbox.setChecked(self.default_use_template)
        self.extra_fields_layout.addWidget(self.use_pdf_checkbox)

    def init_table(self):
        """Initialize table layout."""
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Date", "From", "To", "Work Time", "Break Time", "Location", ""])
        self.layout.addWidget(self.table)

        # Buttons
        self.add_row_button = QPushButton("Add Row")
        self.add_row_button.clicked.connect(self.add_row)
        self.layout.addWidget(self.add_row_button)

        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_data)
        self.layout.addWidget(self.export_button)

    def add_row(self):
        """Add a new row with default values."""
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        # Date default to first of selected month and restricted to that month
        selected_month = self.month_combo.currentIndex() + 1
        selected_year = int(self.year_combo.currentText())
        first_of_month = QDate(selected_year, selected_month, 1)
        date_input = QDateEdit(first_of_month)
        date_input.setCalendarPopup(True)

        # Set min and max date to the selected month
        max_day = QDate(selected_year, selected_month, 1).daysInMonth()
        date_input.setMinimumDate(QDate(selected_year, selected_month, 1))
        date_input.setMaximumDate(QDate(selected_year, selected_month, max_day))

        self.table.setCellWidget(row_position, 0, date_input)

        # Time From/To default to 12:00
        time_from_input = QTimeEdit(QTime(12, 0))
        time_from_input.setDisplayFormat("HH:mm")
        self.table.setCellWidget(row_position, 1, time_from_input)
        time_from_input.timeChanged.connect(lambda _: self.update_timings(row_position))

        time_to_input = QTimeEdit(QTime(12, 0))
        time_to_input.setDisplayFormat("HH:mm")
        self.table.setCellWidget(row_position, 2, time_to_input)
        time_to_input.timeChanged.connect(lambda _: self.update_timings(row_position))

        # Spent Time
        spent_time_item = QTableWidgetItem("00:00")
        spent_time_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row_position, 3, spent_time_item)

        # Spent Time
        spent_time_item = QTableWidgetItem("00:00")
        spent_time_item.setFlags(Qt.ItemIsEnabled)
        self.table.setItem(row_position, 4, spent_time_item)

        # Location dropdown
        location_combo = QComboBox()
        location_combo.addItems(self.locations_list)
        location_combo.setEditable(True)
        location_combo.lineEdit().setMaxLength(MAX_INFO)
        self.table.setCellWidget(row_position, 5, location_combo)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)

        # Delete button
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(lambda _, button=delete_button: self.remove_row(button))
        self.table.setCellWidget(row_position, 6, delete_button)

        # Determine if add row is greyed out
        if self.table.rowCount() >= MAX_TABLE_ENTRIES:
            self.add_row_button.setDisabled(True)
        else:
            self.add_row_button.setDisabled(False)

    def update_timings(self, row):
        """Calculate and update spent time for a given row."""
        time_from = self.table.cellWidget(row, 1).time()
        time_to = self.table.cellWidget(row, 2).time()

        from_minutes = time_from.hour() * 60 + time_from.minute()
        to_minutes = time_to.hour() * 60 + time_to.minute()
        work_minutes = (to_minutes - from_minutes) % (24 * 60)

        if work_minutes > 9 * 60:
            break_minutes = 45
        elif work_minutes > 6 * 60:
            break_minutes = 30
        else:
            break_minutes = 0

        hours, minutes = divmod(work_minutes - break_minutes, 60)
        self.table.item(row, 3).setText(f"{hours:02}:{minutes:02}")
        hours, minutes = divmod(break_minutes, 60)
        self.table.item(row, 4).setText(f"{hours:02}:{minutes:02}")
        if break_minutes:
            self.table.item(row, 4).setBackground(Qt.yellow)
            self.table.item(row, 4).setForeground(Qt.black)
        else:
            palette = self.table.palette()  # Get the current palette of the table
            self.table.item(row, 4).setBackground(palette.color(palette.Base))
            self.table.item(row, 4).setForeground(palette.color(palette.Text))

    def remove_row(self, button):
        for row in range(self.table.rowCount()):
            if self.table.cellWidget(row, 6) == button:
                self.table.removeRow(row)
                if self.table.rowCount() >= MAX_TABLE_ENTRIES:
                    self.add_row_button.setDisabled(True)
                else:
                    self.add_row_button.setDisabled(False)
                return
        else:
            print("No row found")

    def update_all_row_months(self):
        """Update all rows' dates to the first of the selected month."""
        selected_month = self.month_combo.currentIndex() + 1
        selected_year = int(self.year_combo.currentText())
        max_day = QDate(selected_year, selected_month, 1).daysInMonth()

        for row in range(self.table.rowCount()):
            date_widget = self.table.cellWidget(row, 0)
            if date_widget:
                # Set date to first of month
                new_date = QDate(selected_year, selected_month, 1)
                date_widget.setDate(new_date)
                date_widget.setMinimumDate(QDate(selected_year, selected_month, 1))
                date_widget.setMaximumDate(QDate(selected_year, selected_month, max_day))

    def check_iban(self):
        cursor_pos = self.iban_input.cursorPosition()

        """Check if IBAN is valid."""
        iban = self.iban_input.text()
        if re.search(iban_re, iban.strip()):
            self.iban_input.setStyleSheet("")
            self.export_button.setDisabled(False)
        else:
            self.iban_input.setStyleSheet("background-color: red")
            self.iban_input.setToolTip("That does not look like a valid IBAN ._. Check again.")
            self.export_button.setDisabled(True)

        # Remove all spaces
        cleaned = iban.replace(" ", "").upper()

        # Group every 4 characters
        grouped = ' '.join(cleaned[i:i + 4] for i in range(0, len(cleaned), 4))

        # Calculate new cursor position
        diff = len(grouped) - len(iban)
        new_cursor_pos = max(0, cursor_pos + diff)

        # Block signals to avoid recursion
        self.iban_input.blockSignals(True)
        self.iban_input.setText(grouped)
        self.iban_input.setCursorPosition(new_cursor_pos)
        self.iban_input.blockSignals(False)

    def export_data(self):
        entries = []
        for row in range(self.table.rowCount()):
            data = [self.table.cellWidget(row, 0).date(),
                    self.table.cellWidget(row, 1).time(),
                    self.table.cellWidget(row, 2).time(),
                    self.table.item(row, 3).text(),
                    self.table.cellWidget(row, 5).currentText()]
            entries.append(data)
            print(f"- Date: {data[0]}, From: {data[1]}, To: {data[2]}, Spent: {data[3]}, Location: {data[4]}")

        payload = {
            "name": self.name_input.text(),
            "month": self.month_combo.currentIndex(),
            "year": self.year_combo.currentText(),
            "iban": self.iban_input.text(),
            "use_pdf_template": self.use_pdf_checkbox.isChecked(),
            "entries": entries
        }
        print(payload)
        export_to_pdf(payload)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimeTrackingApp(default_iban="DE12345678901234567890", default_name="John Doe")
    window.show()
    sys.exit(app.exec_())
