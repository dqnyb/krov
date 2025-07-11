from openai import OpenAI
from flask import Flask, request, jsonify, render_template, send_from_directory
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
from test import traducere_produse
from bs4 import BeautifulSoup
import requests 
import urllib.parse


app = Flask(__name__)
CORS(app)

load_dotenv()

TELEGRAM = os.getenv("TELEGRAM_API_KEY")
CHAT_ID = os.getenv("CHAT_ID")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY
# Pentru acest proiect am lăsat cheia publică (pentru a fi testată mai repede), dar desigur că nu se face așa!
# Aș fi folosit client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) și aș fi dat export în env la key: export OPENAI_API_KEY="sk-..."

client = OpenAI(
    api_key=OPENAI_API_KEY,  # pune aici cheia ta reală!
)

preferinte = {}
preferinte['interes_salvat'] = ""

df = pd.read_excel('chatBot/p.xlsx')
categorii = df['Categorie']
categorii_unice = list(dict.fromkeys(categorii.dropna().astype(str)))
print("categorii unice = " , categorii_unice)




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
            "💬 <em>Хотите узнать о товаре</em> или <em>сделать заказ</em>?<br><br>"
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
        "trimit date", "comand", "cumpăr", "pregătiți comanda", "ofertă pentru", "cerere ofertă",
        "cât costă x bucăți", "preț 50 mp", "livrare comandă", "plată", "comanda", "comanda" "curier",
        
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
        "- expresii vagi sau generale de interes: 'vreau produs' ,'vreau produsul', 'doresc un model', 'aș vrea să văd', 'ce aveți în categoria X'\n"
        "- întrebări despre specificații, caracteristici, opțiuni de personalizare, materiale, întreținere\n"
        "- comparații între produse/serii\n"
        "- solicitări de imagini, cataloage, mostre\n"
        "- întrebări despre disponibilitate, dimensiuni, stoc, livrare (doar dacă nu menționează acțiunea de a comanda)\n"
        "- întrebări despre garanție, montaj\n"
        "- mențiuni despre preț fără cerere explicită de ofertă sau acțiune\n"
        "- orice exprimare incertă sau ambiguu-intenționată\n\n"
        
        "2. comandă - DOAR când există acțiune explicită, clar formulată:\n"
        "- 'comand', 'cumpăr', 'să achiziționez'\n"
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
        "- Verbe generice precum „vreau”, „doresc”, „aș vrea” NU implică automat comandă dacă nu sunt urmate de „să comand”, „să cumpăr”, „factură”, etc.\n\n"
        
    
        "EXEMPLE CLASIFICATE:\n"
        "'Ce modele impermeabile aveți?' => produs_informații\n"
        "'Aveți și alte categorii?' => produs_informații\n"
        "'Produse?' => produs_informații\n"
        "'Vreau produs?' => produs_informații\n"
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

def check_interest_rus(interest):

    if is_fuzzy_comanda(interest):
        return "comandă"

    interests_prompt = (
        "Анализируй сообщение пользователя, чтобы точно определить намерение по следующим категориям:\n\n"
        
        "1. produs_informații - ВКЛЮЧАЕТ предварительные намерения покупки, общие выражения, интерес или запрос категорий. В эту категорию относится любой интерес к:\n"
        "- товару, товаре, продуктам, моделям, сериям, коллекциям, цветам, категориям ('Что у вас есть?', 'Какие еще модели?', 'Есть ли еще продукты?', 'Какие у вас товары?')\n"
        "- общие или неполные выражения: 'продукты?', 'категории?', 'другие модели?', 'водонепроницаемые?', 'товар?' – даже если вопрос неполный\n"
        "- расплывчатые или общие выражения интереса: 'хочу продукт', 'хочу товар', 'хочу модель', 'хочу посмотреть', 'что у вас в категории X'\n"
        "- вопросы о характеристиках, материалах, опциях персонализации, уходе\n"
        "- сравнения между продуктами/сериями\n"
        "- запросы изображений, каталогов, образцов\n"
        "- вопросы о наличии, размерах, запасах, доставке (только если не упоминается действие заказа)\n"
        "- вопросы о гарантии, монтаже\n"
        "- упоминания цены без явного запроса оферты или действия\n"
        "- любые неясные или двусмысленные выражения\n\n"
        
        "2. comandă - ТОЛЬКО если есть явное, четко сформулированное действие:\n"
        "- 'хочу заказать', 'хочу купить', 'желаю приобрести'\n"
        "- запрос цены на определенное количество: 'сколько стоит 30 штук', 'пришлите цену на 50 кв.м.'\n"
        "- формулировки о условиях доставки/оплаты для предстоящей сделки\n"
        "- любые формулировки с глаголом, обозначающим транзакцию: 'заказываю', 'покупаю', 'оплачиваю', 'пришлите счет'\n"
        "- запросы, связанные с доставкой, транспортом или условиями доставки: 'делаете доставку', 'доставляете по адресу', 'сколько стоит транспорт'\n"
        "- выражения завершения заказа: 'давайте завершим', 'готовьте заказ', 'отправляю данные для счета'\n\n"
        
        "3. altceva - только для:\n"
        "- приветствий, благодарностей без делового контекста\n"
        "- шуток, спама, неуместных комментариев\n"
        "- сообщений, не связанных с продуктами или заказами\n\n"
        
        "ВАЖНЫЕ ПРАВИЛА:\n"
        "- Любое упоминание товаров, продуктов, серий, моделей, категорий или общих выражений => produs_informații\n"
        "- Любая неоднозначность => produs_informații (лучше ложноположительный результат, чем упустить намерение)\n"
        "- Только при наличии четкого глагола заказа => классифицировать как 'comandă'\n\n"
        
        "ПРИМЕРЫ КЛАССИФИКАЦИИ:\n"
        "'Какие у вас есть водонепроницаемые модели?' => produs_informații\n"
        "'Есть ли еще категории?' => produs_informații\n"
        "'Продукты?' => produs_informații\n"
        "'Товар?' => produs_informații\n"
        "'Хотел бы увидеть другие варианты' => produs_informații\n"
        "'Хочу заказать 100 кв.м. на понедельник' => comandă\n"
        "'Пришлите счет на почту' => comandă\n"
        "'Привет, добрый день' => altceva\n\n"
        
        f"Сообщение для анализа: \"{interest}\"\n\n"
        "Ответьте СТРОГО одним из тегов на румынском языке: produs_informații, comandă, altceva. Без дополнительных объяснений."
    )

    
    messages = [{"role": "system", "content": interests_prompt}]
    response = ask_with_ai(messages)
    return response


def format_product_mentions(text):
    # Găsește toate subșirurile delimitate de apostrofuri și le înlocuiește cu <br> + conținutul
    return re.sub(r"'([^']+)'", r"<br>🏠 \1", text)

def clean_punct_except_numbers(text):
    # Pattern: găsește punct sau virgulă care NU sunt între cifre
    # Folosim lookbehind și lookahead pentru cifre
    pattern = r'(?<!\d)[.,]|[.,](?!\d)'
    # Înlocuim cu empty string
    return re.sub(pattern, '', text)

@app.route("/interests", methods=["POST"])
def interests():
    user_data = request.get_json()
    interest = user_data.get("name", "prieten")
    language_saved = user_data.get("language")
    print(language_saved)
    if language_saved == "RO":
        interest_checked = check_interest(interest)
    elif language_saved == "RU":
        interest_checked = check_interest_rus(interest)
    
    print(interest_checked)


    if (interest_checked == "produs_informații"):
        if language_saved == "RO":
            messages = [
                {
                    "role": "user",
                    "content": (
                        "Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
                        "Fa promptul frumos , nu foloseste emoji-uri deloc ( este despre un business de acoperisuri ) , scrie categoriile in '' , gen 'china' , fara '-' in fata"
                        "Esti un chatbot inteligent care creezi un prompt interactiv si frumos pentru user si il intrebi ce produse doreste , din cele de mai jos (trebuie incluse toate in prompt fara RoofArt in fata):"
                        f"Acestea sunt toate categoriile disponibile : {categorii_unice}"
                        "Rogi userul sa raspunda cu denumirea exacta a produsului din lista de categorii"
                    )
                }
            ]
        elif language_saved == "RU":
            messages = [
                {
                    "role": "user",
                    "content": (
                        "Никогда не говори «Привет», никаких вступительных фраз, потому что мы уже ведём разговор и знаем друг друга. "
                        "Сделай подсказку красивой, не используй вообще никаких эмодзи (это про крышный бизнес), пиши категории в '' кавычках, например 'china', без дефиса перед ними. "
                        "Ты — умный чатбот, который создаёт интерактивную и красивую подсказку для пользователя и спрашивает, какие продукты он хочет из следующих (все должны быть включены в подсказку без RoofArt перед ними): "
                        f"Это все доступные категории: {categorii_unice} "
                        "Попроси пользователя ответить точным названием продукта из списка категорий."
                    )
                }
            ]


    elif (interest_checked == "comandă"):
        if language_saved == "RO":
            message  = "🌟 Mulțumim că ai ales KROV! Pentru a putea procesa comanda ta cât mai rapid, te rugăm frumos să ne spui <strong>numele și prenumele</strong> tău. 😊"
        elif language_saved == "RU":
            message  = "🌟 Спасибо, что выбрали KROV! Чтобы мы могли как можно быстрее обработать ваш заказ, пожалуйста, укажите <strong>ваше имя и фамилию</strong>. 😊"
        return jsonify({"ask_interests": message})
    else:
        if language_saved == "RO":
            messages = [
                {
                    "role": "user",
                    "content": (
                        f"Ești un bot inteligent care răspunde la întrebarea: {interest}. In maxim 100 tokenuri"
                    )
                }
            ]
        elif language_saved == "RU":
            messages = [
                {
                    "role": "user",
                    "content": (
                        f"Ты умный бот, который отвечает на вопрос: {interest}. Максимум 100 токенов."
                    )
                }
            ]


    response = ask_with_ai(messages, temperature= 0.9 , max_tokens= 400)
    pos = response.rfind("'")
    if pos != -1:
        response = response[:pos+1] + "<br><br>" + response[pos+1:]

    pos = response.rfind(":")
    if pos != -1:
        response = response[:pos+1] + "<br>" + response[pos+1:]

    response = format_product_mentions(response)
    response = clean_punct_except_numbers(response)

    if (interest_checked == "altceva"):
        if language_saved == "RO":
            response = response + (
                "<br><br><strong>🏠🔧 Te rog să alegi ce dorești:</strong><br>"
                "Să afli informații despre un <em>produs</em><br>"
                "sau să plasezi o <em>comandă</em>? 😊"
            )
        elif language_saved == "RU":
            response = response + (
                "<br><br><strong>🏠🔧 Пожалуйста, выберите, что вы хотите:</strong><br>"
                "Узнать информацию о <em>товаре</em><br>"
                "или оформить <em>заказ</em>? 😊"
            )

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
        # Română
        "vreau să comand", "vreau sa comand", "doresc să cumpăr", "as dori sa cumpar",
        "aș vrea să achiziționez", "comand", "achiziționez", "cumpăr", "plătesc",
        "trimiteți factura", "hai să finalizăm", "pregătiți comanda", "trimit datele",
        # Rusă
        "хочу заказать", "хочу купить", "хочу приобрести", "заказываю", "покупаю",
        "оплачу", "отправьте счёт", "давайте закончим", "подготовьте заказ", "отправляю данные"
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



def format_products_list_with_intro(text):
    if ':' not in text:
        return text  # Fără două părți, returnează textul original

    intro, rest = text.split(':', 1)
    rest = rest.strip()

    # Verificăm dacă există numerotare (1. 2. etc.)
    if not re.search(r'\d+\.', rest):
        return text  # Dacă nu există numerotare, nu formatăm

    # Separăm după numerotare

    items = re.split(r'\s*\d+\.\s*', rest)
    items = [item.strip() for item in items if item.strip()]

    # Formatăm cu 🏠 și <br>
    formatted_items = [f"🛠️ {item}" for item in items]
    result = f"{intro.strip()}:<br><br>" + "<br>".join(formatted_items)

    return result




print("Categorii fara numere = ", categorii_new)
@app.route("/welcome", methods=["POST"])
def welcome():
    global counter
    data = request.json
    name = data.get("name", "")
    interests = data.get("interests", "")
    language_saved = data.get("language","")

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

    categoria_aleasa = check_and_get_category(interests, categorii_unice)

    print("categoria_aleasa = ", categoria_aleasa)

    if is_fuzzy_match(interests,"ds") :
        if is_fuzzy_match(interests, "decor"):
            categoria_aleasa = "ds 0.40 décor"
            preferinte["Categorie"] = categoria_aleasa
            request_categorie = categoria_preferata(categoria_aleasa)
            preferinte["Produsele_RO"] = request_categorie
            if language_saved == "RU":
                request_categorie = traducere_produse(request_categorie)
            preferinte["Produsele"] = request_categorie
            mesaj = request_categorie
            mesaj = format_products_list_with_intro(mesaj)
            if language_saved == "RU":
                mesaj += "<br><br> 📚 Хотите узнать информацию и про другие категории или 🚀 хотите сделать заказ? 🤔"
            elif language_saved == "RO":
                mesaj += " . <br><br> 📚 Doriti să aflați informații și despre alte categorii sau 🚀 doriți să comandați? 🤔"
            return jsonify({"message": mesaj})
        elif is_fuzzy_match(interests, "alzn"):
            categoria_aleasa = "ds 0.40 alzn"
            preferinte["Categorie"] = categoria_aleasa
            request_categorie = categoria_preferata(categoria_aleasa)
            preferinte["Produsele_RO"] = request_categorie
            if language_saved == "RU":
                request_categorie = traducere_produse(request_categorie)
            preferinte["Produsele"] = request_categorie
            mesaj = request_categorie
            # mesaj += " . <br><br> Care produs te intereseaza ? "
            mesaj = format_products_list_with_intro(mesaj)
            if language_saved == "RU":
                mesaj += "<br><br> 📚 Хотите узнать информацию и про другие категории или 🚀 хотите сделать заказ? 🤔"
            elif language_saved == "RO":
                mesaj += " . <br><br> 📚 Doriti să aflați informații și despre alte categorii sau 🚀 doriți să comandați? 🤔"

            return jsonify({"message": mesaj})
    elif is_fuzzy_match(interests,"china"):
        if "mat" in interests.lower():
            categoria_aleasa = "china mat 0.40"
            preferinte["Categorie"] = categoria_aleasa
            request_categorie = categoria_preferata(categoria_aleasa)
            preferinte["Produsele_RO"] = request_categorie
            if language_saved == "RU":
                request_categorie = traducere_produse(request_categorie)
                print(request_categorie)
            preferinte["Produsele"] = request_categorie
            mesaj = request_categorie

            mesaj = format_products_list_with_intro(mesaj)
            if language_saved == "RU":
                mesaj += "<br><br> 📚 Хотите узнать информацию и про другие категории или 🚀 хотите сделать заказ? 🤔"
            elif language_saved == "RO":
                mesaj += " . <br><br> 📚 Doriti să aflați informații și despre alte categorii sau 🚀 doriți să comandați? 🤔"
            return jsonify({"message": mesaj})



    if categoria_aleasa == "NU":
        if language_saved == "RO":
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
                "<br><br>🏠🔨 Suntem gata să te ajutăm cu tot ce ține de acoperișuri! <br><br>"
                "📋 Te rugăm să scrii <strong>denumirea exactă a categoriei</strong> din listă pentru a putea trece la pasul următor. 🔽"
            )

            preferinte['interes_salvat'] = ""
        elif language_saved == "RU":
            prompt = (
                f"Пользователь выбрал категорию: '{interests}'.\n\n"
                "Никогда не приветствуй словами вроде «Привет», избегай вводных фраз, так как мы уже общаемся и знакомы. "
                "Напиши вежливое, дружелюбное и естественное сообщение, которое:\n"
                "1. Кратко отвечает на то, что сказал пользователь.\n"
                "2. Сообщение должно быть коротким, тёплым, эмпатичным и дружелюбным.\n"
                "Не больше 2-3 предложений.\n"
                "Не используй кавычки и не объясняй, что делаешь — пиши только финальный текст сообщения."
            )
            messages = [{"role": "system", "content": prompt}]
            mesaj = ask_with_ai(messages).strip()
            mesaj += (
                "<br><br>🏠🔨 Мы готовы помочь вам со всем, что связано с крышами! <br><br>"
                "📋 Напишите <strong>точное название категории</strong> из списка, чтобы мы могли перейти к следующему шагу. 🔽"
            )

            preferinte['interes_salvat'] = ""

    elif categoria_aleasa == "comandă":
        if language_saved == "RO":
            mesaj = "🌟 Mulțumim că ai ales KROV! Pentru a putea procesa comanda ta cât mai rapid, te rugăm frumos să ne spui numele și prenumele tău. 😊"
        elif language_saved == "RU":
            mesaj  = "🌟 Спасибо, что выбрали KROV! Чтобы мы могли как можно быстрее обработать ваш заказ, пожалуйста, укажите <strong>ваше имя и фамилию</strong>. 😊"
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
                if language_saved == "RO":
                    mesaj = (
                        f"Am găsit mai multe variante pentru '{categoria_aleasa.split()[0]}':\n\n"
                        f"{options_list}\n\n"
                        "Te rog să alegi varianta exactă care te interesează. 😊"
                    )
                elif language_saved == "RU":
                    mesaj = (
                        f"Я нашёл несколько вариантов для '{categoria_aleasa.split()[0]}':\n\n"
                        f"{options_list}\n\n"
                        "Пожалуйста, выберите именно тот вариант, который вас интересует. 😊"
                    )


                preferinte['counter'] = 1
            else:
                preferinte["Categorie"] = categoria_aleasa
                request_categorie = categoria_preferata(categoria_aleasa)
                preferinte["Produsele_RO"] = request_categorie
                if language_saved == "RU":
                    request_categorie = traducere_produse(request_categorie)
                preferinte["Produsele"] = request_categorie
                mesaj = request_categorie
                mesaj = format_products_list_with_intro(mesaj)
                if language_saved == "RU":
                    mesaj += "<br><br> 📚 Хотите узнать информацию и про другие категории или 🚀 хотите сделать заказ? 🤔"
                elif language_saved == "RO":
                    mesaj += " . <br><br> 📚 Doriti să aflați informații și despre alte categorii sau 🚀 doriți să comandați? 🤔"
        
        else:
            preferinte["Categorie"] = categoria_aleasa
            request_categorie = categoria_preferata(categoria_aleasa)
            preferinte["Produsele_RO"] = request_categorie
            if language_saved == "RU":
                request_categorie = traducere_produse(request_categorie)
            preferinte["Produsele"] = request_categorie
            mesaj = request_categorie
            mesaj = format_products_list_with_intro(mesaj)
            if language_saved == "RU":
                mesaj += "<br><br> 📚 Хотите узнать информацию и про другие категории или 🚀 хотите сделать заказ? 🤔"
            elif language_saved == "RO":
                mesaj += " . <br><br> 📚 Doriti să aflați informații și despre alte categorii sau 🚀 doriți să comandați? 🤔"

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


def construieste_prompt_selectie(produse_similare, language):

    if not produse_similare:
        if language == "RO":
            return "⚠️ Nu există produse similare pentru a selecta."
        else:
            return "⚠️ Нет похожих товаров для выбора."

    if language == "RO":
        prompt = (
            "🔍 Am găsit mai multe produse care se potrivesc cu ce ai scris.\n"
            "👇 Te rog alege unul dintre produsele de mai jos:<br>\n\n"
        )
    else:
        prompt = (
            "🔍 Мы нашли несколько товаров, которые соответствуют вашему запросу.\n"
            "👇 Пожалуйста, выберите один из следующих вариантов:<br>\n\n"
        )

    for i, produs in enumerate(produse_similare, start=1):
        prompt += f"{i}. 🛒 {produs}<br>\n"

    if language == "RO":
        prompt += "\n Scrie **numele exact** al produsului dorit"
    else:
        prompt += "\n Напишите **точное название** нужного вам товара"
    return prompt


def check_product(message, language):
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
        produse_similare = construieste_prompt_selectie(produse_similare, language)
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
    language_saved = data.get("language", "")
    response,lista = check_product(message,language_saved)
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
        "Clientul a trimis un mesaj, în orice limbă. Extrage, te rog, cantitatea numerică exprimată în orice formă. "
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
    try:
        # Încearcă să extragi partea de după ":"
        parti = text.split(":")
        if len(parti) > 1:
            text_parte = parti[1]
        else:
            text_parte = text
        print("aceasta e partea = ", text_parte)

        # Caută număr în partea respectivă
        numere = re.findall(r"(?<![a-zA-Z])(\d+(?:[.,]\d+)?)", text_parte)
        if numere:
            return float(numere[0].replace(",", "."))
        
        # Dacă nu a găsit în partea după ":", încearcă din tot textul
        numere_totale = re.findall(r"(?<![a-zA-Z])(\d+(?:[.,]\d+)?)", text)
        if numere_totale:
            return float(numere_totale[0].replace(",", "."))
        
    except Exception as e:
        print("Eroare la extragere preț:", e)
    
    return None


def print_price(pret_produs, cantitate, produsul_extras, culoare_aleasa, masurare, language):
    print("pret produssss = ", pret_produs)
    total = float(pret_produs) * float(cantitate)
    categorie = preferinte["Categorie"]
    print()
    if language == "RO":
        return (
            f"✅ Comanda ta a fost <strong>înregistrată cu succes</strong>! 🧾🎉<br><br>"
            f"📦 <strong>Categoria:</strong> {categorie}<br>"
            f"📦 <strong>Produs:</strong> {produsul_extras}<br>"
            f"🎨 <strong>Culoare aleasă:</strong> {culoare_aleasa}<br>"
            f"💲 <strong>Preț unitar:</strong> {pret_produs:.2f} MDL<br>"
            f"📐 <strong>Cantitate:</strong> {cantitate} {masurare}<br>"
            f"🧮 <strong>Preț total:</strong> <strong>{total:.2f} MDL</strong><br><br>"
            "📞 Vei fi <strong>contactat în scurt timp</strong> de către echipa noastră pentru confirmare și detalii suplimentare. 🤝<br><br>"
            "🙏 Îți mulțumim pentru încredere! 💚<br><br>"
            "❓ Dacă mai ai întrebări, dorești să afli despre alte produse 🏠 sau vrei să adaugi ceva în comandă, sunt aici să te ajut! 😊"
        )
    else:
        return (
            f"✅ Ваш заказ был <strong>успешно зарегистрирован</strong>! 🧾🎉<br><br>"
            f"📦 <strong>Категория:</strong> {categorie}<br>"
            f"📦 <strong>Товар:</strong> {produsul_extras}<br>"
            f"🎨 <strong>Выбранный цвет:</strong> {culoare_aleasa}<br>"
            f"💲 <strong>Цена за единицу:</strong> {pret_produs:.2f} MDL<br>"
            f"📐 <strong>Количество:</strong> {cantitate} {masurare}<br>"
            f"🧮 <strong>Общая стоимость:</strong> <strong>{total:.2f} MDL</strong><br><br>"
            "📞 В ближайшее время с вами свяжется наша команда для подтверждения и дополнительной информации. 🤝<br><br>"
            "🙏 Спасибо за доверие! 💚<br><br>"
            "❓ Если у вас есть вопросы, хотите узнать о других товарах 🏠 или добавить что-то в заказ, я здесь, чтобы помочь! 😊"
        )






@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    name = data.get("name", "")
    interests = data.get("interests", "")
    message = data.get("message", "")
    language_saved = data.get("language","")
    response = check_response(message)
    print("raspuns = " , response)
    if response == "DA":
        if language_saved == "RO":
            messages = [
                {
                    "role": "user",
                    "content": (
                        "Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
                        "Fa promptul frumos , nu foloseste emoji-uri deloc ( este despre un business de acoperisuri ) , scrie categoriile in '' , gen 'china' , fara '-' in fata"
                        "Esti un chatbot inteligent care creezi un prompt interactiv si frumos pentru user si il intrebi ce produse doreste , din cele de mai jos (trebuie incluse toate in prompt fara RoofArt in fata):"
                        f"Acestea sunt toate categoriile disponibile : {categorii_unice}"
                        "Rogi userul sa raspunda cu denumirea exacta a produsului din lista de categorii"
                    )
                }
            ]
        elif language_saved == "RU":
            messages = [
                {
                    "role": "user",
                    "content": (
                        "Никогда не говори «Привет», никаких вступительных фраз, потому что мы уже ведём разговор и знаем друг друга. "
                        "Сделай подсказку красивой, не используй вообще никаких эмодзи (это про крышный бизнес), пиши категории в '' кавычках, например 'china', без дефиса перед ними. "
                        "Ты — умный чатбот, который создаёт интерактивную и красивую подсказку для пользователя и спрашивает, какие продукты он хочет из следующих (все должны быть включены в подсказку без RoofArt перед ними): "
                        f"Это все доступные категории: {categorii_unice} "
                        "Попроси пользователя ответить точным названием продукта из списка категорий."
                    )
                }
            ]


    elif response == "NU":
        if language_saved == "RO":
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
        else:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Спасибо за разговор! 🙏 Если у вас появятся вопросы или вы захотите узнать больше о наших товарах — "
                        "я всегда здесь, чтобы помочь. 🏠💬\n"
                        "Желаю вам прекрасного дня и успехов в вашем кровельном проекте! ☀️🔨"
                    )
                }
            ]


        messages[0]['content'] += "!!!"
    else:
        if language_saved == "RO":
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
        else:
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"Пользователь написал категорию: '{interests}'.\n\n"
                        "Никогда не начинай с «Привет» или других вступительных фраз — мы уже ведем диалог и знакомы. "
                        "Напиши вежливое, дружелюбное и естественное сообщение, которое:\n"
                        "1. Кратко отвечает на то, что написал пользователь.\n"
                        "2. Затем вежливо попроси его ответить, хочет ли он узнать о другом товаре — Да/Нет."
                    )
                }
            ]

    reply = ask_with_ai(messages, temperature=0.9 , max_tokens= 400)

    pos = reply.rfind("'")
    if pos != -1:
        reply = reply[:pos+1] + "<br><br>" + reply[pos+1:]

    pos = reply.rfind(":")
    if pos != -1:
        reply = reply[:pos+1] + "<br>" + reply[pos+1:]

    reply = format_product_mentions(reply)
    reply = clean_punct_except_numbers(reply)
    

    # reply = response.choices[0].message.content.strip()
    # log_message("AI BOT", reply)
    return jsonify({"reply": reply})

def check_surname_command_ro(command):
    prompt = f"""
    Ești un validator automat inteligent care răspunde STRICT cu "DA" sau "NU" dacă textul conține un nume complet valid de persoană, format din cel puțin două cuvinte consecutive (prenume + nume) SAU (nume + prenume). Textul poate conține și alte cuvinte, dar trebuie să existe o secvență clară de două sau mai multe cuvinte ce pot fi un nume complet.

    Reguli adaptate pentru a fi mai flexibile:
    0. Daca este o intrebare atunci raspunde strict "NU" .
    1. Numele complet trebuie să aibă cel puțin două cuvinte consecutive, fără întreruperi, în orice ordine (prenume + nume SAU nume + prenume).
    2. Cuvintele pot avea majuscule sau minuscule, și pot conține mici greșeli de tastare uzuale (ex: lipsa diacriticelor sau greșeli mici de scriere).
    3. NU accepta cifre, simboluri, emoji, abrevieri sau semne de punctuație în nume.
    4. Numele trebuie să fie format din cuvinte reale valide de prenume și nume proprii, cu un nivel rezonabil de toleranță la mici erori.
    5. NU accepta nume incomplete (un singur cuvânt), cuvinte izolate sau răspunsuri vagi.
    6. Textul poate fi în orice limbă.
    7. Răspunde STRICT cu "DA" sau "NU", fără alte explicații.

    Exemple valide (răspunde cu DA):
    - mă numesc daniel brinza
    - ma numesc daniel brinza
    - brinza daniel
    - numele meu este elena popescu
    - eu sunt andrei mihai
    - da, mă cheamă maria ionescu
    - acesta este numele meu: vlad stoica
    - numele complet este ana maria popa
    - sunt ionel gheorghe
    - mă prezint: george enescu
    - numele meu complet este cristina dumitrescu
    - mă numesc alexandru ivan
    - eu mă numesc gabi nistor
    - sunt robert constantinescu
    - mă cheamă ioana mariuța
    - numele meu este georgiana bratu
    - pot să mă prezint: elena vasilescu


    Exemple invalide (răspunde cu NU):
    - daniel
    - popescu
    - 😊😊😊
    - 12345
    - nu știu
    - cum te numești?
    - numele meu este ion
    - mă numesc!
    - numele meu este a. b.
    - numele meu este ion2 popescu!
    - @maria ionescu
    - ion! popescu?
    - ion😊 brinza

    Text de verificat:
    \"\"\"{command}\"\"\"

    Răspuns STRICT:
    """

    messages = [{"role": "system", "content": prompt}]

    response1 = ask_with_ai(messages,temperature=1 ,max_tokens=5).strip().upper()

    if response1 == "NU":
        response1 = ask_with_ai(messages,temperature=1 ,max_tokens=5).strip().upper()

    if response1 == "DA":
        return "DA"
    else:
        return "NU"




def check_surname_command_ru(command):
    prompt = f"""
    Ты — умный автоматический валидатор, который ОТВЕЧАЕТ СТРОГО "ДА" или "НЕТ", если в тексте есть полное корректное имя человека, состоящее минимум из двух подряд идущих слов (имя + фамилия) ИЛИ (фамилия + имя). В тексте могут быть и другие слова, но должна быть четкая последовательность из двух или более слов, которые могут быть полным именем.

    Правила с адаптацией для большей гибкости:
    0. Если это вопрос, отвечай строго "НЕТ".
    1. Полное имя должно состоять минимум из двух подряд идущих слов, без пропусков, в любом порядке (имя + фамилия ИЛИ фамилия + имя).
    2. Слова могут быть с заглавными или строчными буквами и могут содержать небольшие орфографические ошибки (например, отсутствие ударений или мелкие опечатки).
    3. НЕ принимай цифры, символы, эмодзи, сокращения или знаки препинания в имени.
    4. Имя должно состоять из реальных корректных слов, соответствующих именам и фамилиям, с разумной толерантностью к небольшим ошибкам.
    5. НЕ принимай неполные имена (одно слово), отдельные слова или неопределённые ответы.
    6. Текст может быть на любом языке.
    7. Отвечай СТРОГО "ДА" или "НЕТ", без других объяснений.

    Примеры корректных (отвечать "ДА"):
    - меня зовут данил брынза
    - я данил брынза
    - брынза данил
    - моё имя елена попеску
    - я андрей михай
    - да, меня зовут мария ионеску
    - это моё имя: влад стойка
    - полное имя ана мария попа
    - я ионел гыорге
    - представляюсь: георгий энеску
    - полное имя кристина думитреску
    - меня зовут александр иван
    - я габи нистор
    - я роберт константинеску
    - меня зовут иоана мариуца
    - моё имя георгиана брачу
    - могу представиться: елена василеску

    Примеры некорректных (отвечать "НЕТ"):
    - данил
    - брынза
    - 😊😊😊
    - 12345
    - не знаю
    - как тебя зовут?
    - моё имя ион
    - меня зовут!
    - моё имя а. б.
    - моё имя ион2 попеску!
    - @мария ионеску
    - ион! попеску?
    - ион😊 брынза

    Текст для проверки:
    \"\"\"{command}\"\"\"

    СТРОГО ответ:
    """

    messages = [{"role": "system", "content": prompt}]

    # Первая проверка
    response1 = ask_with_ai(messages, max_tokens=5).strip().upper()

    if response1 == "НЕТ":
        response1 = ask_with_ai(messages, max_tokens=5).strip().upper()
    

    # Возвращаем "ДА", если оба ответа "ДА", иначе "НЕТ"
    if response1 == "ДА":
        return "DA"
    else:
        return "NU"


@app.route("/comanda", methods=["POST"])
def comanda():
    data = request.get_json()
    name = data.get("name", "")
    interests = data.get("interests", "")
    message = data.get("message", "")
    language_saved = data.get("language","")
    print(message)
    if language_saved == "RO":
        check_sur = check_surname_command_ro(message)
    else:
        check_sur = check_surname_command_ru(message)

    print("nume prenume response = " , check_sur)

    if check_sur == "DA":
        preferinte["Nume_Prenume"] = message
        if language_saved == "RO":
            reply = (
                "😊 Mulțumim! Ai un nume frumos! 💬<br>"
                "Ne-ai putea lăsa și un număr de telefon pentru a te putea contacta? 📞<br>"
                "Te rugăm să te asiguri că numărul începe cu <strong>0</strong> sau <strong>+373</strong>. ✅"
            )
        else:
            reply = (
                "😊 Спасибо! У тебя красивое имя! 💬<br>"
                "Не мог бы ты также оставить свой номер телефона, чтобы мы могли с тобой связаться? 📞<br>"
                "Пожалуйста, убедись, что номер начинается с <strong>0</strong> или <strong>+373</strong>. ✅"
            )

    else:
        if language_saved == "RO":
            prompt_ai = (
                f"Nu te saluta niciodata pentru ca deja avem o discutie.\n"
                f"Acționează ca un asistent prietenos și politicos.\n"
                f"Răspunde la următorul mesaj ca și cum ai fi un agent uman care vrea să ajute clientul.\n"
                f"Răspunsul trebuie să fie cald, clar și la obiect. "
                f'Mesajul clientului: "{message}"\n\n'
                f"Răspuns:"
            )
        else:
            prompt_ai = (
                f"Никогда не начинай с приветствия, так как у нас уже идет разговор.\n"
                f"Веди себя как дружелюбный и вежливый помощник.\n"
                f"Ответь на следующее сообщение так, как будто ты человек-агент, который хочет помочь клиенту.\n"
                f"Ответ должен быть теплым, понятным и по делу.\n"
                f'Сообщение клиента: "{message}"\n\n'
                f"Ответ:"
            )

        messages = [{"role": "system", "content": prompt_ai}]
        reply = ask_with_ai(messages, temperature=0.9 , max_tokens= 150)
        
        if language_saved =="RO":
            reply += "<br><br>📞 Introdu, te rog, <strong>doar</strong> numele si prenumele – este foarte important pentru a trece la pasul următor. Mulțumim ! 🙏😊"
        else:
            reply += "<br><br>📞 Пожалуйста, укажи <strong>только</strong> имя и фамилию — это очень важно, чтобы перейти к следующему шагу. Благодарим! 🙏😊"
    
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
    language_saved = data.get("language", "")

    print("message = ", message)
    valid = check_numar(message)

    print("valid = " , valid)
    if valid == "NU":
        if language_saved == "RO":
            prompt = (
                "Nu te saluta pentru ca deja avem o discutie.\n"
                "Acționează ca un asistent prietenos și politicos.\n"
                "Răspunde natural și cald la mesajul clientului.\n"
                f"Mesaj client: \"{message}\"\n\n"
                "Răspuns:"
            )
        else:
            prompt = (
                "Не приветствуй, так как у нас уже идет разговор.\n"
                "Веди себя как дружелюбный и вежливый помощник.\n"
                "Отвечай естественно и тепло на сообщение клиента.\n"
                f"Сообщение клиента: \"{message}\"\n\n"
                "Ответ:"
            )


        messages = [{"role": "system", "content": prompt}]
        ai_reply = ask_with_ai(messages, max_tokens=150)
        if language_saved == "RO":
            ai_reply += "<br><br> 🙏 Te rog să introduci un număr de telefon valid pentru a putea continua. 📞"
        else:
            ai_reply += "<br><br> 🙏 Пожалуйста, введи действительный номер телефона, чтобы мы могли продолжить. 📞"


        return jsonify({"reply": ai_reply})

    print(message)
    nr, status = extrage_si_valideaza_numar(message)
    print(f"valid = {status}")


    if status != "VALID":
        if language_saved == "RO":
            reply = (
                "🚫 Numărul acesta nu pare corect.\n"
                "Te rog să introduci un număr valid care începe cu `0` sau `+373`. 📞"
            )
        else:
            reply = (
                "🚫 Этот номер кажется некорректным.\n"
                "Пожалуйста, введи действительный номер, начинающийся с `0` или `+373`. 📞"
            )


    else:
        preferinte["Numar_Telefon"] = message
        if language_saved == "RO":
            messages = [
                {
                    "role": "user",
                    "content": (
                        "Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
                        "Fa promptul frumos , nu foloseste emoji-uri deloc ( este despre un business de acoperisuri ) , scrie categoriile in '' , gen 'china' , fara '-' in fata"
                        "Esti un chatbot inteligent care creezi un prompt interactiv si frumos pentru user si il intrebi ce produse doreste , din cele de mai jos (trebuie incluse toate in prompt fara RoofArt in fata):"
                        f"Acestea sunt toate categoriile disponibile : {categorii_unice}"
                        "Rogi userul sa raspunda cu denumirea exacta a produsului din lista de categorii"
                    )
                }
            ]
        elif language_saved == "RU":
            messages = [
                {
                    "role": "user",
                    "content": (
                        "Никогда не говори «Привет», никаких вступительных фраз, потому что мы уже ведём разговор и знаем друг друга. "
                        "Сделай подсказку красивой, не используй вообще никаких эмодзи (это про крышный бизнес), пиши категории в '' кавычках, например 'china', без дефиса перед ними. "
                        "Ты — умный чатбот, который создаёт интерактивную и красивую подсказку для пользователя и спрашивает, какие продукты он хочет из следующих (все должны быть включены в подсказку без RoofArt перед ними): "
                        f"Это все доступные категории: {categorii_unice} "
                        "Попроси пользователя ответить точным названием продукта из списка категорий."
                    )
                }
            ]

        reply = ask_with_ai(messages, temperature=0.9 , max_tokens= 400)

        pos = reply.rfind("'")
        if pos != -1:
            reply = reply[:pos+1] + "<br><br>" + reply[pos+1:]

        pos = reply.rfind(":")
        if pos != -1:
            reply = reply[:pos+1] + "<br>" + reply[pos+1:]

        reply = format_product_mentions(reply)
        reply = clean_punct_except_numbers(reply)

    return jsonify({"reply": reply})

@app.route("/categorie", methods=["POST"])
def categorie():
    data = request.get_json()
    name = data.get("name", "")
    interests = data.get("message", "")
    language_saved = data.get("language", "")
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
            preferinte["Produsele_RO"] = request_categorie
            if language_saved == "RU":
                request_categorie = traducere_produse(request_categorie)

            preferinte["Produsele"] = request_categorie
            mesaj = request_categorie
            mesaj = format_products_list_with_intro(mesaj)
            # mesaj += " . <br><br> Care produs te intereseaza ? "
            if language_saved == "RO":
                mesaj += (
                    "🔍 Dacă ai găsit ceva interesant mai sus, te rog alege <strong>exact</strong> produsul dorit din listă pentru a continua! 💬<br><br>"
                    "✍️ Scrie numele produsului <strong>exact așa cum apare mai sus</strong> și te voi ajuta imediat! 🚀"
                )
            else:
                mesaj += (
                    "🔍 Если ты нашёл что-то интересное выше, пожалуйста, выбери <strong>именно</strong> тот товар из списка, чтобы продолжить! 💬<br><br>"
                    "✍️ Напиши название товара <strong>точно так, как указано выше</strong>, и я сразу помогу тебе! 🚀"
                )

            return jsonify({"message": mesaj})
        elif is_fuzzy_match(interests, "alzn"):
            categoria_aleasa = "ds 0.40 alzn"
            preferinte["Categorie"] = categoria_aleasa
            request_categorie = categoria_preferata(categoria_aleasa)
            preferinte["Produsele_RO"] = request_categorie
            if language_saved == "RU":
                request_categorie = traducere_produse(request_categorie)

            preferinte["Produsele"] = request_categorie
            mesaj = request_categorie
            mesaj = format_products_list_with_intro(mesaj)
            # mesaj += " . <br><br> Care produs te intereseaza ? "
            if language_saved == "RO":
                mesaj += (
                    "🔍 Dacă ai găsit ceva interesant mai sus, te rog alege <strong>exact</strong> produsul dorit din listă pentru a continua! 💬<br><br>"
                    "✍️ Scrie numele produsului <strong>exact așa cum apare mai sus</strong> și te voi ajuta imediat! 🚀"
                )
            else:
                mesaj += (
                    "🔍 Если ты нашёл что-то интересное выше, пожалуйста, выбери <strong>именно</strong> тот товар из списка, чтобы продолжить! 💬<br><br>"
                    "✍️ Напиши название товара <strong>точно так, как указано выше</strong>, и я сразу помогу тебе! 🚀"
                )
            return jsonify({"message": mesaj})
        
    elif is_fuzzy_match(interests,"china"):
        if "mat" in interests.lower():
            categoria_aleasa = "china mat 0.40"
            preferinte["Categorie"] = categoria_aleasa
            request_categorie = categoria_preferata(categoria_aleasa)
            preferinte["Produsele_RO"] = request_categorie
            if language_saved == "RU":
                request_categorie = traducere_produse(request_categorie)

            preferinte["Produsele"] = request_categorie
            
            mesaj = request_categorie
            mesaj = format_products_list_with_intro(mesaj)
            # mesaj += " . <br><br> Care produs te intereseaza ? "
            if language_saved == "RO":
                mesaj += (
                    "🔍 Dacă ai găsit ceva interesant mai sus, te rog alege <strong>exact</strong> produsul dorit din listă pentru a continua! 💬<br><br>"
                    "✍️ Scrie numele produsului <strong>exact așa cum apare mai sus</strong> și te voi ajuta imediat! 🚀"
                )
            else:
                mesaj += (
                    "🔍 Если ты нашёл что-то интересное выше, пожалуйста, выбери <strong>именно</strong> тот товар из списка, чтобы продолжить! 💬<br><br>"
                    "✍️ Напиши название товара <strong>точно так, как указано выше</strong>, и я сразу помогу тебе! 🚀"
                )
            
            return jsonify({"reply": mesaj})
        

    if categoria_aleasa == "NU":
        if language_saved == "RO":
            prompt = (
                f"Utilizatorul a scris categoria: '{interests}'.\n\n"
                "Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
                "Scrie un mesaj politicos, prietenos și natural, care:\n"
                "1. Răspunde pe scurt la ceea ce a spus utilizatorul . "
                "2. Mesajul să fie scurt, cald, empatic și prietenos. "
                "Nu mai mult de 2-3 propoziții.\n"
                "Nu folosi ghilimele și nu explica ce faci – scrie doar mesajul final pentru utilizator."
            )
            
        else:
            prompt = (
                f"Пользователь указал категорию: '{interests}'.\n\n"
                "Никогда не начинай с «Привет» или других вводных фраз, так как мы уже ведём разговор и знакомы. "
                "Напиши вежливое, дружелюбное и естественное сообщение, которое:\n"
                "1. Кратко отвечает на сказанное пользователем.\n"
                "2. Сообщение должно быть коротким, тёплым, эмпатичным и дружелюбным. "
                "Не более 2-3 предложений.\n"
                "Не используй кавычки и не объясняй, что ты делаешь — пиши только финальное сообщение."
            )


        messages = [{"role": "system", "content": prompt}]
        mesaj = ask_with_ai(messages).strip()
        if language_saved == "RO":
            mesaj += (
                "<br><br>🏠🔨 Suntem gata să te ajutăm cu tot ce ține de acoperișuri! "
                "Te rog să alegi clar dacă dorești să afli detalii despre un <em>produs</em> sau vrei să plasezi o <em>comandă</em>. "
                "😊🛠️"
            )
        else:
            mesaj += (
                "<br><br>🏠🔨 Мы готовы помочь вам со всем, что связано с крышами! "
                 "📋 Напишите <strong>точное название категории</strong> из списка, чтобы мы могли перейти к следующему шагу. 🔽"
            )
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
                if language_saved == "RO":
                    mesaj = (
                        f"Am găsit mai multe variante pentru '{categoria_aleasa.split()[0]}':\n\n"
                        f"{options_list}\n\n"
                        "Te rog să alegi varianta exactă care te interesează. 😊"
                    )
                else:
                    mesaj = (
                        f"Мы нашли несколько вариантов для '{categoria_aleasa.split()[0]}':\n\n"
                        f"{options_list}\n\n"
                        "Пожалуйста, выбери точный вариант, который тебя интересует. 😊"
                    )

                    
                preferinte['counter'] = 1
                
            else:
                preferinte["Categorie"] = categoria_aleasa
                request_categorie = categoria_preferata(categoria_aleasa)
                preferinte["Produsele_RO"] = request_categorie
                if language_saved == "RU":
                    request_categorie = traducere_produse(request_categorie)

                preferinte["Produsele"] = request_categorie
                mesaj = request_categorie
                mesaj = format_products_list_with_intro(mesaj)
                # mesaj += " . <br><br> Care produs te intereseaza ? "
                if language_saved == "RO":
                    mesaj += (
                        "🔍 Dacă ai găsit ceva interesant mai sus, te rog alege <strong>exact</strong> produsul dorit din listă pentru a continua! 💬<br><br>"
                        "✍️ Scrie numele produsului <strong>exact așa cum apare mai sus</strong> și te voi ajuta imediat! 🚀"
                    )
                else:
                    mesaj += (
                        "🔍 Если ты нашёл что-то интересное выше, пожалуйста, выбери <strong>именно</strong> тот товар из списка, чтобы продолжить! 💬<br><br>"
                        "✍️ Напиши название товара <strong>точно так, как указано выше</strong>, и я сразу помогу тебе! 🚀"
                    )

        else:
            preferinte["Categorie"] = categoria_aleasa
            request_categorie = categoria_preferata(categoria_aleasa)
            preferinte["Produsele_RO"] = request_categorie
            if language_saved == "RU":
                request_categorie = traducere_produse(request_categorie)

            preferinte["Produsele"] = request_categorie
            mesaj = request_categorie
            mesaj = format_products_list_with_intro(mesaj)
            # mesaj += " . <br><br> Care produs te intereseaza ? "
            if language_saved == "RO":
                mesaj += (
                    "🔍 Dacă ai găsit ceva interesant mai sus, te rog alege <strong>exact</strong> produsul dorit din listă pentru a continua! 💬<br><br>"
                    "✍️ Scrie numele produsului <strong>exact așa cum apare mai sus</strong> și te voi ajuta imediat! 🚀"
                )
            else:
                mesaj += (
                    "🔍 Если ты нашёл что-то интересное выше, пожалуйста, выбери <strong>именно</strong> тот товар из списка, чтобы продолжить! 💬<br><br>"
                    "✍️ Напиши название товара <strong>точно так, как указано выше</strong>, и я сразу помогу тебе! 🚀"
                )


    print("mesaj = " , mesaj)
    return jsonify({"reply": mesaj})


def genereaza_prompt_produse(rezultat, categorie, language_saved):
    if not rezultat:
        if language_saved == "RO":
            return "❌ Nu am găsit produse pentru categoria selectată."
        else:
            return "❌ Товары для выбранной категории не найдены."

    lista_formatata = ""
    for idx, prod in enumerate(rezultat, 1):
        nume = prod['produs'].replace("**", "")  # elimină markdown
        pret = prod['pret']
        lista_formatata += f"🔹 <strong>{nume}</strong> — 💸 {pret}<br />"

    if language_saved == "RO":
        prompt = (
            f"🔍 La cererea ta, am găsit următoarele produse din categoria <strong>{categorie}</strong>:<br /><br />"
            f"{lista_formatata}<br />"
            "🛒 Te rog să alegi <strong>exact produsul dorit</strong> din listă pentru a ști ce preferi. Mulțumesc! 🙏"
        )
    else:
        prompt = (
            f"🔍 По вашему запросу найдены следующие товары из категории <strong>{categorie}</strong>:<br /><br />"
            f"{lista_formatata}<br />"
            "🛒 Пожалуйста, выберите <strong>точно нужный товар</strong> из списка, чтобы я знал(а), что вы предпочитаете. Спасибо! 🙏"
        )


    return prompt


preferinte["Produs_Ales"] = ""
@app.route("/produs", methods=["POST"])
def produs():
    data = request.get_json()
    name = data.get("name", "")
    interests = data.get("message", "")
    language_saved = data.get("language", "")

    produse = preferinte["Produsele"]
    produse_ro = preferinte["Produsele_RO"]
    if "nu sunt disponibile" in produse_ro.lower():
        culori = False
    else:
        culori = True
    

    rezultat = function_check_product(interests , preferinte["Produsele"], language_saved)
    print("rezultat = " , rezultat)

    if rezultat == "NU":
        length_check = 0
    else:
        length_check = len(rezultat)

    if length_check == 1 :
        preferinte["Produs_Ales"] = rezultat[0]["produs"]
        if culori:
            if language_saved == "RO":
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
                        "✅ Спасибо за ваш выбор! 🛒 Товар успешно добавлен. 💬<br><br>"
                        "🎨 Теперь, пожалуйста, выберите <strong>желаемый цвет</strong> для этого товара.<br>"
                        "📋 Напишите точное название цвета, а я позабочусь обо всем остальном! 😊"
                    )
                })
        else:
            if language_saved == "RO":
                return jsonify({
                    "reply": (
                        "✅ Mulțumim pentru alegerea ta! 🛒 Produsul a fost notat cu succes. 💬<br><br>"
                        "📋 Nu avem culorile disponibile , dar te rog sa imi zici culoarea preferata! 😊"
                    )
                })
            else:
                return jsonify({
                    "reply": (
                        "✅ Спасибо за ваш выбор! 🛒 Товар успешно добавлен. 💬<br><br>"
                        "📋 У нас нет списка доступных цветов, но, пожалуйста, напишите предпочитаемый цвет! 😊"
                    )
                })

                
    elif length_check > 1:
        reply = genereaza_prompt_produse(rezultat, preferinte["Categorie"], language_saved)
        return jsonify({"reply": reply})
    
    else:
        if language_saved == "RO":
            prompt = (
                "Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
                "Scrie un mesaj politicos, prietenos și natural, care:\n"
                f"Răspunde pe scurt la ceea ce a spus utilizatorul {interests}.\n"
                "2. Mesajul să fie scurt, cald, empatic și prietenos. "
                "Nu mai mult de 2-3 propoziții.\n"
                "Nu folosi ghilimele și nu explica ce faci – scrie doar mesajul pentru utilizator."
            )
        else:
            prompt = (
                "Никогда не начинай с «Здравствуйте» или других вводных фраз, потому что разговор уже ведётся и мы знакомы. "
                "Напиши вежливое, дружелюбное и естественное сообщение, которое:\n"
                f"1. Кратко отвечает на то, что написал пользователь: {interests}.\n"
                "2. Сообщение должно быть тёплым, эмпатичным и дружелюбным. "
                "Не более 2–3 предложений.\n"
                "Не используй кавычки и не объясняй, что ты делаешь — просто напиши сообщение для пользователя."
            )

        messages = [{"role": "system", "content": prompt}]
        reply = ask_with_ai(messages).strip()
        if language_saved == "RO":
            reply +="<br><br>📋 Te rog să alegi un <strong>produs valid din listă</strong> ✏️ scriindu-i <strong>denumirea exactă</strong>.<br> 🔍 Doar așa putem continua mai departe cu procesul comenzii! 😊🔧🏠"
        else:
            reply += "<br><br>📋 Пожалуйста, выбери <strong>действительный товар из списка</strong> ✏️, написав его <strong>точное название</strong>.<br> 🔍 Только так мы сможем продолжить оформление заказа! 😊🔧🏠"


    return jsonify({"reply": reply})



def ask_with_ai_3(messages , temperature = 0.3 , max_tokens = 150):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()



def verifica_culoare_cu_ai(interests, culori, language):
    if language == "RO":
        prompt = (
            f"Ești un asistent inteligent care verifică dacă mesajul de mai jos conține o culoare exactă sau un sinonim direct al unei culori din lista de mai jos.\n\n"
            f"Culorile disponibile sunt:\n{culori}\n\n"
            f"Mesajul utilizatorului:\n\"{interests}\"\n\n"
            "1. Dacă mesajul corespunde exact unei singure culori din listă sau este un sinonim direct clar, răspunde DOAR cu acea culoare.\n"
            "2. Dacă mesajul poate însemna mai multe culori (ex: 'gri' se potrivește la 3 variante), răspunde strict cu 'AMBIGUU'.\n"
            "3. Dacă mesajul nu conține nicio culoare exactă sau sinonim direct pentru o culoare din listă, răspunde cu 'NU'.\n\n"
            "Nu explica nimic. Nu folosi ghilimele. Răspunsul trebuie să fie fie o culoare, fie 'AMBIGUU', fie 'NU'."
        )
    else:
        prompt = (
            f"Ты — интеллектуальный помощник, который проверяет, содержит ли сообщение ниже допустимый цвет или его синоним, ИМЕННО из списка доступных цветов.\n\n"
            f"Доступные цвета:\n{culori}\n\n"
            f"Сообщение пользователя:\n\"{interests}\"\n\n"
            "1. Если сообщение точно совпадает с одним цветом из списка, ответь ТОЛЬКО этим цветом.\n"
            "2. Если сообщение может относиться к нескольким цветам (например, 'серый' подходит под 3 варианта), ответь строго 'AMBIGUU'.\n"
            "3. Если сообщение не совпадает ни с одним цветом и не содержит его точный синоним — ответь 'NU'.\n\n"
            "Не объясняй. Не используй кавычки. Ответ должен быть либо цвет, либо 'AMBIGUU', либо 'NU'."
        )



    messages = [{"role": "user", "content": prompt}]
    return ask_with_ai(messages, temperature=0.3, max_tokens=20)


def verifica_culoare_generala_cu_ai(interests):
    if language_saved == "RO":
        prompt = (
            "Ești un asistent care detectează dacă un mesaj conține o denumire validă de culoare, chiar și generică.\n\n"
            f"Mesajul utilizatorului:\n\"{interests}\"\n\n"
            "Dacă mesajul conține o culoare validă (de exemplu: roșu, verde, turcoaz închis, alb mat, maro lucios etc.), "
            "răspunde DOAR cu denumirea culorii așa cum apare ea în mesaj.\n"
            "Dacă NU există nicio culoare validă, răspunde strict cu 'NU'.\n\n"
            "Nu explica nimic. Nu folosi ghilimele. Nu adăuga alt text."
        )
    else:
        prompt = (
            "Ты — ассистент, который определяет, содержит ли сообщение название действительного цвета, даже общего.\n\n"
            f"Сообщение пользователя:\n\"{interests}\"\n\n"
            "Если сообщение содержит действительное название цвета (например: красный, зелёный, тёмно-бирюзовый, матовый белый, блестящий коричневый и т.д.), "
            "отвечай ТОЛЬКО названием цвета так, как оно встречается в сообщении.\n"
            "Если нет ни одного действительного цвета, ответь строго 'NU'.\n\n"
            "Не объясняй ничего. Не используй кавычки. Не добавляй никакой другой текст."
        )
        


    messages = [{"role": "user", "content": prompt}]
    return ask_with_ai(messages, temperature=0.2, max_tokens=15)


culor = ""
preferinte["Culoare_Aleasa"] = ""
@app.route("/culoare", methods=["POST"])
def culoare():
    data = request.get_json()
    name = data.get("name", "")
    interests = data.get("message", "")
    language_saved = data.get("language","")
    # produse = preferinte["Produsele"]
    produse = preferinte["Produsele"]
    produse_ro = preferinte["Produsele_RO"]
    culor = ""

    if "nu sunt disponibile" in produse_ro.lower():
        culori = False
    else:
        culori = True

    if culori:
        produse_split = preferinte["Produsele_RO"].split("Culori disponibile:")
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
            print("lista_culori : " , lista_culori)
            for c in lista_culori:
                print("-", c)
                culor = culor + c + "\n"
            print("culor" , culor)
            if language_saved == "RU":
                prompt = f"Te rog să traduci în limba rusă doar culorile din {culor}."
                messages = [{"role": "system", "content": prompt}]
                culor = ask_with_ai_3(messages).strip()
                print("culori in culori: = " , culor)

        response = verifica_culoare_cu_ai(interests , culor, language_saved)
        print("verificare culoare = " , response)
        print("NU" in response)
        if "NU" in response:
            if language_saved == "RO":
                prompt = (
                    "Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
                    "Scrie un mesaj politicos, prietenos și natural, care:\n"
                    f"Răspunde pe scurt la ceea ce a spus utilizatorul {interests}.\n"
                    "2. Mesajul să fie scurt, cald, empatic și prietenos. "
                    "Nu mai mult de 2-3 propoziții.\n"
                    "Nu folosi ghilimele și nu explica ce faci – scrie doar mesajul pentru utilizator."
                )
            else:
                prompt = (
                    "Никогда не начинай с «Привет» или других вступительных фраз — мы уже ведем диалог и знакомы. "
                    "Напиши вежливое, дружелюбное и естественное сообщение, которое:\n"
                    f"Кратко отвечает на то, что сказал пользователь: {interests}.\n"
                    "Сообщение должно быть коротким, тёплым, эмпатичным и дружелюбным. "
                    "Не более 2–3 предложений.\n"
                    "Не используй кавычки и не объясняй, что ты делаешь — просто напиши сообщение для пользователя."
                )
                

            messages = [{"role": "system", "content": prompt}]
            reply = ask_with_ai(messages).strip()
            if language_saved == "RO":
                reply += (
                    "<br><br>🎨 Te rog să alegi o <strong>culoare validă</strong> din lista afișată ✏️ "
                    "scriind <strong>numele exact al culorii</strong>.<br><br>🔍 Doar așa putem trece la etapa finală a comenzii tale! 🧾🚀😊"
                )
            else:
                reply += (
                    "<br><br>🎨 Пожалуйста, выбери <strong>валидный цвет</strong> из показанного списка ✏️ "
                    "и напиши <strong>точное название цвета</strong>.<br><br>🔍 Только так мы сможем перейти к финальному этапу твоего заказа! 🧾🚀😊"
                )
            
            return jsonify({"reply": reply})
        if response == "AMBIGUU":
            if language_saved == "RO":
                reply = (
                    "🔍 Am observat că ai menționat o culoare care poate avea mai multe nuanțe sau variante. <br><br>"
                    "🎨 Te rog să alegi <strong>exact una</strong> dintre variantele afișate anterior și să scrii numele complet pentru a putea continua comanda. 🧾😊"
                )
            else:
                reply = (
                    "🔍 Я заметил, что ты упомянул цвет, который может иметь несколько оттенков или вариантов. <br><br>"
                    "🎨 Пожалуйста, выбери <strong>именно один</strong> из показанных ранее вариантов и напиши полное название, чтобы мы могли продолжить заказ. 🧾😊"
                )

            return jsonify({"reply": reply})


        else:
            preferinte["Culoare_Aleasa"] = response
            if language_saved == "RO":
                reply = (
                    f"🖌️ Culoarea a fost înregistrată cu succes! ✅<br><br>"
                    "📦 Te rog acum să îmi spui <strong>cantitatea dorită</strong> pentru acest produs, în metri pătrați sau metri liniari – cum preferi tu. 📐🧮<br>"
                    "💬 Aștept mesajul tău pentru a putea continua comanda. 😊"
                )
            else:
                reply = (
                    f"🖌️ Цвет успешно зарегистрирован! ✅<br><br>"
                    "📦 Пожалуйста, теперь укажи <strong>желаемое количество</strong> для этого товара в квадратных метрах или погонных метрах — как тебе удобнее. 📐🧮<br>"
                    "💬 Жду твоё сообщение, чтобы продолжить заказ. 😊"
                )

            return jsonify({"reply": reply})
    else:
        
        response = verifica_culoare_generala_cu_ai(interests, language_saved)

        if response == "НЕТ":
            response == "NU"
        elif response == "ДА":
            response == "DA"

        
        if response == "NU":
            if language_saved == "RO":
                prompt = (
                    "Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
                    "Scrie un mesaj politicos, prietenos și natural, care:\n"
                    f"Răspunde pe scurt la ceea ce a spus utilizatorul {interests}.\n"
                    "2. Mesajul să fie scurt, cald, empatic și prietenos. "
                    "Nu mai mult de 2-3 propoziții.\n"
                    "Nu folosi ghilimele și nu explica ce faci – scrie doar mesajul pentru utilizator."
                )
            else:
                prompt = (
                    "Никогда не начинай с «Привет» или других вступительных фраз — мы уже ведем диалог и знакомы. "
                    "Напиши вежливое, дружелюбное и естественное сообщение, которое:\n"
                    f"Кратко отвечает на то, что сказал пользователь: {interests}.\n"
                    "Сообщение должно быть коротким, тёплым, эмпатичным и дружелюбным. "
                    "Не более 2–3 предложений.\n"
                    "Не используй кавычки и не объясняй, что ты делаешь — просто напиши сообщение для пользователя."
                )

            messages = [{"role": "system", "content": prompt}]
            reply = ask_with_ai(messages).strip()
            if language_saved == "RO":
                reply += (
                    "<br><br>🎨 Te rog să alegi o <strong>culoare validă</strong> ✏️ "
                    "scriind <strong>numele exact al culorii</strong>.<br><br>🔍 Doar așa putem trece la etapa finală a comenzii tale! 🧾🚀😊"
                )
            else:
                reply += (
                    "<br><br>🎨 Пожалуйста, выбери <strong>действительный цвет</strong> ✏️ "
                    "написав <strong>точное название цвета</strong>.<br><br>🔍 Только так мы сможем перейти к финальному этапу твоего заказа! 🧾🚀😊"
                )
            return jsonify({"reply": reply})

        else:
            preferinte["Culoare_Aleasa"] = response
            if language_saved == "RO":
                reply = (
                    f"🖌️ Culoarea a fost înregistrată cu succes! ✅<br><br>"
                    "📦 Te rog acum să îmi spui <strong>cantitatea dorită</strong> pentru acest produs, în metri pătrați , metri liniari sau foaie – cum preferi tu. 📐🧮<br>"
                    "💬 Aștept mesajul tău pentru a putea continua comanda. 😊"
                )
            else:
                reply = (
                    f"🖌️ Цвет успешно зарегистрирован! ✅<br><br>"
                    "📦 Пожалуйста, теперь укажи <strong>желаемое количество</strong> для этого товара в квадратных метрах или погонных метрах — как тебе удобнее. 📐🧮<br>"
                    "💬 Жду твоё сообщение, чтобы продолжить заказ. 😊"
                )

            return jsonify({"reply": reply})


def extrage_nume_din_text(text):
    prompt = f"""
    Extrage doar numele complet (nume și prenume) din următorul text:
    "{text}"
    
    Returnează doar numele complet cu majuscula pentru ca este nume si prenume, fără explicații sau alte informații.
    """
    messages = [{"role": "system", "content": prompt}]

    response = ask_with_ai(messages , temperature=0.3 , max_tokens=50)

    return response


@app.route("/cantitate", methods=["POST"])
def cantitate():
    masurare = ""
    data = request.get_json()
    name = data.get("name", "")
    interests = data.get("interests", "")
    message = data.get("message", "")
    language_saved = data.get("language","")

    cantitate = este_cantitate_valida(message)

    if cantitate == "NU":
        if language_saved == "RO":
            prompt = (
                "Nu spune niciodată „Salut”, gen toate chestiile introductive, pentru că noi deja ducem o discuție și ne cunoaștem. "
                "Scrie un mesaj politicos, prietenos și natural, care:\n"
                f"Răspunde pe scurt la ceea ce a spus utilizatorul {interests}.\n"
                "2. Mesajul să fie scurt, cald, empatic și prietenos. "
                "Nu mai mult de 2-3 propoziții.\n"
                "Nu folosi ghilimele și nu explica ce faci – scrie doar mesajul pentru utilizator."
            )
        else:
            prompt = (
                "Никогда не говори «Привет», как будто это первое наше общение, ведь мы уже общаемся и знакомы. "
                "Напиши вежливое, дружелюбное и естественное сообщение, которое:\n"
                f"Кратко отвечает на то, что сказал пользователь {interests}.\n"
                "Сообщение должно быть коротким, тёплым, эмпатичным и дружелюбным. "
                "Не больше 2–3 предложений.\n"
                "Не используй кавычки и не объясняй, что делаешь — просто напиши сообщение для пользователя."
            )
            

        messages = [{"role": "system", "content": prompt}]
        reply = ask_with_ai(messages).strip()
        if language_saved == "RO":
            reply += (
                "<br><br>📐 Te rog să îmi spui o <strong>cantitate clară</strong> 😊<br><br>"
                "🧮 Doar așa pot calcula prețul total și înregistra comanda. Mulțumesc!"
            )
        else:
            reply += (
                "<br><br>📐 Пожалуйста, укажи <strong>точное количество</strong> 😊<br><br>"
                "🧮 Только так я смогу рассчитать итоговую цену и оформить заказ. Спасибо!"
            )

        return jsonify({"reply": reply})

    produs_exact = preferinte["Produs_Ales"]
    produsul_extras = check_price(produs_exact)
    if language_saved == "RO":
        if "m2" in produsul_extras:
            masurare = "m2"
        elif "ml" in produsul_extras:
            masurare = "ml"
        elif "foaie" in produsul_extras:
            masurare = "foi"
    else:
        if "м2" in produsul_extras:
            masurare = "m2"
        elif "мл" in produsul_extras:
            masurare = "мл"
        elif "лист" in produsul_extras or "бумаг" in produsul_extras:
            masurare = "foi"

    print("Produsul extras : " , produsul_extras)
    pret_produs = extrage_total_din_text(produsul_extras)
    print("pret produs cantitate = ",pret_produs)

    nume_prenume_corect = extrage_nume_din_text(preferinte["Nume_Prenume"])
    preferinte["Nume_Prenume"] = nume_prenume_corect
    total = float(pret_produs) * float(cantitate)

    mesaj_telegram = (
        f"👤 Nume Prenume: {nume_prenume_corect} \n"
        f"📞 Numar de telefon: {preferinte['Numar_Telefon']} \n"
        f"📦 Categoria: {preferinte['Categorie']} \n"
        f"📦 Produs: {produs_exact} \n"
        f"🎨 Culoare aleasă: {preferinte['Culoare_Aleasa']} \n"
        f"💲 Preț unitar: {pret_produs:.2f} MDL \n"
        f"📐 Cantitate: {cantitate} {masurare} \n"
        f"🧮 Preț total: {total:.2f} MDL \n"
    )

    # Encode the message for the URL
    mesaj_encodat = urllib.parse.quote(mesaj_telegram)

    url = f"https://api.telegram.org/bot{TELEGRAM}/sendMessage?chat_id={CHAT_ID}&text={mesaj_encodat}"
    response = requests.get(url)

    print_frumos = print_price(pret_produs,cantitate,produs_exact,preferinte["Culoare_Aleasa"], masurare, language_saved)

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

@app.route("/")
def home():
    return render_template("website.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port,debug=True, use_reloader=False)
