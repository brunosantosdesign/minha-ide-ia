const form = document.getElementById('prompt-form');
const promptInput = document.getElementById('prompt-input');
const chatContainer = document.getElementById('chatContainer');
const generateButton = document.getElementById('generate-button');
const chatIdInput = document.getElementById('chat-id'); // Input escondido para o ID do chat

// Função para adicionar uma mensagem à interface
function addMessage(sender, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${sender}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    // Para evitar problemas com HTML na resposta, usamos textContent
    contentDiv.textContent = text;

    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    // Adiciona um pequeno delay antes do scroll para garantir que a renderização terminou
    setTimeout(() => {
         chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 50); // Reduzido o delay
    return contentDiv; // Retorna o elemento para atualizações futuras (loading)
}

// Lida com o envio do formulário
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = promptInput.value.trim();
    if (!prompt || generateButton.disabled) return; // Não envia se vazio ou se já estiver a carregar

    // Obtém o chat_id atual (pode ser vazio no início)
    const currentChatId = chatIdInput.value;
    console.log("Enviando para Chat ID:", currentChatId || "Novo Chat"); // Log para depuração

    // Adiciona a mensagem do utilizador e limpa o campo de texto
    addMessage('user', prompt);
    promptInput.value = '';
    promptInput.style.height = 'auto'; // Reseta a altura

    // Mostra um indicador de "a carregar"
    const loadingMessage = addMessage('assistant', '');
    loadingMessage.innerHTML = '<div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div>';

    // Desativa o botão de envio e foca no input para feedback visual
    generateButton.disabled = true;
    promptInput.disabled = true;

    try {
        // Envia o prompt e o chat_id (se existir) para o backend Django
        const response = await fetch('/chat/gerar/', { // URL da API Django
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // Para Django, precisamos do token CSRF, mas @csrf_exempt na view desativa.
                // Se remover o @csrf_exempt, precisará adicionar o header 'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                prompt: prompt,
                chat_id: currentChatId // Envia o ID do chat atual (pode ser vazio)
            }),
        });

        // Tenta ler a resposta como JSON, mesmo se houver erro HTTP
        let data;
        try {
            data = await response.json();
        } catch (jsonError) {
             // Se a resposta não for JSON (ex: erro 500 HTML), cria um erro genérico
             console.error("Erro ao parsear JSON:", jsonError);
             const responseText = await response.text(); // Lê como texto para depuração
             console.error("Resposta recebida (não JSON):", responseText);
             throw new Error(`Erro HTTP ${response.status}: Resposta inválida do servidor.`);
        }

        if (!response.ok) {
            // Usa a mensagem de erro do JSON se disponível, senão usa uma genérica
            console.error("Erro da API:", data); // Loga o erro recebido
            throw new Error(data.error || `Erro HTTP ${response.status}.`);
        }


        // Guarda/Atualiza o chat_id retornado pelo backend
        if (data.chat_id) {
            chatIdInput.value = data.chat_id;
             console.log("Chat ID atualizado/confirmado:", data.chat_id); // Log para depuração
        }

        // Atualiza a mensagem de "a carregar" com a resposta final
        loadingMessage.textContent = data.response;

    } catch (error) {
        // Atualiza a mensagem de "a carregar" com a mensagem de erro
        console.error("Erro ao gerar resposta:", error); // Log detalhado no console
        loadingMessage.textContent = `Erro: ${error.message}`;
    } finally {
        // Reativa o botão de envio e o input
        generateButton.disabled = false;
        promptInput.disabled = false;
        promptInput.focus(); // Coloca o cursor de volta no input
        // Scroll final para garantir que a resposta final está visível
        setTimeout(() => {
            chatContainer.scrollTop = chatContainer.scrollHeight;
       }, 100);
    }
});

// Auto-resize da área de texto
promptInput.addEventListener('input', () => {
    promptInput.style.height = 'auto';
    // Limita a altura máxima para evitar que cresça indefinidamente
    promptInput.style.height = `${Math.min(promptInput.scrollHeight, 150)}px`;
});

// Envia com Enter, nova linha com Shift+Enter
promptInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault(); // Impede a criação de nova linha
        // Simula o clique no botão de submit para acionar o evento do formulário
        form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    }
});

// Função auxiliar para obter o cookie CSRF (necessária se remover @csrf_exempt)
/*
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
*/

