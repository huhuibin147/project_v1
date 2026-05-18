"""
游戏数值修改器 - 独立测试工具
用法: python cheat_tool.py
访问: http://localhost:8888
删除此文件即可完全移除，不影响原有系统
"""

import json
import shutil
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from datetime import datetime

PORT = 8888
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
CONFIG_DIR = ROOT_DIR / "config"
SAVE_SLOTS = 3

ITEMS_DB = {}
SKILLS_DB = {}


def save_path(slot: int) -> Path:
    return DATA_DIR / f"save_{slot}" / "player.json"


def backup_path(slot: int) -> Path:
    return DATA_DIR / f"save_{slot}" / "player.json.bak"


def load_player(slot: int) -> dict | None:
    path = save_path(slot)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_player(slot: int, data: dict) -> bool:
    path = save_path(slot)
    if not path.exists():
        return False
    bak = backup_path(slot)
    shutil.copy2(path, bak)
    data["save_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return True


def list_saves() -> list:
    saves = []
    for slot in range(1, SAVE_SLOTS + 1):
        path = save_path(slot)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                saves.append({
                    "slot": slot,
                    "name": data.get("name", "未知"),
                    "class_id": data.get("class_id", ""),
                    "level": data.get("level", 1),
                    "save_time": data.get("save_time", ""),
                    "exists": True,
                })
            except Exception:
                saves.append({"slot": slot, "exists": False})
        else:
            saves.append({"slot": slot, "exists": False})
    return saves


def load_config_db():
    global ITEMS_DB, SKILLS_DB
    items_path = CONFIG_DIR / "items.json"
    if items_path.exists():
        with open(items_path, "r", encoding="utf-8") as f:
            ITEMS_DB = json.load(f)
    skills_path = CONFIG_DIR / "skills.json"
    if skills_path.exists():
        with open(skills_path, "r", encoding="utf-8") as f:
            SKILLS_DB = json.load(f)


def items_list() -> list:
    result = []
    for item_id, info in ITEMS_DB.items():
        result.append({
            "id": item_id,
            "name": info.get("name", item_id),
            "type": info.get("type", "unknown"),
            "equip_slot": info.get("equip_slot"),
            "description": info.get("description", ""),
        })
    return result


def skills_list() -> list:
    result = []
    for skill_id, info in SKILLS_DB.items():
        result.append({
            "id": skill_id,
            "name": info.get("name", skill_id),
            "class_requirement": info.get("class_requirement", []),
            "level_requirement": info.get("level_requirement", 1),
            "description": info.get("description", ""),
            "type": info.get("type", ""),
            "mp_cost": info.get("mp_cost", 0),
        })
    return result


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>游戏数值修改器</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    background: #1a1a2e; color: #e0e0e0;
    min-height: 100vh; padding: 20px;
}
.container { max-width: 960px; margin: 0 auto; }
h1 {
    text-align: center; color: #e94560; font-size: 28px;
    margin-bottom: 8px; text-shadow: 0 0 10px rgba(233,69,96,0.5);
}
.subtitle { text-align: center; color: #888; font-size: 13px; margin-bottom: 20px; }
.slot-bar {
    display: flex; gap: 10px; justify-content: center; margin-bottom: 20px;
}
.slot-btn {
    padding: 10px 28px; border: 2px solid #0f3460; border-radius: 8px;
    background: #16213e; color: #e0e0e0; cursor: pointer; font-size: 15px;
    transition: all 0.2s;
}
.slot-btn:hover { border-color: #e94560; background: #1a1a3e; }
.slot-btn.active { border-color: #e94560; background: #e94560; color: #fff; }
.slot-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.panel {
    background: #16213e; border-radius: 12px; padding: 20px;
    margin-bottom: 16px; border: 1px solid #0f3460;
}
.panel-title {
    color: #e94560; font-size: 16px; font-weight: bold;
    margin-bottom: 14px; padding-bottom: 8px;
    border-bottom: 1px solid #0f3460;
}
.row {
    display: flex; align-items: center; margin-bottom: 10px; gap: 10px;
}
.row label {
    min-width: 90px; color: #aaa; font-size: 14px; text-align: right;
}
.row input[type="number"], .row input[type="text"] {
    flex: 1; max-width: 200px; padding: 6px 10px; border-radius: 6px;
    border: 1px solid #0f3460; background: #1a1a2e; color: #e0e0e0;
    font-size: 14px; outline: none;
}
.row input:focus { border-color: #e94560; }
select, .sel {
    flex: 1; max-width: 260px; padding: 6px 10px; border-radius: 6px;
    border: 1px solid #0f3460; background: #1a1a2e; color: #e0e0e0;
    font-size: 14px; outline: none; cursor: pointer;
}
select:focus { border-color: #e94560; }
select option { background: #16213e; color: #e0e0e0; }
select optgroup { background: #0f3460; color: #53d8fb; font-style: normal; }
.quick-btns { display: flex; gap: 6px; flex-wrap: wrap; }
.qbtn {
    padding: 4px 12px; border-radius: 5px; border: 1px solid #0f3460;
    background: #1a1a2e; color: #53d8fb; cursor: pointer; font-size: 12px;
    transition: all 0.15s;
}
.qbtn:hover { border-color: #53d8fb; background: #0f3460; }
.qbtn.danger { color: #e94560; }
.qbtn.danger:hover { border-color: #e94560; background: #2a1a2e; }
.save-bar {
    display: flex; gap: 10px; justify-content: center; margin-top: 20px;
}
.save-btn {
    padding: 10px 36px; border-radius: 8px; border: none;
    font-size: 16px; cursor: pointer; transition: all 0.2s;
}
.save-btn.primary { background: #e94560; color: #fff; }
.save-btn.primary:hover { background: #c73852; }
.save-btn.secondary { background: #0f3460; color: #e0e0e0; }
.save-btn.secondary:hover { background: #1a4a7e; }
.inventory-table {
    width: 100%; border-collapse: collapse; font-size: 13px;
}
.inventory-table th {
    text-align: left; padding: 6px 10px; color: #53d8fb;
    border-bottom: 1px solid #0f3460; font-weight: normal;
}
.inventory-table td {
    padding: 5px 10px; border-bottom: 1px solid #111;
}
.inventory-table input {
    width: 70px; padding: 4px 6px; border-radius: 4px;
    border: 1px solid #0f3460; background: #1a1a2e; color: #e0e0e0;
    font-size: 13px; text-align: center;
}
.inventory-table .del-btn {
    color: #e94560; cursor: pointer; font-size: 13px;
    background: none; border: none; padding: 2px 8px;
}
.inventory-table .del-btn:hover { text-decoration: underline; }
.add-item-row { display: flex; gap: 8px; margin-top: 10px; align-items: center; flex-wrap: wrap; }
.add-item-row select { max-width: 260px; }
.add-item-row input[type="number"] {
    width: 70px; padding: 5px 8px; border-radius: 4px;
    border: 1px solid #0f3460; background: #1a1a2e; color: #e0e0e0;
    font-size: 13px; text-align: center;
}
.add-item-row button {
    padding: 5px 14px; border-radius: 4px; border: 1px solid #53d8fb;
    background: #0f3460; color: #53d8fb; cursor: pointer; font-size: 13px;
}
.add-item-row button:hover { background: #1a4a7e; }
.toast {
    position: fixed; top: 20px; right: 20px; padding: 12px 24px;
    border-radius: 8px; font-size: 14px; z-index: 9999;
    transition: opacity 0.3s; opacity: 0;
}
.toast.show { opacity: 1; }
.toast.success { background: #1b5e20; color: #a5d6a7; }
.toast.error { background: #b71c1c; color: #ef9a9a; }
.equip-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.equip-row label { min-width: 70px; color: #aaa; font-size: 14px; text-align: right; }
.equip-row select { max-width: 260px; }
.no-data { text-align: center; color: #666; padding: 40px; font-size: 15px; }
.skills-area {
    display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px;
}
.skill-tag {
    padding: 3px 10px; border-radius: 4px; background: #0f3460;
    color: #53d8fb; font-size: 12px; display: flex; align-items: center; gap: 4px;
}
.skill-tag .del { cursor: pointer; color: #e94560; font-weight: bold; }
.skill-tag .del:hover { text-decoration: underline; }
.add-skill-row { display: flex; gap: 8px; margin-top: 8px; align-items: center; }
.add-skill-row select { max-width: 260px; }
.add-skill-row button {
    padding: 5px 14px; border-radius: 4px; border: 1px solid #53d8fb;
    background: #0f3460; color: #53d8fb; cursor: pointer; font-size: 13px;
}
.add-skill-row button:hover { background: #1a4a7e; }
.raw-editor {
    width: 100%; min-height: 200px; padding: 10px; border-radius: 8px;
    border: 1px solid #0f3460; background: #1a1a2e; color: #e0e0e0;
    font-family: "Consolas", monospace; font-size: 13px; resize: vertical;
}
.raw-editor:focus { border-color: #e94560; outline: none; }
.item-name { color: #a5d6a7; }
.item-type { color: #888; font-size: 11px; margin-left: 4px; }
.skill-name { color: #ffcc80; }
.skill-req { color: #888; font-size: 11px; margin-left: 4px; }
</style>
</head>
<body>
<div class="container">
    <h1>🎮 游戏数值修改器</h1>
    <div class="subtitle">独立测试工具 · 直接修改存档文件 · 不影响游戏服务端内存</div>

    <div class="slot-bar" id="slotBar"></div>

    <div id="mainContent">
        <div class="no-data">请选择一个存档槽位</div>
    </div>
</div>

<div class="toast" id="toast"></div>

<script>
let currentSlot = null;
let playerData = null;
let modified = false;
let ITEMS = [];
let SKILLS = [];
let itemsById = {};
let skillsById = {};

const CLASS_MAP = { warrior: '战士', rogue: '盗贼', mage: '法师' };
const TYPE_MAP = { weapon: '武器', armor: '防具', consumable: '消耗品', food: '食物', material: '材料', tool: '工具', accessory: '饰品' };
const TYPE_ORDER = ['weapon', 'armor', 'accessory', 'consumable', 'food', 'material', 'tool'];
const MAP_MAP = { village: '村庄', forest: '森林', royal_city: '王城', dark_cave: '暗洞', desert_oasis: '沙漠绿洲' };

function toast(msg, type = 'success') {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = 'toast ' + type + ' show';
    setTimeout(() => el.className = 'toast', 2000);
}

async function api(path, method = 'GET', body = null) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(path, opts);
    return res.json();
}

async function loadConfigData() {
    const [itemsRes, skillsRes] = await Promise.all([
        api('/api/items'),
        api('/api/skills')
    ]);
    ITEMS = itemsRes.items || [];
    SKILLS = skillsRes.skills || [];
    itemsById = {};
    ITEMS.forEach(it => itemsById[it.id] = it);
    skillsById = {};
    SKILLS.forEach(sk => skillsById[sk.id] = sk);
}

async function loadSlots() {
    const data = await api('/api/saves');
    const bar = document.getElementById('slotBar');
    bar.innerHTML = '';
    data.saves.forEach(s => {
        const btn = document.createElement('button');
        btn.className = 'slot-btn' + (currentSlot === s.slot ? ' active' : '');
        btn.textContent = s.exists ? `存档${s.slot} - ${s.name} Lv.${s.level}` : `存档${s.slot} (空)`;
        btn.disabled = !s.exists;
        btn.onclick = () => selectSlot(s.slot);
        bar.appendChild(btn);
    });
}

async function selectSlot(slot) {
    currentSlot = slot;
    modified = false;
    await loadSlots();
    const data = await api(`/api/player/${slot}`);
    if (!data.success) { toast('加载失败', 'error'); return; }
    playerData = data.data;
    renderEditor();
}

function buildItemSelect(id, includeEmpty = true, filterType = null) {
    let html = `<select id="${id}" class="sel">`;
    if (includeEmpty) html += `<option value="">-- 选择物品 --</option>`;
    const grouped = {};
    ITEMS.forEach(it => {
        if (filterType && it.type !== filterType) return;
        const t = it.type || 'other';
        if (!grouped[t]) grouped[t] = [];
        grouped[t].push(it);
    });
    TYPE_ORDER.forEach(t => {
        if (!grouped[t]) return;
        html += `<optgroup label="${TYPE_MAP[t] || t}">`;
        grouped[t].sort((a, b) => a.name.localeCompare(b.name, 'zh'));
        grouped[t].forEach(it => {
            html += `<option value="${esc(it.id)}">${esc(it.name)}</option>`;
        });
        html += `</optgroup>`;
    });
    html += `</select>`;
    return html;
}

function buildEquipSelect(id, slotName, currentValue) {
    const slotTypeMap = { weapon: 'weapon', shield: 'armor', head: 'armor', body: 'armor', accessory: 'accessory' };
    const slotEquipMap = { weapon: 'weapon', shield: 'shield', head: 'head', body: 'body', accessory: 'accessory' };
    const equipSlot = slotEquipMap[slotName];
    let html = `<select id="${id}" class="sel" onchange="updateEquip('${slotName}', this.value)">`;
    html += `<option value="">(空)</option>`;
    const filtered = ITEMS.filter(it => it.equip_slot === equipSlot);
    filtered.sort((a, b) => a.name.localeCompare(b.name, 'zh'));
    filtered.forEach(it => {
        const sel = currentValue === it.id ? ' selected' : '';
        html += `<option value="${esc(it.id)}"${sel}>${esc(it.name)}</option>`;
    });
    html += `</select>`;
    return html;
}

function buildSkillSelect(id) {
    let html = `<select id="${id}" class="sel">`;
    html += `<option value="">-- 选择技能 --</option>`;
    const grouped = {};
    SKILLS.forEach(sk => {
        const classes = sk.class_requirement || [];
        const key = classes.length ? classes.join(',') : '通用';
        if (!grouped[key]) grouped[key] = { label: classes.map(c => CLASS_MAP[c] || c).join('/'), skills: [] };
        grouped[key].skills.push(sk);
    });
    Object.values(grouped).forEach(g => {
        html += `<optgroup label="${esc(g.label)}">`;
        g.skills.sort((a, b) => a.level_requirement - b.level_requirement);
        g.skills.forEach(sk => {
            html += `<option value="${esc(sk.id)}">${esc(sk.name)} (Lv.${sk.level_requirement})</option>`;
        });
        html += `</optgroup>`;
    });
    html += `</select>`;
    return html;
}

function renderItemName(itemId) {
    const info = itemsById[itemId];
    if (info) {
        return `<span class="item-name">${esc(info.name)}</span><span class="item-type">(${esc(info.id)})</span>`;
    }
    return `<span class="item-name">${esc(itemId)}</span>`;
}

function renderSkillName(skillId) {
    const info = skillsById[skillId];
    if (info) {
        return `<span class="skill-name">${esc(info.name)}</span>`;
    }
    return `<span class="skill-name">${esc(skillId)}</span>`;
}

function renderEditor() {
    if (!playerData) return;
    const p = playerData;
    const main = document.getElementById('mainContent');
    main.innerHTML = `
        <div class="panel">
            <div class="panel-title">📋 基本信息</div>
            <div class="row">
                <label>名称</label>
                <input type="text" id="f_name" value="${esc(p.name)}" onchange="markModified()">
            </div>
            <div class="row">
                <label>职业</label>
                <select id="f_class" class="sel" onchange="markModified()">
                    <option value="warrior" ${p.class_id==='warrior'?'selected':''}>战士</option>
                    <option value="rogue" ${p.class_id==='rogue'?'selected':''}>盗贼</option>
                    <option value="mage" ${p.class_id==='mage'?'selected':''}>法师</option>
                </select>
            </div>
            <div class="row">
                <label>等级</label>
                <input type="number" id="f_level" value="${p.level}" min="1" max="999" onchange="markModified()">
            </div>
            <div class="row">
                <label>经验值</label>
                <input type="number" id="f_exp" value="${p.exp}" min="0" onchange="markModified()">
            </div>
            <div class="row">
                <label>升级所需</label>
                <input type="number" id="f_exp_to_next" value="${p.exp_to_next}" min="1" onchange="markModified()">
            </div>
            <div class="row">
                <label>当前位置</label>
                <select id="f_map" class="sel" onchange="markModified()">
                    ${Object.entries(MAP_MAP).map(([k,v])=>`<option value="${k}" ${p.current_map===k?'selected':''}>${v}</option>`).join('')}
                </select>
            </div>
            <div class="row">
                <label>坐标 X</label>
                <input type="number" id="f_px" value="${p.player_x}" min="0" onchange="markModified()">
                <label>Y</label>
                <input type="number" id="f_py" value="${p.player_y}" min="0" onchange="markModified()">
            </div>
        </div>

        <div class="panel">
            <div class="panel-title">❤️ 生命与魔力</div>
            <div class="row">
                <label>HP</label>
                <input type="number" id="f_hp" value="${p.hp}" min="1" max="99999" onchange="markModified()">
                <span style="color:#666">/</span>
                <input type="number" id="f_max_hp" value="${p.max_hp}" min="1" max="99999" onchange="markModified()">
                <div class="quick-btns">
                    <button class="qbtn" onclick="setVal('f_hp',gid('f_max_hp').value)">HP满</button>
                </div>
            </div>
            <div class="row">
                <label>MP</label>
                <input type="number" id="f_mp" value="${p.mp}" min="0" max="99999" onchange="markModified()">
                <span style="color:#666">/</span>
                <input type="number" id="f_max_mp" value="${p.max_mp}" min="1" max="99999" onchange="markModified()">
                <div class="quick-btns">
                    <button class="qbtn" onclick="setVal('f_mp',gid('f_max_mp').value)">MP满</button>
                </div>
            </div>
        </div>

        <div class="panel">
            <div class="panel-title">⚔️ 战斗属性</div>
            <div class="row">
                <label>攻击力</label>
                <input type="number" id="f_attack" value="${p.attack}" min="1" max="99999" onchange="markModified()">
                <div class="quick-btns">
                    <button class="qbtn" onclick="multVal('f_attack',10)">x10</button>
                    <button class="qbtn" onclick="multVal('f_attack',100)">x100</button>
                    <button class="qbtn" onclick="setVal('f_attack',99999)">MAX</button>
                </div>
            </div>
            <div class="row">
                <label>防御力</label>
                <input type="number" id="f_defense" value="${p.defense}" min="1" max="99999" onchange="markModified()">
                <div class="quick-btns">
                    <button class="qbtn" onclick="multVal('f_defense',10)">x10</button>
                    <button class="qbtn" onclick="multVal('f_defense',100)">x100</button>
                    <button class="qbtn" onclick="setVal('f_defense',99999)">MAX</button>
                </div>
            </div>
            <div class="row">
                <label>速度</label>
                <input type="number" id="f_speed" value="${p.speed}" min="1" max="99999" onchange="markModified()">
                <div class="quick-btns">
                    <button class="qbtn" onclick="multVal('f_speed',10)">x10</button>
                    <button class="qbtn" onclick="setVal('f_speed',99999)">MAX</button>
                </div>
            </div>
        </div>

        <div class="panel">
            <div class="panel-title">💰 金币</div>
            <div class="row">
                <label>金币</label>
                <input type="number" id="f_gold" value="${p.gold}" min="0" max="999999999" onchange="markModified()">
                <div class="quick-btns">
                    <button class="qbtn" onclick="addVal('f_gold',1000)">+1K</button>
                    <button class="qbtn" onclick="addVal('f_gold',10000)">+1W</button>
                    <button class="qbtn" onclick="addVal('f_gold',100000)">+10W</button>
                    <button class="qbtn" onclick="setVal('f_gold',999999999)">MAX</button>
                    <button class="qbtn danger" onclick="setVal('f_gold',0)">清零</button>
                </div>
            </div>
        </div>

        <div class="panel">
            <div class="panel-title">🎒 背包物品</div>
            <table class="inventory-table">
                <thead><tr><th>物品</th><th>数量</th><th>操作</th></tr></thead>
                <tbody id="invBody"></tbody>
            </table>
            <div class="add-item-row">
                ${buildItemSelect('addItemSel')}
                <input type="number" id="addItemQty" placeholder="数量" value="1" min="1">
                <button onclick="addItem()">添加</button>
            </div>
        </div>

        <div class="panel">
            <div class="panel-title">🛡️ 装备</div>
            <div id="equipSlots"></div>
        </div>

        <div class="panel">
            <div class="panel-title">✨ 技能</div>
            <div class="skills-area" id="skillsArea"></div>
            <div class="add-skill-row">
                ${buildSkillSelect('addSkillSel')}
                <button onclick="addSkill()">添加技能</button>
            </div>
        </div>

        <div class="panel">
            <div class="panel-title">📝 原始JSON</div>
            <textarea class="raw-editor" id="rawJson" spellcheck="false"></textarea>
            <div style="margin-top:8px;display:flex;gap:8px">
                <button class="qbtn" onclick="loadRaw()">从编辑器加载</button>
                <button class="qbtn" onclick="formatRaw()">格式化</button>
            </div>
        </div>

        <div class="save-bar">
            <button class="save-btn primary" onclick="saveChanges()" id="saveBtn">💾 保存修改</button>
            <button class="save-btn secondary" onclick="selectSlot(currentSlot)">🔄 重新加载</button>
        </div>
    `;

    renderInventory();
    renderEquipment();
    renderSkills();
    updateRawJson();
}

function renderInventory() {
    const tbody = document.getElementById('invBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    (playerData.inventory || []).forEach((item, i) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${renderItemName(item.item_id)}</td>
            <td><input type="number" value="${item.quantity}" min="0" max="9999"
                onchange="updateInvQty(${i}, this.value)"></td>
            <td><button class="del-btn" onclick="removeInvItem(${i})">删除</button></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderEquipment() {
    const div = document.getElementById('equipSlots');
    if (!div) return;
    const slots = ['weapon', 'shield', 'head', 'body', 'accessory'];
    const names = { weapon: '武器', shield: '盾牌', head: '头部', body: '身体', accessory: '饰品' };
    div.innerHTML = '';
    slots.forEach(s => {
        const val = playerData.equipment ? playerData.equipment[s] : null;
        const row = document.createElement('div');
        row.className = 'equip-row';
        row.innerHTML = `
            <label>${names[s]}</label>
            ${buildEquipSelect('equip_' + s, s, val)}
        `;
        div.appendChild(row);
    });
}

function renderSkills() {
    const div = document.getElementById('skillsArea');
    if (!div) return;
    div.innerHTML = '';
    (playerData.skills || []).forEach((sk, i) => {
        const info = skillsById[sk];
        const tag = document.createElement('span');
        tag.className = 'skill-tag';
        const displayName = info ? `${info.name} (${sk})` : sk;
        tag.innerHTML = `${esc(displayName)} <span class="del" onclick="removeSkill(${i})">✕</span>`;
        div.appendChild(tag);
    });
}

function updateRawJson() {
    const ta = document.getElementById('rawJson');
    if (ta) ta.value = JSON.stringify(playerData, null, 2);
}

function gid(id) { return document.getElementById(id); }
function setVal(id, v) { gid(id).value = v; markModified(); }
function addVal(id, n) { gid(id).value = parseInt(gid(id).value || 0) + n; markModified(); }
function multVal(id, n) { gid(id).value = Math.min(99999, parseInt(gid(id).value || 0) * n); markModified(); }
function markModified() { modified = true; }

function updateInvQty(idx, val) {
    playerData.inventory[idx].quantity = parseInt(val) || 0;
    markModified(); updateRawJson();
}

function removeInvItem(idx) {
    playerData.inventory.splice(idx, 1);
    renderInventory(); markModified(); updateRawJson();
}

function addItem() {
    const sel = gid('addItemSel');
    const id = sel.value;
    const qty = parseInt(gid('addItemQty').value) || 1;
    if (!id) { toast('请选择物品', 'error'); return; }
    const existing = playerData.inventory.find(i => i.item_id === id);
    if (existing) { existing.quantity += qty; }
    else { playerData.inventory.push({ item_id: id, quantity: qty }); }
    sel.value = '';
    renderInventory(); markModified(); updateRawJson();
    const info = itemsById[id];
    toast('已添加 ' + (info ? info.name : id));
}

function updateEquip(slot, val) {
    if (!playerData.equipment) playerData.equipment = {};
    playerData.equipment[slot] = val || null;
    markModified(); updateRawJson();
}

function removeSkill(idx) {
    playerData.skills.splice(idx, 1);
    renderSkills(); markModified(); updateRawJson();
}

function addSkill() {
    const sel = gid('addSkillSel');
    const id = sel.value;
    if (!id) { toast('请选择技能', 'error'); return; }
    if (!playerData.skills) playerData.skills = [];
    if (playerData.skills.includes(id)) { toast('技能已存在', 'error'); return; }
    playerData.skills.push(id);
    sel.value = '';
    renderSkills(); markModified(); updateRawJson();
    const info = skillsById[id];
    toast('已添加技能 ' + (info ? info.name : id));
}

function loadRaw() {
    try {
        const data = JSON.parse(gid('rawJson').value);
        playerData = data;
        renderEditor();
        toast('已从JSON加载');
    } catch (e) {
        toast('JSON格式错误: ' + e.message, 'error');
    }
}

function formatRaw() {
    try {
        const data = JSON.parse(gid('rawJson').value);
        gid('rawJson').value = JSON.stringify(data, null, 2);
    } catch (e) {
        toast('JSON格式错误', 'error');
    }
}

function collectData() {
    return {
        name: gid('f_name').value,
        class_id: gid('f_class').value,
        level: parseInt(gid('f_level').value) || 1,
        exp: parseInt(gid('f_exp').value) || 0,
        exp_to_next: parseInt(gid('f_exp_to_next').value) || 100,
        hp: parseInt(gid('f_hp').value) || 1,
        max_hp: parseInt(gid('f_max_hp').value) || 1,
        mp: parseInt(gid('f_mp').value) || 0,
        max_mp: parseInt(gid('f_max_mp').value) || 1,
        attack: parseInt(gid('f_attack').value) || 1,
        defense: parseInt(gid('f_defense').value) || 1,
        speed: parseInt(gid('f_speed').value) || 1,
        gold: parseInt(gid('f_gold').value) || 0,
        player_x: parseInt(gid('f_px').value) || 0,
        player_y: parseInt(gid('f_py').value) || 0,
        current_map: gid('f_map').value,
        inventory: playerData.inventory,
        equipment: playerData.equipment,
        skills: playerData.skills,
        learned_skills: playerData.learned_skills || [],
        talents: playerData.talents || [],
        status_effects: playerData.status_effects || [],
        map_states: playerData.map_states || {},
        quests: playerData.quests || { active: {}, completed: [], daily_reset: "" },
    };
}

async function saveChanges() {
    if (!currentSlot) return;
    const data = collectData();
    const res = await api(`/api/player/${currentSlot}`, 'PUT', data);
    if (res.success) {
        toast('保存成功！');
        modified = false;
        await selectSlot(currentSlot);
    } else {
        toast('保存失败: ' + (res.error || ''), 'error');
    }
}

function esc(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

(async function init() {
    await loadConfigData();
    await loadSlots();
})();
</script>
</body>
</html>"""


class CheatHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        return {}

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            body = HTML_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        elif path == "/api/saves":
            self._send_json({"success": True, "saves": list_saves()})

        elif path == "/api/items":
            self._send_json({"success": True, "items": items_list()})

        elif path == "/api/skills":
            self._send_json({"success": True, "skills": skills_list()})

        elif path.startswith("/api/player/"):
            slot = int(path.split("/")[-1])
            data = load_player(slot)
            if data:
                self._send_json({"success": True, "data": data})
            else:
                self._send_json({"success": False, "error": "存档不存在"}, 404)

        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/player/"):
            slot = int(path.split("/")[-1])
            data = load_player(slot)
            if not data:
                self._send_json({"success": False, "error": "存档不存在"}, 404)
                return
            new_data = self._read_body()
            for key in new_data:
                data[key] = new_data[key]
            if save_player(slot, data):
                self._send_json({"success": True})
            else:
                self._send_json({"success": False, "error": "保存失败"}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/player/"):
            slot = int(path.split("/")[-1])
            data = load_player(slot)
            if not data:
                self._send_json({"success": False, "error": "存档不存在"}, 404)
                return
            new_data = self._read_body()
            for key in new_data:
                data[key] = new_data[key]
            if save_player(slot, data):
                self._send_json({"success": True})
            else:
                self._send_json({"success": False, "error": "保存失败"}, 500)
        else:
            self.send_response(404)
            self.end_headers()


def main():
    load_config_db()
    print("=" * 50)
    print("  🎮 游戏数值修改器")
    print(f"  访问地址: http://localhost:{PORT}")
    print(f"  已加载 {len(ITEMS_DB)} 个物品, {len(SKILLS_DB)} 个技能")
    print("  按 Ctrl+C 退出")
    print("=" * 50)
    server = HTTPServer(("0.0.0.0", PORT), CheatHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已退出")
        server.server_close()


if __name__ == "__main__":
    main()
