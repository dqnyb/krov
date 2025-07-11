(function() {
    document.head.insertAdjacentHTML('beforeend', '<link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.16/tailwind.min.css" rel="stylesheet">');
  
    // Inject the CSS
    const style = document.createElement('style');
    style.innerHTML = `
    .hidden {
      display: none;
    }

    /* Global */
    html{
    min-height: 100%;
    overflow: hidden;
    }

    body{
    height: calc(100vh - 8em);
    padding: 4em;
    color: rgba(0, 0, 0, 0.75);
    font-family: 'Anonymous Pro', monospace;  
    background-color: rgb(25,25,25);  
    }

    .line-1{
        position: relative;
        top: 50%;  
        width: 35ch;
        margin: 0 auto;
        border-right: 2px solid rgba(0, 0, 0, 0.75);
        font-size: 180%;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        transform: translateY(-50%);    
    }

    /* Animation */
    .anim-typewriter{
    animation: typewriter 4s steps(35) 1s 1 normal both,
                blinkTextCursor 500ms steps(35) infinite normal;
    }

    @keyframes typewriter{
    from{width: 0;}
    to{width: 35ch;}
    }

    @keyframes blinkTextCursor{
    from{border-right-color: rgba(0, 0, 0, 0.75);}
    to{border-right-color: transparent;}
    }
    
    #chat-widget-container {
      position: fixed;
      bottom: 20px;
      right: 20px;
      flex-direction: column;

    }
    
      
    #chat-popup {
      height: 70vh;
      max-height: 70vh;
      transition: all 0.3s;
      overflow: hidden;
    }
    @media (max-width: 768px) {
      #chat-popup {
        position: fixed;
        top: 0;
        right: 0;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 100%;
        max-height: 100%;
        border-radius: 0;
      }
    }

    `;
  
    document.head.appendChild(style);
  
    // Create chat widget container
    const chatWidgetContainer = document.createElement('div');
    chatWidgetContainer.id = 'chat-widget-container';
    document.body.appendChild(chatWidgetContainer);
    
    // Inject the HTML
    chatWidgetContainer.innerHTML = `
      <div id="chat-bubble" class="trans w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center cursor-pointer text-3xl">
        <svg id="chat-icon" xmlns="http://www.w3.org/2000/svg" class="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
        <!-- Close Icon -->
        <svg id="close-icon" xmlns="http://www.w3.org/2000/svg" class="w-10 h-10 text-white hidden" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>
      <div id="chat-popup" class="hidden absolute bottom-20 right-0 w-96 bg-white rounded-md shadow-md flex flex-col transition-all text-sm ">
        <div id="chat-header" class="flex justify-between items-center p-4 bg-gray-800 text-white rounded-t-md">
          <h3 class="m-0 text-lg">ChatBot Widget</h3>
          <button id="close-popup" class="bg-transparent border-none text-white cursor-pointer">
          </button>
        </div>
        <div id="chat-messages" class="flex-1 p-4 overflow-y-auto"></div>
        <div id="chat-input-container" class="p-4 border-t border-gray-200">
          <div class="flex space-x-4 items-center">
            <input type="text" id="chat-input" class="flex-1 border border-gray-300 rounded-md px-4 py-2 outline-none w-3/4" placeholder="Type your message...">
            <button id="chat-submit" class="bg-gray-800 text-white rounded-md px-4 py-2 cursor-pointer">Send</button>
          </div>
          <div class="flex text-center text-xs pt-4">
            <span class="flex-1">Created by <a href = "https://github.com/dqnyb" class = "text-blue-800" style = "color = #3b5998 !important">Daniel Brînza</span>
          </div>
        </div>
      </div>
    `;
  
    // Add event listeners
    const chatInput = document.getElementById('chat-input');
    const chatSubmit = document.getElementById('chat-submit');
    const chatMessages = document.getElementById('chat-messages');
    const chatBubble = document.getElementById('chat-bubble');
    const chatPopup = document.getElementById('chat-popup');
    const closePopup = document.getElementById('close-popup');
    const chatIcon = document.getElementById("chat-icon");
    const closeIcon = document.getElementById("close-icon");

    chatBubble.addEventListener("click", () => {
      const isOpen = !chatPopup.classList.contains("hidden");
    
      // chatPopup.classList.toggle("hidden");
      chatIcon.classList.toggle("hidden");
      closeIcon.classList.toggle("hidden");
    });
    
    closePopup.addEventListener("click", () => {
      chatPopup.classList.add("hidden");
      chatIcon.classList.remove("hidden");
      closeIcon.classList.add("hidden");
    });

    function displayBotReply(text) {
        const messageElement = document.createElement('div');
        messageElement.className = 'flex mb-3';
        messageElement.innerHTML = `
          <div class="bg-gray-200 text-black rounded-lg py-2 px-4 max-w-[70%]">
            ${text}
          </div>
        `;
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
      }
      
  
    chatSubmit.addEventListener('click', function() {
      
      const message = chatInput.value.trim();
      if (!message) return;
      
      chatMessages.scrollTop = chatMessages.scrollHeight;
  
      chatInput.value = '';
  
      onUserRequest(message);
  
    });
  
    chatInput.addEventListener('keyup', function(event) {
      if (event.key === 'Enter') {
        chatSubmit.click();
      }
    });
  
    chatBubble.addEventListener('click', function() {
      togglePopup();
    });
  
    closePopup.addEventListener('click', function() {
      togglePopup();
    });
  
    function togglePopup() {
      
        chatPopup.classList.toggle('hidden');
        chatPopup.classList.toggle('fullscreen');
        if (!chatPopup.classList.contains('hidden')) {
            document.body.classList.add('chat-open');
          chatInput.focus();
      
          if (chatMessages.children.length === 0 && onboardingStep === 0) {
            const typingElement = document.createElement('div');
            typingElement.className = 'flex mb-3';
            typingElement.id = 'typing-indicator';
            typingElement.innerHTML = `
              <div class="typing-dots flex space-x-2 px-4 py-2">
                <span class="dot w-3 h-3 bg-blue-600 rounded-full animate-bounce delay-0"></span>
                <span class="dot w-3 h-3 bg-blue-600 rounded-full animate-bounce delay-150"></span>
                <span class="dot w-3 h-3 bg-blue-600 rounded-full animate-bounce delay-300"></span>
              </div>
            `;
            chatMessages.appendChild(typingElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            fetch("http://127.0.0.1:5000/language")
              .then(res => res.json())
              .then(data => {
                setTimeout(() => {
                  typingElement.remove();
                  displayBotReply(data.ask_name);
                  
                  onboardingStep = -1;
                }, 1000); // Delay de simulare typing
              });
          }
        } else {
            document.body.classList.remove('chat-open');
        }
      }

    let userName = null;
    let userInterests = null;
    let onboardingStep = 0;  // 0 = numele, 1 = interesele, 2 = chat-ul propriu-zis

      

  
    function onUserRequest(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'flex justify-end mb-3';
        messageElement.innerHTML = `
          <div class="bg-gray-800 text-white rounded-lg py-2 px-4 max-w-[70%]">
            ${message}
          </div>
        `;
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        if (onboardingStep === -1) {
          userName = message;
          // onboardingStep = 2;
        
          const typingElement = document.createElement('div');
          typingElement.className = 'flex mb-3';
          typingElement.id = 'typing-indicator';
          typingElement.innerHTML = `
            <div class="typing-dots flex space-x-2 px-4 py-2">
              <span class=""></span>
              <span class=""></span>
              <span class=""></span>
            </div>
          `;
          chatMessages.appendChild(typingElement);
          chatMessages.scrollTop = chatMessages.scrollHeight;
        
          fetch("http://127.0.0.1:5000/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: userName })
          })
            .then(res => res.json())
            .then(data => {
              setTimeout(() => {
                typingElement.remove();
                displayBotReply(data.ask_name);
                window.language = data.language;
                onboardingStep = 1;
              }, 1000); 
            })
            .catch(err => {
              typingElement.remove();
              displayBotReply("Eroare la inițializare: " + err.message);
            });
        
          return;
        }
      
        if (onboardingStep === 1) {
          userName = message;
          // onboardingStep = 2;
        
          const typingElement = document.createElement('div');
          typingElement.className = 'flex mb-3';
          typingElement.id = 'typing-indicator';
          typingElement.innerHTML = `
            <div class="typing-dots flex space-x-2 px-4 py-2">
              <span class=""></span>
              <span class=""></span>
              <span class=""></span>
            </div>
          `;
          chatMessages.appendChild(typingElement);
          chatMessages.scrollTop = chatMessages.scrollHeight;
        
          fetch("http://127.0.0.1:5000/interests", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: userName , language: window.language})
          })
            .then(res => res.json())
            .then(data => {
              setTimeout(() => {
                console.log(language)
                typingElement.remove();
                displayBotReply(data.ask_interests); // răspunsul real după delay
                if (data.ask_interests.includes("China mat 0.40 :") || data.ask_interests.includes("0.45  Arvedi mat :") || data.ask_interests.includes("SSAB")  ){
                  onboardingStep = 2;
                } else if (data.ask_interests.includes("Să afli informații despre un") || data.ask_interests.includes("Узнать информацию о")){
                  onboardingStep = 1;
                } else if (data.ask_interests.includes("Mulțumim că ai ales KROV!") || data.ask_interests.includes("Спасибо, что выбрали KROV!")){
                  onboardingStep = 6;
                }

              }, 1000);
            })
            .catch(err => {
              typingElement.remove();
              displayBotReply("Eroare la inițializare: " + err.message);
            });
        
          return;
        }        
            
        if (onboardingStep === 2) {
          userInterests = message;
          // onboardingStep = 3;
        
          const typingElement = document.createElement('div');
          typingElement.className = 'flex mb-3';
          typingElement.id = 'typing-indicator';
          typingElement.innerHTML = `
            <div class="typing-dots flex space-x-2 px-4 py-2">
              <span class=""></span>
              <span class=""></span>
              <span class=""></span>
            </div>
          `;
          chatMessages.appendChild(typingElement);
          chatMessages.scrollTop = chatMessages.scrollHeight;
        
          fetch("http://127.0.0.1:5000/welcome", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: userName, interests: userInterests , language: window.language})
          })
            .then(res => res.json())
            .then(data => {
              setTimeout(() => {
                typingElement.remove();
                reply(data.message); // Afișează mesajul de bun venit după delay
                if(data.message.includes("Suntem gata să te ajutăm cu tot ce ține de acoperișuri!") || data.message.includes("Мы готовы помочь вам со всем, что связано с крышами!")){
                  onboardingStep = 2;
                } else if (data.message.includes("Mulțumim că ai ales KROV!") || data.message.includes("Спасибо, что выбрали KROV!")){
                  onboardingStep = 6
                } else if (data.message.includes("Te rog să alegi varianta exactă care te interesează. 😊")|| data.message.includes("Пожалуйста, выберите именно тот вариант, который вас интересует. 😊")){
                  onboardingStep = 2;
                } else {
                  onboardingStep = 1;
                }
              }, 1000);
            })
            .catch(err => {
              typingElement.remove();
              reply("Eroare la inițializare: " + err.message);
            });
        
          return;
        }
        
        if (onboardingStep == 3) {
            fetch("http://127.0.0.1:5000/chat", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                name: userName,
                interests: userInterests,
                message: message,
                language: window.language
              })
            })
            .then(res => res.json())
            .then(data => {
              reply(data.reply);
              if (data.reply.includes("China mat 0.40 :") || data.reply.includes("0.45  Arvedi mat :") || data.reply.includes("SSAB") || data.reply.includes("China 0.4")){
                onboardingStep = 2
              } else if (data.reply.includes("!!!")){
                onboardingStep = 4
              }
            })
            .catch(err => reply("Eroare în conversație: " + err.message));
            return;
          }

        if (onboardingStep == 4) {
            fetch("http://127.0.0.1:5000/next_chat", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                name: userName,
                interests: userInterests,
                message: message,
                language: window.language
              })
            })
            .then(res => res.json())
            .then(data => {
              reply(data.reply);
              if (data.reply.includes("!!!")){
                onboardingStep = 4
              } else if (data.reply.includes("Scrie **numele exact** al produsului dorit") || data.reply.includes("Напишите **точное название** нужного вам товара")){
                onboardingStep = 4
              } else {
                onboardingStep = 5
              }
            })
            .catch(err => reply("Eroare în conversație: " + err.message));
            return;
          }

          if (onboardingStep === 6) {
            userInterests = message;
            // onboardingStep = 3;
          
            const typingElement = document.createElement('div');
            typingElement.className = 'flex mb-3';
            typingElement.id = 'typing-indicator';
            typingElement.innerHTML = `
              <div class="typing-dots flex space-x-2 px-4 py-2">
                <span class=""></span>
                <span class=""></span>
                <span class=""></span>
              </div>
            `;
            chatMessages.appendChild(typingElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
          
            fetch("http://127.0.0.1:5000/comanda", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ name: userName, interests: userInterests, message: message , language: window.language})
            })
              .then(res => res.json())
              .then(data => {
                setTimeout(() => {
                  typingElement.remove();
                  reply(data.reply); // Afișează mesajul de bun venit după delay
                  console.log(data.reply)
                  if(data.reply.includes("Mulțumim! Ai un nume frumos!") || data.reply.includes("Спасибо! У тебя красивое имя!")){
                    onboardingStep = 7;
                  } else {
                    onboardingStep = 6;
                  }
                }, 1000);
              })
              .catch(err => {
                typingElement.remove();
                reply("Eroare la inițializare: " + err.message);
              });
          
            return;
          }

          if (onboardingStep === 7) {
            userInterests = message;
            // onboardingStep = 3;
          
            const typingElement = document.createElement('div');
            typingElement.className = 'flex mb-3';
            typingElement.id = 'typing-indicator';
            typingElement.innerHTML = `
              <div class="typing-dots flex space-x-2 px-4 py-2">
                <span class=""></span>
                <span class=""></span>
                <span class=""></span>
              </div>
            `;
            chatMessages.appendChild(typingElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
          
            fetch("http://127.0.0.1:5000/numar_de_telefon", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ name: userName, interests: userInterests, message: message, language: window.language })
            })
              .then(res => res.json())
              .then(data => {
                setTimeout(() => {
                  typingElement.remove();
                  reply(data.reply); // Afișează mesajul de bun venit după delay
                  console.log(data.reply)
                  if(data.reply.includes("Te rog să introduci un număr de telefon valid") || data.reply.includes("Numărul acesta nu pare corect") || data.reply.includes("Пожалуйста, введи действительный номер телефона, чтобы мы могли продолжить.") || data.reply.includes("Этот номер кажется некорректным")){
                    onboardingStep = 7;
                  } else {
                    onboardingStep = 8;
                  }
                }, 1000);
              })
              .catch(err => {
                typingElement.remove();
                reply("Eroare la inițializare: " + err.message);
              });
          
            return;
          }

          if (onboardingStep === 8) {
            userInterests = message;
            // onboardingStep = 3;
          
            const typingElement = document.createElement('div');
            typingElement.className = 'flex mb-3';
            typingElement.id = 'typing-indicator';
            typingElement.innerHTML = `
              <div class="typing-dots flex space-x-2 px-4 py-2">
                <span class=""></span>
                <span class=""></span>
                <span class=""></span>
              </div>
            `;
            chatMessages.appendChild(typingElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
          
            fetch("http://127.0.0.1:5000/categorie", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ name: userName, interests: userInterests, message: message, language: window.language })
            })
              .then(res => res.json())
              .then(data => {
                setTimeout(() => {
                  typingElement.remove();
                  reply(data.reply);
                  console.log(data.reply)
                  if(data.reply.includes("Suntem gata să te ajutăm cu tot ce ține de acoperișuri!") || data.reply.includes("Мы готовы помочь вам со всем, что связано с крышами!")){
                    onboardingStep = 8;
                  } else if (data.reply.includes("Te rog să alegi varianta exactă care te interesează. 😊") || data.reply.includes("Пожалуйста, выбери точный вариант, который тебя интересует. 😊")){
                    onboardingStep = 8;
                  } else {
                    onboardingStep = 9;
                  }
                  
                }, 1000);
              })
              .catch(err => {
                typingElement.remove();
                reply("Eroare la inițializare: " + err.message);
              });
          
            return;
          }

          if (onboardingStep === 9) {
            userInterests = message;
            // onboardingStep = 3;
          
            const typingElement = document.createElement('div');
            typingElement.className = 'flex mb-3';
            typingElement.id = 'typing-indicator';
            typingElement.innerHTML = `
              <div class="typing-dots flex space-x-2 px-4 py-2">
                <span class=""></span>
                <span class=""></span>
                <span class=""></span>
              </div>
            `;
            chatMessages.appendChild(typingElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
          
            fetch("http://127.0.0.1:5000/produs", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ name: userName, interests: userInterests, message: message, language: window.language })
            })
              .then(res => res.json())
              .then(data => {
                setTimeout(() => {
                  typingElement.remove();
                  reply(data.reply);
                  if (data.reply.includes("Mulțumim pentru alegerea ta! 🛒 Produsul a fost notat cu succes.") || data.reply.includes("Спасибо за ваш выбор! 🛒 Товар успешно добавлен.")){
                    onboardingStep = 10;
                  } else if (data.reply.includes("La cererea ta, am găsit următoarele produse din categoria") || data.reply.includes("По вашему запросу найдены следующие товары из категории")){
                    onboardingStep = 9;
                  } else if (data.reply.includes("🔍 Doar așa putem continua mai departe cu procesul") || data.reply.includes("🔍 Только так мы сможем продолжить оформление заказа!")){
                    onboardingStep = 9;
                  }
                }, 1000);
              })
              .catch(err => {
                typingElement.remove();
                reply("Eroare la inițializare: " + err.message);
              });
          
            return;
          }

          if (onboardingStep === 10) {
            userInterests = message;
            // onboardingStep = 3;
          
            const typingElement = document.createElement('div');
            typingElement.className = 'flex mb-3';
            typingElement.id = 'typing-indicator';
            typingElement.innerHTML = `
              <div class="typing-dots flex space-x-2 px-4 py-2">
                <span class=""></span>
                <span class=""></span>
                <span class=""></span>
              </div>
            `;
            chatMessages.appendChild(typingElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
          
            fetch("http://127.0.0.1:5000/culoare", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ name: userName, interests: userInterests, message: message, language: window.language })
            })
              .then(res => res.json())
              .then(data => {
                setTimeout(() => {
                  typingElement.remove();
                  reply(data.reply);
                  if (data.reply.includes("Doar așa putem trece la etapa finală a comenzii tale!") || data.reply.includes("Am observat că ai menționat o culoare care poate avea mai multe nuanțe sau variante.") || data.reply.includes("Только так мы сможем перейти к финальному этапу твоего заказа!") || data.reply.includes("Я заметил, что ты упомянул цвет, который может иметь несколько оттенков или вариантов.")){
                    onboardingStep = 10;
                  } else {
                    onboardingStep = 11;
                  }

                }, 1000);
              })
              .catch(err => {
                typingElement.remove();
                reply("Eroare la inițializare: " + err.message);
              });
          
            return;
          }

          if (onboardingStep === 11) {
            userInterests = message;
            // onboardingStep = 3;
          
            const typingElement = document.createElement('div');
            typingElement.className = 'flex mb-3';
            typingElement.id = 'typing-indicator';
            typingElement.innerHTML = `
              <div class="typing-dots flex space-x-2 px-4 py-2">
                <span class=""></span>
                <span class=""></span>
                <span class=""></span>
              </div>
            `;
            chatMessages.appendChild(typingElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
          
            fetch("http://127.0.0.1:5000/cantitate", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ name: userName, interests: userInterests, message: message, language: window.language })
            })
              .then(res => res.json())
              .then(data => {
                setTimeout(() => {
                  typingElement.remove();
                  reply(data.reply);
                  if(data.reply.includes("Doar așa pot calcula prețul total și înregistra comanda.") || data.reply.includes("Только так я смогу рассчитать итоговую цену и оформить заказ.")){
                    onboardingStep = 11
                  } else {
                    onboardingStep = 1
                  }
                }, 1000);
              })
              .catch(err => {
                typingElement.remove();
                reply("Eroare la inițializare: " + err.message);
              });
          
            return;
          }




          

      
        // Chat normal
        fetch("http://127.0.0.1:5000/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message })
        })
        .then(res => res.json())
        .then(data => reply(data.reply))
        .catch(err => reply("A apărut o eroare: " + err.message));
      }      
    
      function reply(message) {
        const chatMessages = document.getElementById('chat-messages');
      
        const typingElement = document.createElement('div');
        typingElement.className = 'flex mb-3';
        typingElement.id = 'typing-indicator';
        typingElement.innerHTML = `
          <div class="typing-dots flex space-x-2 px-4 py-2">
                <span class=""></span>
                <span class=""></span>
                <span class=""></span>
            </div>
        `;
        chatMessages.appendChild(typingElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
      
        // Simulare răspuns după delay scurt (ex: 500ms)
        setTimeout(() => {
          typingElement.remove();
      
          const replyElement = document.createElement('div');
          replyElement.className = 'flex mb-3';
          replyElement.innerHTML = `
            <div class="bg-gray-200 text-black rounded-lg py-2 px-4 max-w-[70%]">
              ${message}
            </div>
          `;
          chatMessages.appendChild(replyElement);
          chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 2000);
      }
    
  })();