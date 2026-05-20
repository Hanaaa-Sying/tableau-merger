"""
合并 5 个 .twbx 为一个工作簿，仪表板为 Chart 2 留占位区域。
修复：manifest 合并、dashboard zone type、devicelayouts 结构。
运行: python merge_twbx.py
"""
import zipfile, os, re, uuid

OUTPUT_NAME = '超市客户质量分析_仪表板'

# ── 文件 → 工作表重命名 ────────────────────────────────────────
CONFIG = [
    ('图1-地图.twbx',                {'工作表 1': '地图'}),
    ('地区销售与利润对比条形图.twbx',   {'地区销售与利润对比条形图': '区域对比'}),
    ('图3-树地图(2).twbx',            {'工作表 2': '树地图'}),
    ('子类别利润排名及折扣情况.twbx',   {'工作表 1': '利润排名'}),
    ('客户价值(2).twbx',              {'工作表 1': '客户价值', '工作表 2': '客户价值2', '工作表 3': '客户价值3'}),
    ('购买规律分析.twbx',              {'图表六': '购买规律'}),
]


# ── 工具函数 ───────────────────────────────────────────────────

def load_twbx(path):
    with zipfile.ZipFile(path, 'r') as z:
        names = z.namelist()
        twb = [n for n in names if n.endswith('.twb')][0]
        content = z.read(twb)
        extras = {n: z.read(n) for n in names if not n.endswith('.twb')}
    return content.decode('utf-8'), extras


def apply_renames(text, rename_map):
    for old, new in rename_map.items():
        text = text.replace(f"name='{old}'", f"name='{new}'")
        text = text.replace(f'name="{old}"', f'name="{new}"')
    return text


def extract_block(text, tag, match_attr=None, start=0):
    """提取匹配的 XML 块（保持原始文本，不经过解析器）"""
    open_tag = f'<{tag}'
    close_tag = f'</{tag}>'
    pos = start
    while True:
        idx = text.find(open_tag, pos)
        if idx == -1:
            return None, -1
        # 确保是完整 tag 名（防止 datasource-dependencies 匹配 datasource）
        nxt = text[idx + len(open_tag): idx + len(open_tag) + 1]
        if nxt not in (' ', '>', '/', '\n', '\r', '\t'):
            pos = idx + 1
            continue
        tag_end = text.find('>', idx)
        if tag_end == -1:
            return None, -1
        start_tag = text[idx:tag_end + 1]
        if match_attr and match_attr not in start_tag:
            pos = idx + 1
            continue
        # 自闭合？
        if start_tag.rstrip().endswith('/>'):
            return text[idx:tag_end + 1], tag_end + 1
        # 按深度找闭合标签
        depth = 1
        scan = tag_end + 1
        while depth > 0:
            # 下一个同名开标签
            n_open = -1
            s = scan
            while True:
                c = text.find(open_tag, s)
                if c == -1:
                    break
                ca = text[c + len(open_tag): c + len(open_tag) + 1]
                if ca in (' ', '>', '/', '\n', '\r', '\t'):
                    n_open = c
                    break
                s = c + 1
            n_close = text.find(close_tag, scan)
            if n_close == -1:
                return None, -1
            if n_open != -1 and n_open < n_close:
                inner_end = text.find('>', n_open)
                if not text[n_open:inner_end + 1].rstrip().endswith('/>'):
                    depth += 1
                scan = inner_end + 1
            else:
                depth -= 1
                if depth == 0:
                    end = n_close + len(close_tag)
                    return text[idx:end], end
                scan = n_close + len(close_tag)


def extract_all_blocks(text, tag):
    blocks, pos = [], 0
    while True:
        block, end = extract_block(text, tag, start=pos)
        if block is None:
            break
        blocks.append(block)
        pos = end
    return blocks


def get_manifest_tags(text):
    ms = text.find('<document-format-change-manifest')
    if ms == -1:
        return set()
    ms_start = text.find('>', ms) + 1
    me = text.find('</document-format-change-manifest>', ms)
    if me == -1:
        return set()
    return set(re.findall(r'<([\w.]+)\s*/>', text[ms_start:me]))


def remove_block(text, tag):
    block, _ = extract_block(text, tag)
    if block:
        text = text.replace(block, '', 1)
    return text


# ── 仪表板 XML ─────────────────────────────────────────────────

def build_dashboard_xml():
    """
    8 图布局（全 6 文件 + 客户价值 3 张）：
      行1 (h=33000): 地图 50% | 区域对比 50%           ← WHO
      行2 (h=34000): 树地图 34% | 利润排名 33% | 购买规律 33%  ← WHAT
      行3 (h=33000): 客户价值 34% | 客户价值2 33% | 客户价值3 33%  ← WORTH
    """
    dash_uuid  = '{' + str(uuid.uuid4()).upper() + '}'
    phone_uuid = '{' + str(uuid.uuid4()).upper() + '}'

    return f"""  <dashboard name="超市客户质量分析">
    <style />
    <size maxheight="900" maxwidth="1400" minheight="600" minwidth="800" />
    <datasources />
    <zones>
      <zone h="100000" id="1" param="vert" type="layout-flow" w="100000" x="0" y="0">
        <zone h="33000" id="2" param="horz" type="layout-flow" w="100000" x="0" y="0">
          <zone h="33000" id="3" name="地图"   w="50000" x="0"     y="0" />
          <zone h="33000" id="4" name="区域对比" w="50000" x="50000" y="0" />
        </zone>
        <zone h="34000" id="5" param="horz" type="layout-flow" w="100000" x="0" y="33000">
          <zone h="34000" id="6" name="树地图"  w="34000" x="0"     y="33000" />
          <zone h="34000" id="7" name="利润排名" w="33000" x="34000" y="33000" />
          <zone h="34000" id="8" name="购买规律" w="33000" x="67000" y="33000" />
        </zone>
        <zone h="33000" id="9" param="horz" type="layout-flow" w="100000" x="0" y="67000">
          <zone h="33000" id="10" name="客户价值"  w="34000" x="0"     y="67000" />
          <zone h="33000" id="11" name="客户价值2" w="33000" x="34000" y="67000" />
          <zone h="33000" id="12" name="客户价值3" w="33000" x="67000" y="67000" />
        </zone>
      </zone>
    </zones>
    <devicelayouts>
      <devicelayout name="Phone">
        <size maxheight="700" minheight="400" sizing-mode="vscroll" />
        <zones>
          <zone h="100000" id="13" param="vert" type="layout-flow" w="100000" x="0" y="0" />
        </zones>
      </devicelayout>
    </devicelayouts>
    <simple-id uuid="{dash_uuid}" />
  </dashboard>"""


# ── 主流程 ─────────────────────────────────────────────────────

all_extras = {}
workbook_texts = []

for twbx_path, rename in CONFIG:
    if not os.path.exists(twbx_path):
        print(f'[跳过] {twbx_path}')
        continue
    text, extras = load_twbx(twbx_path)
    all_extras.update(extras)
    text = apply_renames(text, rename)
    workbook_texts.append((twbx_path, text))
    print(f'[读取] {twbx_path}')

if not workbook_texts:
    print('未找到任何 .twbx 文件')
    exit(1)

_, base_text = workbook_texts[0]

# 获取 base datasource ID（所有工作表将统一指向这个）
import re as _re
base_ds_id = _re.search(r"name='(federated\.[^']+)'", base_text).group(1)
print(f'[基准 DS] {base_ds_id}')

# 1. 合并 manifest（取所有工作簿 feature flag 的并集）
base_tags = get_manifest_tags(base_text)
extras_to_add = []
for _, t in workbook_texts[1:]:
    for tag in get_manifest_tags(t):
        if tag not in base_tags:
            base_tags.add(tag)
            extras_to_add.append(f'    <{tag} />')
if extras_to_add:
    ins = base_text.find('</document-format-change-manifest>')
    if ins != -1:
        base_text = base_text[:ins] + '\n'.join(extras_to_add) + '\n' + base_text[ins:]

# 2. 合并 worksheets + window 条目（保留 windows 节，WindowsPersistSimpleIdentifiers 要求）
for path, text in workbook_texts[1:]:
    m = _re.search(r"name='(federated\.[^']+)'", text)
    if not m:
        print(f'[警告] {path}: 未找到 federated datasource id')
        continue
    other_ds_id = m.group(1)

    def redirect(s):
        s = s.replace(f"'{other_ds_id}'", f"'{base_ds_id}'")
        s = s.replace(f'"{other_ds_id}"', f'"{base_ds_id}"')
        s = s.replace(f'[{other_ds_id}]', f'[{base_ds_id}]')
        return s

    # 合并 worksheets
    wss = extract_all_blocks(text, 'worksheet')
    if not wss:
        print(f'[警告] {path}: 未找到 worksheets')
        continue
    ins = base_text.rfind('</worksheets>')
    base_text = (base_text[:ins] + '\n' +
                 '\n'.join(redirect(ws) for ws in wss) + '\n' +
                 base_text[ins:])

    # 合并对应的 window 条目到 base 的 windows 节
    wins = extract_all_blocks(text, 'window')
    if wins:
        ins_w = base_text.find('</windows>')
        if ins_w != -1:
            base_text = (base_text[:ins_w] + '\n' +
                         '\n'.join(redirect(w) for w in wins) + '\n' +
                         base_text[ins_w:])

# 3. 只移除 thumbnails，保留 windows
base_text = remove_block(base_text, 'thumbnails')

# 只保留 base 的 hyper 文件
base_hyper = [k for k in all_extras if k.endswith('.hyper') and
              _re.search(r'TableauTemp_1buj97l0tond4e112hdas0m6m5wn', k)]
base_extras = {k: v for k, v in all_extras.items()
               if k in (base_hyper or list(all_extras.keys())[:1])}

# 5. 添加仪表板
dash_xml = build_dashboard_xml()
# 找到 </dashboards> 或 <dashboards /> 或 </workbook>
# dashboards 必须在 windows 之前（workbook 内容模型顺序）
win_pos = base_text.find('<windows')
if win_pos == -1:
    win_pos = base_text.rfind('</workbook>')

db_block = '<dashboards>\n' + dash_xml + '\n</dashboards>\n'

# 先清理已有的 dashboards 节（避免重复）
for marker in ('<dashboards />', ):
    base_text = base_text.replace(marker, '')
old_db, _ = extract_block(base_text, 'dashboards')
if old_db:
    base_text = base_text.replace(old_db, '', 1)

# 插入到 windows 之前
win_pos = base_text.find('<windows')
if win_pos == -1:
    win_pos = base_text.rfind('</workbook>')
base_text = base_text[:win_pos] + db_block + base_text[win_pos:]

# 6. 打包（只含 base 的 hyper，避免多 extract 共存）
output = f'{OUTPUT_NAME}.twbx'
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zout:
    zout.writestr(f'{OUTPUT_NAME}.twb', base_text.encode('utf-8'))
    for name, data in base_extras.items():
        zout.writestr(name, data)

size_kb = os.path.getsize(output) // 1024
print(f'\n完成！{output}  ({size_kb} KB)')
print('工作表: 地图 / 区域对比 / 树地图 / 利润排名 / 客户价值×3 / 购买规律')
print('仪表板: 超市客户质量分析（3行×3列，共8图）')
