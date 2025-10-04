import os
from tkinter import filedialog
import read_bank
import read_csv
import datetime as dt
import customtkinter as ctk
import customcomponents as cc

csv_data_path = "./csv_data/"


class BaseApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.files = []

        self.title("Økonomi Styring")
        self.geometry("1280x700")
        ctk.set_appearance_mode("system")  # "light" or "dark"
        ctk.set_default_color_theme("blue")  # colours

        frame = ctk.CTkFrame(self, corner_radius=10)
        frame.pack(fill="both", expand=True)

        self.title_label = ctk.CTkLabel(frame, text="Økonomi styring", font=("Helvetica", 24, "bold"))
        self.title_label.pack(pady=5)

        self.left_frame = ctk.CTkFrame(frame, corner_radius=0, fg_color="transparent")
        self.left_frame.pack(side="left", fill="both", expand=True)

        self.right_frame = ctk.CTkFrame(frame, corner_radius=0, fg_color="transparent")
        self.right_frame.pack(side="right", fill="both", expand=True)

        self.status_label = ctk.CTkLabel(self.left_frame, text="Status")
        self.status_label.pack(pady=5)
        self.status_text = cc.CTkTextbox(self.right_frame)
        self.status_text = cc.CTkTextbox(self.left_frame, height=200, width=500)
        self.status_text.pack(pady=5)

        self.processed_files_label = ctk.CTkLabel(self.right_frame, text="Prosesserte filer: 0")
        self.processed_files_label.pack(pady=5)

        self.csv_files_btn = ctk.CTkButton(self.right_frame, text="Velg CSVer", command=self.on_csv_button)
        self.csv_files_btn.pack(pady=5)

        self.clear_csv_btn = ctk.CTkButton(self.right_frame, text="Slett prosesserte data", command=self.on_clear_csv)
        self.clear_csv_btn.pack(pady=5)

        self.start_date_label = ctk.CTkLabel(self.right_frame, text="Analyser fra dato (ddmmyyyy):")
        self.start_date_label.pack(pady=5)
        self.start_date = cc.CTkDateSelector(self.right_frame)
        self.start_date.set_date(dt.date(2000, 1, 1))
        self.start_date.pack(pady=5)

        self.end_date_label = ctk.CTkLabel(self.right_frame, text="Analyser til dato (ddmmyyyy):")
        self.end_date_label.pack(pady=5)
        self.end_date = cc.CTkDateSelector(self.right_frame)
        self.end_date.set_date(dt.date(2100, 1, 1))
        self.end_date.pack(pady=5)

        self.name_ignore_label = ctk.CTkLabel(self.right_frame, text="Navnet ditt (for å ignorere interne overføringer)")
        self.name_ignore_label.pack(pady=5)
        self.name_to_ignore = ctk.CTkEntry(self.right_frame)
        self.name_to_ignore.pack(pady=5)

        self.make_graphs_btn = ctk.CTkButton(self.right_frame, text="Lag grafer!", command=self.on_make_graphs)
        self.make_graphs_btn.pack(pady=5)

        self.update_processed_files()

    def update_processed_files(self):
        processed_files = 0
        for file in os.listdir(csv_data_path):
            file_path = os.path.join(csv_data_path, file)
            if file_path.lower().endswith(".csv"):
                processed_files += 1

        self.processed_files_label.configure(text=f"Prosesserte filer: {processed_files}")

    def on_csv_button(self):
        files = filedialog.askopenfilenames(
            title="Velg kontoutskrifter",
            filetypes=(("CSV-filer", "*.csv"), ("Alle filer", "*.*")))

        if not files:
            self.status_text.append_text("Du valgte ingen filer!\n")
            return
        
        # read the files and convert them to csv's. 
        for file in files:
            status = read_bank.read_eika_csv(file)
            self.status_text.append_text(str(status) + "\n")
        
        self.update_processed_files()

    def on_clear_csv(self):
        for file in os.listdir(csv_data_path):
            file_path = os.path.join(csv_data_path, file)
            if file_path.lower().endswith(".csv"):
                os.remove(file_path)
        
        self.status_text.append_text("Slettet alle prosesserte data!\n")
        self.update_processed_files()

    def on_make_graphs(self):
        """ Makes graphs (or something) """
        self.status_text.append_text("Lager grafer!")

        start_date = self.start_date.get_date()
        end_date = self.end_date.get_date()
        duration = (dt.date(1970, 1, 1), dt.date(2100, 1, 1))
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
            self.status_text.append_text("Kunne ikke lage grafer, da ingen filer er prosesserte!\n")


def main():
    app = BaseApp()
    app.mainloop()


necessary_dirs = ["./csv_data/", "./kontoutskrifter"] 
if __name__ == "__main__":
    for dir in necessary_dirs:
        os.makedirs(dir, exist_ok=True)

    main()
