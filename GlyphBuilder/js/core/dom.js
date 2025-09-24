// Small DOM helpers (Single Responsibility: DOM creation & querying)
export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
export function el(tag, attrs = {}, ...children){
  const node = document.createElement(tag);
  for(const [k,v] of Object.entries(attrs||{})){
    if(k === 'class') node.className = v;
    else if(k.startsWith('on') && typeof v === 'function') node.addEventListener(k.substring(2), v);
    else node.setAttribute(k, v);
  }
  for(const c of children){ node.append(c instanceof Node ? c : document.createTextNode(String(c))); }
  return node;
}