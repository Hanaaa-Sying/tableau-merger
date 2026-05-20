# Tableau .twbx 多文件合并技能

将多个 `.twbx` 文件合并为一个包含仪表板的 Tableau Public 工作簿。

用法：`/tableaumerger` 后描述你的文件列表和布局需求。

---

## 核心原理

`.twbx` 是 ZIP 压缩包，内含：
- `*.twb`：XML 格式的工作簿定义（工作表、数据源、仪表板）
- `*.hyper`：Tableau 数据提取文件（实际数据）

Tableau Public 不支持 GUI 跨工作簿复制粘贴，因此通过 Python 直接操作 ZIP + XML 文本来完成合并。

---

## 关键技术发现

### 1. Workbook XML 元素顺序（严格，顺序错误直接报错）

```
document-format-change-manifest
preferences
datasources
worksheets
dashboards        ← 必须在 windows 之前
windows           ← 必须保留，不可删除
thumbnails
```

### 2. `<windows>` 节点不可删除

`WindowsPersistSimpleIdentifiers` manifest flag 要求每个 worksheet 都有对应的 `<window>` 条目。删除 `<windows>` 会触发 501CF476 崩溃。合并时需把每个源工作簿的 `<window>` 条目一并合并进来。

### 3. 单一共享数据源（同数据集时）

所有工作簿使用同一份数据（如 Superstore）时，字段 schema 相同，可将所有 worksheet 的 datasource 引用全部重定向到 base 工作簿的 federated ID，只保留一个 `.hyper` 文件，避免多 extract 冲突（501CF476）。

识别 federated datasource ID 的正则：`name='(federated\.[^']+)'`

**注意**：不能用 `inline='true'` 匹配，因为 Parameters datasource 也有该属性。

### 4. 仪表板 Zone XML 规则

```xml
<!-- 布局容器：需要 type 和 param -->
<zone type="layout-flow" param="vert" ...>

<!-- 工作表 zone：只需 name，不要加 type='worksheet' -->
<zone name="工作表名称" ... />
```

`type='worksheet'` 不在 Tableau 2026.1 枚举中，会触发 D2E8DA72 错误。

### 5. Dashboard XML 必需结构

```xml
<dashboard name="...">
  <style />
  <size maxheight="900" maxwidth="1400" minheight="600" minwidth="800" />
  <datasources />
  <zones>
    <!-- zone 树 -->
  </zones>
  <devicelayouts>
    <devicelayout name="Phone">          <!-- 必须有子元素，不能为空 -->
      <size ... sizing-mode="vscroll" />
      <zones>
        <zone ... type="layout-flow" />
      </zones>
    </devicelayout>
  </devicelayouts>
  <simple-id uuid="{UUID}" />            <!-- 在 dashboard 内，不在 devicelayout 内 -->
</dashboard>
```

### 6. document-format-change-manifest 取并集

合并时需将所有源工作簿的 manifest feature flag（如 `shelf-sorts`）取并集写入 base 工作簿，否则使用了高版本特性的工作表会报 D2E8DA72。

---

## 完整脚本模板

```python
"""
合并多个 .twbx 为一个包含仪表板的工作簿。
运行: python merge_twbx.py
"""
import zipfile, os, re, uuid

OUTPUT_NAME = '合并工作簿'

# 配置：文件路径 → {原工作表名: 新名称}
CONFIG = [
    ('文件1.twbx', {'工作表 1': '图表1'}),
    ('文件2.twbx', {'工作表 1': '图表2'}),
    # ...
]


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
    """提取匹配的 XML 块（文本操作，不经过解析器）"""
    open_tag = f'<{tag}'
    close_tag = f'</{tag}>'
    pos = start
    while True:
        idx = text.find(open_tag, pos)
        if idx == -1:
            return None, -1
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
        if start_tag.rstrip().endswith('/>'):
            return text[idx:tag_end + 1], tag_end + 1
        depth = 1
        scan = tag_end + 1
        while depth > 0:
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


def build_dashboard_xml(name, zones_xml):
    """
    zones_xml 示例（3行2列布局）：
      <zone h="100000" id="1" param="vert" type="layout-flow" w="100000" x="0" y="0">
        <zone h="50000" id="2" param="horz" type="layout-flow" ...>
          <zone h="50000" id="3" name="图表1" w="50000" x="0" y="0" />
          <zone h="50000" id="4" name="图表2" w="50000" x="50000" y="0" />
        </zone>
        ...
      </zone>
    """
    dash_uuid = '{' + str(uuid.uuid4()).upper() + '}'
    return f"""  <dashboard name="{name}">
    <style />
    <size maxheight="900" maxwidth="1400" minheight="600" minwidth="800" />
    <datasources />
    <zones>
{zones_xml}
    </zones>
    <devicelayouts>
      <devicelayout name="Phone">
        <size maxheight="700" minheight="400" sizing-mode="vscroll" />
        <zones>
          <zone h="100000" id="99" param="vert" type="layout-flow" w="100000" x="0" y="0" />
        </zones>
      </devicelayout>
    </devicelayouts>
    <simple-id uuid="{dash_uuid}" />
  </dashboard>"""


# ── 主流程 ────────────────────────────────────────────────────────

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
base_ds_id = re.search(r"name='(federated\.[^']+)'", base_text).group(1)
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

# 2. 合并 worksheets + window 条目
for path, text in workbook_texts[1:]:
    m = re.search(r"name='(federated\.[^']+)'", text)
    if not m:
        print(f'[警告] {path}: 未找到 federated datasource id')
        continue
    other_ds_id = m.group(1)

    def redirect(s):
        s = s.replace(f"'{other_ds_id}'", f"'{base_ds_id}'")
        s = s.replace(f'"{other_ds_id}"', f'"{base_ds_id}"')
        s = s.replace(f'[{other_ds_id}]', f'[{base_ds_id}]')
        return s

    wss = extract_all_blocks(text, 'worksheet')
    if not wss:
        print(f'[警告] {path}: 未找到 worksheets')
        continue
    ins = base_text.rfind('</worksheets>')
    base_text = (base_text[:ins] + '\n' +
                 '\n'.join(redirect(ws) for ws in wss) + '\n' +
                 base_text[ins:])

    wins = extract_all_blocks(text, 'window')
    if wins:
        ins_w = base_text.find('</windows>')
        if ins_w != -1:
            base_text = (base_text[:ins_w] + '\n' +
                         '\n'.join(redirect(w) for w in wins) + '\n' +
                         base_text[ins_w:])

# 3. 移除 thumbnails
base_text = remove_block(base_text, 'thumbnails')

# 4. 只保留 base 的 hyper 文件
base_extras = dict(list(all_extras.items())[:1])

# 5. 插入仪表板（必须在 <windows> 之前）
zones_xml = """      <zone h="100000" id="1" param="vert" type="layout-flow" w="100000" x="0" y="0">
        <!-- 在此定义 zone 树，参考下方布局说明 -->
      </zone>"""
dash_xml = build_dashboard_xml('仪表板', zones_xml)
db_block = '<dashboards>\n' + dash_xml + '\n</dashboards>\n'

for marker in ('<dashboards />', ):
    base_text = base_text.replace(marker, '')
old_db, _ = extract_block(base_text, 'dashboards')
if old_db:
    base_text = base_text.replace(old_db, '', 1)

win_pos = base_text.find('<windows')
if win_pos == -1:
    win_pos = base_text.rfind('</workbook>')
base_text = base_text[:win_pos] + db_block + base_text[win_pos:]

# 6. 打包
output = f'{OUTPUT_NAME}.twbx'
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zout:
    zout.writestr(f'{OUTPUT_NAME}.twb', base_text.encode('utf-8'))
    for name, data in base_extras.items():
        zout.writestr(name, data)

print(f'\n完成！{output}  ({os.path.getsize(output) // 1024} KB)')
```

---

## 仪表板布局示例（zones_xml）

### 2 行 × 3 列（共 6 图）

```xml
<zone h="100000" id="1" param="vert" type="layout-flow" w="100000" x="0" y="0">
  <zone h="50000" id="2" param="horz" type="layout-flow" w="100000" x="0" y="0">
    <zone h="50000" id="3" name="图1" w="34000" x="0"     y="0" />
    <zone h="50000" id="4" name="图2" w="33000" x="34000" y="0" />
    <zone h="50000" id="5" name="图3" w="33000" x="67000" y="0" />
  </zone>
  <zone h="50000" id="6" param="horz" type="layout-flow" w="100000" x="0" y="50000">
    <zone h="50000" id="7" name="图4" w="34000" x="0"     y="50000" />
    <zone h="50000" id="8" name="图5" w="33000" x="34000" y="50000" />
    <zone h="50000" id="9" name="图6" w="33000" x="67000" y="50000" />
  </zone>
</zone>
```

### 3 行（本项目实际布局，8 图）

```xml
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
```

---

## 常见错误速查

| 错误码 | 原因 | 修复 |
|---|---|---|
| D2E8DA72 (element not allowed) | XML 元素顺序错误，或 `type='worksheet'` | 检查 workbook 元素顺序；worksheet zone 不加 type |
| D2E8DA72 (shelf-sorts) | manifest 缺少其他工作簿的 feature flag | 取所有工作簿 manifest tags 的并集 |
| D2E8DA72 (devicelayouts) | `<devicelayout>` 内容为空 | 必须包含 `<size>` 和 `<zones>` 子元素 |
| 501CF476 (内部错误) | `<windows>` 被删除，或多个 `.hyper` 冲突 | 保留 windows 节点并合并 window 条目；只保留一个 hyper |
| 501CF476 (datasource) | 用 `inline='true'` 匹配到 Parameters 数据源 | 改用 `name='federated.'` 匹配主数据源 |

---

## 适用前提

- 所有 `.twbx` 基于**同一份数据**（字段 schema 相同）
- Tableau Public 桌面版（无法使用 REST API / TabPy）
- Python 3.x，仅用标准库

当用户有不同数据源的 `.twbx` 合并需求时，需要保留各自的 datasource 节点和 hyper 文件，并在仪表板 zone 中确保工作表连接正确的数据源，逻辑更复杂，需单独处理。
