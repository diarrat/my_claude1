"""Приводит разные написания одной игры в titles_result3.txt к одному названию.

Результат: titles_result3.txt перезаписывается, словарь замен — game_renames.tsv.
"""
import collections, re

FILE = 'titles_result3.txt'
ROMAN = {'ii': '2', 'iii': '3', 'iv': '4', 'v': '5', 'vi': '6', 'vii': '7', 'viii': '8',
         'x': '10', 'xi': '11', 'xii': '12', 'xiv': '14', 'xv': '15', 'xvi': '16'}
# Аббревиатуры, однозначно указывающие на одну игру
ABBR = {'SWTOR': 'Star Wars: The Old Republic', 'LOTRO': 'The Lord of the Rings Online',
        'DDO': 'Dungeons & Dragons Online', 'D&D Online': 'Dungeons & Dragons Online',
        'GW2': 'Guild Wars 2', 'STO': 'Star Trek Online', 'PWI': 'Perfect World International',
        'DFO': 'Dungeon Fighter Online', 'DOMO': 'Dream of Mirror Online', 'MXM': 'Master X Master',
        'HOTG': 'Hand of the Gods', 'TF2': 'Team Fortress 2', 'LOCO': 'Land of Chaos Online',
        'ELOA': 'Elite Lord of Alliance', 'ZMR': 'Zombies Monsters Robots',
        'Fly For Fun': 'Flyff', 'FFXIV': 'Final Fantasy XIV', 'Final Fantasy 14': 'Final Fantasy XIV',
        'FFXIV ARR': 'Final Fantasy XIV: A Realm Reborn', 'FFXIV: ARR': 'Final Fantasy XIV: A Realm Reborn',
        'FFXIV:ARR': 'Final Fantasy XIV: A Realm Reborn', 'FFXIV: A Realm Reborn': 'Final Fantasy XIV: A Realm Reborn',
        'FFXIV A Realm Reborn': 'Final Fantasy XIV: A Realm Reborn', 'Final Fantasy XIV ARR': 'Final Fantasy XIV: A Realm Reborn',
        'Final Fantasy XIV: ARR': 'Final Fantasy XIV: A Realm Reborn',
        'WoW': 'World of Warcraft', 'LoL': 'League of Legends', 'DCUO': 'DC Universe Online',
        'PUBG': "PlayerUnknown's Battlegrounds", 'PUBG: Battlegrounds': "PlayerUnknown's Battlegrounds",
        'GTA Online': 'Grand Theft Auto Online', 'CS:GO': 'Counter-Strike: Global Offensive',
        'Neverwinter Online': 'Neverwinter', 'Elsword Online': 'Elsword', 'Atlantica': 'Atlantica Online',
        'TERA: Rising': 'TERA', 'TERA Rising': 'TERA', 'Continent of the Ninth Seal': 'C9', 'C9: Continent of the Ninth Seal': 'C9',
        'Flyff: Fly For Fun': 'Flyff',
        'Mabinogi Heroes': 'Vindictus', 'Dekaron': '2Moons', 'Dragonica Online': 'Dragon Saga',
        'MegaTen': 'Shin Megami Tensei: Imagine Online'}


# Не менять: по смыслу это отдельная игра / версия
KEEP = {'Dungeons & Dragons (Giant Skull project)', 'Prince of Persia: The Sands of Time (remake)',
        'Perfect World (Perfect World International)'}
# Ручные исправления итогового названия (после проверки глазами)
FIX = {'Dungeon & Dragons Online': 'Dungeons & Dragons Online', 'Dungeon and Dragons Online': 'Dungeons & Dragons Online',
       'Dungeon&Fighter': 'Dungeon Fighter Online',
       'Dungeon&Fighter Mobile': 'Dungeon&Fighter Mobile', 'Dungeon&Fighter mobile': 'Dungeon&Fighter Mobile',
       'Senua (Senua\'s Saga)': "Senua's Saga",
       'The Witcher 3 (Witcher 3)': 'The Witcher 3', 'The Witcher 3': 'The Witcher 3',
       'Runeterra MMO (League of Legends MMO)': 'League of Legends MMO',
       'Hand of the Gods: SMITE Tactics': 'Hand of the Gods', 'Hand of the Gods: Smite Tactics': 'Hand of the Gods',
       'Dragonica': 'Dragon Saga', 'Dragonica (Dragonica: Cassiopeia)': 'Dragon Saga',
       'RuneScape Classic': 'RuneScape Classic', 'Runescape Classic': 'RuneScape Classic',
       'StarCraft': 'StarCraft', 'Starcraft': 'StarCraft', 'FarmVille': 'FarmVille', 'Farmville': 'FarmVille',
       'XCOM 2': 'XCOM 2', 'XCom 2': 'XCOM 2',
       'Dragon Ball Online': 'Dragon Ball Online', 'Dragonball Online': 'Dragon Ball Online',
       'Dragon Ball Xenoverse 2': 'Dragon Ball Xenoverse 2', 'Dragonball Xenoverse 2': 'Dragon Ball Xenoverse 2'}

# Одна и та же игра под разными названиями (решено по смыслу, вручную).
# Разные игры одной серии (Ragnarok Mobile, Ragnarok 2, продолжения, мобильные версии) НЕ объединяются.
SAME = {
    '3on3 Freestyle Basketball': '3on3 FreeStyle', 'ARGO': 'ARGO Online', 'AdventureQuest World': 'AdventureQuest Worlds',
    'Aika': 'Aika Online', 'AIKA Global': 'Aika Online', 'Aion Online': 'Aion', 'Alfheim Tales': 'Alfheim Tales Online',
    'Allods': 'Allods Online', 'Audition': 'Audition Online', 'AxE': 'AxE: Alliance vs Empire',
    'ArcheAge S': 'ArcheAge S: Strait of Freedom', 'ArcheAge S: Straits of Freedom': 'ArcheAge S: Strait of Freedom',
    'ArcheAge 3.0: Revelation': 'ArcheAge: Revelation', 'Black Desert': 'Black Desert Online',
    'Black Gold': 'Black Gold Online', 'Bounty Hounds': 'Bounty Hounds Online', 'Call of Duty: AW': 'Call of Duty: Advanced Warfare',
    'City of Steam Arkadia': 'City of Steam', 'Civilization: BE Rising Tide': 'Civilization: Rising Tide',
    'Closers Online': 'Closers', 'Dark Blood Online': 'Dark Blood', 'Darkfall Online': 'Darkfall',
    'Digimon Masters Online': 'Digimon Masters', 'Dogs of War': 'Dogs of War Online', 'Dragon Nest EU': 'Dragon Nest',
    'Dragon Quest X Online': 'Dragon Quest X', 'Ecol Tactics': 'Ecol Tactics Online', 'Eclipse War': 'Eclipse War Online',
    'EndWar Online': "Tom Clancy’s Endwar Online", 'Entropia': 'Entropia Universe', 'Erectus': 'Erectus the Game',
    'Ether Saga': 'Ether Saga Online', 'Ether Saga Odyssey': 'Ether Saga Online', 'Eudemons': 'Eudemons Online',
    'EverQuest 2: Extended': 'EverQuest II', 'F1 Online': 'F1 Online: The Game', 'Fairy Story': 'Fairy Story Online',
    'Fairy Tale: Hero’s Journey': 'Fairy Tail: Hero’s Journey', 'Fantasy Westward Journey': 'Fantasy Westward Journey Online',
    'Faxion': 'Faxion Online', 'Fiesta': 'Fiesta Online', 'FINAL FANTASY XIV Online': 'Final Fantasy XIV',
    'Final Fantasy XIV: A Realm Reborn': 'Final Fantasy XIV', 'Final Fantasy Mobius': 'Mobius Final Fantasy',
    'Forced 2': 'FORCED 2: The Rush', 'FreeSky': 'Freesky Online', 'Ghost in the Shell Online': 'Ghost in the Shell: First Assault',
    'GodsWar': 'GodsWar Online', 'Granado Espada Online': 'Granado Espada', 'Guns of Icarus': 'Guns of Icarus Online',
    'GunZ': 'GunZ: The Duel', 'GunZ 2': 'GunZ 2: The Second Duel', 'Heva Clonia': 'Heva Clonia Online',
    'Hellgate: London': 'Hellgate', 'Hex': 'HEX: Shards of Fate', 'Hearthstone: Heroes of Warcraft': 'Hearthstone',
    'Huxley': 'Huxley: The Dystopia', 'Knight Age Online': 'Knight Age', 'Kritika Online': 'Kritika',
    'Kritika: Chaos Unleashed': 'Kritika', 'Krosmaster': 'Krosmaster Arena', 'LEGO Minifigures': 'LEGO Minifigures Online',
    'LoA Fire Raiders': 'League of Angels: Fire Raiders', 'League of Legends MMORPG': 'League of Legends MMO',
    'Luvinia': 'Luvinia Online', 'Magic World': 'Magic World Online', 'Maestia: Rise of Keledus': 'Maestia',
    'Mini Fighter Online': 'Mini Fighter', 'Mordheim': 'Mordheim: City of the Damned', 'Mythos Global': 'Mythos',
    'NTales: Child of Destiny': 'NTales', 'NARUTO SHIPPUDEN: Ultimate Ninja STORM 4': 'Naruto Shippuden: Ultimate Ninja Storm 4',
    'Naruto SUN Storm 4': 'Naruto Shippuden: Ultimate Ninja Storm 4', 'Naruto Storm 4': 'Naruto Shippuden: Ultimate Ninja Storm 4',
    'Naruto: Ultimate Ninja Storm 4': 'Naruto Shippuden: Ultimate Ninja Storm 4', 'Onigiri': 'Onigiri Online',
    'Pantheon': 'Pantheon: Rise of the Fallen', 'Phoenix Dynasty': 'Phoenix Dynasty Online', 'Pokémon Go': 'Pokemon Go',
    'Pokémon': 'Pokemon', 'Prius': 'Prius Online',
    'Ragnarok': 'Ragnarok Online', 'Ragnarok Onlines': 'Ragnarok Online', 'Ragnarok Classic': 'Ragnarok Online Classic',
    'Ragnarok Valkyrie Uprising': 'Ragnarok Online: Valkyrie Uprising', 'Ragnarok 2': 'Ragnarok Online 2',
    'Ragnarok 2: Legend of the Second': 'Ragnarok Online 2', 'Rappelz Online': 'Rappelz', 'Red Stone Online': 'Red Stone',
    'Requiem Online': 'Requiem', 'Requiem: Memento Mori': 'Requiem', 'Requiem: Rise of the Reaver': 'Requiem',
    'Rise of Ragnarok – Asunder': 'Rise of Ragnarok', 'Runescape Old School': 'Old School RuneScape', 'RuneScape 3': 'RuneScape',
    'SD Gundam Capsule Fighter': 'SD Gundam Capsule Fighter Online', 'Salem Online': 'Salem',
    'Seal Online: Blades of Destiny': 'Seal Online', 'Shin Megami Tensei Imagine': 'Shin Megami Tensei: Imagine Online',
    'Skara': 'Skara: The Blade Remains', 'SkySaga: Infinite Isles': 'SkySaga', 'Soldiers': 'Soldiers Inc.',
    'Space Wars': 'Space Wars: Interstellar Empires', 'Star Crusade': 'Star Crusade: War for the Expanse',
    'Star Stable': 'Star Stable Online', 'Swordsman Online': 'Swordsman', 'TERA Online': 'TERA',
    'Tactical Monsters': 'Tactical Monsters Rumble Arena', 'Total War Battles: Kingdoms': 'Total War Battles: Kingdom',
    'Trickster': 'Trickster Online', 'Universal Monsters': 'Universal Monsters Online', 'Vanguard Online': 'Vanguard Saga of Heroes',
    'Voyage Century': 'Voyage Century Online', 'Warhammer 40K: EC': 'Warhammer 40k: Eternal Crusade',
    'Warhammer 40,000: Eternal Crusade': 'Warhammer 40k: Eternal Crusade', 'Eternal Crusade': 'Warhammer 40k: Eternal Crusade',
    'Warlocks': 'Warlocks vs. Shadows', 'Wild Buster': 'Wild Buster: Heroes of Titan', 'Wild Terra Online': 'Wild Terra',
    'WonderKing Online': 'WonderKing', 'Wonderland': 'Wonderland Online',
    'World of Tanks: Xbox 360': 'World of Tanks: Xbox 360 Edition', 'ÆRENA': 'Ærena: Clash of Champions',
    'Kingdom Hearts Union X [Cross]': 'Kingdom Hearts Union χ', 'SMITE Tactics': 'Hand of the Gods',
    'Legend of Edda: Global Edition': 'Legend of Edda',
}


def key(g):
    words = re.sub(r'[^a-z0-9а-яёχæ]+', ' ', g.lower().replace('&', ' and ')).split()
    return ''.join(ROMAN.get(w, w) for w in words if w not in ('the', 'and'))


def base(g):
    """«Name (Alias)» -> «Name»; уточнение года «(2023)» оставляем."""
    m = re.match(r'(.+?)\s*\((?!\d{4}\))[^()]+\)$', g)
    return m.group(1) if m else g


lines = open(FILE, encoding='utf-8', newline='').read().split('\r\n')
parse = lambda l: re.match(r'(\d+) (\d+) - (.+)', l)
count = collections.Counter(g.strip() for l in lines if parse(l)
                            for g in parse(l).group(3).split(', ') if g.strip())

abbr = {key(k): v for k, v in ABBR.items()}
step1 = {g: abbr.get(key(base(g)), base(g)) for g in count}
groups = collections.defaultdict(collections.Counter)
for g, n in count.items():
    groups[key(step1[g])][step1[g]] += n
canon = {k: max(c, key=lambda x: (c[x], x != x.upper(), x)) for k, c in groups.items()}
rename = {g: canon[key(step1[g])] for g in count}
for g in count:
    if g in KEEP:
        rename[g] = g
    elif g in FIX:
        rename[g] = FIX[g]
    elif rename[g] in FIX:
        rename[g] = FIX[rename[g]]
    rename[g] = SAME.get(rename[g], rename[g])

out = []
for l in lines:
    m = parse(l)
    if m:
        gs = list(dict.fromkeys(rename[g.strip()] for g in m.group(3).split(', ') if g.strip()))
        l = f'{m.group(1)} {len(gs)} - {", ".join(gs)}'
    out.append(l)
open(FILE, 'w', encoding='utf-8', newline='').write('\r\n'.join(out))

changed = sorted((g for g in rename if rename[g] != g), key=lambda g: (rename[g].lower(), g))
with open('game_renames.tsv', 'w', encoding='utf-8') as f:
    f.write('было\tстало\tзаписей\n')
    f.writelines(f'{g}\t{rename[g]}\t{count[g]}\n' for g in changed)
print(f'названий: {len(count)} -> {len(set(rename.values()))}, заменено вариантов: {len(changed)}, '
      f'строк изменено: {sum(a != b for a, b in zip(lines, out))}')
