import json
import typing
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

data_source_dir = Path(__file__).parent / 'mcdata'
recipe_dir = data_source_dir / 'recipes'
tags_dir = data_source_dir / 'tags'
lang_file = data_source_dir / 'lang.json'


@dataclass
class Ingredient:
	allowed_items: typing.List[str]
	count: int


@dataclass
class CraftingRecipe:
	name: str
	result: str
	ingredients: typing.List[Ingredient]


def deminecraft(name: str) -> str:
	return name[10:]


class RecipeProvider:

	def __init__(self):
		self.tags: typing.Dict[str, typing.List[str]] = {}
		self.recipes: typing.List[CraftingRecipe] = []
		self.lang: typing.Dict[str, str] = {}
		self.load_everything()

	def get_all_names(self, obj: str) -> typing.List[str]:
		names = [obj]
		obj = obj.casefold()
		item_name = self.lang.get(f'item.minecraft.{obj}')
		if item_name:
			names.append(item_name)
		block_name = self.lang.get(f'block.minecraft.{obj}')
		if block_name:
			names.append(block_name)
		return names

	def load_everything(self):
		self.load_lang()
		self.load_all_tags()
		self.load_all_recipes()

	def load_all_recipes(self):
		for recipe_file in recipe_dir.iterdir():
			with recipe_file.open() as fp:
				self.load_recipe(recipe_file.name.split(".")[0], fp)

	def load_lang(self):
		with lang_file.open() as fp:
			self.lang = json.load(fp)

	def load_all_tags(self):
		for subdir in tags_dir.iterdir():
			self.load_tags(subdir)

	def load_tags(self, tag_dir: Path):
		for tag_file in tag_dir.iterdir():
			with tag_file.open() as fp:
				self.load_tag(tag_file.name.split(".")[0], fp)

	def load_tag(self, name, fp):
		data = json.load(fp)
		if name not in self.tags:
			self.tags[name] = []
		self.tags[name] += data['values']

	def follow_tags(self, tag: str) -> typing.List[str]:
		def internal(t):
			for el in self.tags[t]:
				if el[0] == '#':
					for subel in internal(deminecraft(el[1:])):
						yield subel
				else:
					yield deminecraft(el)

		return list(internal(tag))

	def parse_ingredient(self, obj: dict) -> typing.List[str]:
		if isinstance(obj, list):
			x = []
			for i in obj:
				x += self.parse_ingredient(i)
			return x
		if 'item' in obj:
			return [deminecraft(obj['item'])]
		if 'tag' in obj:
			return self.follow_tags(deminecraft(obj['tag']))
		raise RuntimeError("Invalid recipe")

	def load_crafting_shapeless(self, name: str, data: dict) -> CraftingRecipe:
		result = deminecraft(data['result']['item'])
		ingredient_counts = defaultdict(int)
		ingredients_content = {}
		for i in data['ingredients']:
			ingredient_counts[str(i)] += 1
			ingredients_content[str(i)] = self.parse_ingredient(i)
		ingredients = []
		for ingredient, count in ingredient_counts.items():
			ingredients.append(Ingredient(ingredients_content[ingredient], count))
		return CraftingRecipe(name, result, ingredients)

	def load_crafting_shaped(self, name: str, data: dict) -> CraftingRecipe:
		item_counts = defaultdict(int)
		for row in data['pattern']:
			for cell in row:
				if cell != " ":
					item_counts[cell] += 1
		ingredients = []
		for item, count in item_counts.items():
			obj = data['key'][item]
			ingredients.append(Ingredient(self.parse_ingredient(obj), count))
		result = deminecraft(data['result']['item'])
		return CraftingRecipe(name, result, ingredients)

	def load_recipe(self, name, fp):
		data = json.load(fp)
		loader = 'load_' + deminecraft(data['type'])
		if not hasattr(self, loader):
			return
		recipe = getattr(self, loader)(name, data)
		self.recipes.append(recipe)


DEFAULT_RECIPE_PROVIDER = RecipeProvider()
