import psycopg2
from pprint import pprint
from datetime import date, datetime, timedelta

class DatabaseConnecion:
    def __init__(self):
        try:
             #connect to db
            self.connection = psycopg2.connect(
                                user = "postgres",
                                password = "postgresql",
                                host = 'localhost',
                                port = "5432",
                                database = "lapify"
            )
            self.connection.autocommit = True
            self.cursor = self.connection.cursor()

        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)

    def read(self):
        #execute query
        read_command = "select imie, nazwisko from kierowca"
        self.cursor.execute(read_command)
        rows = self.cursor.fetchall()
        print("Imiona i nazwiska uczestników: ")
        for r in rows:
            print(f"imie: {r[0]}  nazwisko: {r[1]}")

    def insert(self):
        #insert data
        id_bramki = input("Podaj id_bramki: ")
        nr_bramki = input("Podaj nr bramki: ")
        insert_command = \
            "INSERT INTO bramka(id_bramki, nr_bramki) VALUES(" + id_bramki + "," + nr_bramki + ")"
        pprint(insert_command)
        self.cursor.execute(insert_command)

    def query(self):
        print("Wprowadz komende: \n")
        query_command = input()
        self.cursor.execute(query_command)
        rows = self.cursor.fetchall()
        for r in rows:
            print(r)


if __name__ == '__main__':
    database_connection = DatabaseConnecion()
    #database_connection.read()
    #database_connection.insert()
    #database_connection.query()
