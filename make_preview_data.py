"""
    A file to make synthetic data for preview purposes.

    This file is kind of flawed. This file makes it possible to go a lot in the negatives 
    (which shouldn't be happeneing).
    I can fix that later...
"""
import main
import polars as pl
import datetime as dt
from decimal import Decimal
import random
import get_app_data
import calendar

categories = get_app_data.get_categories()


def append_row(
    data,
    Utført_dato=None,
    Bokført_dato=None,
    Rentedato=None,
    Beskrivelse=None,
    Type=None,
    Undertype=None,
    Fra_konto=None,
    Avsender=None,
    Til_konto=None,
    Mottakernavn=None,
    Beløp_inn=None,
    Beløp_ut=None,
    Valuta=None,
    Status=None,
    Melding_KID_Fakt_nr=None,
):
    """ Pain """
    row = {
        'Utført dato': Utført_dato,
        'Bokført dato': Bokført_dato,
        'Rentedato': Rentedato,
        'Beskrivelse': Beskrivelse,
        'Type': Type,
        'Undertype': Undertype,
        'Fra konto': Fra_konto,
        'Avsender': Avsender,
        'Til konto': Til_konto,
        'Mottakernavn': Mottakernavn,
        'Beløp inn': Beløp_inn,
        'Beløp ut': Beløp_ut,
        'Valuta': Valuta,
        'Status': Status,
        'Melding/KID/Fakt.nr': Melding_KID_Fakt_nr,
    }

    for key in data:
        data[key].append(row[key])


def iter_months(duration):
    year, month = duration[0].year, duration[0].month

    while (year < duration[1].year) or (year == duration[1].year and month <= duration[1].month):
        yield dt.date(year, month, 1)
        month += 1
        if month > 12:
            month = 1
            year += 1


def make_data(start_amount=Decimal("1000000"), duration: list = [dt.date(2025, 1, 1), dt.date(2026, 1, 1)]):
    pl.Decimal(10, 2)
    data = {
        'Utført dato': [],
        'Bokført dato': [],
        'Rentedato': [],
        'Beskrivelse': [],
        'Type': [],
        'Undertype': [],
        'Fra konto': [],
        'Avsender': [],
        'Til konto': [],
        'Mottakernavn': [],
        'Beløp inn': [],
        'Beløp ut': [],
        'Valuta': [],
        'Status': [],
        'Melding/KID/Fakt.nr': []
    }

    account = "1234 56 78910"
    valuta = "NOK"
    transaction_types = {
        "food": [("Rema", 50, 500), ("Extra", 80, 600)],
        "transport": [("Ruter", 30, 100), ("Vy", 30, 200)],
        "entertainment": [("Spotify", 129, 129)],
        "health": [("Legekontor", 100, 200), ("Apotek", 100, 500)],
        "misc": [("Amzn", 500, 1200), ("Zalando", 400, 1200)]
    }

    # add fixed expenses - rent, phone, both in NOK - arbitrary
    rent = Decimal("-6000")
    phone = Decimal("-200")
    for date in iter_months(duration):
        formatted_date = date.strftime("%d.%m.%Y")
        append_row(data, Utført_dato=formatted_date, Fra_konto=account, Beløp_ut=rent,
                   Valuta=valuta, Beskrivelse="Studentsamskipnaden")
        append_row(data, Utført_dato=formatted_date, Fra_konto=account, Beløp_ut=phone,
                   Valuta=valuta, Beskrivelse="Lyse Tele")
        
        # add income thing
        income_date = dt.date(date.year, date.month, 15).strftime("%d.%m.%Y")
        append_row(data, Utført_dato=income_date, Fra_konto=account, Beløp_inn=Decimal("14000"),
                   Valuta=valuta, Beskrivelse="Lønn")

        # this should be on the first of the first month
        _, num_days = calendar.monthrange(date.year, date.month)
        for i in range(num_days):
            date_thing = dt.date(date.year, date.month, i+1)
            formatted_date = date_thing.strftime("%d.%m.%Y")
            print(formatted_date)
            # check random amount of transactions
            transactions = random.randint(0, 2)
            for i in range(transactions):
                # add random transaction
                transaction_category = random.choice(list(transaction_types.keys()))
                name, min_amt, max_amt = random.choice(transaction_types[transaction_category])
                amount = Decimal(f"-{random.randint(min_amt, max_amt)}")
                append_row(data, Utført_dato=formatted_date, Fra_konto=account, Beløp_ut=amount,
                           Valuta=valuta, Beskrivelse=name)
                
    inngående_dato = duration[0].strftime("%d.%m.%Y")
    append_row(data, f"Inngående saldo pr. {inngående_dato}:", Rentedato="45 161,69 NOK")  # very arbitrary
    df = pl.DataFrame(data)
    csv_str = df.write_csv(separator=";")
    with open("./csv_data/test_data.csv", "w", encoding="windows-1252") as file:
        file.write(csv_str)
    print(df.head())


if __name__ == "__main__":
    make_data()
    main.main()