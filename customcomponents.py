"""
    Some custom components for the UI
"""
import customtkinter as ctk
import datetime as dt
import calendar


class CTkDateSelector(ctk.CTkFrame):
    def __init__(self, master=None, start_year=2000, end_year=2030, **kwargs):
        super().__init__(master, **kwargs)

        self.days = [str(i).zfill(2) for i in range(1, 32)]
        self.months = [str(i).zfill(2) for i in range(1, 13)]
        self.years = [str(i) for i in range(start_year, end_year + 1)]

        today = dt.date.today()

        self.day_box = ctk.CTkComboBox(self, values=self.days, width=60, command=lambda _: self.update_days())
        self.day_box.set(str(today.day).zfill(2))
        self.day_box.pack(side="left", padx=2)

        self.month_box = ctk.CTkComboBox(self, values=self.months, width=60, command=lambda _: self.update_days())
        self.month_box.set(str(today.month).zfill(2))
        self.month_box.pack(side="left", padx=2)

        self.year_box = ctk.CTkComboBox(self, values=self.years, width=80, command=lambda _: self.update_days())
        self.year_box.set(str(today.year))
        self.year_box.pack(side="left", padx=2)

    def update_days(self):
        """ Make sure the user can't select a date which doesn't exist """
        try:
            year = int(self.year_box.get())
            month = int(self.month_box.get())
            _, last_day = calendar.monthrange(year, month)
            days = [str(i).zfill(2) for i in range(1, last_day + 1)]
        except ValueError:
            days = [str(i).zfill(2) for i in range(1, 32)]

        current_day = self.day_box.get()
        self.day_box.configure(values=days)

        if current_day not in days:  # ie. the user picked a nonexistent date
            self.day_box.set(days[-1])

    def get_date(self):
        """Return the selected date as a datetime.date object."""
        try:
            day = int(self.day_box.get())
            month = int(self.month_box.get())
            year = int(self.year_box.get())
            return dt.date(year, month, day)
        except ValueError:
            return None

    def set_date(self, date: dt.date):
        """Set the selector to a given datetime.date."""
        self.day_box.set(str(date.day).zfill(2))
        self.month_box.set(str(date.month).zfill(2))
        self.year_box.set(str(date.year))