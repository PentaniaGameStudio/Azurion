// /potionBuilder/js/creator/books-panel.js
import { qs, clear } from "/potionBuilder/js/core/dom.js";
import { sub } from "/potionBuilder/js/core/events.js";
import { getState, addBook, removeBook, clearBooks } from "/potionBuilder/js/core/store.js";
import { pill } from "/potionBuilder/js/shared/ui-kit.js";

const elTabs = qs("#booksTabs");
const elOwned = qs("#booksOwned");
const elAdd = qs("#booksAdd");
const elList = qs("#booksList");
const elInput = qs("#bookInput");
const btnAdd = qs("#addBookBtn");
const btnClear = qs("#clearBooksBtn");

function switchTab(which){
  if (which === "add"){
    elAdd.classList.remove("hidden");
    elOwned.classList.add("hidden");
    elTabs.querySelectorAll(".catBtn").forEach(b => b.classList.toggle("on", b.dataset.tab==="add"));
    elInput?.focus();
  } else {
    elOwned.classList.remove("hidden");
    elAdd.classList.add("hidden");
    elTabs.querySelectorAll(".catBtn").forEach(b => b.classList.toggle("on", b.dataset.tab==="owned"));
  }
}

function renderOwned(){
  const { books } = getState();
  clear(elList);
  if (!books.length){
    elList.append((()=>{ const s=document.createElement("span"); s.className="tiny muted"; s.textContent="Aucun livre."; return s; })());
    return;
  }
  books.forEach(name => {
    const p = pill(name, { removable:true, onRemove: () => removeBook(name) });
    p.addEventListener("click", ()=> removeBook(name));
    elList.append(p);
  });
}

function initEvents(){
  // Tabs
  elTabs?.addEventListener("click", (e)=>{
    const b = e.target.closest(".catBtn");
    if (!b) return;
    switchTab(b.dataset.tab);
  });

  // Ajout
  btnAdd?.addEventListener("click", ()=>{
    const v = (elInput?.value || "").trim();
    if (!v) return;
    addBook(v);
    elInput.value = "";
  });
  elInput?.addEventListener("keydown", (e)=>{
    if (e.key === "Enter") btnAdd?.click();
  });

  // Effacer tout
  btnClear?.addEventListener("click", ()=>{
    if (confirm("Effacer tous les livres ?")) clearBooks();
  });

  sub("books:changed", renderOwned);
}

// boot
initEvents();
renderOwned();
