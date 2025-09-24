// /PotionBuilder/js/creator/compute.js
import { findIngredientByName, getRecipes } from "../shared/data.js";

/**
 * @param {{binder:string|null,catalyst:string|null,reactants:string[]}} sel
 * @returns {Promise<{ totalDifficulty:number, mathLine:string, recipe:null|{name:string,emoji?:string,bonus?:number} }>}
 */
export async function computePotion(sel){
  const bits = [];
  let total = 0;

  async function push(name, label){
    if (!name) return;
    const ing = await findIngredientByName(name);
    const diff = Number(ing?.difficulty ?? 0);
    total += diff;
    bits.push(`${diff} (${label})`);
  }

  await push(sel.binder, "Liant");
  await push(sel.catalyst, "Catalyseur");
  for (const r of sel.reactants) await push(r, "Réactif");

  // Sélection (Set) pour comparer exactement aux variantes
  const allPicked = [
    ...(sel.binder ? [sel.binder] : []),
    ...(sel.catalyst ? [sel.catalyst] : []),
    ...sel.reactants
  ];
  const pickedSet = new Set(allPicked);

  // Recette valide si ET SEULEMENT SI la sélection correspond EXACTEMENT
  // aux ingrédients d'une variante (ordre indifférent, ni plus ni moins).
  let matched = null;
  const recipes = await getRecipes();
  for (const r of recipes){
    const variants = Array.isArray(r.ingredients) ? r.ingredients : [];
    const ok = variants.some(variant => {
      if (!Array.isArray(variant)) return false;
      if (variant.length !== allPicked.length) return false;
      const varSet = new Set(variant);
      if (varSet.size !== pickedSet.size) return false;
      for (const v of pickedSet) if (!varSet.has(v)) return false;
      return true;
    });
    if (ok){ matched = r; break; }
  }

  if (matched?.bonus){
    total = Math.max(0, total - Number(matched.bonus));
    bits.push(`- bonus de recette (${matched.bonus})`);
  }

  return {
    totalDifficulty: total,
    mathLine: bits.join(" + ").replace("+ -","- "),
    recipe: matched ? { name: matched.name, emoji: matched.emoji, bonus: matched.bonus } : null
  };
}
