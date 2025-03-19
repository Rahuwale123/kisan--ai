import mysql.connector
from mysql.connector import Error
import json
import logging
from config import Config

class DatabaseManager:
    def __init__(self):
        try:
            self.connection = mysql.connector.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DATABASE
            )
            self.cursor = self.connection.cursor()
            self.create_tables()
        except Error as e:
            logging.error(f"Error connecting to MySQL: {str(e)}")
            raise

    def create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            # Create single farmers table with JSON columns for arrays
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS farmers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    phone_number VARCHAR(15) UNIQUE NOT NULL,
                    name VARCHAR(100),
                    taluka VARCHAR(100),
                    village VARCHAR(100),
                    total_land VARCHAR(50),
                    crops JSON,
                    animals JSON,
                    milk_prod VARCHAR(50),
                    loan VARCHAR(100),
                    water_resource JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)

            self.connection.commit()
            logging.info("Database tables created successfully")

        except Error as e:
            logging.error(f"Error creating tables: {str(e)}")
            raise

    def save_farmer_data(self, farmer_data):
        """Save farmer data to MySQL database"""
        try:
            # Convert lists to JSON strings
            crops_json = json.dumps(farmer_data.get('crops', []))
            animals_json = json.dumps(farmer_data.get('animals', []))
            water_resource_json = json.dumps(farmer_data.get('water_resource', []))

            # Insert or update farmer data
            self.cursor.execute("""
                INSERT INTO farmers (
                    phone_number, name, taluka, village, total_land,
                    crops, animals, milk_prod, loan, water_resource
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    taluka = VALUES(taluka),
                    village = VALUES(village),
                    total_land = VALUES(total_land),
                    crops = VALUES(crops),
                    animals = VALUES(animals),
                    milk_prod = VALUES(milk_prod),
                    loan = VALUES(loan),
                    water_resource = VALUES(water_resource)
            """, (
                farmer_data['phone_number'],
                farmer_data.get('name'),
                farmer_data.get('taluka'),
                farmer_data.get('village'),
                farmer_data.get('total_land'),
                crops_json,
                animals_json,
                farmer_data.get('milk_prod'),
                farmer_data.get('loan'),
                water_resource_json
            ))

            self.connection.commit()
            logging.info(f"Saved farmer data for phone number: {farmer_data['phone_number']}")
            return True

        except Error as e:
            logging.error(f"Error saving farmer data: {str(e)}")
            return False

    def get_farmer_data(self, phone_number):
        """Get farmer data from MySQL database"""
        try:
            self.cursor.execute("""
                SELECT 
                    phone_number, name, taluka, village, total_land,
                    crops, animals, milk_prod, loan, water_resource
                FROM farmers 
                WHERE phone_number = %s
            """, (phone_number,))
            
            result = self.cursor.fetchone()
            if result:
                return {
                    'phone_number': result[0],
                    'name': result[1],
                    'taluka': result[2],
                    'village': result[3],
                    'total_land': result[4],
                    'crops': json.loads(result[5]) if result[5] else [],
                    'animals': json.loads(result[6]) if result[6] else [],
                    'milk_prod': result[7],
                    'loan': result[8],
                    'water_resource': json.loads(result[9]) if result[9] else []
                }
            return None

        except Error as e:
            logging.error(f"Error getting farmer data: {str(e)}")
            return None

    def __del__(self):
        """Close database connection"""
        try:
            if hasattr(self, 'cursor'):
                self.cursor.close()
            if hasattr(self, 'connection'):
                self.connection.close()
        except Exception as e:
            logging.error(f"Error closing database connection: {str(e)}")
