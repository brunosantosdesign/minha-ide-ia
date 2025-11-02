from django.shortcuts import render

def index_view(request):
    """
    Renderiza a página inicial do chat (index.html).
    """
    # O Django procurará por 'core/index.html' dentro da pasta 'templates' da app 'core'
    return render(request, 'core/index.html')

