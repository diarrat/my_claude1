"""Сверяет игры из titles_result2.txt с заголовками articles.tsv с учётом game_aliases.json.

Использование: python3 check_titles.py titles_result2.txt articles.tsv [кол-во строк]
Результат: titles_mismatches_dict.tsv
"""
import csv, json, re, sys

ROMAN = {' iv ': ' 4 ', ' ii ': ' 2 ', ' iii ': ' 3 ', ' xiv ': ' 14 ', ' and ': ' ', ' vs ': ' '}


def norm(s):
    s = re.sub(r"[’']s\b", '', s.lower()).replace('’', '').replace("'", '').replace('&', ' ')
    s = ' ' + re.sub(r'[^a-z0-9χ]+', ' ', s).strip() + ' '
    for a, b in ROMAN.items():
        s = s.replace(a, b).replace(a, b)
    return s


def variants(g, aliases):
    v = {g, re.sub(r'^The ', '', g), re.sub(r' Online$', '', re.sub(r'^The ', '', g))}
    for sep in (':', ' - ', ' – '):
        v.add(g.split(sep)[0])
    words = re.findall(r'[A-Za-z0-9]+', g)
    for ab in (''.join(w[0] for w in words), ''.join(w[0] for w in words if w.lower() not in ('of', 'the'))):
        if len(ab) >= 3:
            v.add(ab)
    return v | set(aliases.get(g, []))


def main(titles_path, articles_path, limit=None, aliases_path='game_aliases.json'):
    aliases = json.load(open(aliases_path, encoding='utf-8'))
    titles = {r['id']: r['title'] for r in csv.DictReader(
        open(articles_path, encoding='utf-8-sig'), delimiter='\t')}
    lines = open(titles_path, encoding='utf-8-sig').read().splitlines()
    if limit:
        lines = lines[:int(limit)]
    out, checked = [], 0
    for line in lines:
        m = re.match(r'\s*(\d+)\s+\d+\s+-\s+(.*)', line)
        if not m or 'уточн' in line:
            continue
        i, games = m.group(1), m.group(2).strip()
        checked += 1
        title = titles.get(i)
        if title is None:
            out.append((i, games, '', 'id нет в articles.tsv'))
            continue
        gs = [g.strip() for g in games.split(', ')]
        miss = [g for g in gs if not any(norm(x) in norm(title) for x in variants(g, aliases))]
        if miss:
            out.append((i, games, title, 'не найдено' if len(miss) == len(gs) else 'не найдены: ' + ', '.join(miss)))
    with open('titles_mismatches_dict.tsv', 'w', encoding='utf-8') as f:
        f.write('id\tgame\ttitle\tstatus\n')
        f.writelines('\t'.join(o) + '\n' for o in out)
    print(f'проверено {checked}, расхождений {len(out)}')


if __name__ == '__main__':
    main(*sys.argv[1:])
