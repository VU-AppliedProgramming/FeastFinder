from flask import Flask, jsonify, request, Response
import os
import requests
from flask_cors import CORS
import re
from favrecipes import FavRecipes, Recipe
from typing import Union, Tuple, Optional, List

try: 
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Spoonacular API key
API_KEY = os.environ.get('API_KEY')
SPOONACULAR_API = "https://api.spoonacular.com/recipes/"

# Default storage file (only used if not overridden in testing)
app.fav_recipes = FavRecipes('myfavrecipes.json')

@app.route('/health')
def health_check():
    """
    This endpoint checks if the back end server is running or not.
    Returns:
        Tuple[str, int]: A tuple containing a message indicating the server status and an HTTP status code.
    """

    return 'OK', 200

@app.route('/test')
def test():
    """
    Endpoint to retrieve recipes from favorites.
    Returns:
        Response: JSON response containing the favorite recipes.
    """
        
    recipes = app.fav_recipes.get_recipes()
    return jsonify(recipes)

@app.route('/show_one_favorite/<recipe_id>')
def s_one_fav(recipe_id: str) -> Response:
    """
    Endpoint to display information about a single favorite recipe based on its ID.
    Args:
        recipe_id (str): The ID of the recipe to retrieve.
    Returns:
        Response: JSON response containing information about the requested recipe.
    """

    recipes = app.fav_recipes.get_recipes()
    if recipe_id in recipes:
        return jsonify({recipe_id: recipes[recipe_id]})
    else:
        return jsonify({"error": "Recipe not found"})
    
### CRUD OPERATIONS ###

@app.route('/add_to_favorites', methods=['POST', 'GET'])
def add_to_favorites() -> Response:
    """
    Endpoint to add a recipe to the favorites.
    Returns:
        Response: JSON response indicating the success or failure of the operation.
    """

    recipe_title = request.form['recipe_title']
    recipe_instructions = request.form['recipe_instructions']
    recipe_ingredients = request.form['recipe_ingredients']
    recipe_image = request.form['recipe_image']
    recipe_id = request.form['recipe_id']

    recipe = Recipe(recipe_title, recipe_id, recipe_instructions, recipe_ingredients, recipe_image)
    success = app.fav_recipes.add_recipe(recipe)

    if success:
        return jsonify({"message": "Recipe added to favorites successfully"})
    else:
        return jsonify({"error": "Failed to add recipe to favorites"})

@app.route('/create_recipe', methods=['POST'])
def create_recipe() -> Response:
    """
    Endpoint to create a new recipe and add it to the favorites.
    Returns:
        Response: JSON response indicating the success or failure of the operation.
    """

    recipe_title = request.form['r_title']
    recipe_id = request.form['r_id']
    recipe_instructions = request.form['r_instructions']
    recipe_ingredients = request.form['r_ingredients']
    recipe_image = request.form['r_image']

    recipe = Recipe(recipe_title, recipe_id, recipe_instructions, recipe_ingredients, recipe_image)
    recipe_added = app.fav_recipes.add_recipe(recipe)

    if recipe_added:
        return jsonify({"message": "Recipe added successfully"}), 201
    else:
        return jsonify({"error": "Recipe with this title already exists"}), 409

@app.route('/delete_recipe', methods=['DELETE'])
def delete_recipe() -> Response:
    """
    Endpoint to delete a recipe from the favorites list.
    Returns:
        Response: JSON response indicating the success or failure of the operation.
    """

    data = request.get_json()
    r_title = data.get('r_title')
    recipes = app.fav_recipes.get_recipes()

    if r_title in recipes:
        recipe = Recipe(
            recipes[r_title]["title"],
            recipes[r_title]["recipe_id"],
            recipes[r_title]["instructions"],
            recipes[r_title]["ingredients"],
            recipes[r_title]["image"]
        )

        if app.fav_recipes.delete_recipe(recipe):
            return jsonify({"message": "Recipe deleted successfully"}), 200

    return jsonify({"error": "Recipe with this title does not exist"}), 404

@app.route('/update_recipe_instructions', methods=['PUT'])
def update_recipe() -> Response:
    """
    Endpoint to update the instructions of a recipe in the favorites.
    Returns:
        Response: JSON response indicating the success or failure of the operation.
    """

    data = request.get_json()
    r_title = data.get('r_title')
    new_instructions = data.get('r_instructions')

    recipes = app.fav_recipes.get_recipes()

    if r_title in recipes:
        recipe = Recipe(
            recipes[r_title]["title"],
            recipes[r_title]["recipe_id"],
            recipes[r_title]["instructions"],
            recipes[r_title]["ingredients"],
            recipes[r_title]["image"]
        )

        if app.fav_recipes.update_recipe(recipe, new_instructions):
            return jsonify({"message": "Ingredients updated successfully"}), 200

    return jsonify({"error": "Recipe with this title does not exist"}), 404

### END OF CRUD OPERATIONS ###

@app.route('/api/meals')
def get_meals() -> Union[dict, Response]:
    """
    Endpoint to retrieve meals based on query parameters.
    Returns:
        Union[dict, Response]: JSON response containing the meals or an error message.
    """

    query = request.args.get('query')
    min_calories = request.args.get('minCalories', type=int)
    max_calories = request.args.get('maxCalories', type=int)

    url = f'{SPOONACULAR_API}/complexSearch?query={query}&apiKey={API_KEY}'
    if min_calories is not None and max_calories is not None:
        url += f'&minCalories={min_calories}&maxCalories={max_calories}'

    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch meals'}), 500

    return response.json()

@app.route('/api/recipe/<int:meal_id>')
def get_recipe(meal_id: int) -> Union[dict, Response]:
    """
    Endpoint to retrieve a recipe by its ID.
    Args:
        meal_id (int): The ID of the recipe.
    Returns:
        Union[dict, Response]: JSON response containing the recipe or an error message.
    """

    url = f'{SPOONACULAR_API}/{meal_id}/information?apiKey={API_KEY}'
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch recipe'}), 500

    return response.json()

@app.route('/api/random')
def get_random_recipe() -> Union[dict, Response]:
    """
    Endpoint to retrieve a random recipe.
    Returns:
        Union[dict, Response]: JSON response containing the random recipe or an error message.
    """

    url = f'{SPOONACULAR_API}/random?apiKey={API_KEY}'
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch random recipe'}), 500

    data = response.json()
    return jsonify(data['recipes'][0])

@app.route('/api/price_breakdown_widget/<int:meal_id>')
def get_price_breakdown_widget(meal_id: int) -> Union[Response, tuple]:
    """
    Endpoint to retrieve the price breakdown widget for a specific meal.
    Args:
        meal_id (int): The ID of the meal.
    Returns:
        Union[Response, tuple]: Response object containing the image data or an error message.
    """

    url = f'{SPOONACULAR_API}/{meal_id}/priceBreakdownWidget.png?apiKey={API_KEY}'
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch price breakdown widget'}), 500

    return Response(response.content, content_type='image/png')

def clean_html_response(html: str) -> Tuple[Optional[List[str]], Optional[List[str]]]:
    """
    Helper function to clean HTML response and extract ingredients and prices.
    Args:
        input_string (str): The HTML string to be cleaned.
    Returns:
        Tuple[Optional[List[str]], Optional[List[str]]]: A tuple containing lists of ingredients and prices, or None if not found.
    """

    parsed_html = BeautifulSoup(html, "html.parser")

    ingredients_container = parsed_html.find('div', id='spoonacularPriceBreakdownTable') \
        .find('div', style=lambda value: value and 'float:left;max-width:80%' in value)
    ingredients = [ingredient.strip() for ingredient in ingredients_container.stripped_strings]

    prices_container = parsed_html.find('div', id='spoonacularPriceBreakdownTable') \
        .find('div', style=lambda value: value and 'text-align:right;display:inline-block;float:left;padding-left:1em' in value)
    prices = [price.strip() for price in prices_container.stripped_strings]

    return ingredients, prices

@app.route('/api/price_breakdown/<int:meal_id>')
def get_price_breakdown(meal_id: int) -> jsonify:
    """
    Fetches the price breakdown widget for a meal from Spoonacular API.

    Parameters:
        meal_id (int): The ID of the meal for which the price breakdown widget is requested.

    Returns:
        jsonify: JSON response containing the price breakdown widget information.
    """

    url = f'{SPOONACULAR_API}/{meal_id}/priceBreakdownWidget?apiKey={API_KEY}'
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch price breakdown widget'}), 500

    data = clean_html_response(response.text)
    return jsonify(data), 200, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/api/recipe/info/<int:meal_id>')
def get_recipe_info(meal_id: int) -> Union[dict, Response]:
    """
    Endpoint to retrieve a recipe by its ID.
    Args:
        meal_id (int): The ID of the recipe.
    Returns:
        Union[dict, Response]: JSON response containing the recipe or an error message.
    """
    
    url = f'{SPOONACULAR_API}/{meal_id}/information?apiKey={API_KEY}'
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch recipe'}), 500

    return response.json()

if __name__ == '__main__':
    app.run(debug=True)
