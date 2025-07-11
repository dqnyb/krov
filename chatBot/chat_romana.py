from openai import OpenAI
from flask import Flask, request, jsonify
from flask_cors import CORS
from openpyxl import Workbook, load_workbook
from datetime import datetime
import openai
import pandas as pd
import os
import random
from dotenv import load_dotenv
import pandas as pd
from thefuzz import fuzz
from thefuzz import process
import test
from test import categoria_preferata
import re
from difflib import SequenceMatcher
import categorie 
from categorie import function_check_product
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY
# Pentru acest proiect am lăsat cheia publică (pentru a fi testată mai repede), dar desigur că nu se face așa!
# Aș fi folosit client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) și aș fi dat export în env la key: export OPENAI_API_KEY="sk-..."

client = OpenAI(
    api_key=OPENAI_API_KEY,  # pune aici cheia ta reală!
)

preferinte = {}
preferinte['interes_salvat'] = ""

df = pd.read_excel('p.xlsx')
categorii = df['Categorie']
categorii_unice = list(dict.fromkeys(categorii.dropna().astype(str)))

# print(categorii_unice)
def log_message(sender, message):
    # Creează calea absolută către folderul logs ! Pentru a salva log-urile in excel !
    base_dir = os.path.expanduser("../logs")
    os.makedirs(base_dir, exist_ok=True)
    file_path = os.path.join(base_dir, "chat_log1.xlsx")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_row = {"Timestamp": timestamp, "Sender": sender, "Message": message}

    try:
        if os.path.exists(file_path):
            df = pd.read_excel(file_path)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            df = pd.DataFrame([new_row])

        df.to_excel(file_path, index=False)
        print(f"[{timestamp}] [LOGGED] {sender}: {message}")
    except Exception as e:
        print(f"[EROARE] Logarea a eșuat: {e}")


def check_language(user_response: str) -> str:
    prompt = (
        f'Utilizatorul a scris: "{user_response}".\n'
        "Trebuie să determini în ce limbă dorește să continue conversația: română (RO) sau rusă (RU).\n\n"
        "Ia în considerare și expresii vagi, regionale, greșite sau colocviale. De exemplu:\n"
        "- Pentru română: „român”, „moldovenească”, „scrie în limba mea”, „romana fără diacritice”, „scrie normal”, „limba de aici”, „ca acasă”, etc.\n"
        "- Pentru rusă: „русский”, „румынский язык нет”, „по-русски”, „по нашему”, „российский”, „кирилица”, „давай по твоему”, etc.\n\n"
        "Acceptă și mesaje fără diacritice, cu greșeli sau în alfabetul greșit.\n\n"
        "Chiar dacă nu există indicii clare despre limba dorită, alege întotdeauna LIMBA cea mai probabilă dintre română (RO) sau rusă (RU).\n\n"
        "Răspunde STRICT cu una dintre cele două opțiuni, fără explicații:\n"
        "- RO\n"
        "- RU\n\n"
        "Exemple:\n"
        "\"scrie ca la țară\" -> RO\n"
        "\"давай по-нашему\" -> RU\n"
        "\"romana\" -> RO\n"
        "\"rusa\" -> RU\n"
        "\"moldoveneasca\" -> RO\n"
        "\"русский\" -> RU\n"
        "\"nu conteaza\" -> RO\n"
        "\"ce vrei tu\" -> RO\n"
        "\"cine e messi?\" -> RO\n\n"
        "Răspuns final:"
    )
    messages = [{"role": "system", "content": prompt}]

    response = ask_with_ai(messages)
    response = response.strip().upper()
    if response in {"RO", "RU"}:
        return response
    return "RO"



@app.route("/language", methods=["GET"])
def language():
    message = (
        "🌟👋 <strong>Bine ai venit la <span style=\"color:#2E86C1;\">Krov</span> – specialiștii în acoperișuri de calitate!</strong> 🌟🏠<br><br>"
        "🗣️ <strong>Te invităm să alegi limba preferată:</strong><br>"
        "<div style='text-align:center; font-size:1em; margin: 10px 0;'>"
        "🇷🇴 <em>Română</em> 🗨️ &nbsp;&nbsp;|&nbsp;&nbsp; 🇷🇺 <em>Русский</em> 🗨️"
        "</div>"
    )

    return jsonify({"ask_name": message})

language_saved = ""

@app.route("/start", methods=["GET","POST"])
def start():
    user_data = request.get_json()
    interest = user_data.get("name", "prieten")
    check_language_rag = check_language(interest)
    
    print(check_language_rag)

    if check_language_rag == "RO":
        language_saved = "RO"
        welcome_message = (
            "❓ <strong>Cu ce te pot ajuta?</strong><br><br>"
            "💬 <em>Vrei detalii despre un produs</em> sau <em>dorești să plasezi o comandă</em>?<br><br>"
            "🏠🔨 Suntem aici să-ți oferim cele mai bune soluții pentru acoperișul tău! 🛠️✨"
        )
    elif check_language_rag == "RU":
        language_saved = "RU"
        welcome_message = (
            "❓ <strong>Чем могу помочь?</strong><br><br>"
            "💬 <em>Хотите узнать о продукте</em> или <em>сделать заказ</em>?<br><br>"
            "🏠🔨 Мы готовы предложить лучшие решения для вашей крыши! 🛠️✨"
        )
    else:
        language_saved = "RO"
        welcome_message = (
            "❓ <strong>Cu ce te pot ajuta?</strong><br><br>"
            "💬 <em>Vrei detalii despre un produs</em> sau <em>dorești să plasezi o comandă</em>?<br><br>"
            "🏠🔨 Suntem aici să-ți oferim cele mai bune soluții pentru acoperișul tău! 🛠️✨"
        )
    
    return jsonify({"ask_name": welcome_message , "language": language_saved})





def is_fuzzy_comanda(user_text, threshold=80):

    comanda_keywords = [
        # română
        "comand", "cumpăr", "achiziționez", "trimit factură", "factura", "plătesc", "finalizez",
        "trimit date", "doresc să comand", "aș vrea să cumpăr", "pregătiți comanda", "ofertă pentru", "cerere ofertă",
        "cât costă x bucăți", "preț 50 mp", "livrare comandă", "plată", "vă rog comanda", "doresc comanda" "curier",
        
        # rusă (litere chirilice, intenție clară de comandă)
        "заказ", "купить", "хочу купить", "покупка", "покупаю", "оплата", "оформить заказ", "счет", "выставите счет",
        "отправьте счет", "хочу приобрести", "доставку", "плачу", "готов оплатить", "оплатить", "сделать заказ"
    ]
        
    user_text = user_text.lower()
    words = user_text.split()

    for keyword in comanda_keywords:
        for word in words:
            score = fuzz.partial_ratio(word, keyword)
            if score >= threshold:
                return True
        # verificăm și fraze întregi
        if fuzz.partial_ratio(user_text, keyword) >= threshold:
            return True
    return False

def check_interest(interest):

    if is_fuzzy_comanda(interest):
        return "comandă"
        

    interests_prompt = (
        "Analizează mesajul utilizatorului pentru a identifica intenția exactă în funcție de următoarele categorii detaliate:\n\n"
        
        "1. produs_informații - INCLUD și intenții preliminare de cumpărare, exprimări generale, curiozitate sau cerere de categorii. Se clasifică aici orice interes pentru:\n"
        "- produse, modele, game, colecții, serii, culori, categorii ('Ce aveți?', 'Ce modele mai sunt?', 'Mai aveți și alte produse?')\n"
        "- expresii generice sau incomplete: 'produse?', 'categorii?', 'alte modele?', 'impermeabile?' – chiar dacă nu există întrebare completă\n"
        "- expresii vagi sau generale de interes: 'vreau produsul', 'doresc un model', 'aș vrea să văd', 'ce aveți în categoria X'\n"
        "- întrebări despre specificații, caracteristici, opțiuni de personalizare, materiale, întreținere\n"
        "- comparații între produse/serii\n"
        "- solicitări de imagini, cataloage, mostre\n"
        "- întrebări despre disponibilitate, dimensiuni, stoc, livrare (doar dacă nu menționează acțiunea de a comanda)\n"
        "- întrebări despre garanție, montaj\n"
        "- mențiuni despre preț fără cerere explicită de ofertă sau acțiune\n"
        "- orice exprimare incertă sau ambiguu-intenționată\n\n"
        
        "2. comandă - DOAR când există acțiune explicită, clar formulată:\n"
        "- 'vreau să comand', 'doresc să cumpăr', 'aș vrea să achiziționez'\n"
        "- cerere de ofertă pentru cantitate definită: 'cât ar costa 30 bucăți', 'trimiteți-mi prețul pentru 50mp'\n"
        "- formulări despre termeni de livrare/plată pentru o tranzacție iminentă\n"
        "- orice formulare cu verb concret de tranzacție: 'comand', 'achiziționez', 'cumpăr', 'plătesc', 'trimiteți factura'\n"
        "- solicitări legate de livrare, transport sau condiții de livrare: 'faceți livrare', 'livrați la adresă', 'cât costă transportul'\n"
        "- expresii de încheiere a comenzii: 'hai să finalizăm', 'pregătiți comanda', 'vă trimit datele de facturare'\n\n"
        
        "3. altceva - doar pentru:\n"
        "- saluturi, mulțumiri fără context de afacere\n"
        "- glume, spam, comentarii irelevante\n"
        "- mesaje fără nicio legătură cu produsele sau comenzile\n\n"
        
        "REGULI IMPORTANTE:\n"
        "- Orice mențiune despre produse, game, modele, categorii sau expresii generale => produs_informații\n"
        "- Orice ambiguitate => produs_informații (mai bine fals pozitiv decât să ratezi o intenție)\n"
        "- Doar când există verb clar de comandă => clasifici ca 'comandă'\n\n"
        
        "EXEMPLE CLASIFICATE:\n"
        "'Ce modele impermeabile aveți?' => produs_informații\n"
        "'Aveți și alte categorii?' => produs_informații\n"
        "'Produse?' => produs_informații\n"
        "'Aș dori să văd și alte variante' => produs_informații\n"
        "'Vreau să comand 100mp pentru luni' => comandă\n"
        "'Trimiteți factura pe email' => comandă\n"
        "'Salut, bună' => altceva\n\n"
        
        f"Mesaj de analizat: \"{interest}\"\n\n"
        "Răspunde STRICT cu unul dintre tag-uri: produs_informații, comandă, altceva. Fără explicații suplimentare."
    )


    messages = [{"role": "system", "content": interests_prompt}]
    response = ask_with_ai(messages)
    return response

@app.route("/interests", methods=["POST"])
def interests():
    user_data = request.get_json()
    interest = user_data.get("name", "prieten")
    language_saved = user_data.get("language")

    interest_checked = check_interest(interest)
    print(interest_checked)
    if (interest_checked == "produs_informații"):
        messages = [
            {
                "role": "user",
                "content": (
                    "Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
                    "Fa promptul frumos , foloseste emoji-uri ( este despre un business de acoperisuri ) si pentur fiecare alegere adauga un emoji in loc de numere dar trebuie ca emojiurile sa fie strict legate de business de acoperisuri ( gen cand enumeri categoriile )"
                    "Esti un chatbot inteligent care creezi un prompt interactiv si frumos pentru user si il intrebi ce produse doreste , din cele de mai jos (trebuie incluse toate in prompt fara RoofArt in fata):"
                    f"Acestea sunt toate categoriile disponibile : {categorii_unice}"
                    "Rogi userul sa raspunda cu denumirea exacta a produsului din lista de categorii"
                )
            }
        ]
    elif (interest_checked == "comandă"):
        message  = "🌟 Mulțumim că ai ales KROV! Pentru a putea procesa comanda ta cât mai rapid, te rugăm frumos să ne spui <strong>numele și prenumele</strong> tău. 😊"
        return jsonify({"ask_interests": message})
    else:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Ești un bot inteligent care răspunde la întrebarea: {interest}. In maxim 80 tokenuri"
                    "La finalul răspunsului tău, te rog să întrebi utilizatorul dacă dorește să aleagă un produs dintr-o categorie sau dacă dorește să plaseze o comandă."
                )
            }
        ]



    response = ask_with_ai(messages, temperature= 0.9 , max_tokens= 400)

    if (interest_checked == "altceva"):
        response = response + "!!!"

    return jsonify({"ask_interests": response})


def normalize_numere(text):
    cuvinte = text.split()
    normalizate = []
    for c in cuvinte:
        # Înlocuim virgula cu punct doar dacă conține cifre
        c_mod = c.replace(',', '.') if any(ch.isdigit() for ch in c) else c
        try:
            num = float(c_mod)
            # Transformăm în string cu exact 2 zecimale
            # %0.2f asigură 2 cifre după punct
            formatted_num = f"{num:.2f}"
            normalizate.append(formatted_num)
        except:
            normalizate.append(c)
    return ' '.join(normalizate)


def normalize_category(cat):
    return ' '.join(cat.replace("RoofArt;", "").split()).lower()

def fuzzy_check_category(user_interest, categorii_unice, threshold=70):
    # Mai întâi, caută cea mai bună potrivire globală
    user_interest = normalize_numere(user_interest)
    categorii_normalizate = [normalize_category(c) for c in categorii_unice]
    categorii_normalizate = [normalize_numere(c) for c in categorii_normalizate]
    # print("user_interest = ", user_interest)
    print("categorii_normalizate = ", categorii_normalizate)

    best_match, best_score = process.extractOne(user_interest, categorii_normalizate, scorer=fuzz.token_set_ratio)
    print("------------------------------------------------")
    if best_score >= threshold:
        print("best match = " ,best_match)
        return best_match

    # Dacă nu găsește potriviri bune, încearcă să compari fiecare cuvânt din user_interest separat
    words = user_interest.split()
    for word in words:
        best_match, best_score = process.extractOne(word, categorii_normalizate, scorer=fuzz.token_set_ratio)
        if best_score >= threshold:
            return best_match

    # Nu s-a găsit nimic relevant
    return "NU"


def smart_category_prompt(user_interest, categorii_unice):
    prompt = (
        "Având în vedere lista de categorii:\n"
        f"{', '.join(categorii_unice)}\n"
        f"Utilizatorul a spus: '{user_interest}'\n"
        "Sugerează cea mai potrivită categorie dintre lista de mai sus. "
        "Răspunde doar cu numele categoriei, fără alte explicații. "
        "Dacă niciuna nu se potrivește, răspunde cu NU."
    )
    messages = [{"role": "system", "content": prompt}]
    response = ask_with_ai(messages).strip()

    if not response or response.upper() == "NU":
        return "NU"
    
    # Poți face o verificare suplimentară să vezi dacă răspunsul chiar face parte din categorii
    if response not in categorii_unice:
        return "NU"

    return response


def este_numar(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    

def check_and_get_category(user_interest, categorii_unice, threshold=70):

    if este_numar(user_interest):
        return "NU"

    # Prima încercare: fuzzy matching
    if is_comanda(user_interest):
        return "comandă"

    fuzzy_result = fuzzy_check_category(user_interest, categorii_unice, threshold)

    if fuzzy_result != "NU":
        return fuzzy_result

    ai_result = smart_category_prompt(user_interest, categorii_unice)
    return ai_result


def check_and_get_category_new(user_interest, categorii_unice, threshold=70):

    if este_numar(user_interest):
        return "NU"

    fuzzy_result = fuzzy_check_category(user_interest, categorii_unice, threshold)

    if fuzzy_result != "NU":
        return fuzzy_result

    ai_result = smart_category_prompt(user_interest, categorii_unice)
    return ai_result



def is_comanda(user_interest):
    intentii_comanda = [
        "vreau să comand", "vreau sa comand", "doresc să cumpăr", "as dori sa cumpar",
        "aș vrea să achiziționez", "comand", "achiziționez", "cumpăr", "plătesc",
        "trimiteți factura", "hai să finalizăm", "pregătiți comanda", "trimit datele"
    ]
    # Listez toate cuvintele din expresiile cheie
    # Cuvintele din textul user
    cuvinte_user = user_interest.lower().split()
    # Verific fuzzy matching pentru fiecare cuvânt din user cu fiecare cuvânt cheie
    for cuv_user in cuvinte_user:
        for cuv_cheie in intentii_comanda:
            similarity = SequenceMatcher(None, cuv_user, cuv_cheie).ratio()
            if similarity > 0.8:  # prag de similaritate
                return True
    return False

def extrage_numar(text):
    # Caută primul număr în format zecimal, ex: 0.30 sau 1,25 etc.
    match = re.search(r'\d+[.,]?\d*', text)
    if match:
        return match.group().replace(',', '.')
    return ''

def exista_numere_in_variante(variante):
    for v in variante:
        if re.search(r'\d+[.,]?\d*', v):
            return True
    return False

def toate_valorile_egale(lista):
    # Elimină elementele vide sau None
    lista_curata = [x for x in lista if x]
    
    if not lista_curata:
        return False
    
    primul = lista_curata[0]
    return all(abs(float(x) - float(primul)) < 1e-6 for x in lista_curata)



def check_variante_manual(user_interest, variante_posibile):
    # user_interest_norm = normalize_numere(user_interest)

    # extrage doar numărul din fiecare variantă
    numere_din_variante = [normalize_numere(extrage_numar(v)) for v in variante_posibile]
    
    print(numere_din_variante)

    for numar in numere_din_variante:
        if numar in user_interest:
            return "DA"
    return "NU"


def check_variante(user_interest, variante_posibile):
    user_interest = normalize_numere(user_interest)
    variante_fara_primul_cuvant = [' '.join(v.split()[1:]) for v in variante_posibile]
    print("user din check_variante = " , user_interest)
    print("variante fara primul cuvant din check_variante = " , variante_fara_primul_cuvant)
    print(exista_numere_in_variante(variante_posibile))

    if exista_numere_in_variante(variante_posibile):
        if check_variante_manual(user_interest, variante_fara_primul_cuvant) == "NU":
            return "NU"
        return "DA"
    
    print(variante_fara_primul_cuvant)
    prompt = (
        f"Având în vedere următoarele opțiuni de produse:\n"
        f"{', '.join(variante_fara_primul_cuvant)}\n\n"
        f"Utilizatorul a spus: '{user_interest}'\n\n"
        "Răspunde cu un singur cuvânt: \n"
        "- DA, dacă a specificat clar și complet una dintre opțiuni cu toate datele\n"
        "- NU, dacă trebuie să aleagă mai clar\n"
        "Nu oferi explicații, doar DA, NU."
    )
    messages = [{"role": "system", "content": prompt}]
    response = ask_with_ai(messages).strip().upper()
    return response

def is_fuzzy_match(text, keyword, threshold=75):
    words = text.lower().split()
    keyword = keyword.lower()
    for w in words:
        if fuzz.partial_ratio(w, keyword) >= threshold:
            return True
    return False


preferinte['counter'] = 0
preferinte['interes_salvat'] = ""

def remove_numbers(text):
    return re.sub(r'\d+(\.\d+)?', '', text).strip()

categorii_new = [remove_numbers(cat) for cat in categorii_unice]

print("Categorii fara numere = ", categorii_new)
@app.route("/welcome", methods=["POST"])
def welcome():
    global counter
    data = request.json
    name = data.get("name", "")
    interests = data.get("interests", "")

    prompt_verify = (
        f"Ai o listă de categorii valide: {categorii_new}\n\n"
        f"Verifică dacă textul următor conține cel puțin o categorie validă sau o denumire care seamănă suficient (similaritate mare) cu vreuna din categoriile valide.\n\n"
        f'Text de verificat: "{interests}"\n\n'
        f'Răspunde strict cu "DA" dacă există o potrivire validă sau asemănătoare, altfel răspunde cu "NU".'
    )

    messages = [{"role": "system", "content": prompt_verify}] 
    resp = ask_with_ai(messages , max_tokens=10)
    print("RASPUNS = ", resp)
    if resp == "NU":
        if re.search(r'\d', interests):
            interests = preferinte['interes_salvat'] + " " + interests
    elif resp == "DA":
        preferinte['interes_salvat'] = interests
    
    # if preferinte['counter'] == 1:
    #     preferinte['interes_salvat'] += " "
    #     preferinte['interes_salvat'] += interests

    
            # preferinte['counter'] = 0
    # preferinte['interes_salvat'] += " " + interests
    # interests = preferinte['interes_salvat']
    # print("preferinte ================ ",preferinte['interes_salvat'])


    categoria_aleasa = check_and_get_category(interests, categorii_unice)

    print("categoria_aleasa = ", categoria_aleasa)
    # if preferinte['counter'] > 0 :
    #     prompt_verify = (
    #         f"Ai o listă de categorii valide: {categorii_unice}\n\n"
    #         f"Verifică dacă textul următor conține cel puțin o categorie validă sau o denumire care seamănă suficient (similaritate mare) cu vreuna din categoriile valide.\n\n"
    #         f'Text de verificat: "{interests}"\n\n'
    #         f'Răspunde strict cu "DA" dacă există o potrivire validă sau asemănătoare, altfel răspunde cu "NU".'
    #     )

    #     messages = [{"role": "system", "content": prompt_verify}] 
    #     resp = ask_with_ai(messages , max_tokens=10)
    #     print("raspuns prompt = " , resp)
    #     if resp == "NU":
    #         if(categoria_aleasa != "NU"):
    #             interests = preferinte['interes_salvat']
    #     elif resp == "DA":
    #         preferinte['interes_salvat'] = interests
            

    if is_fuzzy_match(interests,"ds") :
        if is_fuzzy_match(interests, "decor"):
            categoria_aleasa = "ds 0.40 décor"
            preferinte["Categorie"] = categoria_aleasa
            request_categorie = categoria_preferata(categoria_aleasa)
            preferinte["Produsele"] = request_categorie
            mesaj = request_categorie
            # mesaj += " . <br><br> Care produs te intereseaza ? "
            mesaj += " . <br><br> Doriti sa aflati informatie si despre alte categorii sau doriti sa comandati ? "
            return jsonify({"message": mesaj})
        elif is_fuzzy_match(interests, "alzn"):
            categoria_aleasa = "ds 0.40 alzn"
            preferinte["Categorie"] = categoria_aleasa
            request_categorie = categoria_preferata(categoria_aleasa)
            preferinte["Produsele"] = request_categorie
            mesaj = request_categorie
            # mesaj += " . <br><br> Care produs te intereseaza ? "
            mesaj += " . <br><br> Doriti sa aflati informatie si despre alte categorii sau doriti sa comandati ? "
            return jsonify({"message": mesaj})
    elif is_fuzzy_match(interests,"china"):
        if "mat" in interests.lower():
            categoria_aleasa = "china mat 0.40"
            preferinte["Categorie"] = categoria_aleasa
            request_categorie = categoria_preferata(categoria_aleasa)
            preferinte["Produsele"] = request_categorie
            mesaj = request_categorie
            mesaj += " . <br><br> Doriti sa aflati informatie si despre alte categorii sau doriti sa comandati ? "
            return jsonify({"message": mesaj})



    if categoria_aleasa == "NU":
        prompt = (
            f"Utilizatorul a scris categoria: '{interests}'.\n\n"
            "Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
            "Scrie un mesaj politicos, prietenos și natural, care:\n"
            "1. Răspunde pe scurt la ceea ce a spus utilizatorul . "
            "2. Mesajul să fie scurt, cald, empatic și prietenos. "
            "Nu mai mult de 2-3 propoziții.\n"
            "Nu folosi ghilimele și nu explica ce faci – scrie doar mesajul final pentru utilizator."
        )
        messages = [{"role": "system", "content": prompt}]
        mesaj = ask_with_ai(messages).strip()
        mesaj += (
            "<br><br>🏠🔨 Suntem gata să te ajutăm cu tot ce ține de acoperișuri! "
            "Te rog să alegi clar dacă dorești să afli detalii despre un <em>produs</em> sau vrei să plasezi o <em>comandă</em>. "
            "😊🛠️"
        )
        preferinte['interes_salvat'] = ""

    elif categoria_aleasa == "comandă":
        mesaj = "🌟 Mulțumim că ai ales KROV! Pentru a putea procesa comanda ta cât mai rapid, te rugăm frumos să ne spui numele și prenumele tău. 😊"
        return jsonify({"message": mesaj})
    else:
        search_key = categoria_aleasa.split()[0].lower()

        sub_variante = [cat for cat in categorii_unice if search_key in cat.lower()]
        variante_fara_primul_cuvant = [' '.join(v.split()[1:]) for v in sub_variante]

        check_sub_variante = check_variante(interests , sub_variante)


        if(check_sub_variante == "NU"):
            if len(sub_variante) > 1:
                emoji_options = ["🔹", "🔸", "▪️", "▫️", "◾", "◽"]  # Emoji-uri neutre pentru variante
                options_list = "\n".join([f"{emoji_options[i%len(emoji_options)]} {variant}" for i, variant in enumerate(variante_fara_primul_cuvant)])
                
                mesaj = (
                    f"Am găsit mai multe variante pentru '{categoria_aleasa.split()[0]}':\n\n"
                    f"{options_list}\n\n"
                    "Te rog să alegi varianta exactă care te interesează. 😊"
                )
                preferinte['counter'] = 1
            else:
                preferinte["Categorie"] = categoria_aleasa
                request_categorie = categoria_preferata(categoria_aleasa)
                preferinte["Produsele"] = request_categorie
                mesaj = request_categorie
                # mesaj += " . <br><br> Care produs te intereseaza ? "
                mesaj += " . <br><br> Doriti sa aflati informatie si despre alte categorii sau doriti sa comandati ? "
                
        
        else:
            preferinte["Categorie"] = categoria_aleasa
            request_categorie = categoria_preferata(categoria_aleasa)
            preferinte["Produsele"] = request_categorie
            mesaj = request_categorie
            # mesaj += " . <br><br> Care produs te intereseaza ? "
            mesaj += " . <br><br> Doriti sa aflati informatie si despre alte categorii sau doriti sa comandati ? "

    # print(preferinte["Produsele"])
    return jsonify({"message": mesaj})

def check_response(user_message):
    prompt = (
        f"Utilizatorul a spus: '{user_message}'\n\n"
        "Clasifică mesajul utilizatorului într-una dintre următoarele categorii, răspunzând cu un singur cuvânt:\n\n"
        "- DA: dacă mesajul exprimă o intenție clară și pozitivă, cum ar fi o confirmare, o dorință de a merge mai departe sau un interes real. "
        "Exemple: 'Da', 'Sigur', 'Aș dori', 'Sunt interesat', 'Vreau acel produs', 'Desigur', 'Perfect', 'sunt curios' etc.\n\n"
        "- NU: dacă mesajul exprimă o refuzare, o ezitare sau o lipsă de interes. "
        "Exemple: 'Nu', 'Nu acum', 'Nu sunt sigur', 'Mai târziu', etc.\n\n"
        "- ALTCEVA: dacă mesajul nu se încadrează în niciuna dintre categoriile de mai sus, de exemplu dacă utilizatorul pune o întrebare nespecifică, schimbă subiectul sau oferă informații fără legătură cu decizia, comanda sau interesul față de produs. "
    )
    messages = [{"role": "system", "content": prompt}]
    result = ask_with_ai(messages).strip().upper()
    return result


def construieste_prompt_selectie(produse_similare):
    if not produse_similare:
        return "⚠️ Nu există produse similare pentru a selecta."

    prompt = (
        "🔍 Am găsit mai multe produse care se potrivesc cu ce ai scris.\n"
        "👇 Te rog alege unul dintre produsele de mai jos:<br>\n\n"
    )

    for i, produs in enumerate(produse_similare, start=1):
        prompt += f"{i}. 🛒 {produs}<br>\n"

    prompt += "\n Scrie **numele exact** al produsului dorit"
    return prompt


def check_product(message):
    lista_produse = preferinte.get("Produsele", [])
    prompt = (
        "Primești o listă de produse și un mesaj venit de la client.\n"
        "Scopul tău este să identifici dacă mesajul clientului se referă clar la unul dintre produsele din listă, la mai multe produse, sau deloc.\n\n"
        "Instrucțiuni:\n"
        "- Dacă mesajul se potrivește clar CU UN SINGUR produs din lista normalizată, răspunde DOAR cu numele acelui produs, exact așa cum apare în listă.\n"
        "- Dacă mesajul se potrivește parțial sau ambiguu CU MAI MULTE produse din listă, răspunde cu: AMBIGUU: urmat de lista produselor potrivite separate prin virgulă (ex: AMBIGUU: Produs A, Produs B).\n"
        "- Dacă mesajul NU pare să se refere deloc la vreun produs din listă, sau conținutul este complet diferit (ex: întrebări generale, comentarii care nu au legătură cu produse), răspunde cu: NONE\n\n"
        f"Lista de produse disponibile: {', '.join(lista_produse)}\n"
        f"Mesaj client: \"{message.strip()}\"\n"
        "Răspuns:"
    )

    messages = [{"role": "system", "content": prompt}]
    response = ask_with_ai(messages).strip()

    if response.upper() == "NONE":
        return "NONE", []
    
    if response.upper().startswith("AMBIGUU"):
        _, sugestii = response.split(":", 1)
        produse_similare = [p.strip() for p in sugestii.split(",")]
        produse_similare = construieste_prompt_selectie(produse_similare)
        return "AMBIGUU", produse_similare

    return response, []


def check_category(user_interest, categorii_unice):
    prompt = (
        "Având în vedere lista de categorii:\n"
        f"{', '.join(categorii_unice)}\n"
        f"Utilizatorul a spus: '{user_interest}'\n"
        "Uite daca utilizatorul a specificat clar produsul , de exemplu daca cere tabla cutata , am mai multe variante si nu este clar , insa daca specifica ce tabla cutata atunci este bine si asa pentru toate trebuie"
        "Răspunde doar cu numele produsului daca este specificat bine , fără alte explicații. "
        "Dacă niciuna nu se potrivește, răspunde cu NU."
    )
    messages = [{"role": "system", "content": prompt}]
    response = ask_with_ai(messages).strip()

    if not response or response.upper() == "NU":
        return "NU"
    
    # Poți face o verificare suplimentară să vezi dacă răspunsul chiar face parte din categorii
    if response not in categorii_unice:
        return "NU"

    return response


@app.route("/next_chat", methods=["POST"])
def next_chat():
    data = request.get_json()
    name = data.get("name", "")
    interests = data.get("interests", "")
    message = data.get("message", "")
    response,lista = check_product(message)
    # response_name = check_category(interests,preferinte["Produsele"])
    # if response_name == "NU":
    if response == "AMBIGUU":

        return jsonify({"reply": lista})

    if response != "NONE" :
        preferinte['produs_exact'] = response
        response = (
            "Îți mulțumesc! Te rog să-mi spui doar cantitatea dorită pentru produs, "
            "ca să pot continua comanda ta.\n\n"
            "Aștept cantitatea, mulțumesc! 😊"
        )

    else:
        prompt = (
            "Nu trebuie sa te saluti pentru ca deja ducem o conversatie , trebuie sa raspunzi strict la mesaje ! "
            "Esti un chatbot inteligent care raspunde la intrebari intr-o maniera foarte prietenoasa ."
            "Esti chatbot-ul companiei KROV care se ocupa de acoperisuri . "
            f"Raspunde la mesajul {message} si adauga la final ca nu ai inteles ce produs si roaga userul sa mai aleaga odata produsul cu atentie . ( sa scrie fara greseli ) "
        )

        messages = [{"role": "system", "content": prompt}]
        response = ask_with_ai(messages)
        response += "!!!"

    return jsonify({"reply": response})
    

def este_cantitate_valida(message):
    
    prompt = (
        "Clientul a trimis un mesaj. Extrage, te rog,  cantitatea numerică exprimată în orice formă. "
        "Răspunde DOAR cu numărul, fără alte cuvinte.\n\n"
        "Dacă mesajul NU conține o cantitate sau nu este relevant (ex: „nu știu”, „ce produse mai aveți?”), răspunde strict cu 'NU'.\n\n"
        f"Mesaj: \"{message}\"\n"
        "Răspuns:"
    )

    messages = [{"role": "system", "content": prompt}]
    response = ask_with_ai(messages)
    return response


def check_price(produs_exact):
    lista_produse = preferinte.get("Produsele", [])
    print("list_produse = ", lista_produse)
    print("produsul exact : " , produs_exact)
    prompt = (
        f"Extrage te rog din lista de produse {lista_produse} produsul {produs_exact} , trebuie sa imi extragi fix produsul {produs_exact} si doar pe acesta nu alta informatie te rog!!!"
    )
    messages = [{"role": "system", "content": prompt}]
    response = ask_with_ai(messages)
    return response


def extrage_total_din_text(text):
    numere = re.findall(r"(?<![a-zA-Z])(\d+(?:[.,]\d+)?)", text)
    if numere:
        return float(numere[-1].replace(",", "."))
    return None


def print_price(pret_produs, cantitate, produsul_extras, culoare_aleasa, masurare):
    total = float(pret_produs) * float(cantitate)
    return (
        f"✅ Comanda ta a fost <strong>înregistrată cu succes</strong>! 🧾🎉<br><br>"
        f"📦 <strong>Produs:</strong> {produsul_extras}<br>"
        f"🎨 <strong>Culoare aleasă:</strong> {culoare_aleasa}<br>"
        f"💲 <strong>Preț unitar:</strong> {pret_produs:.2f} MDL<br>"
        f"📐 <strong>Cantitate:</strong> {cantitate} {masurare}<br>"
        f"🧮 <strong>Preț total:</strong> <strong>{total:.2f} MDL</strong><br><br>"
        "📞 Vei fi <strong>contactat în scurt timp</strong> de către echipa noastră pentru confirmare și detalii suplimentare. 🤝<br><br>"
        "🙏 Îți mulțumim pentru încredere! 💚<br><br>"
        "❓ Dacă mai ai întrebări, dorești să afli despre alte produse 🏠 sau vrei să adaugi ceva în comandă, sunt aici să te ajut! 😊"
    )




@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    name = data.get("name", "")
    interests = data.get("interests", "")
    message = data.get("message", "")
    response = check_response(message)
    print("raspuns = " , response)
    if response == "DA":
        messages = [
            {
                "role": "system",
                "content": (
                    "Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
                    "Fa promptul frumos , foloseste emoji-uri ( este despre un business de acoperisuri ) si pentur fiecare alegere adauga un emoji in loc de numere dar trebuie ca emojiurile sa fie strict legate de business de acoperisuri ( gen cand enumeri categoriile )"
                    "Esti un chatbot inteligent care creezi un prompt interactiv si frumos pentru user si il intrebi ce produse doreste , din cele de mai jos (trebuie incluse toate in prompt fara RoofArt in fata):"
                    f"Acestea sunt toate categoriile disponibile : {categorii_unice} , afiseaza-le pe toate"
                    "Afiseaza toate categoriile diponibile , nu scapa niciunu"
                    "Rogi userul sa raspunda cu denumirea exacta a produsului"
                )
            }
        ]

    elif response == "NU":
        messages = [
            {
                "role": "system",
                "content": (
                    "Îți mulțumesc pentru conversație! 🙏 Dacă vei avea întrebări sau vei dori să afli mai multe despre produsele noastre, "
                    "sunt aici oricând pentru tine. 🏠💬\n"
                    "Îți doresc o zi frumoasă și succes în proiectul tău de acoperiș! ☀️🔨"
                )
            }
        ]
        messages[0]['content'] += "!!!"
    else:
        messages = [
            {
                "role": "system",
                "content": (
                    f"Utilizatorul a scris categoria: '{interests}'.\n\n"
                    "Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
                    "Scrie un mesaj politicos, prietenos și natural, care:\n"
                    "1. Răspunde pe scurt la ceea ce a spus utilizatorul . "
                    "2. Apoi roagă-l politicos să raspunda daca doreste sa afle despre alt produs cu Da/Nu . "
                )
            }
        ]


    reply = ask_with_ai(messages, temperature=0.9 , max_tokens= 400)

    # reply = response.choices[0].message.content.strip()
    # log_message("AI BOT", reply)
    return jsonify({"reply": reply})


def check_surname_command(command):
    prompt = f"""
    Ești un validator automat care răspunde doar cu "DA" sau "NU" în funcție de faptul dacă un text conține un nume complet valid al unei persoane (prenume + nume).

    🔒 REGULI stricte:
    1. Numele complet trebuie să fie format din **exact două sau mai multe cuvinte**, fiecare fiind posibil un nume real.
    2. Nu trebuie să conțină **emoji, cifre, simboluri sau abrevieri**.
    3. Acceptă doar formulări declarative, nu întrebări sau răspunsuri vagi.
    4. Nu interpreta sau ghici – evaluează strict pe baza textului dat.

    📌 Exemple de mesaje valide (răspunde cu DA):
    - Mă numesc Ion Popescu
    - Sunt Maria Ionescu
    - Numele meu este Andrei Vasilescu
    - Mă cheamă Vlad Stoica
    - Eu sunt Radu Mihai
    - Da, mă numesc Elena Dobre

    📌 Exemple de mesaje invalide (răspunde cu NU):
    - Ion
    - Popescu
    - 😊😊😊
    - 12345
    - Nu știu
    - Poate mai târziu
    - Cum te numești?
    - Care este numele tău?
    - Andrei!
    - Numele meu este Ion (un singur cuvânt)

    🧪 Text de verificat:
    "{command}"

    🔍 Răspuns corect: (scrie exact "DA" sau "NU", fără explicații sau text suplimentar)
    """ 




    messages = [{"role": "system", "content": prompt}]
    response = ask_with_ai(messages, max_tokens=5)

    return response.strip()


@app.route("/comanda", methods=["POST"])
def comanda():
    data = request.get_json()
    name = data.get("name", "")
    interests = data.get("interests", "")
    message = data.get("message", "")
    print(message)
    check_sur = check_surname_command(message)

    print("nume prenume response = " , check_sur)

    if check_sur == "DA":
        reply = (
            "😊 Mulțumim! Ai un nume frumos! 💬<br>"
            "Ne-ai putea lăsa și un număr de telefon pentru a te putea contacta? 📞<br>"
            "Te rugăm să te asiguri că numărul începe cu <strong>0</strong> sau <strong>+373</strong>. ✅"
        )
    else:
        prompt_ai = (
            f"Nu te saluta niciodata pentru ca deja avem o discutie.\n"
            f"Acționează ca un asistent prietenos și politicos.\n"
            f"Răspunde la următorul mesaj ca și cum ai fi un agent uman care vrea să ajute clientul.\n"
            f"Răspunsul trebuie să fie cald, clar și la obiect. "
            f'Mesajul clientului: "{message}"\n\n'
            f"Răspuns:"
        )
        messages = [{"role": "system", "content": prompt_ai}]
        reply = ask_with_ai(messages, temperature=0.9 , max_tokens= 150)

        reply += "<br><br>📞 Introdu, te rog, numele si prenumele – este foarte important pentru a trece la pasul următor. Mulțumim ! 🙏😊"
    
    print(reply)
    return jsonify({"reply": reply})


def este_numar_valid_local(numar):
    numar = numar.strip()
    if numar.startswith('0') and len(numar) == 9:
        return numar[1] in ['6', '7']
    elif numar.startswith('+373') and len(numar) == 12:
        return numar[4] in ['6', '7']
    elif numar.startswith('373') and len(numar) == 11:
        return numar[3] in ['6', '7']
    else:
        return False


def extrage_si_valideaza_numar(text):
    pattern = r'(?<!\d)(\+?373\d{8}|373\d{8}|0\d{8})(?!\d)'
    posibile_numere = re.findall(pattern, text)
    nr = None
    for nr in posibile_numere:
        if este_numar_valid_local(nr):
            return nr , "VALID"
    return nr , "INVALID"

def check_numar(message):
    prompt = (
        "Verifică dacă textul de mai jos conține un număr de telefon, indiferent de format (poate conține spații, paranteze, simboluri, prefix +, etc.).\n"
        "Important este să existe o secvență de cifre care să poată fi considerată un număr de telefon.\n\n"
        f'Text: "{message}"\n\n'
        "RĂSPUNDE STRICT cu:\n"
        "DA – dacă există un număr de telefon în text\n"
        "NU – dacă nu există niciun număr de telefon în text\n\n"
        "Răspunde doar cu DA sau NU. Fără explicații. Fără alte cuvinte."
    )

    messages = [{"role": "system", "content": prompt}]
    response = ask_with_ai(messages, max_tokens=10)
    return response
    

@app.route("/numar_de_telefon", methods=["POST"])
def numar_de_telefon():
    data = request.get_json()
    name = data.get("name", "")
    interests = data.get("interests", "")
    message = data.get("message", "")
    print("message = ", message)
    valid = check_numar(message)

    print("valid = " , valid)
    if valid == "NU":
        prompt = (
            "Nu te saluta pentru ca deja avem o discutie.\n"
            "Acționează ca un asistent prietenos și politicos.\n"
            "Răspunde natural și cald la mesajul clientului.\n"
            f"Mesaj client: \"{message}\"\n\n"
            "Răspuns:"
        )

        messages = [{"role": "system", "content": prompt}]
        ai_reply = ask_with_ai(messages, max_tokens=150)
        ai_reply += "<br><br> 🙏 Te rog să introduci un număr de telefon valid pentru a putea continua. 📞"

        return jsonify({"reply": ai_reply})

    print(message)
    nr, status = extrage_si_valideaza_numar(message)
    print(f"valid = {status}")


    if status != "VALID":
        reply = (
            "🚫 Numărul acesta nu pare corect.\n"
            "Te rog să introduci un număr valid care începe cu `0` sau `+373`. 📞"
        )
    else:
        messages = [
            {
                "role": "user",
                "content": (
                    "Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
                    "Trebuie sa ii zici userului sa aleaga din categoriile de mai jos pentru a putea finisa comanda"
                    "Fa promptul frumos , foloseste emoji-uri ( este despre un business de acoperisuri ) si pentur fiecare alegere adauga un emoji in loc de numere dar trebuie ca emojiurile sa fie strict legate de business de acoperisuri ( gen cand enumeri categoriile )"
                    "Esti un chatbot inteligent care creezi un prompt interactiv si frumos pentru user si il intrebi ce produse doreste , din cele de mai jos (trebuie incluse toate in prompt fara RoofArt in fata):"
                    f"Acestea sunt toate categoriile disponibile : {categorii_unice}"
                    "Rogi userul sa raspunda cu denumirea exacta a produsului din lista de categorii"
                )
            }
        ]
        reply = ask_with_ai(messages , temperature=0.8 , max_tokens= 400)

    return jsonify({"reply": reply})

@app.route("/categorie", methods=["POST"])
def categorie():
    data = request.get_json()
    name = data.get("name", "")
    interests = data.get("message", "")

    prompt_verify = (
        f"Ai o listă de categorii valide: {categorii_new}\n\n"
        f"Verifică dacă textul următor conține cel puțin o categorie validă sau o denumire care seamănă suficient (similaritate mare) cu vreuna din categoriile valide.\n\n"
        f'Text de verificat: "{interests}"\n\n'
        f'Răspunde strict cu "DA" dacă există o potrivire validă sau asemănătoare, altfel răspunde cu "NU".'
    )

    messages = [{"role": "system", "content": prompt_verify}] 
    resp = ask_with_ai(messages , max_tokens=10)
    print("RASPUNS = ", resp)
    if resp == "NU":
        if re.search(r'\d', interests):
            interests = preferinte['interes_salvat'] + " " + interests
    elif resp == "DA":
        preferinte['interes_salvat'] = interests


    categoria_aleasa = check_and_get_category_new(interests, categorii_unice)

    if is_fuzzy_match(interests,"ds") :
        if is_fuzzy_match(interests, "decor"):
            categoria_aleasa = "ds 0.40 décor"
            preferinte["Categorie"] = categoria_aleasa
            request_categorie = categoria_preferata(categoria_aleasa)
            preferinte["Produsele"] = request_categorie
            mesaj = request_categorie
            # mesaj += " . <br><br> Care produs te intereseaza ? "
            mesaj += (
                "🔍 Dacă ai găsit ceva interesant mai sus, te rog alege <strong>exact</strong> produsul dorit din listă pentru a continua! 💬<br><br>"
                "✍️ Scrie numele produsului <strong>exact așa cum apare mai sus</strong> și te voi ajuta imediat! 🚀"
            )
            return jsonify({"message": mesaj})
        elif is_fuzzy_match(interests, "alzn"):
            categoria_aleasa = "ds 0.40 alzn"
            preferinte["Categorie"] = categoria_aleasa
            request_categorie = categoria_preferata(categoria_aleasa)
            preferinte["Produsele"] = request_categorie
            mesaj = request_categorie
            # mesaj += " . <br><br> Care produs te intereseaza ? "
            mesaj += (
                "🔍 Dacă ai găsit ceva interesant mai sus, te rog alege <strong>exact</strong> produsul dorit din listă pentru a continua! 💬<br><br>"
                "✍️ Scrie numele produsului <strong>exact așa cum apare mai sus</strong> și te voi ajuta imediat! 🚀"
            )
            return jsonify({"message": mesaj})
    elif is_fuzzy_match(interests,"china"):
        if "mat" in interests.lower():
            categoria_aleasa = "china mat 0.40"
            preferinte["Categorie"] = categoria_aleasa
            request_categorie = categoria_preferata(categoria_aleasa)
            preferinte["Produsele"] = request_categorie
            mesaj = request_categorie
            mesaj += (
                "🔍 Dacă ai găsit ceva interesant mai sus, te rog alege <strong>exact</strong> produsul dorit din listă pentru a continua! 💬<br><br>"
                "✍️ Scrie numele produsului <strong>exact așa cum apare mai sus</strong> și te voi ajuta imediat! 🚀"
            )
            return jsonify({"reply": mesaj})
        

    if categoria_aleasa == "NU":
        prompt = (
            f"Utilizatorul a scris categoria: '{interests}'.\n\n"
            "Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
            "Scrie un mesaj politicos, prietenos și natural, care:\n"
            "1. Răspunde pe scurt la ceea ce a spus utilizatorul . "
            "2. Apoi roagă-l politicos să rescrie cu atenție denumirea categoriei dorite, "
            "pentru a-l putea ajuta cât mai bine.\n"
            "3. Mesajul să fie scurt, cald, empatic și prietenos. "
            "Nu mai mult de 2-3 propoziții.\n"
            "Nu folosi ghilimele și nu explica ce faci – scrie doar mesajul final pentru utilizator."
        )
        messages = [{"role": "system", "content": prompt}]
        mesaj = ask_with_ai(messages).strip()
        mesaj += "!!!"
        preferinte['interes_salvat'] = ""
    else:
        search_key = categoria_aleasa.split()[0].lower()
        sub_variante = [cat for cat in categorii_unice if search_key in cat.lower()]
        variante_fara_primul_cuvant = [' '.join(v.split()[1:]) for v in sub_variante]
        check_sub_variante = check_variante(interests , sub_variante)

        if(check_sub_variante == "NU"):
            if len(sub_variante) > 1:
                emoji_options = ["🔹", "🔸", "▪️", "▫️", "◾", "◽"]  # Emoji-uri neutre pentru variante
                options_list = "\n".join([f"{emoji_options[i%len(emoji_options)]} {variant}" for i, variant in enumerate(variante_fara_primul_cuvant)])
                
                mesaj = (
                    f"Am găsit mai multe variante pentru '{categoria_aleasa.split()[0]}':\n\n"
                    f"{options_list}\n\n"
                    "Te rog să alegi varianta exactă care te interesează. 😊"
                )
                preferinte['counter'] = 1
                
            else:
                preferinte["Categorie"] = categoria_aleasa
                request_categorie = categoria_preferata(categoria_aleasa)
                preferinte["Produsele"] = request_categorie
                mesaj = request_categorie
                # mesaj += " . <br><br> Care produs te intereseaza ? "
                mesaj += (
                    "🔍 Dacă ai găsit ceva interesant mai sus, te rog alege <strong>exact</strong> produsul dorit din listă pentru a continua! 💬<br><br>"
                    "✍️ Scrie numele produsului <strong>exact așa cum apare mai sus</strong> și te voi ajuta imediat! 🚀"
                )

        else:
            preferinte["Categorie"] = categoria_aleasa
            request_categorie = categoria_preferata(categoria_aleasa)
            preferinte["Produsele"] = request_categorie
            mesaj = request_categorie
            # mesaj += " . <br><br> Care produs te intereseaza ? "
            mesaj += (
                "🔍 Dacă ai găsit ceva interesant mai sus, te rog alege <strong>exact</strong> produsul dorit din listă pentru a continua! 💬<br><br>"
                "✍️ Scrie numele produsului <strong>exact așa cum apare mai sus</strong> și te voi ajuta imediat! 🚀"
            )


    print("mesaj = " , mesaj)
    return jsonify({"reply": mesaj})


def genereaza_prompt_produse(rezultat, categorie):
    if not rezultat:
        return "❌ Nu am găsit produse pentru categoria selectată."

    lista_formatata = ""
    for idx, prod in enumerate(rezultat, 1):
        nume = prod['produs'].replace("**", "")  # elimină markdown
        pret = prod['pret']
        lista_formatata += f"🔹 <strong>{nume}</strong> — 💸 {pret}<br />"

    prompt = (
        f"🔍 La cererea ta, am găsit următoarele produse din categoria <strong>{categorie}</strong>:<br /><br />"
        f"{lista_formatata}<br />"
        "🛒 Te rog să alegi <strong>exact produsul dorit</strong> din listă pentru a ști ce preferi. Mulțumesc! 🙏"
    )
    return prompt


preferinte["Produs_Ales"] = ""
@app.route("/produs", methods=["POST"])
def produs():
    data = request.get_json()
    name = data.get("name", "")
    interests = data.get("message", "")

    produse = preferinte["Produsele"]
    if "nu sunt disponibile" in produse.lower():
        culori = False
    else:
        culori = True
    

    rezultat = function_check_product(interests , preferinte["Produsele"])
    print("rezultat = " , rezultat)

    if rezultat == "NU":
        length_check = 0
    else:
        length_check = len(rezultat)

    if length_check == 1 :
        preferinte["Produs_Ales"] = rezultat[0]["produs"]
        if culori:
            return jsonify({
                "reply": (
                    "✅ Mulțumim pentru alegerea ta! 🛒 Produsul a fost notat cu succes. 💬<br><br>"
                    "🎨 Acum, te rog să alegi <strong>culoarea dorită</strong> pentru acest produs.<br>"
                    "📋 Scrie numele exact al culorii , iar eu mă ocup de restul! 😊"
                )
            })
        else:
            return jsonify({
                "reply": (
                    "✅ Mulțumim pentru alegerea ta! 🛒 Produsul a fost notat cu succes. 💬<br><br>"
                    "📋 Nu avem culorile disponibile , dar te rog sa imi zici culoarea preferata! 😊"
                )
            })
    elif length_check > 1:
        reply = genereaza_prompt_produse(rezultat, preferinte["Categorie"])
        return jsonify({"reply": reply})
    
    else:
        prompt = (
            "Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
            "Scrie un mesaj politicos, prietenos și natural, care:\n"
            f"Răspunde pe scurt la ceea ce a spus utilizatorul {interests}.\n"
            "2. Mesajul să fie scurt, cald, empatic și prietenos. "
            "Nu mai mult de 2-3 propoziții.\n"
            "Nu folosi ghilimele și nu explica ce faci – scrie doar mesajul pentru utilizator."
        )
        messages = [{"role": "system", "content": prompt}]
        reply = ask_with_ai(messages).strip()
        reply +="<br><br>📋 Te rog să alegi un <strong>produs valid din listă</strong> ✏️ scriindu-i <strong>denumirea exactă</strong>.<br> 🔍 Doar așa putem continua mai departe cu procesul comenzii! 😊🔧🏠"


    return jsonify({"reply": reply})




def verifica_culoare_cu_ai(interests, culori):
    lista_culori_str = "\n".join(f"- {c}" for c in culori)

    prompt = (
        f"Ești un asistent inteligent care verifică dacă mesajul de mai jos conține o culoare validă sau apropiată semantic din lista de culori.\n\n"
        f"Culorile disponibile sunt:\n{lista_culori_str}\n\n"
        f"Mesajul utilizatorului:\n\"{interests}\"\n\n"
        "1. Dacă mesajul corespunde exact unei singure culori, răspunde DOAR cu acea culoare.\n"
        "2. Dacă mesajul poate însemna mai multe culori (ex: 'gri' se potrivește la 3 variante), răspunde strict cu 'AMBIGUU'.\n"
        "3. Dacă nu este nicio culoare potrivită, răspunde cu 'NU'.\n\n"
        "Nu explica nimic. Nu folosi ghilimele. Răspunsul trebuie să fie fie o culoare, fie 'AMBIGUU', fie 'NU'."
    )

    messages = [{"role": "user", "content": prompt}]
    return ask_with_ai(messages, temperature=0.3, max_tokens=20)


def verifica_culoare_generala_cu_ai(interests):
    prompt = (
        "Ești un asistent care detectează dacă un mesaj conține o denumire validă de culoare, chiar și generică.\n\n"
        f"Mesajul utilizatorului:\n\"{interests}\"\n\n"
        "Dacă mesajul conține o culoare validă (de exemplu: roșu, verde, turcoaz închis, alb mat, maro lucios etc.), "
        "răspunde DOAR cu denumirea culorii așa cum apare ea în mesaj.\n"
        "Dacă NU există nicio culoare validă, răspunde strict cu 'NU'.\n\n"
        "Nu explica nimic. Nu folosi ghilimele. Nu adăuga alt text."
    )

    messages = [{"role": "user", "content": prompt}]
    return ask_with_ai(messages, temperature=0.2, max_tokens=15)


culori = ""
preferinte["Culoare_Aleasa"] = ""
@app.route("/culoare", methods=["POST"])
def culoare():
    data = request.get_json()
    name = data.get("name", "")
    interests = data.get("message", "")
    # produse = preferinte["Produsele"]
    produse = preferinte["Produsele"]
    if "nu sunt disponibile" in produse.lower():
        culori = False
    else:
        culori = True

    if culori:
        produse_split = preferinte["Produsele"].split("Culori disponibile:")
        if len(produse_split) > 1:
            culori_html = produse_split[1]
            
            # Extragem doar partea cu <div>-urile cu nume de culoare
            soup = BeautifulSoup(culori_html, "html.parser")
            divuri = soup.find_all("div")
            
            lista_culori = []
            for div in divuri:
                culoare = div.get_text(strip=True)
                if culoare:
                    lista_culori.append(culoare)

            print("🎨 Culori extrase:")
            for c in lista_culori:
                print("-", c)
                culori = c + "\n"
        else:
            print("⚠️ Nu există secțiunea 'Culori disponibile:' în text.")

        response = verifica_culoare_cu_ai(interests , lista_culori)

        if response == "NU":
            prompt = (
                "Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
                "Scrie un mesaj politicos, prietenos și natural, care:\n"
                f"Răspunde pe scurt la ceea ce a spus utilizatorul {interests}.\n"
                "2. Mesajul să fie scurt, cald, empatic și prietenos. "
                "Nu mai mult de 2-3 propoziții.\n"
                "Nu folosi ghilimele și nu explica ce faci – scrie doar mesajul pentru utilizator."
            )

            messages = [{"role": "system", "content": prompt}]
            reply = ask_with_ai(messages).strip()
            reply += (
                "<br><br>🎨 Te rog să alegi o <strong>culoare validă</strong> din lista afișată ✏️ "
                "scriind <strong>numele exact al culorii</strong>.<br><br>🔍 Doar așa putem trece la etapa finală a comenzii tale! 🧾🚀😊"
            )
        
        if response == "AMBIGUU":
            reply = (
                "🔍 Am observat că ai menționat o culoare care poate avea mai multe nuanțe sau variante. <br><br>"
                "🎨 Te rog să alegi <strong>exact una</strong> dintre variantele afișate anterior și să scrii numele complet pentru a putea continua comanda. 🧾😊"
            )
            return jsonify({"reply": reply})


        else:
            preferinte["Culoare_Aleasa"] = response
            reply = (
                f"🖌️ Culoarea a fost înregistrată cu succes! ✅<br><br>"
                "📦 Te rog acum să îmi spui <strong>cantitatea dorită</strong> pentru acest produs, în metri pătrați sau metri liniari – cum preferi tu. 📐🧮<br>"
                "💬 Aștept mesajul tău pentru a putea continua comanda. 😊"
            )
            return jsonify({"reply": reply})
    else:
        response = verifica_culoare_generala_cu_ai(interests)
        if response == "NU":
            prompt = (
                "Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
                "Scrie un mesaj politicos, prietenos și natural, care:\n"
                f"Răspunde pe scurt la ceea ce a spus utilizatorul {interests}.\n"
                "2. Mesajul să fie scurt, cald, empatic și prietenos. "
                "Nu mai mult de 2-3 propoziții.\n"
                "Nu folosi ghilimele și nu explica ce faci – scrie doar mesajul pentru utilizator."
            )

            messages = [{"role": "system", "content": prompt}]
            reply = ask_with_ai(messages).strip()
            reply += (
                "<br><br>🎨 Te rog să alegi o <strong>culoare validă</strong> ✏️ "
                "scriind <strong>numele exact al culorii</strong>.<br><br>🔍 Doar așa putem trece la etapa finală a comenzii tale! 🧾🚀😊"
            )
        else:
            preferinte["Culoare_Aleasa"] = response
            reply = (
                f"🖌️ Culoarea a fost înregistrată cu succes! ✅<br><br>"
                "📦 Te rog acum să îmi spui <strong>cantitatea dorită</strong> pentru acest produs, în metri pătrați , metri liniari sau foaie – cum preferi tu. 📐🧮<br>"
                "💬 Aștept mesajul tău pentru a putea continua comanda. 😊"
            )
            return jsonify({"reply": reply})

    return jsonify({"reply": reply})


@app.route("/cantitate", methods=["POST"])
def cantitate():
    masurare = ""
    data = request.get_json()
    name = data.get("name", "")
    interests = data.get("interests", "")
    message = data.get("message", "")
    cantitate = este_cantitate_valida(message)

    if cantitate == "NU":
        prompt = (
            "Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
            "Scrie un mesaj politicos, prietenos și natural, care:\n"
            f"Răspunde pe scurt la ceea ce a spus utilizatorul {interests}.\n"
            "2. Mesajul să fie scurt, cald, empatic și prietenos. "
            "Nu mai mult de 2-3 propoziții.\n"
            "Nu folosi ghilimele și nu explica ce faci – scrie doar mesajul pentru utilizator."
        )

        messages = [{"role": "system", "content": prompt}]
        reply = ask_with_ai(messages).strip()
        reply += (
            "<br><br>📐 Te rog să îmi spui o <strong>cantitate clară</strong> 😊<br><br>"
            "🧮 Doar așa pot calcula prețul total și înregistra comanda. Mulțumesc!"
        )
        return jsonify({"reply": reply})

    produs_exact = preferinte['Produs_Ales']
    produsul_extras = check_price(produs_exact)
    if "m2" in produsul_extras:
        masurare = "m2"
    elif "ml" in produsul_extras:
        masurare = "ml"
    elif "foaie" in produsul_extras:
        masurare = "foi"
    print("Produsul extras : " , produsul_extras)
    pret_produs = extrage_total_din_text(produsul_extras)
    print(pret_produs)
    print_frumos = print_price(pret_produs,cantitate,produs_exact,preferinte["Culoare_Aleasa"], masurare)
    # print(print_frumos)
    return jsonify({"reply": print_frumos})



def ask_with_ai(messages , temperature = 0.9 , max_tokens = 100):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()






if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
