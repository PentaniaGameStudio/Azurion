// /PotionBuilder/js/recipes/view.js
import { qs, el, clear } from "../core/dom.js";
import { sub } from "../core/events.js";
import { getRecipes, findIngredientByName, isUnlockedByBooks } from "../shared/data.js";
import { getState, resetSelection, silent_setBinder, silent_setCatalyst, silent_toggleReactant, refresh } from "../core/store.js";

const list = qs("#recipesList");
let recipesCache = null;
let isActive = false;

async function applyVariant(variantNames, recipe){
  const ownedBooks = getState().books;
  if (!isUnlockedByBooks(recipe?.books, ownedBooks)) return;

  resetSelection();
  for (const name of variantNames){
    const ing = await findIngredientByName(name);
    if (!ing) continue;
    if (ing.cat === "Liant") silent_setBinder(name);
    else if (ing.cat === "Catalyseur") silent_setCatalyst(name);
    else silent_toggleReactant(name);
  }
  
  refresh();
}

function ensureRecipes(){
  if (recipesCache) return Promise.resolve(recipesCache);
  return getRecipes().then(list => (recipesCache = list));
}

function groupCard(recipe){
  const group = el("div", { class: "recipe-group" });
  const title = el("div", { class: "recipe-group-title" }, `${recipe.emoji || "🧪"} ${recipe.name}`);

  const elements = [title];

  if (recipe?.desc){
    elements.push(el("p", { class: "recipe-desc" }, recipe.desc));
  }

  const row   = el("div", { class: "recipe-variants" });
  const variants = Array.isArray(recipe?.ingredients) ? recipe.ingredients : [];
  variants.forEach((variantArr, i) => {
    const n = i + 1;
    const btn = el("button", { class: "recipe-variant-btn", type: "button" }, `recette ${n}`);
    btn.title = Array.isArray(variantArr) ? variantArr.join(", ") : "";
    btn.addEventListener("click", () => applyVariant(variantArr, recipe));
    row.appendChild(btn);
  });
  elements.push(row);

  if (recipe?.books?.length){
    const booksText = recipe.books.join(", ");
    elements.push(el("div", { class: "recipe-info muted" }, `📘 Débloqué avec : ${booksText}`));
  }

  elements.forEach(elm => group.appendChild(elm));
  return group;
}

function render(){
  if (!list || !isActive) return;
  (async () => {
    const recipes = await ensureRecipes();
    const ownedBooks = getState().books;
    clear(list);
    recipes
      .filter(r => isUnlockedByBooks(r?.books, ownedBooks))
      .forEach(r => list.appendChild(groupCard(r)));
  })().catch(e => console.error("[recipes] render error", e));
}

// Ne construit / rafraîchit que quand on ouvre l’onglet Recette
sub("view:change", (v) => {
  isActive = v === "recipe";
  if (isActive) render();
});

// Rafraîchir quand la collection de livres change (si onglet ouvert)
sub("books:changed", () => {
  if (isActive) render();
});

// Si on arrive déjà sur #recipe
if (location.hash.toLowerCase() === "#recipe") {
  isActive = true;
  render();
}