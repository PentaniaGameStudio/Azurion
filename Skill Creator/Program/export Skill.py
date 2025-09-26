# -*- coding: utf-8 -*-
"""
///summary
Extrait les compétences avec dégâts depuis skills_data.json et exporte un Excel:
- Colonnes: Famille | Nom | Niveau | Portée | Cible | Dégâts | EffetTag | Effets
- Tri: Niveau (Niv1<Niv2<Niv3), puis Nom
- Ajoute un tag d'effet (un mot) déduit par mots-clés (ex: Paralysie, Zone, Perce-armure…)
"""

import json, re
from pathlib import Path
import pandas as pd

INPUT_JSON = Path("skills_data.json")
OUTPUT_XLSX = Path("skills_degats_par_niveau.xlsx")

TAG_RULES = [
    (r"paraly", "Paralysie"),
    (r"aveugl", "Cécité"),
    (r"\bzone\b|conique|rayon de|dans la zone", "Zone"),
    (r"travers[eé]-?armure|per[cç]e-?armure|p[eé]n[ée]tration", "Perce-armure"),
    (r"repouss", "Repoussement"),
    (r"\bcharme?\b", "Charme"),
    (r"emp[eê]che de lancer des sorts|silence", "Silence"),
    (r"\baugmente|\bbonus\b|\bb[ée]n[ée]diction", "Buff"),
    (r"\br[ée]duit|\bmalus\b|affaibl", "Debuff"),
    (r"d[ée]tecte|r[ée]v[eè]le", "Détection"),
    (r"regagne|soigne|r[eé]cup[eè]re des? pv", "Soin"),
    (r"bouclier|armure de|prot[eé]ge", "Bouclier"),
    (r"contre", "Contre"),
    (r"\bmarque\b", "Marque"),
    (r"immunit[ée]", "Immunité"),
    (r"transmet|cha[iî]n", "Chaînage"),
    (r"prison|enferme|immobilise|contr[ôo]le", "Contrôle"),
    (r"t[ée]l[ée]porte|se d[eé]placer tr[eè]s rapidement|bond", "Mobilité"),
    (r"\bvole?\b|vol\b|envol", "Vol"),
    (r"r[ée]duit.*d[ée]g[aâ]ts|annule.*d[ée]g[aâ]ts|mur d'eau", "Protection"),
]

def infer_tag(effects_list):
    if not effects_list:
        return ""
    blob = " ".join(effects_list).lower()
    for pat, tag in TAG_RULES:
        if re.search(pat, blob):
            return tag
    return ""

def main():
    with INPUT_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for s in data.get("skills", []):
        dmg = (s.get("damage") or "").strip()
        if not dmg:
            continue
        rows.append({
            "Famille": s.get("family", ""),
            "Nom": s.get("name", ""),
            "Niveau": s.get("level", ""),
            "Portée": s.get("range_", ""),
            "Cible": s.get("target", ""),
            "Dégâts": dmg,
            "EffetTag": infer_tag(s.get("effects")),
            "Effets": " ".join(s.get("effects", [])),
        })

    df = pd.DataFrame(rows)
    level_order = {"Niv1": 1, "Niv2": 2, "Niv3": 3}
    df["__lvl__"] = df["Niveau"].map(level_order).fillna(99).astype(int)
    df = df.sort_values(by=["__lvl__", "Nom"]).drop(columns="__lvl__").reset_index(drop=True)

    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dégâts")
        ws = writer.sheets["Dégâts"]
        # largeur colonnes
        for col_idx, col in enumerate(df.columns, start=1):
            max_len = max([len(str(x)) for x in [col] + df[col].astype(str).tolist()])
            ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = min(max(12, max_len + 2), 60)
        ws.auto_filter.ref = ws.dimensions
        ws.freeze_panes = "A2"

    print(f"Export OK -> {OUTPUT_XLSX.resolve()}")

if __name__ == "__main__":
    main()
