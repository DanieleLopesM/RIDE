# Importa a biblioteca de conexão com banco de dados MySQL.
import mysql.connector

# Função responsável por conectar ao banco de dados.
def connect_to_database():

    # Parâmetros da conexão.
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='root',
        database='ride_db'
    )

    # Retorna a conexão como um objeto.
    return connection
