// /PotionBuilder/js/shared/current-potion.js
import { sub } from "../core/events.js";
import { getState, getCurrentPotion, resetSelection } from "../core/store.js";

import { qs, clear } from "../core/dom.js";
import { findIngredientByName } from "../shared/data.js";

const elEmojis = qs("#cpEmojis");
const elTotals = qs("#cpTotals");
const elDetails = qs("#cpDetails");
const elMath = qs("#cpMath");

let isBatching = false;
let computePotion = null; // injecté dynamiquement si le module existe

(async function lazyLoadCompute(){
  try {
    const mod = await import("../creator/compute.js");
    if (mod && typeof mod.computePotion === "function") computePotion = mod.computePotion;
  } catch {
    // pas grave : fallback
  }
})();

// Fallback de calcul minimal (si compute n'est pas encore dispo)
async function fallbackCompute(selection) {
  // additionne les difficultés, pas de bonus de recette
  let total = 0;
  const parts = [];

  const push = async (name, label) => {
    if (!name) return;
    const ing = await findIngredientByName(name);
    if (ing) {
      total += Number(ing.difficulty || 0);
      parts.push(`${ing.difficulty || 0} (${label})`);
    }
  };

  await push(selection.binder, "Liant");
  await push(selection.catalyst, "Catalyseur");
  for (const r of selection.reactants) await push(r, "Réactif");

  return { totalDifficulty: total, mathLine: parts.join(" + "), recipe: null };
}

function emojiForCat(cat) {
  if (cat === "Liant") return "💧";
  if (cat === "Catalyseur") return "⚗️";
  if (cat === "Réactif") return "🧬";
  return "❓";
}

function summarizeEmojis(sel){
  const bits = [];
  if (sel.binder) bits.push("💧");
  if (sel.catalyst) bits.push("⚗️");
  if (sel.reactants?.length) bits.push("🧬".repeat(Math.max(1, sel.reactants.length)));
  return bits.join(" ");
}

async function render() {
	async function render() {
	  if (isBatching) return;      // <-- ignore les rerenders pendant un reset

	  const _state = getState();   // (non utilisé ici mais utile si besoin)
	  const sel = getCurrentPotion();
	  // ...
	}

  const _state = getState(); // (non utilisé ici mais utile si besoin)
  const sel = getCurrentPotion();

  // Calcul de la difficulté (via compute si dispo, sinon fallback)
  let result;
  try {
    result = computePotion ? await computePotion(sel) : await fallbackCompute(sel);
  } catch (e) {
    console.error("[current-potion] compute error:", e);
    result = await fallbackCompute(sel);
  }

  // Ligne 1 / 2 : si recette trouvée -> deux lignes (nom puis emojis)
  const emojisLine = summarizeEmojis(sel) || "(Aucun ingrédient sélectionné)";
  if (result?.recipe?.name) {
    const title = `${result.recipe.emoji || "🧪"} ${result.recipe.name}`;
    elEmojis.innerHTML = `${title}<br>${emojisLine}`;
  } else {
    elEmojis.textContent = emojisLine;
  }

  // Totaux : boutons façon Glyph, avec valeurs par défaut
  clear(elTotals);
  const totals = [
    { label: "Liant",      icon: "💧", value: sel.binder || "—" },
    { label: "Catalyseur", icon: "⚗️", value: sel.catalyst || "—" },
    { label: "Réactifs",   icon: "🧬", value: String(sel.reactants?.length || 0) },
    { label: "Difficulté", icon: "🧠", value: String(result?.totalDifficulty ?? 0) }
  ];
  for (const t of totals){
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "statBtn catBtn";
    btn.textContent = `${t.icon} ${t.label} : ${t.value}`;
    elTotals.append(btn);
  }

	// Détails ingrédients (entre les boutons et la ligne de calcul)
	clear(elDetails);
	elDetails.style.display = "block"; // toujours visible

	const box = document.createElement("div");
	box.className = "desc-box stack";

	const addDetail = async (name) => {
	  if (!name) return;
	  const ing = await findIngredientByName(name);
	  if (!ing) return;
	  const row = document.createElement("div");
	  row.className = "row desc-line";
	  // Format demandé : "💧  **Eau pure** -> *Potion stable*"
	  row.innerHTML =
		`${emojiForCat(ing.cat)} <b>${ing.name}</b> -> <i>${ing.effect || ""}</i>`;
	  box.appendChild(row);
	};

	await addDetail(sel.binder);
	await addDetail(sel.catalyst);
	for (const r of sel.reactants) await addDetail(r);

	if (box.children.length === 0){
	  const empty = document.createElement("div");
	  empty.className = "tiny muted";
	  empty.textContent = "Aucun ingrédient sélectionné.";
	  box.appendChild(empty);
	}

	elDetails.appendChild(box);


  // Ligne math
  elMath.style.display = result?.mathLine ? "block" : "none";
  elMath.textContent = result?.mathLine || "";
}


const resetBtn = document.getElementById("resetBtn");
if (resetBtn){
  resetBtn.addEventListener("click", () => {
    resetSelection(); // 1 seule mutation + 1 seul event
  });
}

// Écouteurs
["selection:changed","books:changed"].forEach(t => sub(t, render));
["filters:cat","filters:origins"].forEach(t => sub(t, render));

// Première peinture
render();
