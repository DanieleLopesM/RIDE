# Importa a biblioteca de conexão com MySQL.
import mysql.connector

# Função para conectar ao banco de dados.
def database_connection():

    # Configurações da conexão com o banco.
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='root',
        database='ride_db'
    )

    return connection
