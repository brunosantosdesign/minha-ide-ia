const form = document.getElementById('prompt-form');
const promptInput = document.getElementById('prompt-input');
const chatContainer = document.getElementById('chatContainer');
const generateButton = document.getElementById('generate-button');

// Função para adicionar uma mensagem à interface
function addMessage(sender, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${sender}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    
    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight; // Scroll para o final
    return contentDiv; // Retorna o elemento para atualizações futuras (loading)
}

// Lida com o envio do formulário
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = promptInput.value.trim();
    if (!prompt) return;

    // Adiciona a mensagem do utilizador e limpa o campo de texto
    addMessage('user', prompt);
    promptInput.value = '';
    promptInput.style.height = 'auto';

    // Mostra um indicador de "a carregar"
    const loadingMessage = addMessage('assistant', '');
    loadingMessage.innerHTML = '<div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div>';
    
    // Desativa o botão de envio
    generateButton.disabled = true;

    try {
        const response = await fetch('/gerar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt: prompt }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Ocorreu um erro na API.');
        }

        const data = await response.json();
        // Atualiza a mensagem de "a carregar" com a resposta final
        loadingMessage.textContent = data.response;

    } catch (error) {
        // Atualiza a mensagem de "a carregar" com a mensagem de erro
        loadingMessage.textContent = `Erro: ${error.message}`;
    } finally {
        // Reativa o botão de envio
        generateButton.disabled = false;
    }
});

// Auto-resize da área de texto
promptInput.addEventListener('input', () => {
    promptInput.style.height = 'auto';
    promptInput.style.height = `${promptInput.scrollHeight}px`;
});
