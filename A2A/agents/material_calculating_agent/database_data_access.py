import json
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# Database connection parameters
DB_CONFIG = {
    'dbname': 'plantdb',
    'user': os.getenv('DB_USER', 'your_username'),
    'password': os.getenv('DB_PASSWORD', 'your_password'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}


def get_db_connection():
    """Create and return a database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        raise


def get_product_details(product_name: str) -> Optional[List[Dict]]:
    """
    Query product recipe details from the database.
    
    Args:
        product_name (str): Name of the product to query
        
    Returns:
        List[Dict]: List of dictionaries containing material_name, tank_number, and quantity
        None: If an error occurs
    """
    query = """
    -- Get recipe for product by name
    SELECT
        rm.name AS material_name,
        rm.tank_number,
        pr.quantity
    FROM product_recipes pr
    JOIN raw_materials rm ON pr.material_id = rm.id
    JOIN products p ON pr.product_id = p.id
    WHERE p.name = %s
    ORDER BY rm.tank_number;
    """
    
    conn = None
    cursor = None
    
    try:
        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Execute query with parameterized input to prevent SQL injection
        cursor.execute(query, (product_name,))
        
        # Fetch all results
        results = cursor.fetchall()
        
        # Convert results to list of dictionaries
        recipe_details = []
        for row in results:
            recipe_details.append({
                'material_name': row['material_name'],
                'tank_number': row['tank_number'],
                'quantity': float(row['quantity'])
            })
        
        # Create the final JSON structure
        result = {
            "product_name": product_name,
            "recipe": recipe_details
        }
        
        
        # Return as JSON string
        return json.dumps(result, indent=2)
        #return recipe_details
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return None
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
        
    finally:
        # Clean up connections
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def print_recipe_details(product_name: str, recipe_details: List[Dict]):
    """Pretty print the recipe details."""
    if not recipe_details:
        print(f"No recipe found for product: {product_name}")
        return
        
    print(f"\nRecipe for: {product_name}")
    print("-" * 60)
    print(f"{'Material Name':<30} {'Tank #':<10} {'Quantity':<10}")
    print("-" * 60)
    
    for detail in recipe_details:
        print(f"{detail['material_name']:<30} "
              f"{detail['tank_number']:<10} "
              f"{detail['quantity']:<10}")


# Example usage
if __name__ == "__main__":
    # Example: Get recipe for "Product A"
    product_name = "Product A"
    
    # Query the database
    #recipe = get_product_details(product_name)
    recipe_json = get_product_details(product_name)
    
    if recipe_json is not None:
        recipe_data = json.loads(recipe_json)
        recipe = recipe_data['recipe']  # Extract the recipe list
        print_recipe_details(product_name, recipe)
        #print_recipe_details(product_name, recipe)
        
        # You can also work with the raw data
        print(f"\nRaw data (as list of dictionaries):")
        for item in recipe:
            print(item)
    else:
        print("Failed to retrieve product details.")
    
