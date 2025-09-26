# Start.py
from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from config import Config

# Infrastructure
from infrastructure.repositories import JsonIngredientRepo, JsonRecipeRepo, JsDataRepo

# Application services
from application.validators import ValidationService
from application.integrity import IntegrityService

# Presenters
from adapters.presenters import (
    BooksPresenter,
    IngredientsPresenter,
    OriginsPresenter,
    InspectionPresenter,
    RecipesPresenter,
)

# UI
from UI.main_window import MainWindow

from application.use_cases import (
    CreateIngredient, UpdateIngredient, DeleteIngredient, DuplicateIngredient,
    CreateRecipe, UpdateRecipe, DeleteRecipe, DuplicateRecipe,
    AddBook, RenameBook, RemoveBook, MigrateBookRefs,
    AddOrigin, RenameOrigin, RemoveOrigin, MigrateOriginRefs
)

def build_container(cfg: Config):
    # Repositories
    ingredients_repo = JsonIngredientRepo(cfg.ingredients_path)
    recipes_repo = JsonRecipeRepo(cfg.recipes_path)
    data_repo = JsDataRepo(cfg.data_js_path)

    # Services Application
    validator = ValidationService(
        ingredients_repo=ingredients_repo,
        recipes_repo=recipes_repo,
        data_repo=data_repo,
    )
    integrity = IntegrityService(
        ingredients_repo=ingredients_repo,
        recipes_repo=recipes_repo,
        data_repo=data_repo,
    )

    # Presenters
    books_presenter = BooksPresenter(data_repo, ingredients_repo)
    ingredients_presenter = IngredientsPresenter(ingredients_repo, data_repo, recipes_repo)
    origins_presenter = OriginsPresenter(data_repo, ingredients_repo)
    inspection_presenter = InspectionPresenter(integrity)
    recipes_presenter = RecipesPresenter(recipes_repo, ingredients_repo)

    # Use-cases (ingrédients – ceux nécessaires pour ce tab)
    uc_create_ing = CreateIngredient(ingredients_repo, validator)
    uc_update_ing = UpdateIngredient(ingredients_repo, validator)
    uc_delete_ing = DeleteIngredient(ingredients_repo, validator)
    uc_duplicate_ing = DuplicateIngredient(ingredients_repo, validator)

    return {
        "repos": {
            "ingredients": ingredients_repo,
            "recipes": recipes_repo,
            "data": data_repo,
            },
        "services": {
            "validator": validator,
            "integrity": integrity,
            },
        "presenters": {
            "books": books_presenter,
            "ingredients": ingredients_presenter,
            "origins": origins_presenter,
            "inspection": inspection_presenter,
            "recipes": recipes_presenter,
            },
        "use_cases": {
            "ingredients": {
                "create": uc_create_ing,
                "update": uc_update_ing,
                "delete": uc_delete_ing,
                "duplicate": uc_duplicate_ing,
                },
            "recipes": {
                "create":    CreateRecipe(recipes_repo, ingredients_repo, validator),
                "update":    UpdateRecipe(recipes_repo, ingredients_repo, validator),
                "delete":    DeleteRecipe(recipes_repo, validator),
                "duplicate": DuplicateRecipe(recipes_repo, validator),
                },
            "books": {
                "add":          AddBook(data_repo, validator),
                "rename":       RenameBook(data_repo, validator),
                "remove":       RemoveBook(data_repo, validator),
                "migrate_refs": MigrateBookRefs(data_repo, ingredients_repo, recipes_repo, validator),
                },
            "origins": {
                "add":          AddOrigin(data_repo, validator),
                "rename":       RenameOrigin(data_repo, validator),
                "remove":       RemoveOrigin(data_repo, validator),
                "migrate_refs": MigrateOriginRefs(data_repo, ingredients_repo, recipes_repo, validator),
            },
            }   
        }
    



def main():
    app = QApplication(sys.argv)
    cfg = Config.load()
    container = build_container(cfg)

    win = MainWindow(cfg, container, app)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
