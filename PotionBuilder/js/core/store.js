// /PotionBuilder/js/core/store.js
import { pub } from "PotionBuilder/js/core/events.js";

const LS_KEY = "PotionBuilder:v1";
const DEFAULT = {
  books: [],                 // ["Herbier de base", ...]
  selection: {               // Ingrédients sélectionnés
    binder: null,            // string | null
    catalyst: null,          // string | null
    reactants: []            // string[]
  },
  filters: {
    cat: "all",              // 'all' | 'binder' | 'catalyst' | 'reactant'
    origins: []              // ["Hearthlen","Frostgard",...]
  }
};

function safeParse(str, fallback){
  try { return JSON.parse(str); } catch { return { ...fallback }; }
}
let state = (() => {
  const raw = localStorage.getItem(LS_KEY);
  const parsed = raw ? safeParse(raw, DEFAULT) : { ...DEFAULT };
  // Sanity minimal
  if (!parsed.selection) parsed.selection = { ...DEFAULT.selection };
  if (!parsed.filters) parsed.filters = { ...DEFAULT.filters };
  if (!Array.isArray(parsed.books)) parsed.books = [];
  if (!Array.isArray(parsed.selection.reactants)) parsed.selection.reactants = [];
  if (!Array.isArray(parsed.filters.origins)) parsed.filters.origins = [];
  return parsed;
})();

function save(){ localStorage.setItem(LS_KEY, JSON.stringify(state)); }

export function getState(){ return structuredClone(state); }

// ---------- BOOKS ----------
export function addBook(title){
  if (!title || !title.trim()) return;
  if (!state.books.includes(title)) {
    state.books.push(title.trim());
    save(); pub("books:changed", getState());
  }
}
export function removeBook(title){
  const i = state.books.indexOf(title);
  if (i >= 0) {
    state.books.splice(i,1);
    save(); pub("books:changed", getState());
  }
}
export function clearBooks(){
  if (state.books.length){
    state.books = [];
    save(); pub("books:changed", getState());
  }
}

// ---------- FILTERS ----------
export function setCategory(cat){         // 'all' | 'binder' | 'catalyst' | 'reactant'
  if (state.filters.cat !== cat){
    state.filters.cat = cat;
    save(); pub("filters:cat", getState());
  }
}
export function setOrigins(origins){      // string[]
  state.filters.origins = Array.from(new Set(origins||[]));
  save(); pub("filters:origins", getState());
}

// ---------- SELECTION ----------
export function setBinder(name){          // exclusif
  if (state.selection.binder === name) { // toggle off
    state.selection.binder = null;
  } else {
    state.selection.binder = name;
  }
  save(); pub("selection:changed", getState());
}

export function setCatalyst(name){        // exclusif
  if (state.selection.catalyst === name) {
    state.selection.catalyst = null;
  } else {
    state.selection.catalyst = name;
  }
  save(); pub("selection:changed", getState());
}

export function toggleReactant(name){     // multi
  const arr = state.selection.reactants;
  const i = arr.indexOf(name);
  if (i >= 0) arr.splice(i,1); else arr.push(name);
  save(); pub("selection:changed", getState());
}

export function clearByType(type){        // 'binder' | 'catalyst' | 'reactant'
  if (type === 'reactant') state.selection.reactants = [];
  else state.selection[type] = null;
  save(); pub("selection:changed", getState());
}

function silent_clearByType(type){        // 'binder' | 'catalyst' | 'reactant'
  if (type === 'reactant') state.selection.reactants = [];
  else state.selection[type] = null;
  save();
}


export function resetSelection(){
  silent_clearByType("binder");
  silent_clearByType("catalyst");
  silent_clearByType("reactant");
   pub("selection:changed", getState());
}

export function silent_setBinder(name){          // exclusif
  if (state.selection.binder === name) { // toggle off
    state.selection.binder = null;
  } else {
    state.selection.binder = name;
  }
  save();
}

export function silent_setCatalyst(name){        // exclusif
  if (state.selection.catalyst === name) {
    state.selection.catalyst = null;
  } else {
    state.selection.catalyst = name;
  }
  save(); 
}

export function silent_toggleReactant(name){     // multi
  const arr = state.selection.reactants;
  const i = arr.indexOf(name);
  if (i >= 0) arr.splice(i,1); else arr.push(name);
  save(); 
}

export function refresh()
{
	pub("selection:changed", getState());
}

// ---------- VIEW ROUTER ----------
export function setView(name){            // 'creator' | 'recipe'
  pub("view:change", name);
}

// ---------- HELPERS ----------
/** Retourne la sélection courante dans un format simple */
export function getCurrentPotion(){
  const s = state.selection;
  return {
    binder: s.binder, catalyst: s.catalyst, reactants: [...s.reactants]
  };
}
