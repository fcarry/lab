#!/usr/bin/env python3
"""
Visor de Base de Datos DBF - Sistema de Sueldos
Aplicación Flask con vistas relacionales inteligentes.
"""

import os
import datetime
from functools import wraps
from flask import Flask, render_template_string, jsonify, request, session, redirect, url_for
import dbfread

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'contper-dbf-2026-key')
APP_PIN = os.environ.get('APP_PIN', 'silvana')
DATA_DIR = os.path.dirname(os.path.abspath(__file__))


def pin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            if request.path.startswith('/api/'):
                return jsonify({'error': 'No autorizado'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


LOGIN_HTML = r"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Acceso - Sistema de Sueldos</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center}
.box{background:#1e293b;border:1px solid #475569;border-radius:12px;padding:40px;width:340px;text-align:center}
.box h1{font-size:20px;margin-bottom:6px} .box h1 b{color:#38bdf8}
.box p{font-size:13px;color:#94a3b8;margin-bottom:24px}
.box input{width:100%;padding:12px;background:#0f172a;border:1px solid #475569;border-radius:8px;color:#e2e8f0;font-size:16px;text-align:center;letter-spacing:3px;outline:none;margin-bottom:16px}
.box input:focus{border-color:#38bdf8}
.box button{width:100%;padding:12px;background:#38bdf8;border:none;border-radius:8px;color:#0f172a;font-size:14px;font-weight:600;cursor:pointer}
.box button:hover{background:#7dd3fc}
.err{color:#f87171;font-size:13px;margin-bottom:12px}
</style>
</head>
<body>
<div class="box">
  <h1><b>SILVANA</b></h1>
  <p>Ingrese el PIN de acceso</p>
  {% if error %}<div class="err">PIN incorrecto</div>{% endif %}
  <form method="POST">
    <input type="password" name="pin" placeholder="PIN" autofocus>
    <button type="submit">Ingresar</button>
  </form>
</div>
</body>
</html>
"""


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pin') == APP_PIN:
            session['authenticated'] = True
            return redirect(url_for('index'))
        return render_template_string(LOGIN_HTML, error=True)
    return render_template_string(LOGIN_HTML, error=False)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/api/reload-cache', methods=['POST'])
@pin_required
def reload_cache():
    _cache.clear()
    return jsonify({'ok': True})


# ── Helpers ────────────────────────────────────────────────────────────────

def safe_value(val):
    if val is None:
        return None
    if isinstance(val, datetime.date):
        return val.isoformat()
    if isinstance(val, datetime.datetime):
        return val.isoformat()
    if isinstance(val, bytes):
        try:
            return val.decode('latin-1')
        except:
            return str(val)
    if isinstance(val, (int, float, str, bool)):
        return val
    return str(val)


def read_dbf(path):
    try:
        table = dbfread.DBF(path, encoding='latin-1', ignore_missing_memofile=True)
        fields = [{'name': f.name, 'type': f.type, 'length': f.length, 'decimal_count': f.decimal_count}
                  for f in table.fields]
        records = [{k: safe_value(v) for k, v in r.items()} for r in table]
        return fields, records, None
    except Exception as e:
        return [], [], str(e)


def read_dbf_records(path):
    _, records, _ = read_dbf(path)
    return records


def dbf_count(path):
    try:
        t = dbfread.DBF(path, encoding='latin-1', ignore_missing_memofile=True, load=False)
        return t.header.numrecords
    except:
        return 0


def empr_path(empr_dir, filename):
    return os.path.join(DATA_DIR, empr_dir, filename)


def root_path(filename):
    return os.path.join(DATA_DIR, filename)


# ── Cache & Lookups ───────────────────────────────────────────────────────

_cache = {}

def cached(key, loader):
    if key not in _cache:
        _cache[key] = loader()
    return _cache[key]


def load_lookup(filename, key_field, val_field):
    """Load a lookup table as {key: value} dict."""
    path = root_path(filename)
    if not os.path.exists(path):
        return {}
    records = read_dbf_records(path)
    result = {}
    for r in records:
        k = r.get(key_field)
        v = r.get(val_field)
        if k is not None:
            result[str(k).strip()] = str(v).strip() if v else ''
    return result


def get_lookups():
    return cached('lookups', _build_lookups)


def _build_lookups():
    return {
        'tip_liq': load_lookup('TIP_LIQ.DBF', 'CODIGO', 'LEYENDA'),
        'tipoitem': load_lookup('TIPOITEM.DBF', 'CODIGO', 'LEYENDA'),
        'tiposuel': load_lookup('TIPOSUEL.DBF', 'TIPO', 'LEYENDA'),
        'aporte': load_lookup('APORTE.DBF', 'CODIGO', 'TEXTO'),
        'causal': load_lookup('CAUSAL.DBF', 'CODIGO', 'LEYENDA'),
        'segsal': load_lookup('SEGSAL.DBF', 'CODIGO', 'LEYENDA'),
        'vinfun': load_lookup('VINFUN.DBF', 'CODIGO', 'LEYENDA'),
        'compesp': load_lookup('COMPESP.DBF', 'CODIGO', 'LEYENDA'),
        'tipoamp': load_lookup('TIPOAMP.DBF', 'TIPO', 'LEYENDA'),
        'deptos': load_lookup('Deptos.dbf', 'DEPID', 'DEPDSC'),
        'localidades': load_lookup('Locali.dbf', 'LOCID', 'LOCDSC'),
        'grupos': load_lookup('Grupo.dbf', 'GRUCOD', 'GRUDSC'),
        'natjur': load_lookup('Natjur.dbf', 'NATJURID', 'NATJURDSC'),
        'periodo': load_lookup('PERIODO.DBF', 'CODIGO', 'LEYENDA'),
        'nacional': load_lookup('NACIONAL.DBF', 'CODIGO', 'LEYENDA'),
    }


def get_empresas():
    return cached('empresas', lambda: read_dbf_records(root_path('EMPRESAS.DBF')))


def get_empr_dirs():
    def _load():
        dirs = []
        for d in os.listdir(DATA_DIR):
            if (d.startswith('EMPR') or d.startswith('Empr')) and os.path.isdir(os.path.join(DATA_DIR, d)):
                dirs.append(d)
        return sorted(dirs, key=lambda x: int(''.join(filter(str.isdigit, x)) or '0'))
    return cached('empr_dirs', _load)


def resolve_empresa(emp):
    """Enrich an empresa record with resolved lookup values."""
    lk = get_lookups()
    e = dict(emp)
    e['_depto_nombre'] = lk['deptos'].get(str(e.get('DEPARTAM', '')).strip(), '')
    e['_grupo_nombre'] = lk['grupos'].get(str(e.get('GRUPO', '')).strip(), '')
    e['_aporte_nombre'] = lk['aporte'].get(str(e.get('TIP_APOR', '')).strip(), '')
    return e


def resolve_empleado(emp):
    """Enrich an employee record with resolved lookup values."""
    lk = get_lookups()
    e = dict(emp)
    e['_nombre_completo'] = ' '.join(filter(None, [
        str(e.get('NOMBRE1', '')).strip(), str(e.get('NOMBRE2', '')).strip(),
        str(e.get('APELLIDO1', '')).strip(), str(e.get('APELLIDO2', '')).strip()
    ]))
    e['_tip_suel'] = lk['tiposuel'].get(str(e.get('TIP_SUEL', '')).strip(), '')
    e['_segsal'] = lk['segsal'].get(str(e.get('SEGSAL', '')).strip(), '')
    e['_causal'] = lk['causal'].get(str(e.get('CAUSAL', '')).strip(), '')
    e['_compesp'] = lk['compesp'].get(str(e.get('COMPESP', '')).strip(), '')
    e['_activo'] = 'No' if e.get('EGRESO') == '1' or e.get('FEC_EGR') else 'Si'
    return e


# ── API Routes ─────────────────────────────────────────────────────────────

@app.route('/')
@pin_required
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/empresas')
@pin_required
def api_empresas():
    return jsonify(cached('api_empresas', _build_empresas_list))


def _build_empresas_list():
    empresas_dbf = get_empresas()
    lk = get_lookups()
    empr_dirs = get_empr_dirs()

    # Index EMPRESAS.DBF by NUM_EMP
    emp_by_num = {}
    for emp in empresas_dbf:
        emp_by_num[str(emp.get('NUM_EMP', ''))] = emp

    result = []
    seen = set()
    for d in empr_dirs:
        num = d.replace('EMPR', '').replace('Empr', '')
        seen.add(num)

        # Start from EMPRESAS.DBF if available
        base = dict(emp_by_num.get(num, {}))

        # Enrich/override with CONTRIB.DBF from the directory
        contrib_path = empr_path(d, 'CONTRIB.DBF')
        if os.path.exists(contrib_path):
            contribs = read_dbf_records(contrib_path)
            if contribs:
                c = contribs[0]
                # Fill missing fields from CONTRIB
                for k, v in c.items():
                    if v and str(v).strip() and (not base.get(k) or not str(base[k]).strip()):
                        base[k] = v
                if not base.get('NOMBRE') or not str(base['NOMBRE']).strip():
                    base['NOMBRE'] = c.get('NOMBRE', '')

        if not base.get('NUM_EMP'):
            base['NUM_EMP'] = int(num) if num.isdigit() else num

        e = resolve_empresa(base)
        e['_dir'] = d
        ep = empr_path(d, 'EMPLEADO.DBF')
        e['_num_empleados'] = dbf_count(ep) if os.path.exists(ep) else 0
        result.append(e)

    return result


@app.route('/api/empresa/<empr_dir>')
@pin_required
def api_empresa_detail(empr_dir):
    """Full empresa detail with CONTRIB data merged."""
    num = empr_dir.replace('EMPR', '').replace('Empr', '')
    emp = next((e for e in get_empresas() if str(e.get('NUM_EMP', '')) == num), {})
    empresa = resolve_empresa(emp)

    # Load CONTRIB from empresa dir
    contrib_path = empr_path(empr_dir, 'CONTRIB.DBF')
    contrib = {}
    if os.path.exists(contrib_path):
        recs = read_dbf_records(contrib_path)
        if recs:
            contrib = recs[0]
            lk = get_lookups()
            contrib['_natjur'] = lk['natjur'].get(str(contrib.get('NATU_JUR', '')).strip(), '')
            contrib['_depto'] = lk['deptos'].get(str(contrib.get('DEPARTAM', '')).strip(), str(contrib.get('DEPARTAM', '')))
            contrib['_aporte'] = lk['aporte'].get(str(contrib.get('TIP_APOR', '')).strip(), '')

    # List available tables with counts
    tablas = []
    if os.path.isdir(os.path.join(DATA_DIR, empr_dir)):
        for f in sorted(os.listdir(os.path.join(DATA_DIR, empr_dir))):
            if f.upper().endswith('.DBF'):
                tablas.append({'name': f, 'records': dbf_count(empr_path(empr_dir, f))})

    return jsonify({'empresa': empresa, 'contrib': contrib, 'tablas': tablas})


@app.route('/api/empresa/<empr_dir>/empleados')
@pin_required
def api_empleados(empr_dir):
    """Employees with resolved lookups."""
    path = empr_path(empr_dir, 'EMPLEADO.DBF')
    if not os.path.exists(path):
        return jsonify([])
    records = read_dbf_records(path)
    return jsonify([resolve_empleado(r) for r in records])


@app.route('/api/empresa/<empr_dir>/empleado/<int:numero>')
@pin_required
def api_empleado_detail(empr_dir, numero):
    """Single employee with all related data: sueldos, items, horas."""
    lk = get_lookups()

    # Employee
    emp_path = empr_path(empr_dir, 'EMPLEADO.DBF')
    empleados = read_dbf_records(emp_path) if os.path.exists(emp_path) else []
    empleado = next((resolve_empleado(e) for e in empleados if e.get('NUMERO') == numero), None)
    if not empleado:
        return jsonify({'error': 'Empleado no encontrado'}), 404

    # Sueldos (liquidaciones)
    sue_path = empr_path(empr_dir, 'SUELDOS.DBF')
    sueldos_raw = read_dbf_records(sue_path) if os.path.exists(sue_path) else []
    sueldos = []
    for s in sueldos_raw:
        if s.get('NUMERO') == numero:
            s = dict(s)
            s['_tip_liq'] = lk['tip_liq'].get(str(s.get('TIP_LIQ', '')).strip(), '')
            sueldos.append(s)
    sueldos.sort(key=lambda x: x.get('FECHA', '') or '', reverse=True)

    # Items de sueldo
    item_path = empr_path(empr_dir, 'ITEM_SUE.DBF')
    items_raw = read_dbf_records(item_path) if os.path.exists(item_path) else []
    items = []
    for it in items_raw:
        if it.get('NUMERO') == numero:
            it = dict(it)
            it['_tipo'] = lk['tipoitem'].get(str(it.get('CODIGO', '')).strip(), '')
            it['_hab_des'] = 'Haber' if it.get('HABODES') == 'H' else 'Descuento' if it.get('HABODES') == 'D' else ''
            items.append(it)
    items.sort(key=lambda x: (x.get('FECHA', '') or '', x.get('TIP_LIQ', 0)))

    # Horas
    horas_path = empr_path(empr_dir, 'HORAS.DBF')
    horas_raw = read_dbf_records(horas_path) if os.path.exists(horas_path) else []
    horas = [h for h in horas_raw if h.get('NUMERO') == numero]

    return jsonify({
        'empleado': empleado,
        'sueldos': sueldos,
        'items': items,
        'horas': horas,
    })


@app.route('/api/empresa/<empr_dir>/liquidaciones')
@pin_required
def api_liquidaciones(empr_dir):
    """All liquidaciones with employee names and item totals."""
    lk = get_lookups()

    # Employees index
    emp_path = empr_path(empr_dir, 'EMPLEADO.DBF')
    empleados = read_dbf_records(emp_path) if os.path.exists(emp_path) else []
    emp_map = {}
    for e in empleados:
        n = e.get('NUMERO')
        nombre = ' '.join(filter(None, [str(e.get('APELLIDO1', '')).strip(), str(e.get('APELLIDO2', '')).strip(),
                                         str(e.get('NOMBRE1', '')).strip()]))
        emp_map[n] = nombre

    # Patrones index
    pat_path = empr_path(empr_dir, 'PATRONES.DBF')
    patrones = read_dbf_records(pat_path) if os.path.exists(pat_path) else []
    for p in patrones:
        n = p.get('NUMERO')
        nombre = ' '.join(filter(None, [str(p.get('APELLIDO1', '')).strip(), str(p.get('APELLIDO2', '')).strip(),
                                         str(p.get('NOMBRE1', '')).strip()]))
        if n not in emp_map:
            emp_map[n] = nombre + ' (patron)'

    # Sueldos
    sue_path = empr_path(empr_dir, 'SUELDOS.DBF')
    sueldos = read_dbf_records(sue_path) if os.path.exists(sue_path) else []
    result = []
    for s in sueldos:
        r = dict(s)
        r['_empleado'] = emp_map.get(s.get('NUMERO'), '?')
        r['_tip_liq'] = lk['tip_liq'].get(str(s.get('TIP_LIQ', '')).strip(), '')
        result.append(r)
    result.sort(key=lambda x: x.get('FECHA', '') or '', reverse=True)
    return jsonify(result)


@app.route('/api/empresa/<empr_dir>/boletas')
@pin_required
def api_boletas(empr_dir):
    """BPS boletas with their items."""
    lk = get_lookups()

    bol_path = empr_path(empr_dir, 'BOL_BPS.DBF')
    boletas = read_dbf_records(bol_path) if os.path.exists(bol_path) else []

    item_path = empr_path(empr_dir, 'ITEM_BPS.DBF')
    items = read_dbf_records(item_path) if os.path.exists(item_path) else []

    # Group items by boleta
    items_by_bol = {}
    for it in items:
        key = (str(it.get('TIP_BOL', '')), str(it.get('FEC_CARGO', '')))
        items_by_bol.setdefault(key, []).append(it)

    result = []
    for b in boletas:
        b = dict(b)
        key = (str(b.get('TIP_BOL', '')), str(b.get('FEC_CARGO', '')))
        b['_items'] = items_by_bol.get(key, [])
        result.append(b)
    result.sort(key=lambda x: x.get('FEC_CARGO', '') or '', reverse=True)
    return jsonify(result)


@app.route('/api/empresa/<empr_dir>/tabla/<name>')
@pin_required
def api_tabla_raw(empr_dir, name):
    """Raw table view for any table."""
    path = empr_path(empr_dir, name)
    if not os.path.exists(path):
        return jsonify({'error': 'No encontrado'}), 404
    fields, records, error = read_dbf(path)
    if error:
        return jsonify({'error': error})
    return jsonify({'fields': fields, 'records': records})


@app.route('/api/tabla/<name>')
@pin_required
def api_tabla_root(name):
    """Raw root table view."""
    path = root_path(name)
    if not os.path.exists(path):
        return jsonify({'error': 'No encontrado'}), 404
    fields, records, error = read_dbf(path)
    if error:
        return jsonify({'error': error})
    return jsonify({'fields': fields, 'records': records})


@app.route('/api/lookups')
@pin_required
def api_lookups():
    return jsonify(get_lookups())


@app.route('/api/root-tables')
@pin_required
def api_root_tables():
    files = []
    for f in sorted(os.listdir(DATA_DIR)):
        if f.upper().endswith('.DBF') and os.path.isfile(root_path(f)):
            files.append({'name': f, 'records': dbf_count(root_path(f))})
    return jsonify(files)


# ── HTML Template ──────────────────────────────────────────────────────────

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sistema de Sueldos - Visor</title>
<style>
:root{--bg:#0f172a;--s1:#1e293b;--s2:#334155;--brd:#475569;--tx:#e2e8f0;--tx2:#94a3b8;--ac:#38bdf8;--ac2:#818cf8;--grn:#4ade80;--ylw:#fbbf24;--red:#f87171;--org:#fb923c}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--tx);min-height:100vh}
.hdr{background:var(--s1);border-bottom:1px solid var(--brd);padding:14px 20px;display:flex;align-items:center;gap:16px;position:sticky;top:0;z-index:100}
.hdr h1{font-size:18px;font-weight:600} .hdr h1 b{color:var(--ac)}
.hdr .st{margin-left:auto;font-size:12px;color:var(--tx2);display:flex;gap:14px} .hdr .st em{color:var(--ac);font-style:normal;font-weight:600}
.lay{display:flex;min-height:calc(100vh - 53px)}
.sb{width:260px;min-width:260px;background:var(--s1);border-right:1px solid var(--brd);overflow-y:auto;padding:8px 0}
.sb h3{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--tx2);padding:12px 14px 4px}
.sb a{display:flex;align-items:center;gap:6px;padding:7px 14px;color:var(--tx);text-decoration:none;font-size:12.5px;cursor:pointer;transition:background .15s}
.sb a:hover{background:var(--s2)} .sb a.ac{background:var(--ac);color:var(--bg);font-weight:600}
.sb .bg{margin-left:auto;font-size:10px;background:var(--s2);padding:1px 6px;border-radius:8px;color:var(--tx2)}
.sb a.ac .bg{background:rgba(0,0,0,.2);color:var(--bg)}
.sb input{margin:6px 10px;padding:6px 8px;width:calc(100% - 20px);background:var(--bg);border:1px solid var(--brd);border-radius:5px;color:var(--tx);font-size:12px;outline:none}
.sb input:focus{border-color:var(--ac)}
.mn{flex:1;padding:20px;overflow-x:auto}
.mn h2{font-size:17px;margin-bottom:14px} .mn h2 small{font-size:12px;color:var(--tx2);font-weight:400}
.cds{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;margin-bottom:20px}
.cd{background:var(--s1);border:1px solid var(--brd);border-radius:7px;padding:14px;cursor:pointer;transition:border-color .15s}
.cd:hover{border-color:var(--ac)}
.cd .lb{font-size:10px;text-transform:uppercase;color:var(--tx2);margin-bottom:3px}
.cd .vl{font-size:22px;font-weight:700;color:var(--ac)} .cd .su{font-size:11px;color:var(--tx2);margin-top:2px}
.tw{background:var(--s1);border:1px solid var(--brd);border-radius:7px;overflow:hidden;margin-bottom:16px}
.tb{padding:10px 14px;border-bottom:1px solid var(--brd);display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.tb input{padding:5px 8px;background:var(--bg);border:1px solid var(--brd);border-radius:5px;color:var(--tx);font-size:12px;outline:none;flex:1;min-width:180px}
.tb input:focus{border-color:var(--ac)} .tb .nf{font-size:11px;color:var(--tx2)}
table{width:100%;border-collapse:collapse;font-size:12px}
thead th{background:var(--s2);padding:8px 10px;text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:.4px;color:var(--tx2);white-space:nowrap;border-bottom:1px solid var(--brd);cursor:pointer;position:sticky;top:0}
thead th:hover{color:var(--ac)} thead th.so{color:var(--ac)}
tbody td{padding:7px 10px;border-bottom:1px solid rgba(71,85,105,.3);max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
tbody tr:hover{background:rgba(56,189,248,.05)} tbody tr.click:hover{background:rgba(56,189,248,.1);cursor:pointer}
td.n{text-align:right;font-variant-numeric:tabular-nums} td.d{color:var(--ylw)} td.e{color:var(--s2)} td.m{color:var(--grn);font-weight:600}
.det{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin-bottom:20px;background:var(--s1);border:1px solid var(--brd);border-radius:7px;padding:16px}
.det .f{font-size:12px} .det .f .k{color:var(--tx2);font-size:10px;text-transform:uppercase} .det .f .v{margin-top:1px}
.tabs{display:flex;gap:3px;margin-bottom:14px;flex-wrap:wrap}
.tab{padding:7px 14px;background:var(--s1);border:1px solid var(--brd);border-radius:5px;color:var(--tx2);cursor:pointer;font-size:12px;transition:all .15s}
.tab:hover{border-color:var(--ac);color:var(--tx)} .tab.ac{background:var(--ac);color:var(--bg);border-color:var(--ac);font-weight:600}
.tag{display:inline-block;padding:1px 6px;border-radius:3px;font-size:10px;font-weight:600}
.tag-h{background:#064e3b;color:#6ee7b7} .tag-d{background:#7f1d1d;color:#fca5a5} .tag-a{background:#1e3a5f;color:#93c5fd}
.pg{display:flex;gap:6px;margin-top:10px;align-items:center}
.pg button{padding:5px 10px;background:var(--s1);border:1px solid var(--brd);border-radius:5px;color:var(--tx);cursor:pointer;font-size:12px}
.pg button:hover{border-color:var(--ac)} .pg button:disabled{opacity:.3;cursor:default} .pg .pi{font-size:12px;color:var(--tx2)}
.ld{text-align:center;padding:40px;color:var(--tx2)} .er{color:var(--red);padding:14px;background:rgba(248,113,113,.1);border-radius:7px}
.sec{margin-top:20px} .sec h3{font-size:14px;margin-bottom:10px;color:var(--tx)}
.liq-row:hover{background:var(--s2)}
.brc{font-size:12px;color:var(--tx2);margin-bottom:12px} .brc a{color:var(--ac);cursor:pointer;text-decoration:none} .brc a:hover{text-decoration:underline}
.menu-btn{display:none;background:none;border:1px solid var(--brd);border-radius:5px;color:var(--tx);font-size:20px;padding:2px 8px;cursor:pointer;line-height:1}
.sb-overlay{display:none}
.tw{overflow-x:auto;-webkit-overflow-scrolling:touch}
@media(max-width:768px){
  .menu-btn{display:block}
  .hdr{padding:10px 12px;gap:8px}
  .hdr h1{font-size:15px}
  .hdr .st{display:none}
  .sb{position:fixed;left:-280px;top:0;bottom:0;z-index:200;transition:left .25s ease;width:280px;min-width:280px}
  .sb.open{left:0}
  .sb-overlay{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:150;display:none}
  .sb-overlay.open{display:block}
  .lay{flex-direction:column}
  .mn{padding:12px;overflow-x:hidden}
  .mn h2{font-size:15px;margin-bottom:10px}
  .cds{grid-template-columns:1fr 1fr;gap:8px}
  .cd{padding:10px} .cd .vl{font-size:18px}
  .det{grid-template-columns:1fr;padding:12px;gap:8px}
  .tabs{gap:4px} .tab{padding:6px 10px;font-size:11px}
  table{font-size:11px;min-width:600px}
  thead th{padding:6px 8px;font-size:9px}
  tbody td{padding:5px 8px;max-width:150px}
  .tb{padding:8px 10px} .tb input{min-width:120px;font-size:12px}
  .pg{flex-wrap:wrap} .pg button{padding:4px 8px;font-size:11px}
  .sec h3{font-size:13px}
  .brc{font-size:11px}
}
@media(max-width:400px){
  .cds{grid-template-columns:1fr}
  .hdr h1{font-size:13px}
  table{min-width:500px}
}
</style>
</head>
<body>
<div class="hdr">
  <button class="menu-btn" onclick="toggleSb()">&#9776;</button>
  <h1><b>SILVANA</b> Sistema de Sueldos</h1>
  <div class="st" id="hst"></div>
  <button onclick="reloadCache()" style="padding:5px 10px;background:var(--s2);border:1px solid var(--brd);border-radius:5px;color:var(--tx2);cursor:pointer;font-size:11px" title="Recargar datos (detectar nuevos archivos)">Recargar</button>
  <a href="/logout" style="font-size:11px;color:var(--tx2);text-decoration:none">Salir</a>
</div>
<div class="lay">
  <div class="sb-overlay" id="sbOverlay" onclick="toggleSb()"></div>
  <div class="sb" id="sb"></div>
  <div class="mn" id="mn"><div class="ld">Cargando...</div></div>
</div>

<script>
const PS=50;
let S={v:'dash',empresas:[],dirs:[],lk:{},cur:null,tab:null,sc:null,sa:true,ft:'',pg:0,_d:null};

async function api(u){const r=await fetch(u);return r.json()}

async function init(){
  const [emp,lk]=await Promise.all([api('/api/empresas'),api('/api/lookups')]);
  S.empresas=emp; S.lk=lk;
  S.dirs=emp.filter(e=>e._dir).map(e=>e._dir);
  renderSb(); renderDash(true);
  history.replaceState({v:'dash'},'');
}

// ── Sidebar ──
function renderSb(){
  const sb=document.getElementById('sb');
  let h='<a onclick="renderDash()" class="'+(S.v==='dash'?'ac':'')+'">Dashboard</a>';
  h+='<h3>Empresas ('+S.empresas.length+')</h3>';
  h+='<input placeholder="Buscar empresa..." oninput="fltSb(this.value)" id="sflt">';
  for(const e of S.empresas){
    const d=e._dir; if(!d) continue;
    const nm=e.NOMBRE||e.FANTASIA||d;
    const ac=S.v==='emp'&&S.cur===d?'ac':'';
    h+='<a class="sb-e '+ac+'" onclick="showEmp(\''+d+'\')" data-s="'+(nm+' '+d+' '+(e.GIRO||'')).toLowerCase()+'">'
      +'<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="'+esc(nm)+'">'+esc(trn(nm,28))+'</span>'
      +'<span class="bg">'+e._num_empleados+'</span></a>';
  }
  h+='<h3>Tablas de Referencia</h3>';
  h+='<a onclick="showRef()" class="'+(S.v==='ref'?'ac':'')+'">Ver Tablas Maestras</a>';
  sb.innerHTML=h;
  const t=S.empresas.length;
  const te=S.empresas.reduce((s,e)=>s+(e._num_empleados||0),0);
  document.getElementById('hst').innerHTML='<span><em>'+t+'</em> empresas</span><span><em>'+te+'</em> empleados</span>';
}

function fltSb(t){
  const tl=t.toLowerCase();
  document.querySelectorAll('.sb-e').forEach(el=>{el.style.display=el.dataset.s.includes(tl)?'':'none'});
}

// ── History API ──
function pushNav(state){
  history.pushState(state,'');
}
window.addEventListener('popstate',function(e){
  if(!e.state) return;
  const st=e.state;
  if(st.v==='dash') renderDash(true);
  else if(st.v==='emp'){showEmp(st.dir,true,st.tab||'general');}
  else if(st.v==='empleado'){showEmpleado(st.dir,st.num,true);}
  else if(st.v==='ref') showRef(true);
});

// ── Dashboard ──
function renderDash(fromPop){
  S.v='dash';S.cur=null;renderSb();closeSb();
  if(!fromPop) pushNav({v:'dash'});
  const m=document.getElementById('mn');
  const te=S.empresas.reduce((s,e)=>s+(e._num_empleados||0),0);
  const lk=S.lk;
  let h='<h2>Dashboard General</h2>';
  h+='<div class="cds">';
  h+=cd('Empresas',S.empresas.length,'registradas');
  h+=cd('Empleados',te,'en todas las empresas');
  h+=cd('Departamentos',Object.keys(lk.deptos||{}).length,'del Uruguay');
  h+=cd('Grupos Salariales',Object.keys(lk.grupos||{}).length,'consejos de salarios');
  h+='</div>';

  // Top empresas by employees
  const top=[...S.empresas].sort((a,b)=>(b._num_empleados||0)-(a._num_empleados||0)).slice(0,10);
  h+='<div class="sec"><h3>Empresas con Mas Empleados</h3>';
  h+='<div class="tw"><table><thead><tr><th>Empresa</th><th>Giro</th><th>Departamento</th><th>Grupo</th><th>Empleados</th><th>Desde</th></tr></thead><tbody>';
  for(const e of top){
    h+='<tr class="click" onclick="showEmp(\''+e._dir+'\')">'
      +'<td><b>'+esc(e.NOMBRE||'')+'</b></td>'
      +'<td>'+esc(e.GIRO||'')+'</td>'
      +'<td>'+esc(e._depto_nombre||e.DEPARTAM||'')+'</td>'
      +'<td>'+esc(e._grupo_nombre||'Grupo '+(e.GRUPO||'').trim())+'</td>'
      +'<td class="n m">'+e._num_empleados+'</td>'
      +'<td class="d">'+(e.FEC_INI||'-')+'</td></tr>';
  }
  h+='</tbody></table></div></div>';

  // All empresas
  h+='<div class="sec"><h3>Todas las Empresas</h3>';
  h+='<div class="tw"><div class="tb"><input placeholder="Filtrar empresas..." oninput="fltDash(this.value)"><span class="nf">'+S.empresas.length+' empresas</span></div>';
  h+='<div id="dashTbl"></div></div></div>';
  m.innerHTML=h;
  renderDashTbl(S.empresas);
}

function renderDashTbl(data){
  let h='<table><thead><tr><th>NUM</th><th>Nombre</th><th>Fantasia</th><th>Giro</th><th>RUC</th><th>BPS</th><th>Departamento</th><th>Grupo</th><th>Aporte</th><th>Empleados</th></tr></thead><tbody>';
  for(const e of data){
    if(!e._dir) continue;
    h+='<tr class="click" onclick="showEmp(\''+e._dir+'\')">'
      +'<td class="n">'+e.NUM_EMP+'</td>'
      +'<td>'+esc(e.NOMBRE||'')+'</td>'
      +'<td>'+esc(e.FANTASIA||'')+'</td>'
      +'<td>'+esc(trn(e.GIRO||'',30))+'</td>'
      +'<td>'+esc(e.RUC||'')+'</td>'
      +'<td>'+esc(e.BPS||'')+'</td>'
      +'<td>'+esc(e._depto_nombre||'')+'</td>'
      +'<td>'+esc(e._grupo_nombre||'')+'</td>'
      +'<td>'+esc(e._aporte_nombre||'')+'</td>'
      +'<td class="n m">'+(e._num_empleados||0)+'</td></tr>';
  }
  h+='</tbody></table>';
  document.getElementById('dashTbl').innerHTML=h;
}

function fltDash(t){
  const tl=t.toLowerCase();
  const f=S.empresas.filter(e=>JSON.stringify(e).toLowerCase().includes(tl));
  renderDashTbl(f);
}

// ── Empresa Detail ──
async function showEmp(dir,fromPop,tab){
  S.v='emp';S.cur=dir;S.tab=tab||'general';renderSb();closeSb();
  if(!fromPop) pushNav({v:'emp',dir:dir,tab:S.tab});
  const m=document.getElementById('mn');
  m.innerHTML='<div class="ld">Cargando empresa...</div>';

  const data=await api('/api/empresa/'+dir);
  S._emp=data;
  renderEmpTabs(data,dir);
}

function renderEmpTabs(data,dir){
  const m=document.getElementById('mn');
  const e=data.empresa;
  const c=data.contrib;
  const nm=e.NOMBRE||c.NOMBRE||dir;

  let h='<div class="brc"><a onclick="renderDash()">Dashboard</a> &rsaquo; '+esc(nm)+'</div>';
  h+='<h2>'+esc(nm)+' <small>EMPR '+esc(String(e.NUM_EMP||''))+'</small></h2>';

  // Tabs
  h+='<div class="tabs">';
  const tabs=[['general','Datos Generales'],['empleados','Empleados'],['liquidaciones','Liquidaciones'],['boletas','Boletas BPS'],['tablas','Todas las Tablas']];
  for(const[k,v] of tabs){
    h+='<div class="tab'+(S.tab===k?' ac':'')+'" onclick="empTab(\''+k+'\')">'+v+'</div>';
  }
  h+='</div>';
  h+='<div id="empContent"></div>';
  m.innerHTML=h;
  empTabContent(S.tab,data,dir);
}

function empTab(t){S.tab=t;empTabContent(t,S._emp,S.cur);pushNav({v:'emp',dir:S.cur,tab:t});}

async function empTabContent(tab,data,dir){
  const ct=document.getElementById('empContent');
  if(tab==='general') renderEmpGeneral(ct,data);
  else if(tab==='empleados') await renderEmpEmpleados(ct,dir);
  else if(tab==='liquidaciones') await renderEmpLiqs(ct,dir);
  else if(tab==='boletas') await renderEmpBoletas(ct,dir);
  else if(tab==='tablas') renderEmpTablas(ct,data,dir);
  // Update tab active state
  document.querySelectorAll('.tabs .tab').forEach(el=>{
    el.className='tab'+(el.textContent===({'general':'Datos Generales','empleados':'Empleados','liquidaciones':'Liquidaciones','boletas':'Boletas BPS','tablas':'Todas las Tablas'}[tab]||'')?' ac':'');
  });
}

function renderEmpGeneral(ct,data){
  const e=data.empresa, c=data.contrib, lk=S.lk;
  let h='<div class="sec"><h3>Datos de la Empresa</h3><div class="det">';
  const pairs=[
    ['Nombre',e.NOMBRE],['Fantasia',e.FANTASIA],['Giro',e.GIRO||c.GIRO],
    ['Direccion',c.DOM_CONS||e.DIR],['Dir. Fiscal',c.DOM_FIS],['Telefono',c.TEL||e.TEL],
    ['RUC',e.RUC||c.RUC],['BPS',e.BPS||c.BPS],['BSE',e.BSE||c.BSE],
    ['MTSS',e.MTSS||c.MTSS],['Cod. Postal',c.COD_POST],
    ['Departamento',e._depto_nombre||(lk.deptos||{})[String(c.DEPARTAM||'').trim()]||c.DEPARTAM||e.DEPARTAM],
    ['Localidad',(lk.localidades||{})[String(e.LOCALIDAD||'').trim()]||c.LOCALIDAD||e.LOCALIDAD],
    ['Naturaleza Juridica',c.NATU_JUR||c._natjur||(lk.natjur||{})[String(c.NATU_JUR||'').trim()]],
    ['Grupo Salarial',e._grupo_nombre||'Grupo '+(e.GRUPO||'').trim()],
    ['Subgrupo',(e.SUBGRUPO||'').trim()],
    ['Tipo Aporte',e._aporte_nombre||c._aporte],['Tipo Contribuyente',(e.TIP_CON||c.TIP_CON||'').trim()],
    ['Fecha Inicio',e.FEC_INI],['Fecha Cierre',c.FEC_CIE||e.FEC_EGR],
    ['Firmante',c.FIRMANTE],['CI Firmante',c.CED_FIRMA],['Caracter',c.CARACTER],
    ['Cert. BPS',e.CERTBPS],['Cert. DGI',e.CERTDGI],['Fecha MTSS',e.FEC_MTSS||c.FEC_MTSS],
    ['Exonerada',c.EXONERADA],['Construccion',c.CONST],['Manufactura',c.MANUFAC],
    ['Franja BPS',e.FRANJABPS],['THA',c.THA||e.THA],
  ];
  for(const[k,v] of pairs){
    if(v && String(v).trim() && v!=='N') h+='<div class="f"><div class="k">'+k+'</div><div class="v">'+esc(String(v))+'</div></div>';
  }
  h+='</div></div>';

  // Sectores
  const secs=[c.SECTOR1,c.SECTOR2,c.SECTOR3,c.SECTOR4,c.SECTOR5,c.SECTOR6].filter(s=>s&&String(s).trim());
  if(secs.length){
    h+='<div class="sec"><h3>Sectores</h3><div class="cds">';
    for(const s of secs) h+='<div class="cd"><div class="vl" style="font-size:14px">'+esc(s)+'</div></div>';
    h+='</div></div>';
  }

  // Summary cards
  h+='<div class="sec"><h3>Resumen de Datos</h3><div class="cds">';
  for(const t of data.tablas){
    const names={'EMPLEADO.DBF':'Empleados','PATRONES.DBF':'Patrones','SUELDOS.DBF':'Liquidaciones',
      'SUELPAT.DBF':'Liq. Patrones','ITEM_SUE.DBF':'Items Sueldo','ITEM_PAT.DBF':'Items Patron',
      'BOL_BPS.DBF':'Boletas BPS','ITEM_BPS.DBF':'Items BPS','HORAS.DBF':'Reg. Horas',
      'OBRAS.DBF':'Obras','CONVENIO.DBF':'Convenios','AMPAROS.DBF':'Amparos','COMULIC.DBF':'Licencias'};
    const label=names[t.name.toUpperCase()]||t.name;
    h+=cd(label,t.records,t.name);
  }
  h+='</div></div>';
  ct.innerHTML=h;
}

async function renderEmpEmpleados(ct,dir){
  ct.innerHTML='<div class="ld">Cargando empleados...</div>';
  const emps=await api('/api/empresa/'+dir+'/empleados');
  let h='<div class="tw"><div class="tb"><input placeholder="Buscar empleado..." oninput="fltTbl(this.value)"><span class="nf">'+emps.length+' empleados</span></div>';
  h+='<div id="tblC"></div></div>';
  ct.innerHTML=h;
  S._tblData=emps;S.ft='';S.pg=0;S.sc=null;
  renderEmpTbl();
}

function renderEmpTbl(){
  let data=[...S._tblData];
  if(S.ft){const f=S.ft.toLowerCase();data=data.filter(r=>JSON.stringify(r).toLowerCase().includes(f));}
  const tp=Math.ceil(data.length/PS)||1;
  if(S.pg>=tp)S.pg=tp-1;
  const sl=data.slice(S.pg*PS,S.pg*PS+PS);
  let h='<table><thead><tr><th>Num</th><th>Nombre Completo</th><th>CI</th><th>Cargo</th><th>Tipo Sueldo</th><th>Sueldo</th><th>Ingreso</th><th>Egreso</th><th>Activo</th><th>Seg. Salud</th></tr></thead><tbody>';
  for(const e of sl){
    h+='<tr class="click" onclick="showEmpleado(\''+S.cur+'\','+e.NUMERO+')">'
      +'<td class="n">'+e.NUMERO+'</td>'
      +'<td><b>'+esc(e._nombre_completo||'')+'</b></td>'
      +'<td>'+esc(e.CED_IDEN||'')+'</td>'
      +'<td>'+esc(e.CARGO||'')+'</td>'
      +'<td>'+esc(e._tip_suel||e.TIP_SUEL||'')+'</td>'
      +'<td class="n m">'+(e.SUELD?fmtN(e.SUELD):'-')+'</td>'
      +'<td class="d">'+(e.FEC_ING||'-')+'</td>'
      +'<td class="d">'+(e.FEC_EGR||'-')+'</td>'
      +'<td>'+(e._activo==='Si'?'<span class="tag tag-h">Activo</span>':'<span class="tag tag-d">Egresado</span>')+'</td>'
      +'<td>'+esc(e._segsal||'')+'</td></tr>';
  }
  h+='</tbody></table>';
  h+=pgn(tp);
  document.getElementById('tblC').innerHTML=h;
}

async function showEmpleado(dir,num,fromPop){
  S.v='empleado';S.cur=dir;renderSb();
  if(!fromPop) pushNav({v:'empleado',dir:dir,num:num});
  const m=document.getElementById('mn');
  m.innerHTML='<div class="ld">Cargando empleado...</div>';
  const data=await api('/api/empresa/'+dir+'/empleado/'+num);
  if(data.error){m.innerHTML='<div class="er">'+data.error+'</div>';return;}
  const e=data.empleado;
  const emp=S.empresas.find(x=>x._dir===dir);
  const empNm=emp?emp.NOMBRE||'':dir;

  let h='<div class="brc"><a onclick="renderDash()">Dashboard</a> &rsaquo; <a onclick="showEmp(\''+dir+'\')">'+esc(empNm)+'</a> &rsaquo; '+esc(e._nombre_completo)+'</div>';
  h+='<h2>'+esc(e._nombre_completo)+' <small>Empleado #'+e.NUMERO+'</small></h2>';

  // Employee info
  h+='<div class="det">';
  const pairs=[
    ['CI',e.CED_IDEN],['Cargo',e.CARGO],['Sexo',e.SEXO],['Estado Civil',e.EST_CIV],
    ['Fecha Nacimiento',e.FEC_NAC],['Fecha Ingreso',e.FEC_ING],['Fecha Egreso',e.FEC_EGR],
    ['Tipo Sueldo',e._tip_suel||e.TIP_SUEL],['Sueldo',e.SUELD?fmtN(e.SUELD):null],
    ['Horas/Dia',e.HORA_DIA],['Horario',e.HORARIO],['Descanso',e.DESCANSO],
    ['Mutual',e.MUTUAL],['Seguro Salud',e._segsal],
    ['Comp. Especial',e._compesp],['Causal Egreso',e._causal],
    ['Activo',e._activo],['Direccion',e.DIREC],['Ciudad',e.CIUDAD],['Departamento',e.DEPARTAM],
    ['Credencial',e.CREDENC],['Cuenta Banco',e.CTABANCO],
  ];
  for(const[k,v] of pairs){
    if(v&&String(v).trim()) h+='<div class="f"><div class="k">'+k+'</div><div class="v">'+esc(String(v))+'</div></div>';
  }
  h+='</div>';

  // Liquidaciones con items integrados (acordeon)
  if(data.sueldos.length){
    // Index items by FECHA+TIP_LIQ
    const itemsByLiq={};
    for(const it of data.items){
      const k=(it.FECHA||'')+'|'+it.TIP_LIQ;
      if(!itemsByLiq[k])itemsByLiq[k]=[];
      itemsByLiq[k].push(it);
    }

    h+='<div class="sec"><h3>Liquidaciones ('+data.sueldos.length+')</h3>';
    h+='<p style="font-size:11px;color:var(--tx2);margin:-6px 0 10px">Click en una liquidacion para ver el detalle de items</p>';
    for(let si=0;si<data.sueldos.length;si++){
      const s=data.sueldos[si];
      const liqKey=(s.FECHA||'')+'|'+s.TIP_LIQ;
      const its=itemsByLiq[liqKey]||[];
      const liqId='liq_'+si;

      // Liquidacion header row
      h+='<div class="tw" style="margin-bottom:8px">';
      h+='<div class="liq-row" onclick="toggleLiq(\''+liqId+'\')" style="padding:10px 14px;cursor:pointer;display:flex;align-items:center;gap:12px;flex-wrap:wrap">';
      h+='<span class="liq-arrow" id="arr_'+liqId+'" style="color:var(--ac);font-size:14px;width:16px">&#9654;</span>';
      h+='<span class="d" style="min-width:85px">'+(s.FECHA||'-')+'</span>';
      h+='<span style="min-width:120px;color:var(--ac)"><b>'+esc(s._tip_liq||String(s.TIP_LIQ||''))+'</b></span>';
      h+='<span style="min-width:80px">Nominal: <b>'+fmtN(s.NOMINAL)+'</b></span>';
      h+='<span style="min-width:80px;color:var(--red)">Desc: <b>'+fmtN(s.DESCUENTO)+'</b></span>';
      h+='<span style="min-width:80px;color:var(--grn)">Liquido: <b>'+fmtN(s.SUELDO)+'</b></span>';
      h+='<span style="min-width:60px">Gravado: '+fmtN(s.GRAVADO)+'</span>';
      if(s.DIASTRAB) h+='<span>'+s.DIASTRAB+' dias</span>';
      if(its.length) h+='<span class="bg" style="font-size:10px">'+its.length+' items</span>';
      h+='</div>';

      // Items detail (hidden by default)
      h+='<div id="'+liqId+'" style="display:none;border-top:1px solid var(--brd)">';
      if(its.length){
        let totH=0,totD=0;
        h+='<table><thead><tr><th>Cod</th><th>Concepto</th><th>H/D</th><th>Importe</th><th>Gravada</th><th>Dias</th><th>Horas</th></tr></thead><tbody>';
        for(const it of its){
          const hd=it.HABODES==='H'?'Haber':it.HABODES==='D'?'Descuento':'';
          const cls=it.HABODES==='H'?'tag-h':'tag-d';
          const imp=it.IMPORTE||0;
          if(it.HABODES==='H')totH+=imp; else totD+=imp;
          h+='<tr><td class="n">'+it.CODIGO+'</td>'
            +'<td>'+esc(it.TEXTO||it._tipo||'')+'</td>'
            +'<td><span class="tag '+cls+'">'+hd+'</span></td>'
            +'<td class="n'+(it.HABODES==='D'?' style="color:var(--red)"':'')+'">'+fmtN(imp)+'</td>'
            +'<td>'+(it.GRAVADA==='S'?'Si':'No')+'</td>'
            +'<td class="n">'+(it.DIAS||'-')+'</td>'
            +'<td class="n">'+(it.HORAS||'-')+'</td></tr>';
        }
        h+='<tr style="font-weight:700;border-top:2px solid var(--brd);background:var(--s2)">'
          +'<td></td><td>TOTALES</td><td></td>'
          +'<td class="n"><span class="tag tag-h">H: '+fmtN(totH)+'</span> <span class="tag tag-d">D: '+fmtN(totD)+'</span></td>'
          +'<td></td><td></td><td></td></tr>';
        h+='</tbody></table>';
      } else {
        h+='<div style="padding:12px;color:var(--tx2);font-size:12px">Sin items para esta liquidacion</div>';
      }
      h+='</div></div>';
    }
    h+='</div>';
  }

  m.innerHTML=h;
}

async function renderEmpLiqs(ct,dir){
  ct.innerHTML='<div class="ld">Cargando liquidaciones...</div>';
  const data=await api('/api/empresa/'+dir+'/liquidaciones');
  let h='<div class="tw"><div class="tb"><input placeholder="Buscar..." oninput="fltTbl(this.value)"><span class="nf">'+data.length+' liquidaciones</span></div>';
  h+='<div id="tblC"></div></div>';
  ct.innerHTML=h;
  S._tblData=data;S.ft='';S.pg=0;S.sc=null;
  renderLiqTbl();
}

function renderLiqTbl(){
  let data=[...S._tblData];
  if(S.ft){const f=S.ft.toLowerCase();data=data.filter(r=>JSON.stringify(r).toLowerCase().includes(f));}
  const tp=Math.ceil(data.length/PS)||1;
  if(S.pg>=tp)S.pg=tp-1;
  const sl=data.slice(S.pg*PS,S.pg*PS+PS);
  let h='<table><thead><tr><th>Fecha</th><th>Empleado</th><th>CI</th><th>Tipo Liquidacion</th><th>Nominal</th><th>Descuentos</th><th>Liquido</th><th>Gravado</th><th>Dias</th></tr></thead><tbody>';
  for(const s of sl){
    h+='<tr class="click" onclick="showEmpleado(\''+S.cur+'\','+s.NUMERO+')">'
      +'<td class="d">'+(s.FECHA||'-')+'</td>'
      +'<td><b>'+esc(s._empleado||'')+'</b></td>'
      +'<td>'+esc(s.CED_IDEN||'')+'</td>'
      +'<td>'+esc(s._tip_liq||'')+'</td>'
      +'<td class="n">'+fmtN(s.NOMINAL)+'</td>'
      +'<td class="n" style="color:var(--red)">'+fmtN(s.DESCUENTO)+'</td>'
      +'<td class="n m">'+fmtN(s.SUELDO)+'</td>'
      +'<td class="n">'+fmtN(s.GRAVADO)+'</td>'
      +'<td class="n">'+(s.DIASTRAB||'-')+'</td></tr>';
  }
  h+='</tbody></table>';
  h+=pgn(tp);
  document.getElementById('tblC').innerHTML=h;
}

async function renderEmpBoletas(ct,dir){
  ct.innerHTML='<div class="ld">Cargando boletas BPS...</div>';
  const data=await api('/api/empresa/'+dir+'/boletas');
  if(!data.length){ct.innerHTML='<div class="ld">Sin boletas BPS</div>';return;}
  let h='';
  for(const b of data){
    h+='<div class="tw" style="margin-bottom:12px"><div class="tb">'
      +'<b>Boleta '+(b.SEYNROBOL||'')+'</b>'
      +'<span class="nf">Cargo: '+(b.FEC_CARGO||'-')+' | Venc: '+(b.FEC_VENC||'-')+'</span>'
      +'<span class="nf">Importe: <b style="color:var(--ac)">'+fmtN(b.IMPORTE)+'</b></span>'
      +'<span class="nf">Empleados: '+(b.CANT_EMP||0)+' | Monto Patronal: '+fmtN(b.MONTO_PAT)+' | Personal: '+fmtN(b.MONTO_PER)+'</span>'
      +'</div>';
    if(b._items&&b._items.length){
      h+='<table><thead><tr><th>Codigo</th><th>Concepto</th><th>Monto Gravado</th><th>%</th><th>Aporte</th><th>Mul/Rec</th></tr></thead><tbody>';
      for(const it of b._items){
        h+='<tr><td class="n">'+it.CODIGO+'</td>'
          +'<td>'+esc(it.TEXTO||'')+'</td>'
          +'<td class="n">'+fmtN(it.MONTOGRAV)+'</td>'
          +'<td class="n">'+esc(it.LEY_PORC||'')+'</td>'
          +'<td class="n m">'+fmtN(it.APORTE)+'</td>'
          +'<td class="n">'+(it.MULREC||'-')+'</td></tr>';
      }
      h+='</tbody></table>';
    }
    h+='</div>';
  }
  ct.innerHTML=h;
}

function renderEmpTablas(ct,data,dir){
  let h='<div class="cds">';
  for(const t of data.tablas){
    h+='<div class="cd" onclick="showRawTbl(\''+dir+'\',\''+t.name+'\')">'
      +'<div class="lb">'+t.name+'</div><div class="vl">'+t.records+'</div><div class="su">registros</div></div>';
  }
  h+='</div><div id="rawTbl"></div>';
  ct.innerHTML=h;
}

async function showRawTbl(dir,name){
  const ct=document.getElementById('rawTbl');
  ct.innerHTML='<div class="ld">Cargando '+name+'...</div>';
  const url=dir?'/api/empresa/'+dir+'/tabla/'+name:'/api/tabla/'+name;
  const data=await api(url);
  if(data.error){ct.innerHTML='<div class="er">'+data.error+'</div>';return;}
  let h='<h3 style="margin:12px 0 8px">'+esc(name)+' <small style="color:var(--tx2)">'+data.records.length+' registros</small></h3>';
  h+='<div class="tw"><table><thead><tr>';
  for(const f of data.fields) h+='<th>'+f.name+'</th>';
  h+='</tr></thead><tbody>';
  for(const r of data.records.slice(0,200)){
    h+='<tr>';
    for(const f of data.fields){
      const v=r[f.name];
      if(v===null||v==='') h+='<td class="e">-</td>';
      else if(f.type==='N') h+='<td class="n">'+v+'</td>';
      else if(f.type==='D') h+='<td class="d">'+v+'</td>';
      else h+='<td title="'+esc(String(v))+'">'+esc(trn(String(v),35))+'</td>';
    }
    h+='</tr>';
  }
  if(data.records.length>200) h+='<tr><td colspan="'+data.fields.length+'" style="text-align:center;color:var(--tx2)">...mostrando 200 de '+data.records.length+'</td></tr>';
  h+='</tbody></table></div>';
  ct.innerHTML=h;
}

// ── Tablas de Referencia ──
async function showRef(fromPop){
  S.v='ref';S.cur=null;renderSb();closeSb();
  if(!fromPop) pushNav({v:'ref'});
  const m=document.getElementById('mn');
  m.innerHTML='<div class="ld">Cargando tablas...</div>';
  const tables=await api('/api/root-tables');
  // Group by category
  const cats={
    'Clasificacion':[/APORTE/i,/TIPCONT/i,/DEFAPOR/i,/CodExo/i],
    'Sueldos e Items':[/TIP_LIQ/i,/TIPOITEM/i,/TIPOSUEL/i,/ITEMS/i,/TIPOAMP/i,/TPSUEL/i],
    'Empleados':[/SEGSAL/i,/VINFUN/i,/COMPESP/i,/CAUSAL/i,/NACIONAL/i,/CODCAU/i,/CODDED/i,/RELFIL/i],
    'Grupos Salariales':[/Grupo/i,/Subgru/i,/GRUPSUB/i,/Catgru/i,/AUMENTOS/i],
    'Geografia':[/Deptos/i,/Locali/i,/Pais/i],
    'Vencimientos':[/VENC/i,/VENMTSS/i],
    'Parametros':[/SUELMINI/i,/DESCUENT/i,/PERIODO/i,/FRECUE/i,/GENERAL/i],
    'Boletas y Contabilidad':[/BOLB_TOT/i,/CONTDIS/i,/CONTRIB/i,/BANCOS/i,/DOCPEND/i,/DISQBAN/i],
  };
  let h='<div class="brc"><a onclick="renderDash()">Dashboard</a> &rsaquo; Tablas de Referencia</div>';
  h+='<h2>Tablas de Referencia</h2>';
  const used=new Set();
  for(const[cat,pats] of Object.entries(cats)){
    const matched=tables.filter(t=>pats.some(p=>p.test(t.name)));
    if(!matched.length) continue;
    h+='<div class="sec"><h3>'+cat+'</h3><div class="cds">';
    for(const t of matched){
      used.add(t.name);
      h+='<div class="cd" onclick="showRefTbl(\''+t.name+'\')">'
        +'<div class="lb">'+t.name+'</div><div class="vl">'+t.records+'</div><div class="su">registros</div></div>';
    }
    h+='</div></div>';
  }
  // Others
  const others=tables.filter(t=>!used.has(t.name));
  if(others.length){
    h+='<div class="sec"><h3>Otras</h3><div class="cds">';
    for(const t of others) h+='<div class="cd" onclick="showRefTbl(\''+t.name+'\')"><div class="lb">'+t.name+'</div><div class="vl">'+t.records+'</div><div class="su">registros</div></div>';
    h+='</div></div>';
  }
  h+='<div id="rawTbl"></div>';
  m.innerHTML=h;
}

async function showRefTbl(name){
  const ct=document.getElementById('rawTbl');
  ct.innerHTML='<div class="ld">Cargando '+name+'...</div>';
  const data=await api('/api/tabla/'+name);
  if(data.error){ct.innerHTML='<div class="er">'+data.error+'</div>';return;}
  let h='<h3 style="margin:12px 0 8px">'+esc(name)+' <small style="color:var(--tx2)">'+data.records.length+' registros, '+data.fields.length+' campos</small></h3>';
  h+='<div class="tw"><div class="tb"><input placeholder="Filtrar..." oninput="fltRef(this.value)"><span class="nf" id="refNf">'+data.records.length+' registros</span></div>';
  h+='<div id="refTblC"></div></div>';
  ct.innerHTML=h;
  S._refData=data;
  renderRefTbl(data.records);
}

function fltRef(t){
  const f=t.toLowerCase();
  const d=f?S._refData.records.filter(r=>JSON.stringify(r).toLowerCase().includes(f)):S._refData.records;
  document.getElementById('refNf').textContent=d.length+' de '+S._refData.records.length;
  renderRefTbl(d);
}

function renderRefTbl(records){
  const data=S._refData;
  let h='<table><thead><tr>';
  for(const f of data.fields) h+='<th>'+f.name+'</th>';
  h+='</tr></thead><tbody>';
  for(const r of records.slice(0,300)){
    h+='<tr>';
    for(const f of data.fields){
      const v=r[f.name];
      if(v===null||v==='') h+='<td class="e">-</td>';
      else if(f.type==='N') h+='<td class="n">'+v+'</td>';
      else if(f.type==='D') h+='<td class="d">'+v+'</td>';
      else h+='<td title="'+esc(String(v))+'">'+esc(trn(String(v),40))+'</td>';
    }
    h+='</tr>';
  }
  h+='</tbody></table>';
  document.getElementById('refTblC').innerHTML=h;
}

// ── Shared helpers ──
function fltTbl(t){S.ft=t;S.pg=0;
  if(S.tab==='empleados')renderEmpTbl();
  else if(S.tab==='liquidaciones')renderLiqTbl();
}
function chPg(d){S.pg+=d;
  if(S.tab==='empleados')renderEmpTbl();
  else if(S.tab==='liquidaciones')renderLiqTbl();
}
function pgn(tp){
  return '<div class="pg"><button onclick="chPg(-1)"'+(S.pg===0?' disabled':'')+'>Anterior</button>'
    +'<span class="pi">Pag '+(S.pg+1)+' de '+tp+'</span>'
    +'<button onclick="chPg(1)"'+(S.pg>=tp-1?' disabled':'')+'>Siguiente</button></div>';
}
function esc(s){return s?s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'):'';}
function trn(s,n){return s&&s.length>n?s.substring(0,n)+'...':s||'';}
function fmtN(v){if(v===null||v===undefined)return'-';const n=Number(v);return isNaN(n)?String(v):n.toLocaleString('es-UY',{minimumFractionDigits:0,maximumFractionDigits:2});}
function cd(l,v,s){return '<div class="cd"><div class="lb">'+l+'</div><div class="vl">'+v+'</div><div class="su">'+s+'</div></div>';}

function toggleLiq(id){
  const el=document.getElementById(id);
  const arr=document.getElementById('arr_'+id);
  if(el.style.display==='none'){el.style.display='block';arr.innerHTML='&#9660;';}
  else{el.style.display='none';arr.innerHTML='&#9654;';}
}

function toggleSb(){
  document.getElementById('sb').classList.toggle('open');
  document.getElementById('sbOverlay').classList.toggle('open');
}
function closeSb(){
  document.getElementById('sb').classList.remove('open');
  document.getElementById('sbOverlay').classList.remove('open');
}

async function reloadCache(){
  await fetch('/api/reload-cache',{method:'POST'});
  S={v:'dash',empresas:[],dirs:[],lk:{},cur:null,tab:null,sc:null,sa:true,ft:'',pg:0,_d:null};
  await init();
}

init();
</script>
</body>
</html>
"""

if __name__ == '__main__':
    print("\n  SILVANA - Sistema de Sueldos")
    print("  http://localhost:5001\n")
    app.run(host='0.0.0.0', port=5001, debug=False)
