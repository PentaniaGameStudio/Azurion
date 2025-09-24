import { el } from "/PotionBuilder/js/core/dom.js";
import { getState, setOrigins } from "/PotionBuilder/js/core/store.js";

// --- Chips / Pills ---
export function chip(text) {
  return el("span", { class: "chip" }, text);
}

export function pill(label, { removable = false, onRemove = null } = {}) {
  const root = el("span", { class: "pill" }, label);
  if (removable) {
    const x = el("span", { class: "x", title: "Retirer" }, "×");
    x.addEventListener("click", (e) => {
      e.stopPropagation();
      onRemove && onRemove();
    });
    root.append(" ", x);
  }
  return root;
}

export function renderOriginTree(treeObj, { selected = new Set() } = {}) {
  // --- Indexation de l'arbre pour connaître parents/enfants ---
  const parentOf = new Map();   // key -> parentKey | null
  const childrenOf = new Map(); // key -> string[]

  (function indexTree(obj, parentKey = null){
    for (const [k, v] of Object.entries(obj || {})) {
      parentOf.set(k, parentKey);
      const kids = Object.keys(v || {});
      childrenOf.set(k, kids);
      indexTree(v, k);
    }
  })(treeObj, null);

  const ul = el("ul", { class: "tree" });

  function buildNode(parentUl, key, value) {
    const li = el("li");
    const cb = el("input", { type: "checkbox" });
    cb.dataset.key = key;

    // état initial
    cb.checked = selected.has(key);
    li.append(cb, " ", key);
    parentUl.append(li);

    const kids = childrenOf.get(key) || [];
    if (kids.length) {
      const childUl = el("ul", { class: "tree" });
      li.append(childUl);
      kids.forEach(k => buildNode(childUl, k, value[k]));

      // --- CLIC UTILISATEUR SUR PARENT ---
      cb.addEventListener("change", (e) => {
        const newSelected = new Set(getState().filters.origins);
        if (cb.checked) {
          // Cocher parent => parent + tous enfants
          addWithChildren(key, newSelected);
        } else {
          // Décoche parent (clic user) => parent + tous enfants (règle stricte)
          removeWithChildren(key, newSelected);
        }
        setOrigins([...newSelected]);
      });

      // --- CHANGEMENT D'UN ENFANT (bubbling jusqu'au parent) ---
      childUl.addEventListener("change", (e) => {
        const target = e.target;
        if (!(target instanceof HTMLInputElement)) return;

        // Si l'enfant vient d'être décoché par l'utilisateur,
        // on applique la règle spéciale "mono-enfant".
        if (e.isTrusted && target.checked === false) {
          const newSelected = new Set(getState().filters.origins);

          // parent immédiat
          const p = key; // ici "key" = parent immédiat du childUl
          const siblingsCount = (childrenOf.get(p) || []).length;

          // 1) Si le parent a >1 enfant => on décoche ce parent
          //    Si le parent a 1 seul enfant => on laisse ce parent coché
          newSelected.delete(p);

          // 2) Tous les ancêtres au-dessus du parent immédiat sont décochés
          let g = parentOf.get(p);
          while (g) {
            newSelected.delete(g);
            g = parentOf.get(g);
          }

          setOrigins([...newSelected]);
        }

        // Re-cochage automatique du parent si TOUS ses enfants sont cochés
        const childChecks = childUl.querySelectorAll('input[type="checkbox"]');
        const allChecked = Array.from(childChecks).every(c => c.checked);
        const newSelected2 = new Set(getState().filters.origins);
        if (allChecked) {
          newSelected2.add(key);
          setOrigins([...newSelected2]);
          cb.checked = true; // maj visuelle immédiate
        }
      });
    } else {
      // --- FEUILLE ---
      cb.addEventListener("change", (e) => {
        const newSelected = new Set(getState().filters.origins);
        if (cb.checked) newSelected.add(key);
        else newSelected.delete(key);
        setOrigins([...newSelected]);

        // si on coche à la main toutes les feuilles d'une branche,
        // les handlers parents se chargeront de recocher les parents.
      });
    }
  }

  function addWithChildren(key, selectedSet) {
    selectedSet.add(key);
    const kids = childrenOf.get(key) || [];
    for (const k of kids) addWithChildren(k, selectedSet);
  }

  function removeWithChildren(key, selectedSet) {
    selectedSet.delete(key);
    const kids = childrenOf.get(key) || [];
    for (const k of kids) removeWithChildren(k, selectedSet);
  }

  // racines
  Object.entries(treeObj || {}).forEach(([k, v]) => buildNode(ul, k, v));
  return ul;
}


function catEmoji(cat){
  if (cat === "Liant") return "💧";
  if (cat === "Catalyseur") return "⚗️";
  if (cat === "Réactif") return "🧬";
  return "❓";
}

/**
 * Carte d’ingrédient — version simplifiée :
 * 1) "Nom  +  emoji catégorie" (sur la même ligne)
 * 2) Description
 * 3) "🧠 difficulté"
 * 4) "🌏 origines"
 * ⚠️ On n’affiche PAS les livres.
 */
export function ingredientCard({ name, cat, difficulty, shortEffect, effect, origins = [] }) {
  const root = el("article", { class: "ing-card", title: name });

  // --- Vérifier si cet ingrédient est actuellement sélectionné ---
  const sel = getState().selection;
  const isActive =
    sel.binder === name ||
    sel.catalyst === name ||
    (sel.reactants && sel.reactants.includes(name));

  if (isActive) {
    root.classList.add("on");
  }

  // Tête
const head = el(
  "div",
  { class: "ing-top" },                                // <-- flex + space-between (déjà dans le CSS)
  el("span", { class: "ing-name" }, name),
  el("span", { class: "ing-cat", title: cat, "aria-label": cat }, catEmoji(cat)) // <-- cat à DROITE
);

  // Corps
  const desc = el("div", { class: "ing-effect" }, shortEffect || effect || "");
  const diff = el("div", { class: "ing-meta" }, `🧠 ${difficulty ?? "?"}`);
  const ori  = origins?.length ? el("div", { class: "ing-meta" }, `🌏 ${origins.join(", ")}`) : null;

  root.append(head, desc, diff);
  if (ori) root.append(ori);
  return root;
}