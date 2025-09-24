// /potionBuilder/js/core/router.js
import { qs, addClass, removeClass } from "/potionBuilder/js/core/dom.js";
import { sub, pub } from "/potionBuilder/js/core/events.js";

const BTN_CRE = qs("#btnCreator");
const BTN_REC = qs("#btnRecipe");
const VIEW_CRE = qs("#creatorView");
const VIEW_REC = qs("#recipeView");

function show(view){
  const isCreator = view !== "recipe";
  if (isCreator){
    VIEW_CRE?.classList.remove("hidden");
    VIEW_REC?.classList.add("hidden");
    BTN_CRE?.classList.add("on");
    BTN_REC?.classList.remove("on");
  } else {
    VIEW_REC?.classList.remove("hidden");
    VIEW_CRE?.classList.add("hidden");
    BTN_REC?.classList.add("on");
    BTN_CRE?.classList.remove("on");
  }
  pub("view:change", view);
}

BTN_CRE?.addEventListener("click", ()=> show("creator"));
BTN_REC?.addEventListener("click", ()=> show("recipe"));

// Optionnel: hash routing très simple (#creator / #recipe)
function syncFromHash(){
  const h = (location.hash||"").replace("#","");
  if (h === "recipe") show("recipe"); else show("creator");
}
window.addEventListener("hashchange", syncFromHash);
syncFromHash();

// Consumers peuvent écouter view:change si besoin
sub("view:change", (v)=> {
  // future hooks
  // console.debug("[router] view:", v);
});
