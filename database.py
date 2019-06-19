import sqlite3, json, os

with open('config.json', 'r') as f: 
    config = json.load(f)
    database = config['database']

NEW_PACK = """INSERT OR IGNORE INTO packdb (pid, uid, def, name)
VALUES ("{}", {}, {}, "{}");"""

DELETE_PACK = """DELETE
FROM packdb
WHERE pid = "{}";"""

LIST_PACKS = """SELECT *
FROM packdb
WHERE uid = {}
ORDER BY name ASC;"""

GET_PACK_BY_ID = """SELECT *
FROM packdb
WHERE pid = "{}";"""

GET_PACK_BY_NAME = """SELECT *
FROM packdb
WHERE name = "{}" AND uid = {};"""

GET_DEFAULT_PACK = """SELECT *
FROM packdb
WHERE uid = {} AND def = 1;"""

SET_DEFAULT_BY_ID = """UPDATE packdb
SET def = 1
WHERE pid = "{}";"""

SET_DEFAULT_BY_NAME = """UPDATE packdb
SET def = 1
WHERE name = "{}" AND uid = {};"""

REMOVE_DEFAULT = """UPDATE packdb
SET def = 0
WHERE uid = {} AND def = 1;"""

CREATE_DB = """CREATE TABLE IF NOT EXISTS packdb (
    pid NVARCHAR(128) PRIMARY KEY,
    uid INTEGER,
    def BOOLEAN,
    name NVARCHAR(64)
);"""

def execute(query):
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    cursor.execute(query)
    r = cursor.fetchall()
    connection.commit()
    cursor.close()
    connection.close()
    return(r)

def new_pack(pid, uid, default, packname):
    return(execute(NEW_PACK.format(pid, uid, default, packname)))

def delete_pack(pid):
    return(execute(DELETE_PACK.format(pid)))

def list_packs(uid):
    return(execute(LIST_PACKS.format(uid)))

def get_pack_by_id(pid):
    return(execute(GET_PACK_BY_ID.format(pid)))

def get_pack_by_name(packname, uid):
    return(execute(GET_PACK_BY_NAME.format(packname, uid)))

def get_default_pack(uid):
    return(execute(GET_DEFAULT_PACK.format(uid)))

def set_default_by_id(pid):
    return(execute(SET_DEFAULT_BY_ID.format(pid)))

def set_default_by_name(packname, uid):
    return(execute(SET_DEFAULT_BY_NAME.format(packname, uid)))

def remove_default(uid):
    return(execute(REMOVE_DEFAULT.format(uid)))

def create_db(database):
    return(execute(CREATE_DB))

if not os.path.exists(database): 
    create_db(database)
