// --- Données de référence --------------------------------------------------
export const GLYPH_TABLE = {
	
		// Ciblage
  "🎯 Cible unique":			{diff:5,mana:0.2, cat:"Ciblage"},
  "🌌 Zone":					{diff:5,mana:1, cat:"Ciblage"},
  "🔜 Cible la plus proche":	{diff:5,mana:0.2, cat:"Ciblage"},
  "↩️ Utilisateur":				{diff:5,mana:0.2, cat:"Ciblage"},
  
  "🛜 Conique":					{diff:10,mana:0.5, cat:"Ciblage"},
  "↕️ Ligne (4m)":				{diff:10,mana:0.5, cat:"Ciblage"},
  "🔢 Multi-cible (jusqu’à 4)":	{diff:10,mana:0.5, cat:"Ciblage"},
  "👥 Chaîne":					{diff:10,mana:0.3, cat:"Ciblage"},
  
  "🌐 Toute entitée":			{diff:20,mana:.5, cat:"Ciblage"},
  "👍 Allié":					{diff:20,mana:.5, cat:"Ciblage"},
  "👎 Ennemi":					{diff:20,mana:.5, cat:"Ciblage"},
	
  "🎲 Aléatoire":				{diff:40,mana:.2, cat:"Ciblage"},
  "🧭 Directionnel":			{diff:40,mana:0.3, cat:"Ciblage"},
	
  "📍 Persistante (zone)":		{diff:80,mana:.5, cat:"Ciblage"},
	
	
		// Éléments
  "🔥 Feu":				{diff:5,mana:0.3, cat:"Éléments"},
  "💧 Eau":				{diff:5,mana:0.3, cat:"Éléments"},
  "🏔 Terre":			{diff:5,mana:0.3, cat:"Éléments"},
  "🌪 Vent":			{diff:5,mana:0.3, cat:"Éléments"},
  "💚 Soin":			{diff:5,mana:0.3, cat:"Éléments"},
  "❄️ Glace":			{diff:5,mana:0.3, cat:"Éléments"},
  "⚡ Foudre":			{diff:5,mana:0.3, cat:"Éléments"},
  
  "🟣 Ombre":			{diff:10,mana:0.5, cat:"Éléments"},
  "☀️ Lumière":			{diff:10,mana:0.5, cat:"Éléments"},
  "🌱 Nature":			{diff:10,mana:0.5, cat:"Éléments"},
  "💙 Bénédiction":		{diff:10,mana:0.5, cat:"Éléments"},
  
  "🩸 Sang":			{diff:20,mana:0.75, cat:"Éléments"},
  "🪞 Illusion":		{diff:20,mana:0.75, cat:"Éléments"},
  "💀 Nécromantie":		{diff:20,mana:0.75, cat:"Éléments"},
  "🎶 Sons":			{diff:20,mana:0.75, cat:"Éléments"},
  
  "🕚 Temporel":		{diff:40,mana:1.5, cat:"Éléments"},
  "🌌 Cosmique":		{diff:40,mana:1.5, cat:"Éléments"},
  
  "🪦 Mort":			{diff:80,mana:3, cat:"Éléments"},
  "🐦‍🔥 Résurection":		{diff:80,mana:3, cat:"Éléments"},
  
  		// États
  "💀 Affaiblissement":		{diff:5,mana:0.3, cat:"États"},
  "💫 Étourdissement":		{diff:5,mana:0.3, cat:"États"},
  "🧊 Gel":					{diff:5,mana:0.3, cat:"États"},
  "🫧 Poison":				{diff:5,mana:0.3, cat:"États"},
  
  "🔥 Brûlure":				{diff:10,mana:0.3, cat:"États"},
  "💤 Sommeil":				{diff:10,mana:0.3, cat:"États"},
  "🌀 Confusion":			{diff:10,mana:0.3, cat:"États"},
  
  "❤️ Charme":				{diff:20,mana:1, cat:"États"},
  "🤐 Silence":				{diff:20,mana:0.3, cat:"États"},
  "👁‍🗨 Cécité":				{diff:20,mana:0.3, cat:"États"},
    
	
  		// Amplification
  "💪 Physique":		{diff:5,mana:0.5, cat:"Amplification"},
  "💬 Social":			{diff:5,mana:0.5, cat:"Amplification"},
  "🧠 Mental":			{diff:5,mana:0.5, cat:"Amplification"},
  
  "🔼 Power-Up":		{diff:40,mana:2, cat:"Amplification"},
  "🔽 Power-Down":		{diff:40,mana:2, cat:"Amplification"},
  "➕ Puissance":		{diff:40,mana:2, cat:"Amplification"},
  "📏 Portée":			{diff:40,mana:2, cat:"Amplification"},
  "⏳ Durée":			{diff:40,mana:2, cat:"Amplification"},
  
  "📊 Répétition":		{diff:80,mana:2, cat:"Amplification"},
  "✴️ Création":		{diff:80,mana:4, cat:"Amplification"},
  
  
  
  		// Actions
  "💥 Destruction":			{diff:5,mana:0.2, cat:"Actions"},
  "🤚 Contact":				{diff:5,mana:0.2, cat:"Actions"},  
  "🛡 Défensif":			{diff:10,mana:0.3, cat:"Actions"},
  "⚔️ Offensif":			{diff:10,mana:0.3, cat:"Actions"},
  "🪬 Marquage":			{diff:20,mana:0.3, cat:"Actions"},
  
  
  "💣 Explosion":	{diff:40,mana:2, cat:"Contrôle"},
  "🕧 Retardement":	{diff:80,mana:2, cat:"Contrôle"},
  "💯 Critique":	{diff:80,mana:3, cat:"Contrôle"},
  "🎲 Variance":	{diff:80,mana:3, cat:"Contrôle"},

  "♾️ Infinité":	{diff:160,mana:5, cat:"Ultime"},
  "🌒 Éclipse":		{diff:160,mana:5, cat:"Ultime"}
};

export const CATEGORIES = ["Éléments","Ciblage","États","Amplification","Actions","Contrôle","Ultime"];
