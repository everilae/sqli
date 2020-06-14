import pytest

from sqli import check
from textwrap import dedent

ok = [
    (0, """
        import sqlite3

        with sqlite3.connect("Quiz.db") as db:
            cursor = db.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user(
        userID INTEGER PRIMARY KEY
        username VARCHAR(20) NOT NULL,
        firstname VARCHAR(20) NOT NULL,
        surname VARCHAR(20) NOT NULL,
        password VARCHAR(20) NOT NULL,);
        ''')
        """),
    (0, '''
        def search(x,y):
            c.execute("""SELECT * FROM Table
            INNER JOIN Genres ON Table.GenreID = Genres.GenreID
            WHERE ?=?""",(x,y))
            rows = c.fetchall
            for row in rows:
                print(row)

        search("Genres.Genre", input("Genre: "))
        '''),
    (0, """
        import sqlite3
        import os
        from werkzeug.security import generate_password_hash
        from uuid import uuid4

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        DB_PATH = os.path.join(BASE_DIR, "chat.sqlite")


        def insert_row_in_db(username, firstname, lastname, email, password):
            \"\"\" Creates a row in chat.sqlite's users table \"\"\"
            uid = uuid4().hex
            pwd_hash = generate_password_hash(password)
            login_time = set_lastlogin(uid)
            row_data = (uid, username, firstname, lastname, email, pwd_hash, login_time, True)

            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute('''INSERT INTO users (uid, username, firstname, lastname, email, passwordhash,
                          lastlogin, loggedin) VALUES (?, ?, ?, ?, ?, ?, ?, ?);''', row_data)
        """),
    (0, """
        with open(poll, encoding='utf-8') as p:
            f_csv = csv.reader(p)
            for row in f_csv:
                c.execute(u'SELECT id FROM senators WHERE name LIKE ?', ('%'+row[0]+'%',))
                data = c.fetchone()
                print(data) # I should not get None results here, but I do, exactly when the query has UTF-8 characters.
        """),
    (0, """
        if count == 1:
            cursor.execute("SELECT * FROM PacketManager WHERE ? = ?", filters[0], parameters[0])
            all_rows = cursor.fetchall()

        elif count == 2:
            cursor.execute("SELECT * FROM PacketManager WHERE ? = ? AND ? = ?", filters[0], parameters[0], filters[1], parameters[1])
            all_rows = cursor.fetchall()

        elif count == 3 :
            cursor.execute("SELECT * FROM PacketManager WHERE ? = ? AND ? = ? AND ? = ?", filters[0], parameters[0], filters[1], parameters[1], filters[2], parameters[2])
            all_rows = cursor.fetchall()
        """),
    (0, """stmt = f"SELECT * FROM foo" """),
    (0, """cur.execute(
               sql.SQL(intersecta)
               .format(nome0=sql.Identifier(nomecompleto),
                       nome1=sql.Identifier(tabelagerada),
                       nome2=sql.Identifier(segmentnome)),
               [nomedosegmento,])
        """),
    (0, """
        stmt = "SELECT * FROM foo"
        stmt += " WHERE x = ?"
        engine.execute(stmt, (x,))
        """),
    (0, """engine.execute(f"SELECT 1")"""),
    (0, """
        grey_area = "1"
        engine.execute(f"SELECT {grey_area}")
        """),
    (0, """
        foo = "SELECT * FROM foo WHERE bar = {}"
        cur.execute(foo.format(1))
        """),
    (0, """
        foo = "SELECT * FROM {}"
        cur.execute(foo.format("{}").format("foo"))
        """),
]

injectable = [
    (3, """
        import sqlite3 as lite
        db = lite.connect("test.db")
        id_to_be_added = "123456789101112"
        db.execute("CREATE TABLE USERS (ID TEXT, NUM INT)")
        Query = "{ SOMETHING IN SQL }"  # This returns either True or False
        if Query:
            db.execute("UPDATE USERS SET NUM = NUM + 1 WHERE ID =  {};".format(id_to_be_added))

        else:
            db.execute("INSERT INTO USERS ({}, 0)".format(id_to_be_added))

        num_to_be_printed = db.execute("SELECT NUM FROM USERS WHERE ID = {}".format(id_to_be_added))
        print("{0} has {1}").format(id_to_be_added, num_to_be_printed)
        """),
    (1, """
        query = "delete from zoznam where name = '%s' " % data3
        c.execute(query)
        conn.commit()
        """),
    (1, """mydata = c.execute("DELETE FROM Zoznam WHERE Name='%s'" % data3)"""),
    (1, """
        conn = sqlite3.connect('databaza.db')
        c = conn.cursor()
        conn.text_factory = str
        data3 = str(input('Please enter name: '))
        query = "DELETE FROM Zoznam WHERE Name = '%s';" % data3.strip()
        print(query)
        mydata = c.execute(query)
        """),
    (1, """insert_sql = 'INSERT INTO pcp(date,stations,pcp) VALUES( ' + kdm + ',' + station + ',' + klm + ')'
c.execute(insert_sql)"""),
    (1, """statement = u"select * from senators where name like '" + '%'+row[0]+'%'+"'"
c.execute(statement)"""),
    (1, """
        stmt = f"SELECT * FROM foo WHERE bar = {bar}"
        c.execute(stmt)
        """),
    (1, """cur.execute("SELECT * FROM foo WHERE x = {x}".format_map(bar))"""),
    (1, """stmt = text("SELECT * FROM foo WHERE x = '" + str(x) + "'")
engine.execute(stmt)"""),
    (1, """Person.objects.raw('SELECT last_name, birth_date, first_name, id FROM myapp_person WHERE last_name LIKE \\'%' + search + '%\\'')"""),
    (1, """
        stmt = "SELECT * FROM foo"
        stmt += "WHERE x = " + x
        engine.execute(stmt)
        """),
    (1, """
        sql = "SELECT * FROM foo "+\\
              "WHERE baz = " + baz +\\
              "  AND bat = " + bat
        cur.execute(sql)
        """),
    (1, """
        cur.execute("SELECT * FROM foo WHERE x = {}".format(x()))
        """),
    (1, """
        cur.execute("SELECT * FROM foo WHERE x = {}".format(y.x()))
        """),
    (1, """
        pd.read_sql_query(
            'SELECT * FROM foo WHERE bar in ({0})'.format(
                ','.join(f"'{d}'" for d in data)))
        """),
]

dynamic_placeholders = [
    (0, '''
        query = """SELECT *
                      FROM [dbo].[viewA]
                      WHERE [Id] IN ({0})"""
        query = query.format(",".join("?" * len(idList)))

        data = pandas.read_sql_query(query, conn, params = tuple(idList))
        '''),
    (0, """
        sql_query = "DELETE FROM multiusingfuncs WHERE muf_id IN (%s) " % ','.join(['?'] * len(list))
        cursor.execute(sql_query, list)
        """),
    (0, """
        query = 'select * from foo where x in {}'
        query = query.format(','.join('?' * (int(len(columns)))))
        print(query)   #for debug purposes
        cursor = connection.cursor()
        for data in reader:
            cursor.execute(query, data)
        """),
    (0, """
        args = input().split()
        placeholders = ",".join("?" * len(args))
        stmt = f"SELECT * FROM foo WHERE x IN ({placeholders})"
        engine.execute(stmt, args)
        """),
    (0, """
        pd.read_sql_query('SELECT * FROM foo WHERE bar in ({0})'.format(', '.join(('?' for _ in data))), data, conn)
        """),
    (0, """
        pd.read_sql_query('SELECT * FROM foo WHERE bar in ({0})'.format(', '.join(['?' for _ in data])), data, conn)
        """),
]


@pytest.mark.parametrize(
    "expected,source", ok + injectable + dynamic_placeholders)
def test_check(expected, source):
    poisoned = check(dedent(source))
    assert len(poisoned) == expected


#def test_py_2():
#    source = dedent("""\
#        sql = "SELECT * FROM foo WHERE x = " + x
#        print sql
#        cur.execute(sql)""")
#    poisoned = check(source)
#    assert len(poisoned) == 1
