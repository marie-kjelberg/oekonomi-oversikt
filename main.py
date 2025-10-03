import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import read_bank
import read_csv
import re
import datetime as dt

csv_data_path = "./csv_data/"


class BaseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.files = []

        self.title("Økonomi Styring")
        self.geometry("1280x700")

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        self.title_label = ttk.Label(frame, text="Økonomi styring", font=("Helvetica", 24, "bold"))
        self.title_label.pack(pady=5)

        self.left_frame = tk.Frame(frame)
        self.left_frame.pack(side="left", fill="both", expand=True)

        self.right_frame = tk.Frame(frame)
        self.right_frame.pack(side="right", fill="both", expand=True)

        self.status_label = ttk.Label(self.left_frame, text="Status")
        self.status_label.pack(pady=5)
        self.status_text = tk.Text(self.left_frame, height=20, width=50)
        self.status_text.pack(pady=5)

        self.processed_files_label = ttk.Label(self.right_frame, text="Prosesserte filer: 0")
        self.processed_files_label.pack(pady=5)

        self.csv_files_btn = ttk.Button(self.right_frame, text="Velg CSVer", command=self.on_csv_button)
        self.csv_files_btn.pack(pady=5)

        self.clear_csv_btn = ttk.Button(self.right_frame, text="Slett prosesserte data", command=self.on_clear_csv)
        self.clear_csv_btn.pack(pady=5)

        self.set_dates_label = ttk.Label(self.right_frame, text="Velg dato (dd-mm-yyyy:dd-mm-yyyy):")
        self.set_dates_label.pack(pady=5)
        self.set_dates_input = tk.Entry(self.right_frame)
        self.set_dates_input.pack(pady=5)

        self.name_ignore_label = ttk.Label(self.right_frame, text="Navnet ditt (for å ignorere interne overføringer)")
        self.name_ignore_label.pack(pady=5)
        self.name_to_ignore = tk.Entry(self.right_frame)
        self.name_to_ignore.pack(pady=5)

        self.make_graphs_btn = ttk.Button(self.right_frame, text="Lag grafer!", command=self.on_make_graphs)
        self.make_graphs_btn.pack(pady=5)

        self.update_processed_files()

    def update_processed_files(self):
        processed_files = 0
        for file in os.listdir(csv_data_path):
            file_path = os.path.join(csv_data_path, file)
            if file_path.lower().endswith(".csv"):
                processed_files += 1

        self.processed_files_label.config(text=f"Prosesserte filer: {processed_files}")

    def on_csv_button(self):
        files = filedialog.askopenfilenames(
            title="Velg kontoutskrifter",
            filetypes=(("CSV-filer", "*.csv"), ("Alle filer", "*.*")))

        if not files:
            self.status_text.insert(tk.END, "Du valgte ingen filer!")
            return
        
        # read the files and convert them to csv's. 
        for file in files:
            status = read_bank.read_eika_csv(file)
            self.status_text.insert(tk.END, str(status))
        
        self.update_processed_files()

    def on_clear_csv(self):
        for file in os.listdir(csv_data_path):
            file_path = os.path.join(csv_data_path, file)
            if file_path.lower().endswith(".csv"):
                os.remove(file_path)
        
        self.status_text.insert(tk.END, "Slettet alle prosesserte data!")
        self.update_processed_files()

    def on_make_graphs(self):
        """ Makes graphs (or something) """
        date_text = self.set_dates_input.get()
        dates = re.findall(r"(\d{2})-(\d{2})-(\d{4}):(\d{2})-(\d{2})-(\d{4})", date_text)
        duration = (dt.datetime(1970, 1, 1), dt.datetime(2100, 1, 1))
        if len(dates) == 1:
            dates = dates[0]
            dates = [int(d) for d in dates]
            dates.reverse()  # dd mm yyyy, dd2 mm2 yyyy2 --> yyyy2 mm2 dd2, yyyy mm dd
            start_date = dt.datetime(*dates[3:])
            end_date = dt.datetime(*dates[:3])
            if end_date > start_date:
                duration = (start_date, end_date)

        # honestly, this could be better (it's very redudant)
        files = []
        for file in os.listdir(csv_data_path):
            file_path = os.path.join(csv_data_path, file)
            if file_path.lower().endswith(".csv"):
                files.append(file_path)

        if len(files) != 0:
            read_csv.graph_everything(files, duration, self.name_to_ignore.get())
        else:
            self.status_text.insert(tk.END, "Kunne ikke lage grafer, da ingen filer er prosesserte!")


def main():
    app = BaseApp()
    app.mainloop()


necessary_dirs = ["./csv_data/", "./kontoutskrifter"] 
if __name__ == "__main__":
    for dir in necessary_dirs:
        os.makedirs(dir, exist_ok=True)

    main()