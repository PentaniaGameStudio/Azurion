// Local storage access (Single Responsibility: persistence)
const DB_KEY = 'glyph_skills_v1';
const SELECTED_KEY = 'glyph_selected_v1';

export function loadSkills(){
  try{
    const parsed = JSON.parse(localStorage.getItem(DB_KEY) || '[]');
    return Array.isArray(parsed) ? parsed : [];
  }catch{
    return [];
  }
}
export function saveSkills(arr){ localStorage.setItem(DB_KEY, JSON.stringify(arr)); }

export function loadSelection(){ try{ return JSON.parse(localStorage.getItem(SELECTED_KEY) || '[]'); }catch{return []} }
export function saveSelection(arr){ localStorage.setItem(SELECTED_KEY, JSON.stringify(arr)); }