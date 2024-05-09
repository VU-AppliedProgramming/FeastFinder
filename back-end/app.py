from flask import Flask, jsonify, request
import os
import requests
from flask_cors import CORS
import re
import matplotlib.pyplot as plt
import base64
import io
from test import Test
from favrecipes import FavRecipes

app = Flask(__name__)
CORS(app)

# Spoonacular API key
API_KEY = os.environ.get('API_KEY')

SPOONACULAR_API = "https://api.spoonacular.com/recipes/"

fav_recipes = FavRecipes('myfavrecipes.json')

@app.route('/health')
def health_check():
    return 'OK', 200

@app.route('/test')
def test():
    recipes= fav_recipes.get_recipes()
    return jsonify(recipes)




@app.route('/show_one_favorite/<recipe_id>')
def s_one_fav(recipe_id):
    recipes = fav_recipes.get_recipes()
    if recipe_id in recipes:
        return jsonify({recipe_id: recipes[recipe_id]})
    else:
        return jsonify({"error": "Recipe not found"})
    




### CRUD OPERATIONS ###

@app.route('/create_recipe', methods=['POST'])
def create_recipe():
    r_title = request.form['r_title']
    r_id = request.form['r_id']
    r_instructions = request.form['r_instructions']
    r_ingredients = request.form['r_ingredients']
    r_image = request.form['r_image']
    
    recipe_added = fav_recipes.add_recipe(r_title, r_instructions, r_ingredients, r_image, r_id)
    
    if recipe_added:
        return jsonify({"message": "Recipe added successfully"}), 201
    else:
        return jsonify({"error": "Recipe with this title already exists"}), 409
    


@app.route('/delete_recipe', methods=['DELETE'])
def delete_recipe():
    data = request.get_json()
    r_title = data.get('r_title')

    if fav_recipes.delete_recipe(r_title):
        return jsonify({"message": "Recipe deleted successfully"}), 200
    else:
        return jsonify({"error": "Recipe with this title does not exist"}), 404
    

@app.route('/update_recipe_instructions', methods=['PUT'])
def update_recipe():
    data = request.get_json()
    r_title = data.get('r_title')
    new_instructions = data.get('r_instructions')

    if fav_recipes.update_recipe(r_title, new_instructions):
        return jsonify({"message": "Instructions updated successfully"}), 200
    else:
        return jsonify({"error": "Recipe with this title does not exist"}), 404


### CRUD OPERATIONS ###

@app.route('/api/meals')
def get_meals():
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
def get_recipe(meal_id):
    url = f'{SPOONACULAR_API}/{meal_id}/information?apiKey={API_KEY}'
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch recipe'}), 500
    
    data = response.json()
    return data

@app.route('/api/random')
def get_random_recipe():
    url = f'{SPOONACULAR_API}/random?apiKey={API_KEY}'
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch random recipe'}), 500
    
    data = response.json()
    return jsonify(data['recipes'][0])

@app.route('/api/price_breakdown_widget/<int:meal_id>')
def get_price_breakdown_widget(meal_id):
    url = f'{SPOONACULAR_API}/{meal_id}/priceBreakdownWidget?apiKey={API_KEY}'
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch price breakdown widget'}), 500
    
    return response.text, 200, {'Content-Type': 'text/html'}

def clean_html_response(input_string):
    # Extract prices
    price_section = re.search(r'<b>Price<\/b>(.*?)<div', input_string, re.DOTALL)
    if price_section:
        prices_with_br = re.findall(r'\$(.*?)<br>', price_section.group(1))
        prices = [price.replace('$', '').replace('<br>', '').strip() for price in prices_with_br]
    else:
        prices = None

    # Extract ingredients
    ingredients_section = re.search(r'<b>Ingredient<\/b>(.*?)<div', input_string, re.DOTALL)
    if ingredients_section:
        ingredients_with_br = re.findall(r'<br>(.*?)<br>', ingredients_section.group(1))
        ingredients = [ingredient.strip() for ingredient in ingredients_with_br]
    else:
        ingredients = None

    return ingredients, prices

@app.route('/clean_html', methods=['POST'])
def clean_html():
    html_string = request.data.decode("utf-8")
    ingredient_names, prices = clean_html_response(html_string)
    
    pie_chart_image_base64 = create_pie_chart(ingredient_names, prices) 

    return jsonify({'pie_chart_image_base64': pie_chart_image_base64})

def create_pie_chart(labels, values):
    values = [float(v) for v in values]

    plt.figure(figsize=(15, 8))
    patches, _, _ = plt.pie(values, labels=None, startangle=140, autopct=lambda p: '${:.2f}'.format(p * sum(values) / 100), pctdistance=0.85)

    plt.legend(patches, labels, loc="best")
    plt.title("Ingredients Distribution")
    plt.axis('equal')

    # Save the pie chart as a PNG image
    img_data = io.BytesIO()
    plt.savefig(img_data, format='png')
    img_data.seek(0)
    img_base64 = base64.b64encode(img_data.read()).decode('utf-8')

    return img_base64

if __name__ == '__main__':
    app.run(debug=True)




###################################
###################################



### https://api.spoonacular.com/recipes/1082038/priceBreakdownWidget?apiKey=25f10c03748a4a99bed2f8dfb40d284f ### to check response
