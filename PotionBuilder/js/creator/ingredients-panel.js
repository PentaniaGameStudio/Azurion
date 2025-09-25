// /PotionBuilder/js/creator/ingredients-panel.js
import { qs, qsa, clear } from "../core/dom.js";
import { sub } from "../core/events.js";
import { getState, setCategory, setBinder, setCatalyst, toggleReactant } from "../core/store.js";
import { getIngredients, isUnlockedByBooks } from "../shared/data.js";
import { ingredientCard } from "../shared/ui-kit.js";

const elTabs = qs("#ingCatTabs");
const elGrid = qs("#ingredientsGrid");

// map catégorie texte -> type store
const CAT_MAP = {
  "Liant": "binder",
  "Catalyseur": "catalyst",
  "Réactif": "reactant"
};

const CAT_ORDER = {
  "Liant": 0,
  "Catalyseur": 1,
  "Réactif": 2
};

function passesCategoryFilter(item, cat){
  if (!cat || cat === "all") return true;
  const t = CAT_MAP[item.cat] || "";
  return t === cat;
}
function passesOriginFilter(item, origins){
  if (!origins?.length) return true;
  const list = item.origins || [];
  return list.some(o => origins.includes(o));
}

function selectIngredient(item){
  const type = CAT_MAP[item.cat] || "";
  if (type === "binder") setBinder(item.name);
  else if (type === "catalyst") setCatalyst(item.name);
  else toggleReactant(item.name);
}

async function render(){
  const state = getState();
  const list = await getIngredients();

  // MAJ onglets visuels
  elTabs?.querySelectorAll(".catBtn").forEach(b => b.classList.toggle("on", b.dataset.cat === state.filters.cat));

  clear(elGrid);
   const filtered = list.filter(i =>
    passesCategoryFilter(i, state.filters.cat) &&
    passesOriginFilter(i, state.filters.origins)
  );

  const sorted = filtered.slice().sort((a, b) => {
    const ca = CAT_ORDER[a?.cat] ?? 99;
    const cb = CAT_ORDER[b?.cat] ?? 99;
    if (ca !== cb) return ca - cb;
    const na = String(a?.name || "").toLocaleLowerCase();
    const nb = String(b?.name || "").toLocaleLowerCase();
    return na.localeCompare(nb);
  });

  if (!sorted.length){
    const empty = document.createElement("div");
    empty.className = "muted";
    empty.textContent = "Aucun ingrédient ne correspond aux filtres.";
    elGrid.append(empty);
    return;
  }

  sorted.forEach(item => {
    const card = ingredientCard(item);

    // Locked si pas débloqué par livre
    const unlocked = isUnlockedByBooks(item?.books, state.books);
    if (!unlocked)
      return;
    else
      card.addEventListener("click", ()=> selectIngredient(item));
    

    // Etat actif selon selection
    const t = CAT_MAP[item.cat] || "";
    const sel = state.selection;
    const active =
      (t === "binder" && sel.binder === item.name) ||
      (t === "catalyst" && sel.catalyst === item.name) ||
      (t === "reactant" && sel.reactants.includes(item.name));
    if (active) card.classList.add("active");

    elGrid.append(card);
  });
}

function initEvents(){
  // Clic catégorie
  elTabs?.addEventListener("click", (e)=>{
    const b = e.target.closest(".catBtn");
    if (!b) return;
    setCategory(b.dataset.cat);
  });

  // Re-render sur changements pertinents
  ["filters:cat","filters:origins","books:changed","selection:changed"].forEach(t => sub(t, render));
}

// boot
initEvents();
render();
