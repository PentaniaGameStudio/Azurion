// /PotionBuilder/js/core/dom.js
export const qs  = (sel, root=document) => root.querySelector(sel);
export const qsa = (sel, root=document) => Array.from(root.querySelectorAll(sel));

export function el(tag, attrs={}, ...children){
  const node = document.createElement(tag);
  for (const [k,v] of Object.entries(attrs||{})){
    if (k === 'style' && typeof v === 'object') Object.assign(node.style, v);
    else if (k.startsWith('on') && typeof v === 'function') node.addEventListener(k.slice(2), v);
    else if (v === true) node.setAttribute(k, k);
    else if (v !== false && v != null) node.setAttribute(k, v);
  }
  for (const c of children){
    if (c == null) continue;
    node.append(c.nodeType ? c : document.createTextNode(String(c)));
  }
  return node;
}

export const clear = (node) => { while (node.firstChild) node.removeChild(node.firstChild); };

export function on(target, type, handler, opts){
  target.addEventListener(type, handler, opts);
  return () => target.removeEventListener(type, handler, opts);
}

/** Délégation d’événements */
export function delegate(root, selector, type, handler){
  return on(root, type, (e)=>{
    const match = e.target.closest(selector);
    if (match && root.contains(match)) handler(e, match);
  });
}

/** Utils classes */
export function addClass(node, ...cls){ node.classList.add(...cls); }
export function removeClass(node, ...cls){ node.classList.remove(...cls); }
export function toggle(node, show){ node.classList[show ? 'remove' : 'add']('hidden'); }
