import psycopg2
from psycopg2 import sql

# -----------------------
# Connection Parameters
# -----------------------
connection_params = {
    'dbname': 'photon',
    'user': 'student',
    'password': 'student',  
    'host': 'localhost',
    'port': '5432'
}

# -----------------------
# Helper Functions
# -----------------------
def create_table_if_not_exists(cursor):
    """Create the players table if it does not already exist."""
    create_table_query = """
    CREATE TABLE IF NOT EXISTS players (
        id INT PRIMARY KEY,
        codename VARCHAR(30)
    );
    """
    cursor.execute(create_table_query)

def check_player_exists(cursor, player_id):
    """Check if a player with the given ID exists in the database."""
    cursor.execute("SELECT codename FROM players WHERE id = %s;", (player_id,))
    return cursor.fetchone()  # Returns None if player doesn't exist

def insert_player(cursor, player_id, codename):
    """Insert a new player into the database."""
    cursor.execute("INSERT INTO players (id, codename) VALUES (%s, %s);", (player_id, codename))

# -----------------------
# Main Program
# -----------------------
def main():
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()
        
        # Create the table if it does not exist
        create_table_if_not_exists(cursor)
        conn.commit()
        
        # Loop to process two players
        for i in range(2):
            player_id_input = input(f"Enter Player {i+1} ID: ").strip()
            if not player_id_input.isdigit():
                print("Player ID must be an integer.")
                continue
            
            player_id = int(player_id_input)
            existing_player = check_player_exists(cursor, player_id)
            
            if existing_player:
                print(f"Player {player_id} already exists with codename '{existing_player[0]}'.")
            else:
                codename = input("Enter your codename: ").strip()
                if not codename:
                    print("Codename cannot be empty.")
                    continue
                insert_player(cursor, player_id, codename)
                conn.commit()
                print(f"New player added: {player_id} - {codename}")
        
        # Display all players in the database
        cursor.execute("SELECT * FROM players;")
        rows = cursor.fetchall()
        print("\nCurrent Players in Database:")
        for row in rows:
            print(row)
    
    except Exception as error:
        print(f"Error connecting to PostgreSQL database: {error}")
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
