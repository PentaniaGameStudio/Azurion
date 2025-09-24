// /PotionBuilder/js/recipes/view.js
import { qs, el, clear } from "../core/dom.js";
import { sub } from "../core/events.js";
import { getRecipes, findIngredientByName } from "../shared/data.js";
import { resetSelection, silent_setBinder, silent_setCatalyst, silent_toggleReactant, refresh } from "../core/store.js";

const list = qs("#recipesList");
let builtOnce = false;

async function applyVariant(variantNames){
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

function groupCard(recipe){
  const group = el("div", { class: "recipe-group" });
  const title = el("div", { class: "recipe-group-title" }, `${recipe.emoji || "🧪"} ${recipe.name}`);

  const row   = el("div", { class: "recipe-variants" });

  const variants = Array.isArray(recipe.ingredients) ? recipe.ingredients : [];
  variants.forEach((variantArr, i) => {
    const n = i + 1;
    const btn = el("button", { class: "recipe-variant-btn", type: "button" }, `recette ${n}`);
    btn.addEventListener("click", () => applyVariant(variantArr));
    row.appendChild(btn);
  });

  group.append(title, row);
  return group;
}

async function build(){
  if (!list) return;
  clear(list);
  const recipes = await getRecipes();
  recipes.forEach(r => list.appendChild(groupCard(r)));
  builtOnce = true;
}

// Ne construit que quand on ouvre l’onglet Recette
sub("view:change", (v) => {
  if (v === "recipe" && !builtOnce) build();
});

// Si on arrive déjà sur #recipe
if (location.hash.toLowerCase() === "#recipe") build();
