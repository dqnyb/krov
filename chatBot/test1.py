import pandas as pd

# Încarcă fișierul sursă
df_raw = pd.read_excel("preturi.xlsx", header=None, names=["Nume"])

# Inițializează variabile
data = []
current_category = None

# Detectăm categoria și asociem produsele
for index, row in df_raw.iterrows():
    value = str(row["Nume"]).strip()

    if value.endswith(":"):
        current_category = value
    elif value and current_category:
        data.append({"Categorie": current_category.strip(), "Produs": value.strip()})

# Convertim în DataFrame
df = pd.DataFrame(data)

# Eliminăm eventuale produse goale
df = df[df["Produs"].notna() & df["Produs"].str.strip().ne("")]

# Verificare
print(df.head(10))
