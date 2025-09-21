import pandas as pd
import camelot
# import re
import hashlib
import os

# date_pattern = r'\b(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.(\d{4})\b'

def hash_file(file_path, chunk_size = 8192):
    """ Hashes file and checks for dupes in csv_data """
    hasher = hashlib.md5() # shouldn't cause any problems to use md5 here
    with open(file_path, "rb") as file:
        while chunk := file.read(chunk_size):
            hasher.update(chunk)

    hash = hasher.hexdigest()
    if os.path.exists(f"./csv_data/{hash}.csv"):
        return None # the file has already been processed
    
    return hash


def read_eika(file_path = None):
    hash = hash_file(file_path)
    if hash == None:
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
    
    '''
    Honestly, this can be done by keeping track of the dates in the csv. 
    I'm just keeping this here in case that fails

    find_date_period = merged_df[merged_df[0].str.contains("perioden", na=False)]
    date_period_matches = re.findall(date_pattern, str(find_date_period))
    if len(date_period_matches) < 2:
        print(f"Could not find which period this statement is for! File: {file_path}")
        return
    print(date_period_matches[:2])
    '''

    merged_df.columns = ["Forklaring", "Rentedato", "Ut av konto", "Inn på konto", "Bokført", "Referanse del 1", "Referanse del 2"]
    merged_df = merged_df[
        merged_df["Ut av konto"].str.replace(',', '').str.replace('.', '').str.isnumeric() |
        merged_df["Inn på konto"].str.replace(',', '').str.replace('.', '').str.isnumeric()
    ].reset_index(drop=True)

    merged_df.to_csv(csv_file_name, index=False)
    return f"Leste og prosesserte filen {file_path}!"

if __name__ == "__main__":
    pass