# Importa a função responsável por criar e configurar a aplicação da web.
from application import create_application

# Cria a instância da aplicação da web com base nas configurações iniciais.
web_application = create_application()

# Verifica se este arquivo está sendo executado diretamente.
if __name__ == '__main__':

    # Inicia o servidor da aplicação da web em modo de depuração.
    web_application.run(debug=True)
