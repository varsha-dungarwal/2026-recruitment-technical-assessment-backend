from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	name: str

@dataclass
class RequiredItem():
	name: str
	quantity: int

@dataclass
class Recipe(CookbookEntry):
	required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
	cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook: Dict[str, CookbookEntry] = {}

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str) -> Union[str | None]:
	if not recipeName: 
		return None
	name = re.sub(r'[-_]+', ' ', recipeName)
	name = re.sub(r'[^A-Za-z\s]', '', name)
	name = re.sub(r'\s+', ' ', name).strip()
	if len(name) == 0:
		return None
	name = name.title()
	return name


# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
	data = request.get_json()
	if not data: 
		return  return_message("Request body is invalid", 400)
	entry_type = data.get("type")
	name = data.get("name")
	if entry_type not in {"recipe", "ingredient"}:
		return return_message("Type must be 'recipe' or 'ingredient'", 400)
	if name is None or name in cookbook: 
		return return_message("Entry name must be unique", 400)
	# --- Ingredient ---
	if entry_type == "ingredient":
		cook_time = data.get("cookTime")
		if not isinstance(cook_time, int) or cook_time < 0:
			return  return_message("cookTime must be a positive integer", 400)
		cookbook[name] = Ingredient(name = name, cook_time = cook_time)
		return {}, 200
	# --- Recipe ---
	required_items = data.get("requiredItems")
	if not isinstance(required_items,list) :
		return return_message("requiredItems must be a list", 400)
	seen = set()
	items = []
	for item in required_items:
		item_name = item.get("name")
		quantity = item.get("quantity")
		if (not item_name or item_name in seen):  
			return return_message("Invalid required item name", 400)
		if (not isinstance(quantity,int) or quantity < 0):
			return return_message("Quantity must be a positive integer", 400)
		seen.add(item_name)
		items.append(RequiredItem(name = item_name, quantity = quantity))
	cookbook[name] = Recipe(name = name, required_items=items)		
	return {}, 200

# Helper function to return the error message and successful message in the required form 
def return_message(message: str, statuscode: int):
    return jsonify({"error": message}), statuscode

# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route('/summary', methods=['GET'])
def summary():
	name = request.args.get("name")
	if not name or name not in cookbook:
		return return_message("Recipe not found", 400)
	entry = cookbook[name]
	if not isinstance(entry, Recipe):
		return return_message("Not a recipe", 400)
	ingredients, cook_time = get_ingredients(name)
	if ingredients is None:
		return return_message("Recipe contains missing items", 400)
	ingredient_list = [
        {"name": n, "quantity": q}
        for n, q in ingredients.items()
    ]
	return jsonify({
        "name": name,
        "cookTime": cook_time,
        "ingredients": ingredient_list
    }), 200

def get_ingredients(name: str, time: int = 1):
	if name not in cookbook:
		return None, None
	entry = cookbook[name]
	if isinstance(entry, Ingredient):
		return (
            {name: time}, 
            entry.cook_time * time
        )
	
	ingredients = {}
	total_time = 0
	for item in entry.required_items:
		sub_ingredients, sub_time = get_ingredients(
            item.name,
            time * item.quantity
        )
		if sub_ingredients is None:
			return None, None
		total_time += sub_time
		for name, qty in sub_ingredients.items():
			ingredients[name] = ingredients.get(name, 0) + qty

	return ingredients, total_time


# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)
