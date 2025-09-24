// /PotionBuilder/js/shared/data.js
// Objectif : fournir ORIGIN_TREE, getIngredients(), getRecipes(), plus quelques helpers.
// - Tente d'importer /assets/data.js comme module (export ORIGIN_TREE).
// - Sinon, fallback : fetch du JS puis extraction du literal.
// - Ingredients / Recipes sont chargés via fetch JSON (mise en cache).

let ORIGIN_TREE = {};
let _ingredients = null;
let _recipes = null;

// Caches en mémoire (module-scope)
let _recipesCache = null;
let _ingredientsCache = null;
const PATHS = {
  tree: "/PotionBuilder/assets/data.js",
  ingredients: "/PotionBuilder/assets/ingredients.json",
  recipes: "/PotionBuilder/assets/recipes.json"
};

// --- Chargement ORIGIN_TREE ---
async function loadTree() {
  if (Object.keys(ORIGIN_TREE).length) return ORIGIN_TREE;

  // 1) Essai import ESM
  try {
    const mod = await import(PATHS.tree + `?v=${Date.now()}`);
    if (mod && mod.ORIGIN_TREE) {
      ORIGIN_TREE = mod.ORIGIN_TREE;
      return ORIGIN_TREE;
    }
  } catch { /* ignore */ }

  // 2) Fallback : fetch + parse
  try {
    const txt = await (await fetch(PATHS.tree, { cache: "no-store" })).text();
    // Cherche "ORIGIN_TREE = { ... }"
    const match = txt.match(/ORIGIN_TREE\s*=\s*({[\s\S]*});?/);
    if (match) {
      // On parse avec Function pour éviter eval dans le scope global
      ORIGIN_TREE = (new Function(`return (${match[1]});`))();
      return ORIGIN_TREE;
    }
    // OU "const ORIGIN_TREE = {...}"
    const matchConst = txt.match(/const\s+ORIGIN_TREE\s*=\s*({[\s\S]*});?/);
    if (matchConst) {
      ORIGIN_TREE = (new Function(`return (${matchConst[1]});`))();
      return ORIGIN_TREE;
    }
  } catch (e) {
    console.error("[data] ORIGIN_TREE load error:", e);
  }

  console.warn("[data] ORIGIN_TREE introuvable, utilisation d'un arbre vide.");
  return ORIGIN_TREE;
}

// --- Chargement JSON ---
async function loadJSONOnce(path, targetName) {
  try {
    const res = await fetch(path, { cache: "no-store" });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const data = await res.json();
    return data;
  } catch (e) {
    console.error(`[data] Échec chargement ${targetName}:`, e);
    return [];
  }
}

// --- API Publique ---
export async function getOriginTree() {
  return await loadTree();
}

export async function getIngredients() {
  if (_ingredients) return _ingredients;
  _ingredients = await loadJSONOnce(PATHS.ingredients, "ingredients.json");
  return _ingredients;
}

export async function getRecipes(){
  if (Array.isArray(_recipesCache)) return _recipesCache;

  const res = await fetch(PATHS.recipes, { cache: "no-store" });
  if (!res.ok) throw new Error(`recipes fetch failed: ${res.status}`);

  const arr = await res.json();

  // Dédoublonne les variantes identiques pour un même nom de recette
  const seen = new Set();
  _recipesCache = arr.map(r => ({
    emoji: r.emoji || "🧪",
    name:  String(r.name || "").trim(),
    bonus: Number(r.bonus || 0),
    ingredients: (Array.isArray(r.ingredients) ? r.ingredients : []).filter(v => {
      if (!Array.isArray(v)) return false;
      const key = JSON.stringify([...v].sort());
      const sig = `${r.name}|${key}`;
      if (seen.has(sig)) return false;
      seen.add(sig);
      return true;
    })
  }));

  return _recipesCache;
}

// Helpers de catégorisation (chaînes normalisées)
export const CATS = Object.freeze({
  binder: "Liant",
  catalyst: "Catalyseur",
  reactant: "Réactif",
});

// Trouve un ingrédient par son nom
export async function findIngredientByName(name) {
  const list = await getIngredients();
  return list.find(i => i?.name === name) || null;
}
