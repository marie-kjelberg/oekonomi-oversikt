import pandas as pd
import camelot
import re
import hashlib
import os
import main
import shutil
from pathlib import Path


def hash_file(file_path, chunk_size=8192):
    """ Hashes file and checks for dupes in csv_data """
    hasher = hashlib.md5()  # shouldn't cause any problems to use md5 here
    with open(file_path, "rb") as file:
        while chunk := file.read(chunk_size):
            hasher.update(chunk)

    hash = hasher.hexdigest()
    if os.path.exists(f"./csv_data/{hash}.csv"):
        return None  # the file has already been processed

    return hash


def read_eika_csv(file_path=None):
    hash = hash_file(file_path)
    if hash is None:
        return f"Fil: {file_path} har allerede blitt prosessert!"
    
    csv_destination_name = f"./csv_data/{hash}.csv"
    csv_path = Path(csv_destination_name)
    shutil.copy(file_path, csv_path)
    return f"Fil {file_path} har blitt prosessert!"


def read_eika(file_path=None):
    hash = hash_file(file_path)
    if hash is None:
        return f"Fil: {file_path} har allerede blitt prosessert!"
    
    csv_file_name = f"./csv_data/{hash}.csv"
    pd.set_option('display.max_colwidth', None)

    tables = camelot.read_pdf(file_path, pages='all', flavor='stream', suppress_stdout=True)
    if tables.n == 0:
        return f"Kunne ikke lese fil: {file_path}. Ingen tabell funnet!"

    dfs = [table.df for table in tables]
    merged_df = pd.concat(dfs, ignore_index=True)

    columns = merged_df.iloc[0].to_list()
    if len(columns) != 7:
        return f"Kunne ikke lese fil: {file_path}. Kunne ikke lese riktig tabell!"

    # should always be present, but I should also do proper checking
    # ¯\_(ツ)_/¯
    first_row = merged_df.iloc[0]
    first_row_str = first_row[0]
    account_number = re.findall(r"\b\d{4}\.?\d{2}\.?\d{5}\b", first_row_str)
    if len(account_number) != 0:
        account_number = account_number[0]
    else:
        account_number = re.findall(r'\d{4}\s\d{4}\s\d{3}', first_row_str)
        if len(account_number) == 0:
            return f"Kunne ikke finne kontonummer! Fil: {file_path}"
        account_number = account_number[0]

    merged_df.columns = ["Forklaring", "Rentedato", "Ut av konto", "Inn på konto", "Bokført", "Referanse del 1", "Referanse del 2"]
    merged_df = merged_df[
        merged_df["Ut av konto"].str.replace(',', '').str.replace('.', '').str.isnumeric() |
        merged_df["Inn på konto"].str.replace(',', '').str.replace('.', '').str.isnumeric()
    ].reset_index(drop=True)

    merged_df.loc[0, "Referanse del 1"] = str(account_number)
    merged_df.to_csv(csv_file_name, index=False, encoding="utf-8")
    return f"Leste og prosesserte filen {file_path}!"


if __name__ == "__main__":
    main.main()
