from fuzzywuzzy import fuzz
import unicodedata
import pandas as pd
from itertools import permutations
import re

produse = """
Iată toate produsele din categoria "RoofArt; China 0.30" cu prețul din listă:

Профилированный лист HP&HA-18
    - Цена по прайсу: 106,8 MDL / м²

Профилированный лист HP&HA-7
    -Цена по прайсу: 106,8 MDL / м²

Профилированный лист HPV&HV-7
    -Цена по прайсу: 106,8 MDL / м²

Профилированный лист HP&HA-12
    -Цена по прайсу: 117,48 MDL / м²

Сорт Стреасина
    -Цена по прайсу: 63,45 MDL / п.м.

Аксессуары B250 мм
    -Цена по прайсу: 100,05 MDL / п.м.

Прямой конек, Полукруглый конек
    -Цена по прайсу: 124,74 MDL / п.м.

Обычный жёлоб
    -Цена по прайсу: 166,79 MDL / п.м.

Жёлоб RoofArt
    -Цена по прайсу: 251,1 MDL / п.м.

Плоский лист (1250x2000)
    -Цена по прайсу: 106,8 MDL / м²

"""


def clean_nume(text):
    # Elimină simboluri nefolositoare, păstrează litere, cifre și spații
    text = re.sub(r"[\*\n\r\t]", "", text)  # elimină ** și caractere speciale
    text = re.sub(r"[^\w\s\-&]", "", text)  # păstrează doar litere, cifre, - și &
    return text.strip().lower()


def data_procces_df(produse, language):
    lines = [line.strip() for line in produse.strip().split("\n") if line.strip()]
    data = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Asigură-te că linia conține un punct + spațiu (ex: '1. ')
        if ". " not in line:
            i += 1
            continue

        # Extrage numele produsului
        try:
            nume_parte = line.split(". ", 1)[1]
        except IndexError:
            i += 1
            continue

        # Următoarea linie trebuie să fie prețul
        pret_line = lines[i+1] if i+1 < len(lines) else ""
        if language == "RO":
            pret = pret_line.split("Preț listă:")[-1].strip() if "Preț listă:" in pret_line else ""
        else:
            pret = pret_line.split("Цена по прайсу:")[-1].strip() if "Цена по прайсу:" in pret_line else ""

        data.append({"nume": clean_nume(nume_parte), "pret": pret})
        i += 2  # Treci la următoarea pereche
    df = pd.DataFrame(data)
    return df




def elimina_duplicate_rezultate(rezultate):
    seen = set()
    rezultate_unice = []
    for r in rezultate:
        cheie = (r['produs'], " ".join(sorted(r['cuvinte_cautate'].split())))
        if cheie not in seen:
            rezultate_unice.append(r)
            seen.add(cheie)
    return rezultate_unice

def normalize_text(text):
    text = text.lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')
    return text

def extract_keywords(text):
    text = clean_nume(text)
    cuvinte = normalize_text(text).split()

    # Descompune tokenuri gen 'hp&ha-18' în 'hp', 'ha', '18'
    cuvinte_extinse = []
    for c in cuvinte:
        cuvinte_extinse.append(c)
        if '-' in c:
            cuvinte_extinse.extend(c.split('-'))
        if '&' in c:
            cuvinte_extinse.extend(c.split('&'))

    # Păstrăm doar cele utile
    return [x for x in cuvinte_extinse if len(x) > 2 or x.isdigit()]

def score_relevanta_cuvinte(interogare, df, fuzzy_threshold=70):
    keywords_interogare = extract_keywords(interogare)
    toate_cuvintele_produse = set()
    for nume in df['nume']:
        toate_cuvintele_produse.update(extract_keywords(nume))
        print(toate_cuvintele_produse)

    relevante = []
    scoruri = []
    for cuv in keywords_interogare:
        max_scor = 0
        for prod_cuv in toate_cuvintele_produse:
            scor = fuzz.ratio(cuv, prod_cuv)
            if scor > max_scor:
                max_scor = scor
        if max_scor >= fuzzy_threshold:
            relevante.append(cuv)
            scoruri.append(max_scor)
    cuvinte_ordonate = [c for _, c in sorted(zip(scoruri, relevante), reverse=True)]
    return cuvinte_ordonate[:5]

def cauta_produs_inteligent_prioritate_lungime(interogare, df, threshold=80):
    relevante = score_relevanta_cuvinte(interogare, df, fuzzy_threshold=70)
    if not relevante:
        return None

    for lungime in range(len(relevante), 0, -1):
        potriviri_curente = []
        max_scor = 0
        for comb in permutations(relevante, lungime):
            text_cautat = " ".join(comb)
            for idx, row in df.iterrows():
                nume_norm = normalize_text(row['nume'])
                scor = fuzz.token_set_ratio(text_cautat, nume_norm)
                if scor >= threshold and scor > max_scor:
                    max_scor = scor
                    potriviri_curente = [{
                        "produs": row['nume'].title(),
                        "pret": row['pret'],
                        "scor": scor,
                        "cuvinte_cautate": text_cautat
                    }]
                elif scor >= threshold and scor == max_scor:
                    potriviri_curente.append({
                        "produs": row['nume'].title(),
                        "pret": row['pret'],
                        "scor": scor,
                        "cuvinte_cautate": text_cautat
                    })
        if potriviri_curente:
            potriviri_curente = elimina_duplicate_rezultate(potriviri_curente)
            return potriviri_curente
    return None



def function_check_product(interogare, produse , language):
    # interogare = "M-ar interesa foarte mult sa vad toate variantele legate de dolie"
    df = data_procces_df(produse, language)
    print(interogare)
    rezultate = cauta_produs_inteligent_prioritate_lungime(interogare, df)
    print(rezultate)
    if rezultate:
        print("Cea mai bună potrivire/ potriviri (prioritate lungime expresie):")
        for r in rezultate:
            print(f"- {r['produs']} | {r['pret']} | scor: {r['scor']} (cuvinte căutate: '{r['cuvinte_cautate']}')")
    else:
        print("Niciun produs potrivit găsit.")
        rezultate = "NU"

    return rezultate

interogare = "меня итересует Профилированный"
function_check_product(interogare , produse, "RU")
