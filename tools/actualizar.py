#!/usr/bin/env python3
"""Herramienta de la revisión automática diaria de Distorsión.

Lee y escribe data/agenda.json con reglas fijas, para que la revisión
automática no pueda hacer cambios que no le corresponden:

  - nunca publica ni despublica un show (visibility no se toca)
  - nunca borra shows
  - nunca cambia el nivel de verificación, el destacado, el flyer,
    las fotos ni la descripción que escribió un editor
  - los shows nuevos entran siempre como borrador
  - en los shows publicados, cada cambio de fecha, horario, lugar,
    estado, line-up o precio queda anotado en el historial público

Uso:
  python3 tools/actualizar.py listar
  python3 tools/actualizar.py aplicar cambios.json [--prueba]

Formato de cambios.json:
{
  "resumen": "Texto corto de lo que se revisó hoy",
  "actualizar": [
    {"id": "<id del show>",
     "campos": {"ticketStatus": "agotado", "price": "...", "start": "21:00",
                "tickets": [{"label": "Entradas en X", "url": "https://..."}]},
     "fuentes": [{"label": "Nombre de la fuente", "url": "https://..."}],
     "revisado": true,
     "nota_interna": "Qué se confirmó y qué falta"}
  ],
  "nuevos": [
    {"date": "2026-11-20", "lineup": [{"name": "Banda", "role": "headliner", "from": "País"}],
     "venue": "...", "city": "...", "province": "CABA", "genres": ["Death"],
     "fuentes": [{"label": "...", "url": "https://..."}],
     "nota_interna": "Cómo se encontró y qué confirmar"}
  ]
}
"""
import json, os, re, sys, random, string, unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data', 'agenda.json')
REPORTS = os.path.join(ROOT, 'reports')
FUENTES = os.path.join(ROOT, 'tools', 'FUENTES.md')

STATUS = {'anunciado': 'Anunciado', 'venta': 'Entradas a la venta', 'ultimas': 'Últimas entradas', 'agotado': 'Agotado',
          'gratis': 'Gratis', 'puerta': 'Entrada en puerta', 'reprogramado': 'Reprogramado', 'cancelado': 'Cancelado'}
ROLES = {'headliner', 'soporte', 'invitado'}
PROVS = ['CABA', 'Buenos Aires', 'Catamarca', 'Chaco', 'Chubut', 'Córdoba', 'Corrientes', 'Entre Ríos', 'Formosa', 'Jujuy',
         'La Pampa', 'La Rioja', 'Mendoza', 'Misiones', 'Neuquén', 'Río Negro', 'Salta', 'San Juan', 'San Luis', 'Santa Cruz',
         'Santa Fe', 'Santiago del Estero', 'Tierra del Fuego', 'Tucumán']
EDITABLE = {'ticketStatus', 'price', 'start', 'doors', 'tickets', 'lineup', 'date', 'venue', 'address', 'city', 'province',
            'age', 'genres'}
BLANK = {'visibility': 'draft', 'featured': False, 'ticketStatus': 'anunciado', 'verify': 'anunciado', 'checked': '',
         'internal': '', 'sources': [], 'changes': [], 'title': '', 'lineup': [], 'genres': [], 'date': '', 'doors': '',
         'start': '', 'venue': '', 'address': '', 'city': '', 'province': '', 'price': '', 'age': '', 'tickets': [],
         'links': [], 'description': '', 'flyer': None, 'gallery': []}


def today():
    return datetime.now(ZoneInfo('America/Argentina/Buenos_Aires')).strftime('%Y-%m-%d')


def num_date(d):
    return f'{d[8:10]}/{d[5:7]}/{d[0:4]}' if re.match(r'^\d{4}-\d{2}-\d{2}$', d or '') else (d or 'sin fecha')


def slug(s):
    s = unicodedata.normalize('NFD', str(s or '').lower()).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def uid():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(11))


def bands(s):
    return [b for b in s.get('lineup') or [] if str(b.get('name') or '').strip()]


def headliner(s):
    lu = bands(s)
    h = [b['name'] for b in lu if b.get('role') == 'headliner'] or [b['name'] for b in lu[:1]]
    return s.get('title') or ' + '.join(h) or 'Show sin nombre'


def load():
    with open(DATA, encoding='utf-8') as f:
        return json.load(f)


def save(d):
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


class Invalid(Exception):
    pass


def allowed_domains():
    """Dominios activos de tools/FUENTES.md: los que están entre comillas invertidas
    en las tablas, antes de la sección "Para sumar"."""
    with open(FUENTES, encoding='utf-8') as f:
        text = f.read().split('## Para sumar')[0]
    return {m.lower() for m in re.findall(r'^\|\s*`([a-z0-9.-]+\.[a-z]{2,})`', text, re.M)}


def host(u):
    m = re.match(r'^https?://([^/:?#]+)', str(u or ''), re.I)
    h = (m.group(1) if m else '').lower()
    return h[4:] if h.startswith('www.') else h


def in_domains(u, domains):
    h = host(u)
    return any(h == d or h.endswith('.' + d) for d in domains)


def check_sources(fuentes, domains, where):
    for f in fuentes:
        if not in_domains(f['url'], domains):
            raise Invalid(f"{where}: {host(f['url'])} no está en tools/FUENTES.md ni entre los links guardados del show")


def check_url(u, where):
    if not re.match(r'^https?://[^\s]+$', str(u or '')):
        raise Invalid(f'{where}: link inválido {u!r}')


def check_links(arr, where):
    if not isinstance(arr, list):
        raise Invalid(f'{where}: tiene que ser una lista')
    out = []
    for t in arr:
        check_url(t.get('url'), where)
        out.append({'label': str(t.get('label') or '').strip() or 'Link', 'url': t['url'].strip()})
    return out


def check_fields(campos, where):
    clean = {}
    for k, v in (campos or {}).items():
        if k not in EDITABLE:
            raise Invalid(f'{where}: el campo {k!r} no se puede cambiar desde la revisión automática')
        if k == 'date' and not re.match(r'^\d{4}-\d{2}-\d{2}$', str(v)):
            raise Invalid(f'{where}: fecha inválida {v!r}')
        if k in ('start', 'doors') and v and not re.match(r'^\d{2}:\d{2}$', str(v)):
            raise Invalid(f'{where}: hora inválida {v!r}')
        if k == 'ticketStatus' and v not in STATUS:
            raise Invalid(f'{where}: estado inválido {v!r}')
        if k == 'province' and v and v not in PROVS:
            raise Invalid(f'{where}: provincia inválida {v!r}')
        if k == 'tickets':
            v = check_links(v, where + ' tickets')
        if k == 'genres':
            if not isinstance(v, list):
                raise Invalid(f'{where}: genres tiene que ser una lista')
            v = [str(g).strip() for g in v if str(g).strip()]
        if k == 'lineup':
            if not isinstance(v, list) or not v:
                raise Invalid(f'{where}: lineup tiene que ser una lista con al menos una banda')
            lu = []
            for b in v:
                if not str(b.get('name') or '').strip():
                    raise Invalid(f'{where}: banda sin nombre')
                role = b.get('role') or 'soporte'
                if role not in ROLES:
                    raise Invalid(f'{where}: rol inválido {role!r}')
                lu.append({'name': b['name'].strip(), 'role': role, 'from': str(b.get('from') or '').strip(),
                           'setlist': str(b.get('setlist') or '')})
            v = lu
        if isinstance(v, str):
            v = v.strip()
        clean[k] = v
    return clean


def diff_show(a, b):
    """Las mismas frases que usa el editor del sitio para el historial."""
    out = []
    if a.get('date') != b.get('date'):
        out.append(f"Cambió la fecha: {num_date(a.get('date'))} → {num_date(b.get('date'))}")
    if (a.get('doors') or '', a.get('start') or '') != (b.get('doors') or '', b.get('start') or ''):
        out.append(f"Cambió el horario: {a.get('start') or a.get('doors') or 'sin hora'} → {b.get('start') or b.get('doors') or 'sin hora'}")
    if slug(a.get('venue')) != slug(b.get('venue')):
        out.append(f"Cambió el lugar: {a.get('venue') or 'sin lugar'} → {b.get('venue') or 'sin lugar'}")
    if a.get('ticketStatus') != b.get('ticketStatus'):
        out.append(f"Estado: {STATUS.get(a.get('ticketStatus'), '')} → {STATUS.get(b.get('ticketStatus'), '')}")
    sa = [slug(x['name']) for x in bands(a)]
    sb = [slug(x['name']) for x in bands(b)]
    out += [f"Se sumó {x['name']}" for x in bands(b) if slug(x['name']) not in sa]
    out += [f"Se bajó {x['name']}" for x in bands(a) if slug(x['name']) not in sb]
    if (a.get('price') or '') != (b.get('price') or '') and b.get('price'):
        out.append(f"Cambió el precio: {b['price']}")
    return out


def add_sources(s, fuentes):
    have = {x.get('url') for x in s.get('sources') or []}
    for f in fuentes:
        if f['url'] not in have:
            s.setdefault('sources', []).append(f)
            have.add(f['url'])


def cmd_listar():
    d, t = load(), today()
    rows = []
    for s in sorted(d['shows'], key=lambda x: (x.get('date') or '', x.get('start') or '')):
        if not (s.get('date') or '') >= t:
            continue
        rows.append({
            'id': s['id'], 'date': s.get('date'), 'start': s.get('start'), 'doors': s.get('doors'),
            'visibility': s.get('visibility'), 'ticketStatus': s.get('ticketStatus'), 'verify': s.get('verify'),
            'checked': s.get('checked'), 'show': headliner(s),
            'lineup': [[b['name'], b.get('role'), b.get('from', '')] for b in bands(s)],
            'venue': s.get('venue'), 'address': s.get('address'), 'city': s.get('city'), 'province': s.get('province'),
            'price': s.get('price'), 'tickets': s.get('tickets'), 'sources': s.get('sources'),
            'internal': s.get('internal'),
        })
    print(json.dumps({'hoy': t, 'proximos': len(rows), 'shows': rows}, ensure_ascii=False, indent=1))


def cmd_aplicar(path, prueba=False):
    with open(path, encoding='utf-8') as f:
        req = json.load(f)
    d, t = load(), today()
    by_id = {s['id']: s for s in d['shows']}
    domains = allowed_domains()
    report = {'actualizados': [], 'confirmados': [], 'notas': [], 'nuevos': [], 'repetidos': []}

    for i, u in enumerate(req.get('actualizar') or []):
        where = f'actualizar[{i}]'
        s = by_id.get(u.get('id'))
        if not s:
            raise Invalid(f'{where}: no existe un show con id {u.get("id")!r}')
        where += f' ({headliner(s)} {num_date(s.get("date"))})'
        campos = check_fields(u.get('campos'), where)
        fuentes = check_links(u.get('fuentes') or [], where + ' fuentes')
        if campos and not fuentes:
            raise Invalid(f'{where}: todo cambio necesita al menos una fuente')
        own = {host(x.get('url')) for x in (s.get('sources') or []) + (s.get('tickets') or []) if host(x.get('url'))}
        check_sources(fuentes, domains | own, where)
        if campos and (s.get('date') or '') < t:
            raise Invalid(f'{where}: el show ya pasó; no se cambian sus datos')
        before = json.loads(json.dumps(s))
        s.update(campos)
        changes = diff_show(before, s)
        if s.get('visibility') != 'draft':
            for c in changes:
                s.setdefault('changes', []).append({'date': t, 'text': c})
        add_sources(s, fuentes)
        if u.get('revisado') and fuentes:
            s['checked'] = t
        if u.get('nota_interna'):
            s['internal'] = f"Revisión automática {num_date(t)}: {str(u['nota_interna']).strip()}"
        if changes or campos:
            s['updatedAt'] = int(datetime.now().timestamp() * 1000)
            report['actualizados'].append({'show': headliner(s), 'fecha': s.get('date'), 'publicado': s.get('visibility') != 'draft',
                                           'cambios': changes or ['Datos complementados: ' + ', '.join(sorted(campos))],
                                           'fuentes': [f['url'] for f in fuentes]})
        elif u.get('revisado') and fuentes:
            report['confirmados'].append({'show': headliner(s), 'fecha': s.get('date')})
        elif u.get('nota_interna'):
            report['notas'].append({'show': headliner(s), 'fecha': s.get('date'), 'nota': u['nota_interna']})

    existing = {(s.get('date'), slug(bands(s)[0]['name']) if bands(s) else slug(s.get('title'))) for s in d['shows']}
    for i, n in enumerate(req.get('nuevos') or []):
        where = f'nuevos[{i}]'
        fields = {k: v for k, v in n.items() if k in EDITABLE}
        campos = check_fields(fields, where)
        if 'date' not in campos or 'lineup' not in campos:
            raise Invalid(f'{where}: un show nuevo necesita date y lineup')
        if campos['date'] < t:
            raise Invalid(f'{where}: la fecha ya pasó')
        fuentes = check_links(n.get('fuentes') or [], where + ' fuentes')
        if not fuentes:
            raise Invalid(f'{where}: un show nuevo necesita al menos una fuente')
        check_sources(fuentes, domains, where)
        key = (campos['date'], slug(campos['lineup'][0]['name']))
        if key in existing:
            report['repetidos'].append(f"{campos['lineup'][0]['name']} {num_date(campos['date'])}")
            continue
        s = json.loads(json.dumps(BLANK))
        s.update(campos)
        now = int(datetime.now().timestamp() * 1000)
        s.update({'id': uid(), 'visibility': 'draft', 'sources': fuentes, 'createdAt': now, 'updatedAt': now,
                  'internal': f"Encontrado por la revisión automática del {num_date(t)}. " + str(n.get('nota_interna') or '').strip()})
        d['shows'].append(s)
        existing.add(key)
        report['nuevos'].append({'show': headliner(s), 'fecha': s['date'], 'lugar': ', '.join(x for x in [s['venue'], s['city'], s['province']] if x),
                                 'fuentes': [f['url'] for f in fuentes]})

    lines = [f'# Revisión automática del {num_date(t)}', '']
    if req.get('resumen'):
        lines += [str(req['resumen']).strip(), '']
    lines += [f"- Shows actualizados: {len(report['actualizados'])}",
              f"- Confirmados sin cambios: {len(report['confirmados'])}",
              f"- Shows nuevos agregados como borrador: {len(report['nuevos'])}", '']
    if report['actualizados']:
        lines.append('## Actualizados')
        for r in report['actualizados']:
            lines.append(f"- **{r['show']}** ({num_date(r['fecha'])}{'' if r['publicado'] else ', borrador'}): " + '; '.join(r['cambios']) +
                         ' · ' + ' '.join(f'[fuente]({u})' for u in r['fuentes']))
        lines.append('')
    if report['nuevos']:
        lines.append('## Nuevos (borradores para revisar)')
        for r in report['nuevos']:
            lines.append(f"- **{r['show']}** · {num_date(r['fecha'])} · {r['lugar'] or 'lugar a confirmar'} · " +
                         ' '.join(f'[fuente]({u})' for u in r['fuentes']))
        lines.append('')
    if report['notas']:
        lines.append('## Para revisar')
        for r in report['notas']:
            lines.append(f"- **{r['show']}** ({num_date(r['fecha'])}): {r['nota']}")
        lines.append('')
    if report['confirmados']:
        lines.append('## Confirmados sin cambios')
        lines.append(', '.join(f"{r['show']} ({num_date(r['fecha'])})" for r in report['confirmados']))
        lines.append('')
    if report['repetidos']:
        lines.append('Ya estaban en la agenda: ' + ', '.join(report['repetidos']))
    text = '\n'.join(lines).rstrip() + '\n'

    if prueba:
        print(text)
        print('(prueba: no se guardó nada)')
        return
    save(d)
    os.makedirs(REPORTS, exist_ok=True)
    with open(os.path.join(REPORTS, f'{t}.md'), 'w', encoding='utf-8') as f:
        f.write(text)
    print(text)


if __name__ == '__main__':
    try:
        if len(sys.argv) >= 2 and sys.argv[1] == 'listar':
            cmd_listar()
        elif len(sys.argv) >= 3 and sys.argv[1] == 'aplicar':
            cmd_aplicar(sys.argv[2], '--prueba' in sys.argv)
        else:
            print(__doc__)
            sys.exit(2)
    except Invalid as e:
        print('ERROR: ' + str(e), file=sys.stderr)
        print('No se guardó nada. Corregí cambios.json y volvé a correrlo.', file=sys.stderr)
        sys.exit(1)
