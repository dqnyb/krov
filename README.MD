# ChatBot Interactiv cu Flask și OpenAI

Acest proiect este un chatbot interactiv scris în Python, folosind Flask pentru backend și OpenAI GPT-3.5 pentru generarea de mesaje conversaționale.
Botul este capabil să interacționeze prietenos cu utilizatorii, ținând cont de numele și interesele acestora, oferind răspunsuri personalizate, relevante și calde.

## Funcționalități principale

- Salută utilizatorul și cere numele într-un mod prietenos.
- Întreabă despre interese/hobby-uri.
- Generează mesaje personalizate și conversații adaptate la utilizator.
- Loghează toate mesajele într-un fișier Excel (timestamp, expeditor, mesaj).
- API REST pentru integrare cu frontend sau alte aplicații.
- Frontend-ul este realizat folosind HTML, CSS și JavaScript :
    JavaScript a fost folosit pentru:
        + Trimiterea requesturilor către backend folosind fetch() (/start, /interests, /welcome, /chat).
        + Preluarea și afișarea dinamică a răspunsurilor primite de la chatbot.
        + Gestionarea stării conversației (nume, interese, mesaje).
        + Afișarea mesajelor în interfață într-un format stil chat, cu distincție între mesaje de la utilizator și cele de la bot.

- Frontend-ul comunică cu serverul Flask prin metode HTTP (GET/POST) și trimite date în format JSON. Răspunsurile sunt apoi inserate în DOM .

## Structura proiectului

- `chatbot.py` - Codul principal al aplicației Flask.
- `chat-widget.js` - Codul principal web-site (JavaScript).
- `logs/chat_log1.xlsx` - Fișier în care sunt logate mesajele conversației.
- Folosesc biblioteca `openai`, `flask`, `pandas`, `openpyxl` și `flask_cors`.

-> Proiectul se testează fără extensia Live Server din VSCode, deoarece aceasta provoacă refresh automat la orice modificare în ierarhia proiectului (inclusiv în fișierul Excel unde se loghează mesajele). La fiecare mesaj trimis de utilizator, scriptul scrie într-un fișier Excel (chat_log1.xlsx). Dacă Live Server e activ, modificarea fișierului Excel este detectată ca o schimbare în proiect, ceea ce duce automat la un refresh al paginii. Astfel, conversația este întreruptă și pierdută.

-> Testarea se face rulând serverul Flask local (prin python chatbot.py) și deschizând manual pagina în browser (ex: http://127.0.0.1:5000). Așa se evită orice refresh automat și conversația decurge normal.

-> Ca să rulați cu succes, trebuie să creați un mediu virtual Python, apoi să instalați toate pachetele necesare din fișierul requirements.txt, și abia după aceea să rulați aplicația!

        1. python -m venv venv
        2. source venv/bin/activate ( pe macOS / Linux )
        2. venv\Scripts\activate ( pe Windows )
        3. pip install -r requirements.txt - ca să instalați toate librăriile necesare ! 
        3. python chatbot.py