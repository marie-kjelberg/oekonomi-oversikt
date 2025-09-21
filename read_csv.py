import csv
import json
from decimal import Decimal  # for å unngå flytpunktsfeil, slik som 5152.200000000001
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import re
import datetime as dt

date_pattern = r'\b(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.(\d{4})\b'

categories_path = "./data/categories.json"
categories_string = ""
with open(categories_path, "r", encoding="utf-8") as file:
    categories_string += file.read()

categories = json.loads(categories_string)

def categorize_transaction(transaction: str, categories: dict) -> str:
        transaction_lower = transaction.lower()
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword.lower() in transaction_lower:
                    return category
        return "uncategorized"

def graph_everything(files: list):
    """ Read the created csv list and graph everything """

    skip_words = ["Overført", "favør", "omkostninger", "ikke bokført"]
    category_counts = {}

    # for grafen
    inn_ut = []
    datoer = []
    referanser = []
    account_numbers = []

    for dokument in files:
        current_account_number = ""
        totalt_inn_måned = Decimal("0")
        totalt_ut_måned = Decimal("0")

        current_year = ""
        with open(dokument, 'r', newline='') as csvfile:
            csv_reader = csv.reader(csvfile)
            for i, row in enumerate(csv_reader):
                if i < 1: continue

                forklaring = row[0]
                referanse = row[5] + row[6]
                if i == 1:
                    current_year = forklaring.split(".")[2]
                    dates_trust_me_bro = re.findall(date_pattern, forklaring)[0]
                    dato = "".join(dates_trust_me_bro[::-1])
                    acc_number = referanse
                    
                    current_account_number = acc_number

                if current_account_number in account_numbers and "Saldo" in forklaring: continue
                if any(word in forklaring for word in skip_words): continue

                # ugly, ugly
                if i == 1:
                    account_numbers.append(acc_number)
                
                ut = row[2].replace(".", "").replace(",", ".")
                inn = row[3].replace(".", "").replace(",", ".")
                bokført = row[4] 
                if i != 1:
                    dato = current_year + bokført[2:4] + bokført[0:2]
                # sjekk om infoen stemmer overens med kategoriene:
                category = categorize_transaction(forklaring, categories)
                if ut != "":
                    if category == "uncategorized":
                        pass  # print(forklaring), kan gjøre noe med dette senere
                    if category not in category_counts:
                        category_counts[category] = Decimal(ut)
                    else:
                        category_counts[category] += Decimal(ut)

                try:
                    totalt_ut_måned += Decimal(ut)
                    inn_ut.append(Decimal("-" + ut))
                    datoer.append(dato)
                except: pass
                try:
                    totalt_inn_måned += Decimal(inn)
                    inn_ut.append(Decimal(inn))
                    datoer.append(dato)
                except: pass

                referanser.append(referanse)
    
    paired = list(zip(datoer, inn_ut))
    paired.sort(key=lambda x: int(x[0]))
    sorted_dates, sorted_inn_ut = zip(*paired)
    datoer = list(sorted_dates)
    inn_ut = list(sorted_inn_ut)

    for i, value in enumerate(inn_ut):
        if i == 0:
            continue

        inn_ut[i] = inn_ut[i-1] + value
    datoer = [dt.datetime.strptime(str(d), "%Y%m%d") for d in datoer]
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
    plt.figure(figsize=(8,5))
    plt.bar(categories_keys, counts, color='skyblue')
    plt.xticks(rotation=45)
    plt.title("Utgifter etter kategori")
    plt.xlabel("Kategori")
    plt.ylabel("NOK")
    #plt.show()

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
    plt.figure(figsize=(8,5))
    plt.bar(categories_keys, counts, color='skyblue')
    plt.xticks(rotation=45)
    plt.title(f"Utgifter etter kategori (normalisert for 30 dager): {total_30_day:.2f}NOK")
    plt.xlabel("Kategori")
    plt.ylabel("NOK")
    plt.show()

if __name__ == "__main__":
    pass