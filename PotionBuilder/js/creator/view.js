// /PotionBuilder/js/creator/view.js
import { qs, clear } from "/PotionBuilder/js/core/dom.js";
import { sub } from "/PotionBuilder/js/core/events.js";
import { getState, setOrigins } from "/PotionBuilder/js/core/store.js";
import { getOriginTree, getIngredients } from "/PotionBuilder/js/shared/data.js";
import { renderOriginTree } from "/PotionBuilder/js/shared/ui-kit.js";

const btnOpen  = qs("#btnOriginDropdown");
const dd       = qs("#originDropdown");
let   elTree   = qs("#originTree");
const btnClear = qs("#btnClearOrigins");

// ------------------------
// Build du tree filtré
// ------------------------
async function buildTree(){
  const allTree = await getOriginTree();
  const state = getState();
  const ingredients = await getIngredients();

  // origines réellement disponibles (ingrédients débloqués par les livres)
  const unlocked = new Set();
  for (const ing of ingredients){
    const needed = ing.books || [];
    const owned  = state.books || [];
    const isUnlocked = !needed.length || needed.some(b => owned.includes(b));
    if (isUnlocked && ing.origins) ing.origins.forEach(o => unlocked.add(o));
  }

  // filtre récursif de l'arbre pour ne garder que les branches utiles
  function filterTree(tree){
    const out = {};
    for (const [k, v] of Object.entries(tree || {})){
      const keptSelf = unlocked.has(k);
      const keptKids = filterTree(v);
      if (keptSelf || Object.keys(keptKids).length){
        out[k] = keptSelf ? keptKids : keptKids; // on garde la structure enfant
      }
    }
    return out;
  }

  const filtered = filterTree(allTree);
  clear(elTree);
  const current = new Set(state.filters?.origins || []);
  elTree.append( renderOriginTree(filtered, { selected: current }) );
}

// Déplacer le dropdown dans <body> une seule fois (évite clipping/overflow)
if (dd && dd.parentNode !== document.body) {
  document.body.appendChild(dd);
  elTree = dd.querySelector("#originTree"); // rebind
}

// ------------------------
// Positionnement viewport
// ------------------------
function placeOriginDropdown(anchorEl, panelEl){
  // rendre mesurable sans casser le cycle d'ouverture/fermeture par classe
  const prevDisplay = panelEl.style.display;
  panelEl.style.visibility = "hidden";
  panelEl.style.display = "block";

  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const r  = anchorEl.getBoundingClientRect();
  const pw = panelEl.offsetWidth;
  const ph = Math.min(panelEl.offsetHeight, vh - 16);

  // position préférée : sous le bouton, alignée à gauche
  let left = r.left;
  let top  = r.bottom + 8;

  // clamp horizontal
  if (left + pw > vw - 8) left = vw - pw - 8;
  if (left < 8) left = 8;

  // flip vertical si nécessaire
  if (top + ph > vh - 8) top = Math.max(8, r.top - ph - 8);

  panelEl.style.left = `${left}px`;
  panelEl.style.top  = `${top}px`;

  // restaurer: on laisse la classe .open gérer display
  panelEl.style.visibility = "";
  panelEl.style.display = prevDisplay || "";
}


// ------------------------
// Ouverture / Fermeture
// ------------------------
function openDD(show){
  if (!dd) return;
  if (show) {
    dd.classList.add("open");               // CSS gère display
    placeOriginDropdown(btnOpen, dd);

    // repositionner si resize/scroll pendant l'ouverture
    const onReposition = () => placeOriginDropdown(btnOpen, dd);
    dd._onReposition = onReposition;
    window.addEventListener("resize", onReposition);
    window.addEventListener("scroll", onReposition, true);
  } else {
    dd.classList.remove("open");
	dd.style.display = ""; // enlève tout inline display résiduel

    if (dd._onReposition){
      window.removeEventListener("resize", dd._onReposition);
      window.removeEventListener("scroll", dd._onReposition, true);
      dd._onReposition = null;
    }
  }
}

// ------------------------
// Events
// ------------------------
function initEvents(){
  // toggle au clic sur le bouton
  btnOpen?.addEventListener("click", (e)=>{
    e.stopPropagation();
    const isOpen = dd.classList.contains("open");
    if (!isOpen) {
      buildTree();
      openDD(true);
    } else {
      openDD(false);
    }
	document.addEventListener("keydown", (e)=>{
	  if (e.key === "Escape") openDD(false);
	});

  });

  // fermer au clic ailleurs
  document.addEventListener("click", (e)=>{
    if (!dd.contains(e.target) && e.target !== btnOpen){
      openDD(false);
    }
  });

  // "Effacer" dans le panel
  btnClear?.addEventListener("click", ()=>{
    setOrigins([]);
    buildTree();
  });

  // si les origines changent pendant que le panel est ouvert, on rebâtit
  sub("filters:origins", ()=>{
    if (dd.classList.contains("open")) buildTree();
  });

  // build initial (pour le 1er open rapide)
  buildTree();
}

// boot
initEvents();
