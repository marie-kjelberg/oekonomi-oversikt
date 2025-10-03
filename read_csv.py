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
    category_counts = {}

    # for grafen
    inn_ut = []
    datoer = []
    nodes = {}  # {"<kontonummer>: {"amzn": 199}"}
    # kontonummer er alle koblet til barna sine
    df_list = []
    inngående_saldoer = Decimal("0")
    for dokument in files:
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
    df: pl.DataFrame = df.drop_nulls(subset=["Utført dato"])

    # filtrer bort uønskede datoer
    df = df.filter(duration[0].date() < pl.col("Utført dato"))
    df = df.filter(duration[1].date() > pl.col("Utført dato"))

    df = df.with_columns(
        pl.col("Beskrivelse").map_elements(categorize_transaction).alias("category")
    )

    df_categories: pl.DataFrame = df.group_by("category").agg(
        (-1 * pl.sum("Beløp ut") + pl.sum("Beløp inn")).alias("total_amount")
    ).sort("total_amount")
    print(df_categories.head())

    # jeg klarte ikke å sette inngående saldo først...
    # finn løpende saldo
    df = df.with_columns(
        ((pl.col("Beløp ut").fill_null(0) + pl.col("Beløp inn").fill_null(0)).cum_sum()).alias("inn_ut")
    )

    df = df.with_columns(
        (pl.col("inn_ut") + inngående_saldoer).alias("inn_ut")
    )

    datoer = df["Utført dato"].to_list()
    inn_ut = df["inn_ut"].to_list()

    plt.figure()
    plt.plot(datoer, inn_ut, label="Saldo i banken")
    plt.fill_between(datoer, inn_ut, alpha=0.3)
    plt.title("Banksaldo over tid (NOK)")
    plt.xlabel("Datoer")
    plt.ylabel("NOK")

    categories_list = df_categories["category"].to_list()
    categories_sums = df_categories["total_amount"].to_list()
    plt.figure()
    plt.bar(categories_list, categories_sums, label="bar chart")
    plt.title("Inn/ut kategorisert")
    plt.xlabel("Kategorier")
    plt.ylabel("NOK")
    plt.xticks(rotation=45, ha="right")

    plt.figure()
    G = nx.DiGraph()
    # nodes burde være fra konto + kategorier. så kan add_adges være de ulike kategoriserte transaksjonene + evt.
    # til en konto hvis det er der. Hvis det går inn, så kan man heller ha fra deres konto til vår
    # df_copy = df.clone()
    df = df.drop_nulls(subset=["Fra konto"])

    # df_copy.drop_nulls(subset=["Til konto"])
    # print(df_copy.head())

    edges = list(zip(df["Fra konto"].to_list(), df["category"].to_list()))
    G.add_edges_from(edges)
    pos = nx.spring_layout(G)
    # ax2 = fig.add_subplot(gs[1, 0])
    nx.draw(
        G,
        pos,
        with_labels=True,
    )

    plt.show()


if __name__ == "__main__":
    main.main()  # just for debugging rn
