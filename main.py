import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import read_bank
import read_csv

csv_data_path = "./csv_data/"


class BaseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.files = []

        self.title("Økonomi Styring")
        self.geometry("1280x700")

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        self.title_label = ttk.Label(frame, text="Økonomi styring")
        self.title_label.pack(pady=5)

        self.status_label = ttk.Label(frame, text="Status")
        self.status_label.pack(pady=5)
        self.status_text = tk.Text(frame, height=10, width=100)
        self.status_text.pack(pady=5)

        self.processed_files_label = ttk.Label(frame, text="Prosesserte filer: 0")
        self.processed_files_label.pack(pady=5)

        self.files_button = ttk.Button(frame, text="Velg kontoutskrifter", command=self.on_files_button)
        self.files_button.pack(pady=5)

        self.clear_csv_btn = ttk.Button(frame, text="Slett prosesserte data", command=self.on_clear_csv)
        self.clear_csv_btn.pack(pady=5)

        self.make_graphs_btn = ttk.Button(frame, text="Lag grafer!", command=self.on_make_graphs)
        self.make_graphs_btn.pack(pady=5)

        self.update_processed_files()

    def update_processed_files(self):
        processed_files = 0
        for file in os.listdir(csv_data_path):
            file_path = os.path.join(csv_data_path, file)
            if file_path.lower().endswith(".csv"):
                processed_files += 1

        self.processed_files_label.config(text=f"Prosesserte filer: {processed_files}")

    def on_files_button(self):
        files = filedialog.askopenfilenames(title="Velg kontoutskrifter", 
            filetypes=(("PDF-filer", "*.pdf"), ("Alle filer", "*.*")))

        if not files:
            self.status_text.insert(tk.END, "Du valgte ingen filer!")
            return
        
        # read the files and convert them to csv's. 
        for file in files:
            status = read_bank.read_eika(file)
            self.status_text.insert(tk.END, status + "\n")
        
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

        # honestly, this could be better (it's very redudant)
        files = []
        for file in os.listdir(csv_data_path):
            file_path = os.path.join(csv_data_path, file)
            if file_path.lower().endswith(".csv"):
                files.append(file_path)
    
        if len(files) != 0:
            read_csv.graph_everything(files)
        else: 
            self.status_text.insert(tk.END, "Kunne ikke lage grafer, da ingen filer er prosesserte!")


def main():
    app = BaseApp()
    app.mainloop()


def _debug_read_pdfs():
    """ Debug the pdf-reading thing """
    pass


def _debug_read_csv():
    """ Debug the csv-reading thing """
    pass


necessary_dirs = ["./csv_data/", "./kontoutskrifter"] 
if __name__ == "__main__":
    for dir in necessary_dirs:
        os.makedirs(dir, exist_ok=True)

    main()