import pandas as pd
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.schema import Document
from dotenv import load_dotenv
from chromadb.config import Settings as ClientSettings
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
import os
import re
import openai


load_dotenv()

llm = ChatOpenAI(temperature=0.2, model="gpt-4o")

df = pd.read_excel("p.xlsx")
df.columns = df.columns.str.strip()
df["Categorie"] = df["Categorie"].ffill()
df = df[df["Nume"].notna() & df["Nume"].str.strip().ne("")]

categorii = df["Categorie"].dropna().unique().tolist()
categorii = [c.strip().replace(":", "").replace("Categorie", "") for c in categorii]
categorii = list(set(categorii))

print("📋 Categoriile disponibile sunt:")
for idx, cat in enumerate(categorii, 1):
    print(f"{idx}. {cat}")


culori_hex = {
    "roșu oxizi": "#6E1414",
    "maro ciocolatiu": "#381819",
    "gri închis": "#2F2F2F",
    "roșu vin": "#800020",
    "verde pădure": "#228B22",
    "gri grafit": "#474A51",
    "gri antracit": "#383E42",
    "negru intens": "#000000",
    "roșu": "#FF0000",
    "albastru cobalt": "#0047AB",
    "alb semilucios": "#F5F5F5"
}



docs = []

categorii_text = "Lista categoriilor disponibile este:\n" + "\n".join([f"- {cat}" for cat in categorii])
docs.append(Document(page_content=categorii_text, metadata={"categorie": "lista_categorii"}))

for categorie, group in df.groupby("Categorie"):
    chunk_text = "\n\n".join([
        f"Nume: {row['Nume']}\nCategorie: {row['Categorie']}\nCulori: {row['Culori']}\nU/M: {row['u/m']}\nPreț client: {row['Prețul Client']}\nPreț listă: {row['Prețul de listă']}"
        for _, row in group.iterrows()
    ])
    docs.append(Document(page_content=chunk_text, metadata={"categorie": categorie}))



embedding_model = OpenAIEmbeddings()

vectorstore = Chroma.from_documents(
    docs,
    embedding_model,
    persist_directory="./vector_index",
    client_settings=ClientSettings(
        anonymized_telemetry=False,
        persist_directory="./vector_index"
    )
)


memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True, output_key='answer')


qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
    chain_type="stuff",
    return_source_documents=True,

)


# while True:
#     question = input("\n❓ Întrebare: ")
#     if question.lower() in ["exit", "quit"]:
#         break

#     result = qa_chain.invoke({"query": question})
#     print("\n📊 Răspuns:\n", result['result'])


#     source_doc = result.get('source_documents', [None])[0]
#     if source_doc:
#         print(f"📂 Categorie folosită pentru răspuns: {source_doc.metadata.get('categorie')}")

def extrage_culori_si_coduri(result1_result, culori_hex):
    # Extrage partea cu lista culorilor
    lista_culori = re.findall(r"(?i)(roșu oxizi|maro ciocolatiu|gri închis|roșu vin|verde pădure|gri grafit|gri antracit|negru intens|roșu|albastru cobalt|alb semilucios)", result1_result, re.IGNORECASE)

    # Normalizează și elimină duplicatele
    culori_gasite = sorted(set([c.lower().strip() for c in lista_culori]))

    # Generează listă HTML cu numele și codul
    culori_formatate = []
    for culoare in culori_gasite:
        hex_code = culori_hex.get(culoare)
        print(hex_code)
        if hex_code:
            # exemplu de bulină colorată + nume
            culori_formatate.append(
                f"<div style='margin-bottom:10px; display: flex; align-items: center;'>"
                f"<span style='display:inline-block;width:35px;height:35px;background:{hex_code};"
                f"border-radius:50%;margin-right:10px;'></span>"
                f"{culoare.title()}</div>"
            )

        else:
            culori_formatate.append(culoare.title())

    return "<br><br><b>Culori disponibile:</b><br>" + " ".join(culori_formatate)


def ask_with_ai(messages , temperature = 0.9 , max_tokens = 100):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()


def ask_with_ai_3(messages , temperature = 0.3 , max_tokens = 100):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()

def categoria_preferata(categoria):
    print(categoria)

    question = f"Vreau sa vad toate produsele din categoria {categoria} cu pretul din lista"
    question1 = f"Vreau sa vad toate culorile din categoria {categoria}"
    
    result = qa_chain.invoke({"query": question})
    result1 = qa_chain.invoke({"query": question1})
    

    if "Roșu" in result1['result'] or "Gri închis" in result1['result'] or "Maro ciocolatiu" in result1['result'] or "Roșu vin" in result1['result'] or "Gri antracit" in result1['result'] or "Albastru cobalt" in result1['result'] or "Alb semilucios" in result1['result']:
        decizie = "DA"
    else:
        decizie = "NU" 

    if decizie == "DA":
        culori_formatate = extrage_culori_si_coduri(result1['result'], culori_hex)
    else:
        culori_formatate = "Culorile nu sunt specificate."

    result_final = result['result'] + "<br><br>" + culori_formatate
    return result_final

# question = f"Vreau sa vad toate produsele din categoria china mat cu pretul din lista"


# result = qa_chain.invoke({"query": question})

# prompt = (
#     f"Te rog să traduci întreg conținutul următor în limba rusă, păstrând fix aceeași structură, formatare și format ca în textul original:\n\n"
#     f"{result['result']}\n\n"
#     "Nu schimba nimic în afară de limbă, păstrează toate elementele, formatările, semnele de punctuație și ordinea exactă."
# )

# messages = [{"role": "user", "content": prompt}]
# translated_text = ask_with_ai_3(messages, temperature=0.7, max_tokens=500)

# print(translated_text)

def traducere_produse(text):
    prompt = (
        f"Te rog să traduci întreg conținutul următor în limba rusă, păstrând fix aceeași structură, formatare și format ca în textul original:\n\n"
        f"{text}\n\n"
        "Nu schimba nimic în afară de limbă, păstrează toate elementele, formatările, semnele de punctuație și ordinea exactă.\n"
        "În special, traduce corect și profesional toate tipurile de acoperișuri, așa cum se folosesc în limbajul tehnic specific domeniului."
    )

    messages = [{"role": "user", "content": prompt}]
    translated_text = ask_with_ai_3(messages, temperature=0, max_tokens=700)

    return translated_text

