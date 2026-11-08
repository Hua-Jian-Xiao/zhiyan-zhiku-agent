"""Database driver bootstrap.

Prefer mysqlclient when it is installed. On Windows and lightweight demo
machines we fall back to the pure-Python PyMySQL driver and expose the version
metadata Django 6 expects from MySQLdb.
"""

try:
    import MySQLdb  # noqa: F401
except ImportError:
    try:
        import pymysql

        # Django checks MySQLdb.version_info and expects >= 2.2.1. PyMySQL is
        # API-compatible with the mysqlclient backend for our demo workload.
        pymysql.version_info = (2, 2, 1, "final", 0)
        pymysql.install_as_MySQLdb()
    except ImportError:
        # SQLite users do not need a MySQL driver.
        pass
