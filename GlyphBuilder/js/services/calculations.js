// Pure functions for calculations (Open/Closed for extensions)
import { GLYPH_TABLE } from '../domain/data.js';

export function computeTotals(selected){
  let mana=0, diff=0;
  selected.forEach(g => { const d=GLYPH_TABLE[g]; if(d){ mana+=d.mana; diff+=d.diff; }});
  return { mana: Math.ceil(mana), diff };
}

export function formatSelection(selected){
  const {mana,diff}=computeTotals(selected);
  return `Glyphes: ${selected.join(' · ')}\nMana: ${mana} | Difficulté: ${diff}`;
}