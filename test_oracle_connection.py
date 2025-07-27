import oracledb

# Enable thick mode for better compatibility
oracledb.init_oracle_client()

try:
    # Try connecting as SYSTEM user
    connection = oracledb.connect(
        user="SYSTEM",
        password="oracle123",
        dsn="localhost:1521/XEPDB1"
    )
    print("Successfully connected to Oracle Database as SYSTEM")
    connection.close()

    # Try connecting as APP user
    connection = oracledb.connect(
        user="myuser",
        password="mypassword",
        dsn="localhost:1521/XEPDB1"
    )
    print("Successfully connected to Oracle Database as APP user")
    connection.close()

except oracledb.Error as error:
    print("Error while connecting to Oracle Database")
    print(error) 