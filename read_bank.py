"""
    Module for reading bank csv's.
    Includes the following functions:
    - `hash_file`
    - `read_eika_csv`
"""
import hashlib
import os
import main
import shutil
from pathlib import Path


def hash_file(file_path, chunk_size=8192) -> str | None:
    """
        Hashes file and checks for dupes in csv_data 

        Returns:
        - hash str if file has not yet been processed
        - None if file has been processed
    """
    hasher = hashlib.md5()  # shouldn't cause any problems to use md5 here
    with open(file_path, "rb") as file:
        while chunk := file.read(chunk_size):
            hasher.update(chunk)

    hash = hasher.hexdigest()
    if os.path.exists(f"./csv_data/{hash}.csv"):
        return None  # the file has already been processed

    return hash  # the file has not already been processed


def read_eika_csv(file_path=None) -> str:
    """ 
        Reads Eika's csv files. They should be encoded in Windows-1252 and include the following fields:

        Utført dato;Bokført dato;Rentedato;Beskrivelse;Type;Undertype;Fra konto;Avsender;Til konto;Mottakernavn;
        Beløp inn;Beløp ut;Valuta;Status;Melding/KID/Fakt.nr

        `;` should be the seperator
    """
    hash = hash_file(file_path)
    if hash is None:
        return f"Fil: {file_path} har allerede blitt prosessert!"
    
    csv_destination_name = f"./csv_data/{hash}.csv"
    csv_path = Path(csv_destination_name)
    shutil.copy(file_path, csv_path)
    return f"Fil {file_path} har blitt prosessert!"


if __name__ == "__main__":
    main.main()
