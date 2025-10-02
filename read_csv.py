import csv
import json
from decimal import Decimal  # for å unngå flytpunktsfeil, slik som 5152.200000000001
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import re
import datetime as dt
import main
import networkx as nx
import polars as pl

date_pattern = r'\b(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.(\d{4})\b'

categories_path = "./data/categories.json"
categories_string = ""
with open(categories_path, "r", encoding="utf-8") as file:
    categories_string += file.read()

categories = json.loads(categories_string)


def categorize_transaction(transaction: str, categories: dict = categories) -> str:
    transaction_lower = transaction.lower()
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword.lower() in transaction_lower:
                return category
    return "uncategorized"


def graph_everything(files: list, duration=(dt.datetime(2023, 5, 1), dt.datetime(2050, 1, 1))):
    """ The newer version """
    skip_words = ["Overført", "favør", "omkostninger", "ikke bokført"]
    category_counts = {}

    # for grafen
    inn_ut = []
    datoer = []
    referanser = []
    saldo_inn_ut = []
    nodes = {}  # {"<kontonummer>: {"amzn": 199}"}
    # kontonummer er alle koblet til barna sine
    df_list = []
    inngående_saldoer = Decimal("0")
    for dokument in files:
        totalt_inn_måned = Decimal("0")
        totalt_ut_måned = Decimal("0")
        current_year = ""
        current_acc_number = ""

        # for backwards compatibility reasons, Norwegian financial institutions often use this encoding
        df = pl.read_csv(dokument, separator=";", encoding="windows-1252", dtypes={
            "Beløp inn": pl.Decimal(10, 2),
            "Beløp ut": pl.Decimal(10, 2),
        })
        
        # burde passe på at valuta er riktig, men idk

        # finn inngående saldo
        try:  # hvis du har en bedre måte å gjøre dette på, fortell meg!!!
            inngående_ting = df.filter(pl.col("Utført dato").str.contains("Inngående saldo pr."))
            inngående_saldo = inngående_ting["Rentedato"][0].replace(" ", "").replace(",", ".").replace(" NOK", "")
            inngående_saldo = Decimal(inngående_saldo)
            inngående_dato = re.findall(date_pattern, inngående_ting["Utført dato"][0])[0]
            inngående_dato = dt.datetime(int(inngående_dato[2]), int(inngående_dato[1]), int(inngående_dato[0])).date()
        except Exception as e:
            print("Kunne ikke finne inngående saldo/dato!", e)
            inngående_saldo = Decimal(0)
            inngående_dato = dt.datetime(1970, 1, 1).date()
        inngående_saldoer += inngående_saldo
        df_list.append(df)

    df = pl.concat(df_list)
    # parse dates
    # vi bruker utført dato her, siden transaksjonen trenger ikke alltid være bokført enda. 
    # Kan vurdere å evt. differensiere med dette senere, men dette verktøyet
    # er hovedsakelig ment for å være regnskapsverktøy. Idk, får se~
    df = df.with_columns(
        pl.col("Utført dato").str.strptime(pl.Date, format=("%d.%m.%Y"), strict=False).alias("Utført dato")
    ).sort("Utført dato")

    # fjern ubrukelige rows
    df = df.drop_nulls(subset=["Utført dato"])

    # jeg klarte ikke å sette inngående saldo først... 

    # finn løpende saldo
    df = df.with_columns(
        ((pl.col("Beløp ut").fill_null(0) + pl.col("Beløp inn").fill_null(0)).cum_sum()).alias("inn_ut")
    )

    df = df.with_columns(
        (pl.col("inn_ut") + inngående_saldoer).alias("inn_ut")
    )

    df = df.with_columns(
        pl.col("Beskrivelse").map_elements(categorize_transaction).alias("category")
    )

    df_categories: pl.DataFrame = df.group_by("category").agg(
        pl.sum("inn_ut").alias("total_amount")
    ).sort("total_amount")

    datoer = df["Utført dato"].to_list()
    inn_ut = df["inn_ut"].to_list()

    fig, ax = plt.subplots(1, 2, figsize=(10, 6))
    ax[0].plot(datoer, inn_ut, label="Saldo i banken")
    ax[0].fill_between(datoer, inn_ut, alpha=0.3)
    
    categories_list = df_categories["category"].to_list()
    categories_sums = df_categories["total_amount"].to_list()
    ax[1].bar(categories_list, categories_sums, label="bar chart")

    plt.show()


def _graph_everything(files: list, duration=(dt.datetime(2023, 5, 1), dt.datetime(2050, 1, 1))):
    """ Deprecated: Read the created csv list and graph everything """

    skip_words = ["Overført", "favør", "omkostninger", "ikke bokført"]
    category_counts = {}

    # for grafen
    inn_ut = []
    datoer = []
    referanser = []
    saldo_inn_ut = []
    nodes = {}  # {"<kontonummer>: {"amzn": 199}"}
    # kontonummer er alle koblet til barna sine
    for dokument in files:
        totalt_inn_måned = Decimal("0")
        totalt_ut_måned = Decimal("0")

        current_year = ""
        current_account_number = ""
        with open(dokument, 'r', newline='', encoding="utf-8") as csvfile:
            csv_reader = csv.reader(csvfile)
            for i, row in enumerate(csv_reader):
                if i == 0 or "Dato:" in row[0]:
                    continue

                forklaring = row[0]
                referanse = row[5] + row[6]
                ut = row[2].replace(".", "").replace(",", ".")
                inn = row[3].replace(".", "").replace(",", ".")
                bokført = row[4] 

                # this is stupid
                if i == 1:
                    current_year = forklaring.split(".")[2]
                    dates_trust_me_bro = re.findall(date_pattern, forklaring)[0]
                    dato = "".join(dates_trust_me_bro[::-1])[:4]
                    date_month = int(dates_trust_me_bro[1]) + 1
                    dato += f"{str(date_month).zfill(2) if date_month < 10 else str(date_month)}01"
                    acc_number = referanse
                    current_account_number = acc_number

                if "Saldo fra kontoutskrift" in forklaring:  # dette setter ikke datoene riktig
                    date_find = re.findall(date_pattern, forklaring)[0]
                    current_year = date_find[2]
                    if date_find[1] == "12":
                        current_year = str(int(date_find[2]) + 1)

                    dato = date_find[2] + date_find[1] + date_find[0]
                    saldo = Decimal("0")
                    if inn != "":
                        saldo += Decimal(inn)

                    if ut != "":
                        saldo -= Decimal(ut)
                        
                    obj = {"saldo": saldo, "dato": dato,
                           "account": current_account_number}
                    saldo_inn_ut.append(obj)
                    continue

                if any(word in forklaring for word in skip_words):
                    continue
                
                dato = current_year + bokført[2:4] + bokført[0:2]
                # sjekk om infoen stemmer overens med kategoriene:
                category = categorize_transaction(forklaring, categories)
                print(dato, forklaring, referanse)
                if "Renter og provisjon" in forklaring or "i år" in forklaring:
                    dato += "0101"

                if len(dato) != 8:
                    dato += "0101"
                    
                date_now = dt.datetime.strptime(str(dato), "%Y%m%d")

                if ut != "" and duration[0] <= date_now <= duration[1]:
                    if category == "uncategorized":
                        print(forklaring)  # , kan gjøre noe med dette senere
                    if category not in category_counts:
                        category_counts[category] = Decimal(ut)
                    else:
                        category_counts[category] += Decimal(ut)

                if ut != "":
                    totalt_ut_måned += Decimal(ut)
                    inn_ut.append(Decimal("-" + ut))
                    datoer.append(dato)

                if inn != "":
                    totalt_inn_måned += Decimal(inn)
                    inn_ut.append(Decimal(inn))
                    datoer.append(dato)

                referanser.append(referanse)
                # print(f"Forklaring: {forklaring}, ref: {referanse}, dato: {dato}")

    saldo_sorted = sorted(saldo_inn_ut, key=lambda x: x['dato'])
    saldo_unique_accounts = []
    for entry in saldo_sorted:
        if entry["account"] not in saldo_unique_accounts:
            saldo_unique_accounts.append(entry["account"])
            inn_ut.append(entry["saldo"])
            datoer.append(entry["dato"])

    paired = list(zip(datoer, inn_ut))
    paired.sort(key=lambda x: int(x[0]))
    sorted_dates, sorted_inn_ut = zip(*paired)
    datoer = list(sorted_dates)
    inn_ut = list(sorted_inn_ut)

    datoer = [dt.datetime.strptime(str(d), "%Y%m%d") for d in datoer]
    for i, value in enumerate(inn_ut):
        if i == 0:
            continue

        inn_ut[i] = inn_ut[i-1] + value

    # find the cutoff date
    start_i = min(range(len(datoer)), key=lambda i: abs(datoer[i] - duration[0]))
    end_i = min(range(len(datoer)), key=lambda i: abs(datoer[i] - duration[1]))
    datoer = datoer[start_i:end_i]
    inn_ut = inn_ut[start_i:end_i]

    G = nx.Graph()
    # gå igjennom nodes osv.

    plt.plot(datoer, inn_ut)
    plt.fill_between(datoer, inn_ut, alpha=0.3)
    plt.xticks(rotation=45)
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.xlabel("Datoer")
    plt.ylabel("NOK")
    plt.title("Oversikt over total saldo i banken")

    categories_keys = list(category_counts.keys())
    counts = list(category_counts.values())
    plt.figure(figsize=(8, 5))
    plt.bar(categories_keys, counts, color='skyblue')
    plt.xticks(rotation=45)
    plt.title("Utgifter etter kategori")
    plt.xlabel("Kategori")
    plt.ylabel("NOK")

    # normalise this for a 30 day period
    thrity_day_norm = {}
    start_date, end_date = min(datoer), max(datoer)
    day_diff = (end_date - start_date).days
    total_30_day = Decimal("0")

    for key, count in category_counts.items(): 
        expense = count * Decimal("30") / Decimal(str(day_diff))
        thrity_day_norm[key] = expense
        total_30_day += expense

    counts = list(thrity_day_norm.values())

    # problemet med dette, er at noen måneder er annerledes enn andre. 
    plt.figure(figsize=(8, 5))
    plt.bar(categories_keys, counts, color='skyblue')
    plt.xticks(rotation=45)
    plt.title(f"Utgifter etter kategori (normalisert for 30 dager): {total_30_day:.2f}NOK")
    plt.xlabel("Kategori")
    plt.ylabel("NOK")
    plt.show()


if __name__ == "__main__":
    main.main()  # just for debugging rn
