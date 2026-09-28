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
