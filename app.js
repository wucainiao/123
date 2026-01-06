// 前端JavaScript for 修仙游戏

// 使用相对路径，避免 localhost vs 127.0.0.1 导致的 CORS 问题
const API_BASE = '';
let token = localStorage.getItem('token');

// 路由映射
const routes = {
    'login': { file: 'login.html', init: initLogin },
    'register': { file: 'register.html', init: initRegister },
    'create_character': { file: 'create_character.html', init: initCreateCharacter },
    'home': { file: 'home.html', init: initHome },
    'character': { file: 'character.html', init: initCharacter },
    'equipment': { file: 'equipment.html', init: initEquipment },
    'treasure': { file: 'treasure.html', init: initTreasure },
    'mantra': { file: 'mantra.html', init: initMantra },
    'shentong': { file: 'shentong.html', init: initShentong },
    'skills': { file: 'skills.html', init: initSkills },
    'pet': { file: 'pet.html', init: initPet },
    'sect': { file: 'sect.html', init: initSect },
    'rune': { file: 'rune.html', init: initRune },
    'pill': { file: 'pill.html', init: initPill },
    'lingzhi': { file: 'lingzhi.html', init: initLingzhi },
    'meridian': { file: 'meridian.html', init: initMeridian },
    'battle': { file: 'battle.html', init: initBattle }
};

// 初始路由
function getCurrentRoute() {
    const hash = window.location.hash.substring(1);
    return hash || (token ? 'home' : 'login');
}

// 加载页面
async function loadPage(route) {
    const routeData = routes[route];
    if (!routeData) return;

    const response = await fetch(routeData.file);
    const html = await response.text();
    document.getElementById('main-content').innerHTML = html;
    if (routeData.init) {
        routeData.init();
    }
}

// 初始化函数
function initLogin() {
    document.getElementById('login').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;

        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        if (response.ok) {
            token = data.token;
            localStorage.setItem('token', token);
            window.location.hash = 'home';
        } else {
            alert(data.message);
        }
    });
}

function initRegister() {
    document.getElementById('register').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('register-username').value;
        const password = document.getElementById('register-password').value;
        const email = document.getElementById('register-email').value;

        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, email })
        });
        const data = await response.json();
        alert(data.message);
        if (response.ok) {
            window.location.hash = 'login';
        }
    });
}

function initCreateCharacter() {
    document.getElementById('create-character-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('char-name').value;
        const linggen = document.querySelector('input[name="linggen"]:checked').value;
        const wuxing = parseInt(document.getElementById('char-wuxing').value) || 50;
        const qiyun = parseInt(document.getElementById('char-qiyun').value) || 50;

        const response = await apiCall('/character', {
            method: 'POST',
            body: JSON.stringify({ name, linggen, wuxing, qiyun })
        });
        const data = await response.json();
        if (response.ok) {
            alert('角色创建成功！开始你的修仙之旅吧！');
            window.location.hash = 'character';
        } else {
            alert(data.message || '创建角色失败');
        }
    });
}

function initHome() {
    // 检查是否有角色，如果没有则提示创建
    checkCharacterExists();
}

async function checkCharacterExists() {
    const response = await apiCall('/character');
    if (response.status === 404) {
        // 没有角色，显示创建提示
        const createBtn = document.createElement('div');
        createBtn.className = 'alert alert-warning mt-3';
        createBtn.innerHTML = `
            <h5>欢迎来到修仙世界！</h5>
            <p>你还没有创建角色，请先创建一个角色开始游戏。</p>
            <a href="#create_character" class="btn btn-primary">创建角色</a>
        `;
        const content = document.getElementById('game-content');
        if (content) {
            content.insertBefore(createBtn, content.firstChild);
        }
    }
}

function initCharacter() {
    showCharacter();
}

function initEquipment() {
    showEquipments();
    loadRunes();
}

let currentEquipmentId = null;

function initTreasure() {
    showTreasures();
}

function initMantra() {
    showMantras();
}

function initShentong() {
    showShentongs();
}

function initSkills() {
    showSkillSlots();
}

function initBattle() {
    // 暂无
}

// 路由事件监听
window.addEventListener('hashchange', () => {
    loadPage(getCurrentRoute());
});

// 初始加载
loadPage(getCurrentRoute());



async function apiCall(endpoint, options = {}) {
    return fetch(`${API_BASE}${endpoint}`, {
        headers: {
            'Authorization': token,
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    });
}

// 全局缓存当前法宝列表以供详情查看
let treasuresCache = [];

async function showCharacter() {
    const response = await apiCall('/character');
    const data = await response.json();
    if (response.ok) {
        // 基本信息
        document.getElementById('char-details').innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h5>基本信息</h5>
                    <table class="table table-sm">
                        <tr><td><strong>姓名:</strong></td><td>${data.name}</td></tr>
                        <tr><td><strong>灵根:</strong></td><td>${data.linggen || '无'}</td></tr>
                        <tr><td><strong>悟性:</strong></td><td>${data.wuxing || 0}</td></tr>
                        <tr><td><strong>气运:</strong></td><td>${data.qiyun || 0}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h5>修炼进度</h5>
                    <table class="table table-sm">
                        <tr><td><strong>等级:</strong></td><td>${data.level}</td></tr>
                        <tr><td><strong>境界:</strong></td><td>${data.realm}</td></tr>
                        <tr><td><strong>经验:</strong></td><td>${data.experience}/${data.max_experience || (500 * Math.pow(data.level || 1, 2) * Math.exp(0.05 * ((data.level || 1) - 1)))}</td></tr>
                    </table>
                    <div class="progress mb-2">
                        <div class="progress-bar" role="progressbar" style="width: ${(data.experience / (data.max_experience || 500)) * 100}%" aria-valuenow="${data.experience}" aria-valuemin="0" aria-valuemax="${data.max_experience || 500}"></div>
                    </div>
                </div>
            </div>
        `;

        // 属性面板
        document.getElementById('char-attributes').innerHTML = `
            <table class="table table-sm">
                <tr><td><strong>生命值:</strong></td><td>${data.attributes.hp}</td></tr>
                <tr><td><strong>攻击力:</strong></td><td>${data.attributes.attack}</td></tr>
                <tr><td><strong>防御力:</strong></td><td>${data.attributes.defense}</td></tr>
                <tr><td><strong>速度:</strong></td><td>${data.attributes.speed}</td></tr>
                <tr><td><strong>暴击率:</strong></td><td>${data.attributes.crit_rate || 0}%</td></tr>
            </table>
        `;

        // 境界信息
        const realms = ['凡人期', '筑基期', '金丹期', '元婴期', '化神期', '炼虚期', '合体期', '大乘期', '渡劫期', '大道境'];
        const currentRealmIndex = realms.indexOf(data.realm);
        document.getElementById('char-realm-info').innerHTML = `
            <p><strong>当前境界:</strong> ${data.realm}</p>
            <p><strong>境界等级:</strong> ${data.level}</p>
            <div class="progress mb-2">
                <div class="progress-bar bg-success" role="progressbar" style="width: ${(currentRealmIndex + 1) / realms.length * 100}%" aria-valuenow="${currentRealmIndex + 1}" aria-valuemin="0" aria-valuemax="${realms.length}"></div>
            </div>
            <small class="text-muted">
                下一境界: ${realms[Math.min(currentRealmIndex + 1, realms.length - 1)]}
            </small>
        `;
    } else {
        document.getElementById('char-details').innerHTML = `
            <div class="alert alert-danger">
                <strong>错误:</strong> ${data.message}
            </div>
        `;
        document.getElementById('char-attributes').innerHTML = '';
        document.getElementById('char-realm-info').innerHTML = '';
    }
}

async function levelup() {
    const response = await apiCall('/character/levelup', { method: 'POST' });
    const data = await response.json();
    alert(data.message);
    if (response.ok) showCharacter();
}

async function realmBreakthrough() {
    // 确认境界突破
    if (!confirm('境界突破需要消耗大量灵石，且有失败风险。确定要进行境界突破吗？')) {
        return;
    }

    // 获取纯度参数（可以后续扩展为从界面获取）
    const purity = 0.5; // 默认纯度，实际应该从丹药或界面获取

    const response = await apiCall('/character/realm_breakthrough', {
        method: 'POST',
        body: JSON.stringify({ purity: purity })
    });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n成功率: ${(data.success_rate * 100).toFixed(1)}%`);
        if (data.attribute_bonuses) {
            alert(`属性提升:\n生命值: +${data.attribute_bonuses.hp}\n攻击力: +${data.attribute_bonuses.attack}\n防御力: +${data.attribute_bonuses.defense}\n速度: +${data.attribute_bonuses.speed}`);
        }
    } else {
        alert(data.message);
    }

    showCharacter(); // 重新加载人物信息
}

// 装备相关函数
async function showEquipments() {
    const response = await apiCall('/equipment');
    const data = await response.json();
    if (response.ok) {
        const slotsContainer = document.getElementById('equipment-slots');
        slotsContainer.innerHTML = '';

        // 装备类型图标映射
        const typeIcons = {
            '武器': '⚔️',
            '头盔': '🪖',
            '项链': '📿',
            '衣服': '👕',
            '腰带': '🪢',
            '鞋子': '👢',
            '耳环': '💍',
            '戒指': '💍',
            '手镯': '🪬',
            '护符': '🧿'
        };

        // 品质颜色映射
        const qualityColors = {
            '黄阶': 'warning',
            '玄阶': 'secondary',
            '地阶': 'success',
            '天阶': 'primary'
        };

        data.forEach(equip => {
            const col = document.createElement('div');
            col.className = 'col-6 col-md-4 col-lg-3';

            const qualityColor = qualityColors[equip.quality] || 'secondary';
            const icon = typeIcons[equip.type] || '📦';

            col.innerHTML = `
                <div class="card h-100 equipment-card" onclick="showEquipmentDetail(${equip.id})" style="cursor: pointer;">
                    <div class="card-body text-center">
                        <div class="fs-2 mb-2">${icon}</div>
                        <h6 class="card-title">${equip.name}</h6>
                        <div class="badge bg-${qualityColor} mb-2">${equip.quality}</div>
                        <small class="text-muted d-block">等级 ${equip.level}/${equip.max_level}</small>
                        ${equip.strengthen_times > 0 ? `<small class="text-warning d-block">强化 +${equip.strengthen_times}</small>` : ''}
                    </div>
                </div>
            `;
            slotsContainer.appendChild(col);
        });
    } else {
        alert(data.message);
    }
}

// 全局变量存储装备数据
let equipmentsCache = [];

function showEquipmentDetail(equipId) {
    currentEquipmentId = equipId;
    const equip = equipmentsCache.find(e => e.id === equipId);
    if (equip) {
        document.getElementById('equipmentModalTitle').textContent = `${equip.name} - 详情`;
        document.getElementById('equipmentModalBody').innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>基本信息</h6>
                    <table class="table table-sm">
                        <tr><td>类型:</td><td>${equip.type}</td></tr>
                        <tr><td>品质:</td><td><span class="badge bg-${equip.quality === '黄阶' ? 'warning' : equip.quality === '玄阶' ? 'secondary' : equip.quality === '地阶' ? 'success' : 'primary'}">${equip.quality}</span></td></tr>
                        <tr><td>等级:</td><td>${equip.level}/${equip.max_level}</td></tr>
                        <tr><td>强化:</td><td>${equip.strengthen_times} 次</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>属性加成</h6>
                    <table class="table table-sm">
                        ${equip.attack_bonus ? `<tr><td>攻击:</td><td>+${equip.attack_bonus}</td></tr>` : ''}
                        ${equip.defense_bonus ? `<tr><td>防御:</td><td>+${equip.defense_bonus}</td></tr>` : ''}
                        ${equip.hp_bonus ? `<tr><td>生命:</td><td>+${equip.hp_bonus}</td></tr>` : ''}
                        ${equip.speed_bonus ? `<tr><td>速度:</td><td>+${equip.speed_bonus}</td></tr>` : ''}
                        ${equip.crit_rate_bonus ? `<tr><td>暴击率:</td><td>+${(equip.crit_rate_bonus * 100).toFixed(1)}%</td></tr>` : ''}
                        ${equip.dodge_rate_bonus ? `<tr><td>闪避率:</td><td>+${(equip.dodge_rate_bonus * 100).toFixed(1)}%</td></tr>` : ''}
                    </table>
                </div>
            </div>
        `;

        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('equipmentModal'));
        modal.show();
    }
}

// 更新showEquipments函数以缓存数据
async function showEquipments() {
    const response = await apiCall('/equipment');
    const data = await response.json();
    if (response.ok) {
        equipmentsCache = data; // 缓存装备数据
        const slotsContainer = document.getElementById('equipment-slots');
        slotsContainer.innerHTML = '';

        // 装备类型图标映射
        const typeIcons = {
            '武器': '⚔️',
            '头盔': '🪖',
            '项链': '📿',
            '衣服': '👕',
            '腰带': '🪢',
            '鞋子': '👢',
            '耳环': '💍',
            '戒指': '💍',
            '手镯': '🪬',
            '护符': '🧿'
        };

        // 品质颜色映射
        const qualityColors = {
            '黄阶': 'warning',
            '玄阶': 'secondary',
            '地阶': 'success',
            '天阶': 'primary'
        };

        data.forEach(equip => {
            const col = document.createElement('div');
            col.className = 'col-6 col-md-4 col-lg-3';

            const qualityColor = qualityColors[equip.quality] || 'secondary';
            const icon = typeIcons[equip.type] || '📦';

            col.innerHTML = `
                <div class="card h-100 equipment-card" onclick="showEquipmentDetail(${equip.id})" style="cursor: pointer;">
                    <div class="card-body text-center">
                        <div class="fs-2 mb-2">${icon}</div>
                        <h6 class="card-title">${equip.name}</h6>
                        <div class="badge bg-${qualityColor} mb-2">${equip.quality}</div>
                        <small class="text-muted d-block">等级 ${equip.level}/${equip.max_level}</small>
                        ${equip.strengthen_times > 0 ? `<small class="text-warning d-block">强化 +${equip.strengthen_times}</small>` : ''}
                    </div>
                </div>
            `;
            slotsContainer.appendChild(col);
        });
    } else {
        alert(data.message);
    }
}

async function upgradeEquipment() {
    if (!currentEquipmentId) return;

    const response = await apiCall(`/equipment/upgrade/${currentEquipmentId}`, { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n消耗经验: ${data.exp_cost}, 灵石: ${data.lingshi_cost}`);
        showEquipments(); // 重新加载装备列表
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('equipmentModal'));
        if (modal) modal.hide();
    } else {
        alert(data.message);
    }
}

async function strengthenEquipment() {
    if (!currentEquipmentId) return;

    const materialQuality = prompt('输入材料品质系数 (0.5-2.0，默认1.0):', '1.0');
    if (!materialQuality) return;

    const response = await apiCall(`/equipment/strengthen/${currentEquipmentId}`, {
        method: 'POST',
        body: JSON.stringify({ material_quality_factor: parseFloat(materialQuality) })
    });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n成功率: ${(data.success_rate * 100).toFixed(1)}%\n消耗灵石: ${data.cost}`);
        showEquipments(); // 重新加载装备列表
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('equipmentModal'));
        if (modal) modal.hide();
    } else {
        alert(data.message);
    }
}

async function loadRunes() {
    try {
        const response = await apiCall('/rune');
        const data = await response.json();
        if (response.ok && data.length > 0) {
            const runeListHtml = data.map(rune => `
                <div class="d-flex justify-content-between align-items-center mb-2 p-2 border rounded">
                    <div>
                        <strong>${rune.name}</strong> (${rune.quality})
                        <br><small class="text-muted">${rune.attribute_type}: +${rune.attribute_value}</small>
                    </div>
                    <div>
                        ${rune.equipped ? '<span class="badge bg-success">已装备</span>' : '<span class="badge bg-secondary">未装备</span>'}
                    </div>
                </div>
            `).join('');
            document.getElementById('rune-list').innerHTML = runeListHtml;
        } else {
            document.getElementById('rune-list').innerHTML = '<p class="text-muted">暂无符文数据</p>';
        }
    } catch (error) {
        console.error('Failed to load runes:', error);
        document.getElementById('rune-list').innerHTML = '<p class="text-danger">加载符文失败</p>';
    }
}

function showRuneForge() {
    const modal = new bootstrap.Modal(document.getElementById('runeForgeModal'));
    modal.show();
}

async function forgeRune() {
    const name = document.getElementById('runeName').value;
    const quality = document.getElementById('runeQuality').value;
    const attrType = document.getElementById('runeAttrType').value;
    const attrValue = parseInt(document.getElementById('runeAttrValue').value);
    const materialQuality = parseFloat(document.getElementById('runeMaterialQuality').value);

    if (!name.trim()) {
        alert('请输入符文名称');
        return;
    }

    const response = await apiCall('/rune/forge', {
        method: 'POST',
        body: JSON.stringify({
            name: name,
            quality: quality,
            attribute_type: attrType,
            attribute_value: attrValue,
            material_quality_factor: materialQuality
        })
    });

    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n符文ID: ${data.rune_id}\n成功率: ${(data.success_rate * 100).toFixed(1)}%`);
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('runeForgeModal'));
        if (modal) modal.hide();
        // 清空表单
        document.getElementById('runeForgeForm').reset();
    } else {
        alert(data.message);
    }
}

async function showTreasures() {
    const response = await apiCall('/treasure');
    const data = await response.json();
    if (response.ok) {
        treasuresCache = data || [];
        const ul = document.getElementById('treasure-ul');
        ul.innerHTML = data.map(t => `
            <li class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                    ${t.name} (品质: ${t.quality})
                </div>
                <div>
                    <button class="btn btn-sm btn-secondary me-2" onclick="promptEquipRuneToTreasure(${t.id})">镶嵌符文</button>
                    <button class="btn btn-sm btn-info me-2" onclick="openTreasureModal(${t.id})">详情</button>
                </div>
            </li>
        `).join('');
    } else {
        alert(data.message);
    }
}


function promptEquipRuneToEquipment(equipId) {
    const runeId = prompt('输入要镶嵌的符文ID');
    if (!runeId) return;
    equipRuneToEquipment(parseInt(runeId, 10), equipId);
}

async function equipRuneToEquipment(runeId, equipId) {
    const resp = await apiCall('/rune/equip/equipment', {
        method: 'POST',
        body: JSON.stringify({ rune_id: parseInt(runeId, 10), equip_id: parseInt(equipId, 10) })
    });
    const data = await resp.json();
    if (resp.ok) {
        alert(data.message);
        showEquipments();
    } else {
        alert(data.message);
    }
}

function promptEquipRuneToTreasure(treasureId) {
    const runeId = prompt('输入要镶嵌的符文ID');
    if (!runeId) return;
    equipRuneToTreasure(parseInt(runeId, 10), treasureId);
}

async function equipRuneToTreasure(runeId, treasureId) {
    const resp = await apiCall('/rune/equip/treasure', {
        method: 'POST',
        body: JSON.stringify({ rune_id: parseInt(runeId, 10), treasure_id: parseInt(treasureId, 10) })
    });
    const data = await resp.json();
    if (resp.ok) {
        alert(data.message);
        showTreasures();
    } else {
        alert(data.message);
    }
}

async function forgeTreasure() {
    const slot = prompt('输入槽位 (1-6)');
    const name = prompt('输入法宝名称');
    const material = prompt('材料品质系数（例如1.0-1.5），默认1.0', '1.0');
    if (slot && name) {
        const response = await apiCall('/treasure/forge', {
            method: 'POST',
            body: JSON.stringify({ slot: parseInt(slot), name, material_quality_factor: parseFloat(material || '1.0') })
        });
        const data = await response.json();
        alert(data.message + (data.treasure ? ('\n' + JSON.stringify(data.treasure)) : ''));
        if (response.ok) showTreasures();
    }
}

async function awakenTreasure(treasureId) {
    const material = parseFloat(document.getElementById('treasureMaterialInput').value || '1.0');
    const resp = await apiCall(`/treasure/awaken/${treasureId}`, {
        method: 'POST',
        body: JSON.stringify({ material_quality_factor: material })
    });
    const data = await resp.json();
    alert(data.message + (data.special_skill ? ('\n技能: ' + data.special_skill) : ''));
    if (resp.ok) {
        showTreasures();
        var modalEl = document.getElementById('treasureDetailModal');
        var bsModal = bootstrap.Modal.getInstance(modalEl);
        if (bsModal) bsModal.hide();
    }
}

async function recastTreasure(treasureId) {
    const material = parseFloat(document.getElementById('treasureMaterialInput').value || '1.0');
    const resp = await apiCall(`/treasure/recast/${treasureId}`, {
        method: 'POST',
        body: JSON.stringify({ material_quality_factor: material })
    });
    const data = await resp.json();
    alert(data.message + (data.new_stats ? ('\n新属性: ' + JSON.stringify(data.new_stats)) : ''));
    if (resp.ok) {
        showTreasures();
        var modalEl = document.getElementById('treasureDetailModal');
        var bsModal = bootstrap.Modal.getInstance(modalEl);
        if (bsModal) bsModal.hide();
    }
}

function openTreasureModal(treasureId) {
    const t = (treasuresCache || []).find(x => x.id === treasureId);
    if (!t) return alert('法宝未找到');
    document.getElementById('treasureDetailTitle').innerText = `${t.name} — 详情`;
    document.getElementById('treasureDetailBody').innerHTML = `
        <p><strong>品质:</strong> ${t.quality}</p>
        <p><strong>攻击:</strong> ${t.attack_bonus}</p>
        <p><strong>防御:</strong> ${t.defense_bonus}</p>
        <p><strong>生命:</strong> ${t.hp_bonus}</p>
        <p><strong>槽位:</strong> ${t.rune_slots || 1}</p>
    `;
    document.getElementById('treasureMaterialInput').value = '1.0';
    // 展示预计成功率/消耗信息占位
    document.getElementById('treasureEstimate').innerHTML = '<em>正在计算预计成功率与消耗……</em>';
    // 当材料系数变化时实时刷新估算
    const materialInput = document.getElementById('treasureMaterialInput');
    const onMaterialChange = async () => {
        const val = parseFloat(materialInput.value || '1.0');
        const resp = await apiCall('/treasure/estimate', { method: 'POST', body: JSON.stringify({ treasure_id: treasureId, material_quality_factor: val }) });
        const info = await resp.json();
        if (resp.ok) {
            document.getElementById('treasureEstimate').innerHTML = `
                <div><strong>觉醒成功率:</strong> ${Math.round(info.awaken_rate * 10000)/100}% &nbsp; <small>消耗灵石: ${info.awaken_cost}</small></div>
                <div><strong>重铸成功率:</strong> ${Math.round(info.recast_rate * 10000)/100}% &nbsp; <small>消耗灵石: ${info.recast_cost}</small></div>
            `;
        } else {
            document.getElementById('treasureEstimate').innerText = info.message || '无法估算';
        }
    };
    materialInput.removeEventListener('input', onMaterialChange);
    materialInput.addEventListener('input', onMaterialChange);
    // 触发一次初始估算
    onMaterialChange();
    // 绑定按钮行为
    const awakenBtn = document.getElementById('treasureAwakenBtn');
    const recastBtn = document.getElementById('treasureRecastBtn');
    awakenBtn.onclick = () => awakenTreasure(treasureId);
    recastBtn.onclick = () => {
        if (!confirm('重铸会重新随机法宝基础属性并消耗材料，确认继续？')) return;
        recastTreasure(treasureId);
    };
    var modalEl = document.getElementById('treasureDetailModal');
    var bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
}

async function showBattle() {
    // 简化战斗界面
    alert('战斗功能待实现');
}

// 功法相关函数
let mantrasCache = [];
let currentMantraId = null;

async function showMantras() {
    const response = await apiCall('/mantra');
    const data = await response.json();
    if (response.ok) {
        mantrasCache = data;
        const mantraList = document.getElementById('mantra-list');
        mantraList.innerHTML = '';

        // 品质颜色映射
        const qualityColors = {
            '黄阶': 'warning',
            '玄阶': 'secondary',
            '地阶': 'success',
            '天阶': 'primary'
        };

        data.forEach(mantra => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4 mb-3';

            const qualityColor = qualityColors[mantra.quality] || 'secondary';
            const equippedIcon = mantra.equipped ? '🔵' : '⚪';

            col.innerHTML = `
                <div class="card h-100" onclick="showMantraDetail(${mantra.id})" style="cursor: pointer;">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title">${mantra.name}</h6>
                            <span class="badge bg-${qualityColor}">${mantra.quality}</span>
                        </div>
                        <p class="card-text small">
                            等级: ${mantra.level}/${mantra.max_level}<br>
                            熟练度: ${mantra.proficiency} (${mantra.proficiency_exp}/${mantra.proficiency_max})<br>
                            装备状态: ${equippedIcon} ${mantra.equipped ? '已装备' : '未装备'}
                        </p>
                    </div>
                </div>
            `;
            mantraList.appendChild(col);
        });

        // 更新修炼模态框中的功法选择
        updateCultivateMantraSelect(data);
    } else {
        alert(data.message);
    }
}

function showMantraDetail(mantraId) {
    currentMantraId = mantraId;
    const mantra = mantrasCache.find(m => m.id === mantraId);
    if (mantra) {
        document.getElementById('mantraModalTitle').textContent = `${mantra.name} - 详情`;
        document.getElementById('mantraModalBody').innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>基本信息</h6>
                    <table class="table table-sm">
                        <tr><td>品质:</td><td><span class="badge bg-${mantra.quality === '黄阶' ? 'warning' : mantra.quality === '玄阶' ? 'secondary' : mantra.quality === '地阶' ? 'success' : 'primary'}">${mantra.quality}</span></td></tr>
                        <tr><td>等级:</td><td>${mantra.level}/${mantra.max_level}</td></tr>
                        <tr><td>经验:</td><td>${mantra.experience}</td></tr>
                        <tr><td>熟练度:</td><td>${mantra.proficiency} (${mantra.proficiency_exp}/${mantra.proficiency_max})</td></tr>
                        <tr><td>装备状态:</td><td>${mantra.equipped ? `已装备 (槽位 ${mantra.slot})` : '未装备'}</td></tr>
                        <tr><td>灵根要求:</td><td>${mantra.linggen_required || '无'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>属性加成</h6>
                    <table class="table table-sm">
                        ${mantra.attack_bonus ? `<tr><td>攻击:</td><td>+${mantra.attack_bonus}</td></tr>` : ''}
                        ${mantra.defense_bonus ? `<tr><td>防御:</td><td>+${mantra.defense_bonus}</td></tr>` : ''}
                        ${mantra.hp_bonus ? `<tr><td>生命:</td><td>+${mantra.hp_bonus}</td></tr>` : ''}
                        ${mantra.speed_bonus ? `<tr><td>速度:</td><td>+${mantra.speed_bonus}</td></tr>` : ''}
                        ${mantra.crit_rate_bonus ? `<tr><td>暴击率:</td><td>+${(mantra.crit_rate_bonus * 100).toFixed(1)}%</td></tr>` : ''}
                    </table>
                    ${mantra.special_effect ? `<div class="mt-2"><strong>特殊效果:</strong> ${mantra.special_effect}</div>` : ''}
                </div>
            </div>
        `;

        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('mantraModal'));
        modal.show();
    }
}

async function upgradeMantra() {
    if (!currentMantraId) return;

    // 获取天气系数（用户可以输入）
    const weatherBonus = parseFloat(prompt('输入天气系数 (1.0=晴天, 0.8=阴天, 1.2=雨天, 1.5=雷雨天):', '1.0')) || 1.0;

    const response = await apiCall(`/mantra/upgrade/${currentMantraId}`, {
        method: 'POST',
        body: JSON.stringify({ weather_bonus: weatherBonus })
    });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n悟性系数: ${data.wuxing_factor.toFixed(2)}, 天气系数: ${data.weather_bonus.toFixed(2)}`);
        showMantras(); // 重新加载功法列表
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('mantraModal'));
        if (modal) modal.hide();
    } else {
        alert(data.message);
    }
}

async function equipMantra() {
    if (!currentMantraId) return;

    const slot = parseInt(prompt('输入装备槽位 (0-5):', '0')) || 0;

    const response = await apiCall(`/mantra/equip/${currentMantraId}`, {
        method: 'POST',
        body: JSON.stringify({ slot: slot })
    });
    const data = await response.json();

    if (response.ok) {
        alert(data.message);
        showMantras(); // 重新加载功法列表
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('mantraModal'));
        if (modal) modal.hide();
    } else {
        alert(data.message);
    }
}

async function unequipMantra() {
    if (!currentMantraId) return;

    const response = await apiCall(`/mantra/unequip/${currentMantraId}`, { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        alert(data.message);
        showMantras(); // 重新加载功法列表
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('mantraModal'));
        if (modal) modal.hide();
    } else {
        alert(data.message);
    }
}

function showCultivateModal() {
    const modal = new bootstrap.Modal(document.getElementById('cultivateModal'));
    modal.show();
}

function updateCultivateMantraSelect(mantras) {
    const select = document.getElementById('cultivateMantraSelect');
    select.innerHTML = '<option value="">请选择功法</option>';
    mantras.forEach(mantra => {
        const option = document.createElement('option');
        option.value = mantra.id;
        option.textContent = `${mantra.name} (等级 ${mantra.level}, ${mantra.proficiency})`;
        select.appendChild(option);
    });
}

async function cultivateMantra() {
    const mantraId = document.getElementById('cultivateMantraSelect').value;
    const timeSpent = parseInt(document.getElementById('cultivateTime').value) || 1;
    const weatherBonus = parseFloat(document.getElementById('cultivateWeather').value) || 1.0;

    if (!mantraId) {
        alert('请选择要修炼的功法');
        return;
    }

    const response = await apiCall(`/mantra/cultivate/${mantraId}`, {
        method: 'POST',
        body: JSON.stringify({
            time_spent: timeSpent,
            weather_bonus: weatherBonus
        })
    });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n获得熟练度: ${data.exp_gained}\n当前熟练度: ${data.current_proficiency} (${data.proficiency_exp}/${data.proficiency_max})${data.level_up ? '\n恭喜！熟练度等级提升！' : ''}`);
        showMantras(); // 重新加载功法列表
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('cultivateModal'));
        if (modal) modal.hide();
    } else {
        alert(data.message);
    }
}

// 神通相关函数
let shentongsCache = [];
let currentShentongId = null;

async function showShentongs() {
    const response = await apiCall('/shentong');
    const data = await response.json();
    if (response.ok) {
        shentongsCache = data;
        const shentongList = document.getElementById('shentong-list');
        shentongList.innerHTML = '';

        data.forEach(shentong => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4 mb-3';

            const equippedIcon = shentong.equipped ? '🔵' : '⚪';
            const triggerRatePercent = (shentong.trigger_rate * 100).toFixed(1);

            col.innerHTML = `
                <div class="card h-100" onclick="showShentongDetail(${shentong.id})" style="cursor: pointer;">
                    <div class="card-body">
                        <h6 class="card-title">${shentong.name}</h6>
                        <p class="card-text small">
                            等级: ${shentong.level}/${shentong.max_level}<br>
                            熟练度: ${shentong.proficiency}/100<br>
                            触发概率: ${triggerRatePercent}%<br>
                            装备状态: ${equippedIcon} ${shentong.equipped ? '已装备' : '未装备'}
                        </p>
                    </div>
                </div>
            `;
            shentongList.appendChild(col);
        });

        // 更新修炼模态框中的神通选择
        updateTrainingShentongSelect(data);
    } else {
        alert(data.message);
    }
}

function showShentongDetail(shentongId) {
    currentShentongId = shentongId;
    const shentong = shentongsCache.find(s => s.id === shentongId);
    if (shentong) {
        document.getElementById('shentongModalTitle').textContent = `${shentong.name} - 详情`;
        document.getElementById('shentongModalBody').innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>基本信息</h6>
                    <table class="table table-sm">
                        <tr><td>等级:</td><td>${shentong.level}/${shentong.max_level}</td></tr>
                        <tr><td>经验:</td><td>${shentong.experience}</td></tr>
                        <tr><td>熟练度:</td><td>${shentong.proficiency}/100</td></tr>
                        <tr><td>触发概率:</td><td>${(shentong.trigger_rate * 100).toFixed(1)}%</td></tr>
                        <tr><td>装备状态:</td><td>${shentong.equipped ? `已装备 (槽位 ${shentong.slot})` : '未装备'}</td></tr>
                        <tr><td>冷却回合:</td><td>${shentong.cooldown}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>战斗信息</h6>
                    <table class="table table-sm">
                        <tr><td>伤害倍率:</td><td>${shentong.damage_multiplier.toFixed(2)}x</td></tr>
                    </table>
                    <div class="mt-2">
                        <strong>效果描述:</strong><br>
                        ${shentong.effect_description || '无描述'}
                    </div>
                </div>
            </div>
        `;

        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('shentongModal'));
        modal.show();
    }
}

async function upgradeShentong() {
    if (!currentShentongId) return;

    const response = await apiCall(`/shentong/upgrade/${currentShentongId}`, { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n消耗经验: ${data.exp_cost}, 灵石: ${data.lingshi_cost}\n伤害倍率: ${data.damage_multiplier.toFixed(2)}x, 触发概率: ${(data.trigger_rate * 100).toFixed(1)}%`);
        showShentongs(); // 重新加载神通列表
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('shentongModal'));
        if (modal) modal.hide();
    } else {
        alert(data.message);
    }
}

async function equipShentong() {
    if (!currentShentongId) return;

    const slot = parseInt(prompt('输入装备槽位 (1-3):', '1')) || 1;

    const response = await apiCall(`/shentong/equip/${currentShentongId}`, {
        method: 'POST',
        body: JSON.stringify({ slot: slot })
    });
    const data = await response.json();

    if (response.ok) {
        alert(data.message);
        showShentongs(); // 重新加载神通列表
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('shentongModal'));
        if (modal) modal.hide();
    } else {
        alert(data.message);
    }
}

async function unequipShentong() {
    if (!currentShentongId) return;

    const response = await apiCall(`/shentong/unequip/${currentShentongId}`, { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        alert(data.message);
        showShentongs(); // 重新加载神通列表
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('shentongModal'));
        if (modal) modal.hide();
    } else {
        alert(data.message);
    }
}

function showShentongTrainingModal() {
    const modal = new bootstrap.Modal(document.getElementById('shentongTrainingModal'));
    modal.show();
}

function updateTrainingShentongSelect(shentongs) {
    const select = document.getElementById('trainingShentongSelect');
    select.innerHTML = '<option value="">请选择神通</option>';
    shentongs.forEach(shentong => {
        const option = document.createElement('option');
        option.value = shentong.id;
        option.textContent = `${shentong.name} (等级 ${shentong.level}, 熟练度 ${shentong.proficiency})`;
        select.appendChild(option);
    });
}

async function trainShentong() {
    const shentongId = document.getElementById('trainingShentongSelect').value;
    const timeSpent = parseInt(document.getElementById('trainingTime').value) || 1;
    const environmentBonus = parseFloat(document.getElementById('trainingEnvironment').value) || 1.0;
    const materialQuality = parseFloat(document.getElementById('trainingMaterial').value) || 1.0;

    if (!shentongId) {
        alert('请选择要修炼的神通');
        return;
    }

    // 神通修炼API（需要后端支持，这里先用占位符）
    alert('神通修炼功能正在开发中...');
    // 关闭模态框
    const modal = bootstrap.Modal.getInstance(document.getElementById('shentongTrainingModal'));
    if (modal) modal.hide();
}

// 技能面板相关函数
async function showSkillSlots() {
    // 加载功法和神通数据
    const [mantraResponse, shentongResponse] = await Promise.all([
        apiCall('/mantra'),
        apiCall('/shentong')
    ]);

    if (mantraResponse.ok && shentongResponse.ok) {
        const mantras = await mantraResponse.json();
        const shentongs = await shentongResponse.json();

        // 显示功法槽位
        const mantraSlots = document.getElementById('mantra-slots');
        mantraSlots.innerHTML = '';

        for (let i = 0; i < 6; i++) {
            const equippedMantra = mantras.find(m => m.equipped && m.slot === i);
            const slotDiv = document.createElement('div');
            slotDiv.className = 'col-6 col-md-4 mb-2';

            slotDiv.innerHTML = `
                <div class="card text-center ${equippedMantra ? 'border-primary' : ''}" style="cursor: pointer;" onclick="selectMantraForSlot(${i})">
                    <div class="card-body p-2">
                        <div class="fs-4 mb-1">${equippedMantra ? '📖' : '⬜'}</div>
                        <small class="text-muted">功法槽位 ${i}</small>
                        ${equippedMantra ? `<div class="mt-1"><small>${equippedMantra.name}</small></div>` : ''}
                    </div>
                </div>
            `;
            mantraSlots.appendChild(slotDiv);
        }

        // 显示神通槽位
        const shentongSlots = document.getElementById('shentong-slots');
        shentongSlots.innerHTML = '';

        for (let i = 0; i < 3; i++) {
            const equippedShentong = shentongs.find(s => s.equipped && s.slot === i + 1);
            const slotDiv = document.createElement('div');
            slotDiv.className = 'col-4 mb-2';

            slotDiv.innerHTML = `
                <div class="card text-center ${equippedShentong ? 'border-danger' : ''}" style="cursor: pointer;" onclick="selectShentongForSlot(${i + 1})">
                    <div class="card-body p-2">
                        <div class="fs-4 mb-1">${equippedShentong ? '⚡' : '⬜'}</div>
                        <small class="text-muted">神通槽位 ${i + 1}</small>
                        ${equippedShentong ? `<div class="mt-1"><small>${equippedShentong.name}</small></div>` : ''}
                    </div>
                </div>
            `;
            shentongSlots.appendChild(slotDiv);
        }

        // 显示已装备技能列表
        const equippedMantrasDiv = document.getElementById('equipped-mantras');
        const equippedShentongsDiv = document.getElementById('equipped-shentongs');

        const equippedMantrasList = mantras.filter(m => m.equipped);
        const equippedShentongsList = shentongs.filter(s => s.equipped);

        equippedMantrasDiv.innerHTML = equippedMantrasList.length > 0
            ? equippedMantrasList.map(m => `<div class="badge bg-primary me-1 mb-1">${m.name} (槽位${m.slot})</div>`).join('')
            : '<p class="text-muted">暂无装备的功法</p>';

        equippedShentongsDiv.innerHTML = equippedShentongsList.length > 0
            ? equippedShentongsList.map(s => `<div class="badge bg-danger me-1 mb-1">${s.name} (槽位${s.slot})</div>`).join('')
            : '<p class="text-muted">暂无装备的神通</p>';
    }
}

function selectMantraForSlot(slot) {
    // 这里可以实现功法选择逻辑
    alert(`选择功法装备到槽位 ${slot}\n请前往功法页面进行装备操作`);
}

function selectShentongForSlot(slot) {
    // 这里可以实现神通选择逻辑
    alert(`选择神通装备到槽位 ${slot}\n请前往神通页面进行装备操作`);
}

// 经脉相关函数
let meridiansCache = [];
let acupointsCache = [];
let currentAcupointId = null;
let currentMeridianId = null;

function initSect() {
    showSects();
}

function initRune() {
    showRunes();
    loadEquipmentsForRune();
    loadTreasuresForRune();
}

function initPill() {
    showPills();
}

function initLingzhi() {
    showLingtians();
    showLingzhis();
}

function initPet() {
    showPets();
}

function initMeridian() {
    showMeridians();
}

async function showMeridians() {
    const response = await apiCall('/meridian');
    const data = await response.json();
    if (response.ok) {
        meridiansCache = data;

        // 显示经脉列表
        const meridianList = document.getElementById('meridian-list');
        meridianList.innerHTML = '';

        data.forEach(meridian => {
            const meridianDiv = document.createElement('div');
            meridianDiv.className = `card mb-2 ${meridian.is_open ? 'border-success' : 'border-secondary'}`;

            const openedCount = meridian.acupoints.filter(a => a.level > 0).length;
            const totalCount = meridian.acupoints.length;

            meridianDiv.innerHTML = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="card-title">${meridian.name}</h6>
                            <small class="text-muted">${meridian.type}</small>
                        </div>
                        <span class="badge ${meridian.is_open ? 'bg-success' : 'bg-secondary'}">
                            ${meridian.is_open ? '已开启' : '未开启'}
                        </span>
                    </div>
                    <div class="mt-2">
                        <small>穴位进度: ${openedCount}/${totalCount}</small>
                        <div class="progress mt-1" style="height: 6px;">
                            <div class="progress-bar" role="progressbar" style="width: ${(openedCount/totalCount)*100}%"></div>
                        </div>
                    </div>
                </div>
            `;
            meridianList.appendChild(meridianDiv);
        });

        // 显示经脉图和穴位
        showMeridianDiagram(data);
        calculateAttributeBonuses(data);
    } else {
        alert(data.message);
    }
}

function showMeridianDiagram(meridians) {
    const linesContainer = document.getElementById('meridian-lines');
    const acupointsContainer = document.getElementById('acupoints-container');

    linesContainer.innerHTML = '';
    acupointsContainer.innerHTML = '';

    // 简化：只显示几个主要穴位的示例
    const sampleAcupoints = [
        { name: '百会', x: 200, y: 50, meridian: '督脉' },
        { name: '人迎', x: 180, y: 120, meridian: '足阳明胃经' },
        { name: '气海', x: 200, y: 200, meridian: '任脉' },
        { name: '神阙', x: 200, y: 220, meridian: '任脉' },
        { name: '关元', x: 200, y: 250, meridian: '任脉' },
        { name: '足三里', x: 150, y: 350, meridian: '足阳明胃经' },
        { name: '涌泉', x: 200, y: 550, meridian: '足少阴肾经' },
    ];

    sampleAcupoints.forEach((point, index) => {
        // 创建穴位点
        const acupointDiv = document.createElement('div');
        acupointDiv.className = 'acupoint acupoint-available';
        acupointDiv.style.left = `${point.x - 10}px`;
        acupointDiv.style.top = `${point.y - 10}px`;
        acupointDiv.title = point.name;
        acupointDiv.onclick = () => showAcupointDetail(point, meridians);

        acupointsContainer.appendChild(acupointDiv);
    });
}

function showAcupointDetail(point, meridians) {
    // 查找对应的经脉和穴位数据
    const meridian = meridians.find(m => m.name === point.meridian);
    if (!meridian) return;

    const acupoint = meridian.acupoints.find(a => a.name === point.name);
    if (!acupoint) return;

    currentAcupointId = acupoint.id;
    currentMeridianId = meridian.id;

    document.getElementById('acupointModalTitle').textContent = `${point.name} - 穴位详情`;
    document.getElementById('acupointModalBody').innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6>基本信息</h6>
                <table class="table table-sm">
                    <tr><td>穴位名称:</td><td>${point.name}</td></tr>
                    <tr><td>所属经脉:</td><td>${meridian.name}</td></tr>
                    <tr><td>等级:</td><td>${acupoint.level}/${acupoint.max_level}</td></tr>
                    <tr><td>属性加成:</td><td>${acupoint.attribute_bonus}</td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6>修炼信息</h6>
                <p>点击"开启/升级"按钮来修炼此穴位</p>
                ${!meridian.is_open ? '<div class="alert alert-warning">需要先开启所属经脉</div>' : ''}
            </div>
        </div>
    `;

    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('acupointModal'));
    modal.show();
}

function calculateAttributeBonuses(meridians) {
    const bonusesDiv = document.getElementById('attribute-bonuses');

    // 统计所有已开启穴位的属性加成
    let totalHp = 0, totalAttack = 0, totalDefense = 0, totalSpeed = 0, totalCrit = 0;

    meridians.forEach(meridian => {
        if (meridian.is_open) {
            meridian.acupoints.forEach(acupoint => {
                if (acupoint.level > 0) {
                    // 根据经脉类型分配属性加成
                    if (meridian.name.includes('胃') || meridian.name.includes('脾') || meridian.name === '任脉') {
                        totalHp += acupoint.attribute_bonus;
                    } else if (meridian.name.includes('胆') || meridian.name.includes('肝') || meridian.name === '督脉') {
                        totalAttack += acupoint.attribute_bonus;
                    } else if (meridian.name.includes('膀胱') || meridian.name.includes('肾')) {
                        totalDefense += acupoint.attribute_bonus;
                    } else if (meridian.name.includes('肺') || meridian.name.includes('大肠')) {
                        totalSpeed += acupoint.attribute_bonus;
                    } else {
                        totalCrit += acupoint.attribute_bonus * 0.01; // 转换为百分比
                    }
                }
            });
        }
    });

    bonusesDiv.innerHTML = `
        <table class="table table-sm">
            <tr><td>生命加成:</td><td>+${totalHp}</td></tr>
            <tr><td>攻击加成:</td><td>+${totalAttack}</td></tr>
            <tr><td>防御加成:</td><td>+${totalDefense}</td></tr>
            <tr><td>速度加成:</td><td>+${totalSpeed}</td></tr>
            <tr><td>暴击率加成:</td><td>+${(totalCrit * 100).toFixed(1)}%</td></tr>
        </table>
    `;
}

async function openAcupoint() {
    if (!currentAcupointId) return;

    const response = await apiCall(`/acupoint/open/${currentAcupointId}`, { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n消耗经验: ${data.exp_cost}, 灵石: ${data.lingshi_cost}\n属性加成: ${data.attribute_bonus} (+${data.bonus_increase})`);
        showMeridians(); // 重新加载经脉数据
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('acupointModal'));
        if (modal) modal.hide();
    } else {
        alert(data.message);
    }
}

async function openMeridian() {
    if (!currentMeridianId) return;

    const response = await apiCall(`/meridian/open/${currentMeridianId}`, { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n消耗灵石: ${data.lingshi_cost}`);
        showMeridians(); // 重新加载经脉数据
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('acupointModal'));
        if (modal) modal.hide();
    } else {
        alert(data.message);
    }
}

// 宠物相关函数
let petsCache = [];
let currentPetId = null;

async function showPets() {
    const response = await apiCall('/pet');
    const data = await response.json();
    if (response.ok) {
        petsCache = data;
        const petList = document.getElementById('pet-list');
        petList.innerHTML = '';

        // 品质颜色映射
        const qualityColors = {
            '普通': 'secondary',
            '精良': 'info',
            '稀有': 'success',
            '史诗': 'warning',
            '传说': 'danger'
        };

        data.forEach(pet => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4 mb-3';

            const qualityColor = qualityColors[pet.quality] || 'secondary';
            const intimacyPercent = (pet.intimacy_exp / pet.max_intimacy_exp * 100).toFixed(1);

            col.innerHTML = `
                <div class="card h-100" onclick="showPetDetail(${pet.id})" style="cursor: pointer;">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title">${pet.name}</h6>
                            <span class="badge bg-${qualityColor}">${pet.quality}</span>
                        </div>
                        <p class="card-text small">
                            等级: ${pet.level}<br>
                            亲密度: ${pet.intimacy_level}/10 (${intimacyPercent}%)<br>
                            类型: ${pet.type}
                        </p>
                        <div class="mt-2">
                            <small>属性加成: 攻+${pet.attack_bonus} 防+${pet.defense_bonus} 血+${pet.hp_bonus}</small>
                        </div>
                    </div>
                </div>
            `;
            petList.appendChild(col);
        });
    } else {
        alert(data.message);
    }
}

function showPetDetail(petId) {
    currentPetId = petId;
    const pet = petsCache.find(p => p.id === petId);
    if (pet) {
        document.getElementById('petModalTitle').textContent = `${pet.name} - 宠物详情`;
        document.getElementById('petModalBody').innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>基本信息</h6>
                    <table class="table table-sm">
                        <tr><td>名称:</td><td>${pet.name}</td></tr>
                        <tr><td>品质:</td><td><span class="badge bg-${pet.quality === '普通' ? 'secondary' : pet.quality === '精良' ? 'info' : pet.quality === '稀有' ? 'success' : pet.quality === '史诗' ? 'warning' : 'danger'}">${pet.quality}</span></td></tr>
                        <tr><td>类型:</td><td>${pet.type}</td></tr>
                        <tr><td>等级:</td><td>${pet.level}</td></tr>
                        <tr><td>经验:</td><td>${pet.experience}</td></tr>
                        <tr><td>亲密度等级:</td><td>${pet.intimacy_level}/10</td></tr>
                        <tr><td>亲密度经验:</td><td>${pet.intimacy_exp}/${pet.max_intimacy_exp}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>属性加成</h6>
                    <table class="table table-sm">
                        <tr><td>攻击力:</td><td>+${pet.attack_bonus}</td></tr>
                        <tr><td>防御力:</td><td>+${pet.defense_bonus}</td></tr>
                        <tr><td>生命值:</td><td>+${pet.hp_bonus}</td></tr>
                        <tr><td>速度:</td><td>+${pet.speed_bonus}</td></tr>
                        <tr><td>暴击率:</td><td>+${(pet.crit_rate_bonus * 100).toFixed(1)}%</td></tr>
                        <tr><td>技能:</td><td>${pet.skill_name || '无'}</td></tr>
                        <tr><td>技能概率:</td><td>${(pet.skill_trigger_rate * 100).toFixed(1)}%</td></tr>
                    </table>
                </div>
            </div>
        `;

        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('petModal'));
        modal.show();
    }
}

async function feedPet() {
    if (!currentPetId) {
        alert('请先选择一个宠物');
        return;
    }

    const response = await apiCall(`/pet/feed/${currentPetId}`, { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n获得亲密度经验: ${data.exp_gained}\n当前等级: ${data.current_level} (${data.current_exp}/${data.max_exp})${data.level_up ? '\n恭喜！亲密度等级提升！' : ''}`);
        showPets(); // 重新加载宠物列表
    } else {
        alert(data.message);
    }
}

async function playWithPet() {
    if (!currentPetId) {
        alert('请先选择一个宠物');
        return;
    }

    const response = await apiCall(`/pet/play/${currentPetId}`, { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n获得亲密度经验: ${data.exp_gained}${data.level_up ? '\n恭喜！亲密度等级提升！' : ''}`);
        showPets(); // 重新加载宠物列表
    } else {
        alert(data.message);
    }
}

async function petBattle() {
    if (!currentPetId) {
        alert('请先选择一个宠物');
        return;
    }

    const response = await apiCall(`/pet/battle/${currentPetId}`, { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n宠物获得经验: ${data.pet_exp_gained}\n亲密度经验: ${data.intimacy_exp_gained}${data.pet_level_up ? `\n宠物等级提升到 ${data.pet_new_level}！` : ''}${data.intimacy_level_up ? `\n亲密度等级提升到 ${data.intimacy_new_level}！` : ''}`);
        showPets(); // 重新加载宠物列表
    } else {
        alert(data.message);
    }
}

async function usePetSkill() {
    if (!currentPetId) {
        alert('请先选择一个宠物');
        return;
    }

    const response = await apiCall(`/pet/skill/${currentPetId}`, { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        let message = `${data.message}`;
        if (data.effects) {
            message += `\n技能效果:\n攻击提升: ${data.effects.attack_boost}\n防御提升: ${data.effects.defense_boost}\n生命恢复: ${data.effects.hp_heal}`;
        }
        alert(message);
    } else {
        alert(data.message);
    }
}

async function capturePet() {
    const response = await apiCall('/pet/capture', { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n成功率: ${(data.success_rate * 100).toFixed(1)}%`);
        if (data.pet) {
            alert(`获得宠物: ${data.pet.name} (${data.pet.quality})`);
        }
        showPets(); // 重新加载宠物列表
    } else {
        alert(data.message);
    }
}

async function levelupPet() {
    if (!currentPetId) return;

    const response = await apiCall(`/pet/levelup/${currentPetId}`, { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n消耗经验: ${data.exp_cost}`);
        if (data.attribute_bonuses) {
            alert(`属性提升:\n攻击力: +${data.attribute_bonuses.attack}\n防御力: +${data.attribute_bonuses.defense}\n生命值: +${data.attribute_bonuses.hp}\n速度: +${data.attribute_bonuses.speed}`);
        }
        showPets(); // 重新加载宠物列表
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('petModal'));
        if (modal) modal.hide();
    } else {
        alert(data.message);
    }
}

async function showPetMarket() {
    const response = await apiCall('/pet/market');
    const data = await response.json();

    if (response.ok) {
        const marketList = document.getElementById('pet-market-list');
        marketList.innerHTML = '';

        data.market_pets.forEach(pet => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4 mb-3';

            col.innerHTML = `
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="card-title">${pet.name}</h6>
                        <p class="card-text small">${pet.description}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="badge bg-${pet.quality === '精良' ? 'info' : pet.quality === '稀有' ? 'success' : pet.quality === '史诗' ? 'warning' : 'danger'}">${pet.quality}</span>
                            <span class="text-primary fw-bold">${pet.price} 灵石</span>
                        </div>
                        <button class="btn btn-primary btn-sm mt-2 w-100" onclick="buyPetFromMarket(${pet.id})">购买</button>
                    </div>
                </div>
            `;
            marketList.appendChild(col);
        });

        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('petMarketModal'));
        modal.show();
    } else {
        alert(data.message);
    }
}

async function buyPetFromMarket(petTemplateId) {
    const response = await apiCall(`/pet/market/buy/${petTemplateId}`, { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n获得宠物: ${data.pet.name}`);
        showPets(); // 重新加载宠物列表
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('petMarketModal'));
        if (modal) modal.hide();
    } else {
        alert(data.message);
    }
}

// 宗门相关函数
let currentSectId = null;

async function showSects() {
    const response = await apiCall('/sect');
    const data = await response.json();
    if (response.ok) {
        const sectList = document.getElementById('sect-list');
        sectList.innerHTML = '';

        data.sects.forEach(sect => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4 mb-3';

            col.innerHTML = `
                <div class="card h-100" onclick="showSectDetail(${sect.id})" style="cursor: pointer;">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title">${sect.name}</h6>
                            <span class="badge bg-primary">等级 ${sect.level}</span>
                        </div>
                        <p class="card-text small">
                            成员: ${sect.member_count}<br>
                            繁荣度: ${sect.prosperity}<br>
                            实力值: ${sect.power}
                        </p>
                        <div class="mt-2">
                            <small class="text-muted">${sect.description || '暂无描述'}</small>
                        </div>
                    </div>
                </div>
            `;
            sectList.appendChild(col);
        });
    } else {
        alert(data.message);
    }
}

function showCreateSectModal() {
    const modal = new bootstrap.Modal(document.getElementById('createSectModal'));
    modal.show();
}

async function createSect() {
    const name = document.getElementById('sectName').value.trim();
    const description = document.getElementById('sectDescription').value.trim();

    if (!name) {
        alert('请输入宗门名称');
        return;
    }

    const response = await apiCall('/sect', {
        method: 'POST',
        body: JSON.stringify({ name, description })
    });
    const data = await response.json();

    if (response.ok) {
        alert(data.message);
        showSects(); // 重新加载宗门列表
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('createSectModal'));
        if (modal) modal.hide();
        // 清空表单
        document.getElementById('createSectForm').reset();
    } else {
        alert(data.message);
    }
}

function showSectDetail(sectId) {
    currentSectId = sectId;
    // 这里可以调用获取宗门详情的API
    const modal = new bootstrap.Modal(document.getElementById('sectDetailModal'));
    modal.show();
}

async function joinSect() {
    if (!currentSectId) return;

    const response = await apiCall(`/sect/join/${currentSectId}`, { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        alert(data.message);
        showMySect(); // 显示我的宗门
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('sectDetailModal'));
        if (modal) modal.hide();
    } else {
        alert(data.message);
    }
}

async function showMySect() {
    const response = await apiCall('/sect/my');
    const data = await response.json();

    if (response.ok) {
        const mySectCard = document.getElementById('my-sect-card');
        const mySectInfo = document.getElementById('my-sect-info');

        if (data.sect) {
            mySectCard.style.display = 'block';
            mySectInfo.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <h6>宗门信息</h6>
                        <table class="table table-sm">
                            <tr><td>名称:</td><td>${data.sect.name}</td></tr>
                            <tr><td>等级:</td><td>${data.sect.level}</td></tr>
                            <tr><td>繁荣度:</td><td>${data.sect.prosperity}</td></tr>
                            <tr><td>贡献值:</td><td>${data.sect.contribution}</td></tr>
                            <tr><td>实力值:</td><td>${data.sect.power}</td></tr>
                            <tr><td>威望值:</td><td>${data.sect.prestige}</td></tr>
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h6>成员信息</h6>
                        <table class="table table-sm">
                            <tr><td>职位:</td><td>${data.member.position}</td></tr>
                            <tr><td>个人贡献:</td><td>${data.member.contribution}</td></tr>
                            <tr><td>累计贡献:</td><td>${data.member.total_contribution}</td></tr>
                        </table>
                    </div>
                </div>
            `;
            currentSectId = data.sect.id;
        } else {
            mySectCard.style.display = 'none';
            alert('你还没有加入任何宗门');
        }
    } else {
        alert(data.message);
    }
}

async function upgradeSect() {
    if (!currentSectId) return;

    const response = await apiCall(`/sect/upgrade/${currentSectId}`, { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n新等级: ${data.new_level}\n贡献消耗: ${data.contribution_cost}`);
        showMySect(); // 重新加载我的宗门信息
    } else {
        alert(data.message);
    }
}

async function manageSect() {
    alert('宗门管理功能正在开发中...');
}

async function contributeToSect() {
    const amount = parseInt(prompt('输入贡献的灵石数量:', '100'));
    if (!amount || amount <= 0) return;

    const response = await apiCall('/sect/contribute', {
        method: 'POST',
        body: JSON.stringify({ amount })
    });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n贡献灵石: ${data.contribution_added}\n个人贡献: ${data.personal_contribution}\n宗门繁荣度: ${data.sect_prosperity}\n宗门实力值: ${data.sect_power}`);
        showMySect(); // 重新加载我的宗门信息
    } else {
        alert(data.message);
    }
}

// 符文相关函数
let runesCache = [];
let equipmentsCache = [];
let treasuresCache = [];

async function showRunes() {
    const response = await apiCall('/rune');
    const data = await response.json();
    if (response.ok) {
        runesCache = data;
        const runeList = document.getElementById('rune-list');
        runeList.innerHTML = '';

        // 品质颜色映射
        const qualityColors = {
            '普通': 'secondary',
            '精良': 'info',
            '稀有': 'success',
            '史诗': 'warning',
            '传说': 'danger'
        };

        data.forEach(rune => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4 mb-3';

            const qualityColor = qualityColors[rune.quality] || 'secondary';
            const equippedStatus = rune.equipped ? '已装备' : '未装备';

            col.innerHTML = `
                <div class="card h-100" onclick="showRuneDetail(${rune.id})" style="cursor: pointer;">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title">${rune.name}</h6>
                            <span class="badge bg-${qualityColor}">${rune.quality}</span>
                        </div>
                        <p class="card-text small">
                            ${rune.attribute_type}: +${rune.attribute_value}<br>
                            状态: ${equippedStatus}
                        </p>
                    </div>
                </div>
            `;
            runeList.appendChild(col);
        });

        // 更新符文选择下拉框
        updateRuneSelect();
    } else {
        alert(data.message);
    }
}

async function loadEquipmentsForRune() {
    const response = await apiCall('/equipment');
    const data = await response.json();
    if (response.ok) {
        equipmentsCache = data;
        updateEquipmentSelect();
    }
}

async function loadTreasuresForRune() {
    const response = await apiCall('/treasure');
    const data = await response.json();
    if (response.ok) {
        treasuresCache = data;
        updateTreasureSelect();
    }
}

function updateRuneSelect() {
    const select = document.getElementById('equipRuneSelect');
    select.innerHTML = '<option value="">请选择符文</option>';
    runesCache.forEach(rune => {
        if (!rune.equipped) {
            const option = document.createElement('option');
            option.value = rune.id;
            option.textContent = `${rune.name} (${rune.quality}) - ${rune.attribute_type}: +${rune.attribute_value}`;
            select.appendChild(option);
        }
    });
}

function updateEquipmentSelect() {
    const select = document.getElementById('equipEquipmentSelect');
    select.innerHTML = '<option value="">请选择装备</option>';
    equipmentsCache.forEach(equip => {
        const option = document.createElement('option');
        option.value = equip.id;
        option.textContent = `${equip.name} (${equip.quality}) - 等级 ${equip.level}`;
        select.appendChild(option);
    });
}

function updateTreasureSelect() {
    const select = document.getElementById('equipTreasureSelect');
    select.innerHTML = '<option value="">请选择法宝</option>';
    treasuresCache.forEach(treasure => {
        const option = document.createElement('option');
        option.value = treasure.id;
        option.textContent = `${treasure.name} (${treasure.quality}) - 等级 ${treasure.level}`;
        select.appendChild(option);
    });
}

function showRuneDetail(runeId) {
    const rune = runesCache.find(r => r.id === runeId);
    if (rune) {
        document.getElementById('runeDetailTitle').textContent = `${rune.name} - 符文详情`;
        document.getElementById('runeDetailBody').innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>基本信息</h6>
                    <table class="table table-sm">
                        <tr><td>名称:</td><td>${rune.name}</td></tr>
                        <tr><td>品质:</td><td><span class="badge bg-${rune.quality === '普通' ? 'secondary' : rune.quality === '精良' ? 'info' : rune.quality === '稀有' ? 'success' : rune.quality === '史诗' ? 'warning' : 'danger'}">${rune.quality}</span></td></tr>
                        <tr><td>属性类型:</td><td>${rune.attribute_type}</td></tr>
                        <tr><td>属性值:</td><td>+${rune.attribute_value}</td></tr>
                        <tr><td>装备状态:</td><td>${rune.equipped ? '已装备' : '未装备'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>装备位置</h6>
                    <p>
                        ${rune.equipment_id ? `装备在: ${equipmentsCache.find(e => e.id === rune.equipment_id)?.name || '未知装备'}` : ''}
                        ${rune.treasure_id ? `法宝: ${treasuresCache.find(t => t.id === rune.treasure_id)?.name || '未知法宝'}` : ''}
                        ${!rune.equipment_id && !rune.treasure_id ? '未装备' : ''}
                    </p>
                </div>
            </div>
        `;

        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('runeDetailModal'));
        modal.show();
    }
}

async function forgeRune() {
    const name = document.getElementById('runeName').value.trim();
    const quality = document.getElementById('runeQuality').value;
    const attrType = document.getElementById('runeAttrType').value;
    const attrValue = parseInt(document.getElementById('runeAttrValue').value);
    const materialQuality = parseFloat(document.getElementById('runeMaterialQuality').value);

    if (!name) {
        alert('请输入符文名称');
        return;
    }

    const response = await apiCall('/rune/forge', {
        method: 'POST',
        body: JSON.stringify({
            name: name,
            quality: quality,
            attribute_type: attrType,
            attribute_value: attrValue,
            material_quality_factor: materialQuality
        })
    });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n符文ID: ${data.rune_id}\n成功率: ${(data.success_rate * 100).toFixed(1)}%`);
        showRunes(); // 重新加载符文列表
    } else {
        alert(data.message);
    }
}

async function equipRuneToEquipment() {
    const runeId = document.getElementById('equipRuneSelect').value;
    const equipId = document.getElementById('equipEquipmentSelect').value;

    if (!runeId || !equipId) {
        alert('请选择符文和装备');
        return;
    }

    const response = await apiCall('/rune/equip/equipment', {
        method: 'POST',
        body: JSON.stringify({
            rune_id: parseInt(runeId),
            equip_id: parseInt(equipId)
        })
    });
    const data = await response.json();

    if (response.ok) {
        alert(data.message);
        showRunes(); // 重新加载符文列表
        loadEquipmentsForRune(); // 重新加载装备列表
    } else {
        alert(data.message);
    }
}

async function equipRuneToTreasure() {
    const runeId = document.getElementById('equipRuneSelect').value;
    const treasureId = document.getElementById('equipTreasureSelect').value;

    if (!runeId || !treasureId) {
        alert('请选择符文和法宝');
        return;
    }

    const response = await apiCall('/rune/equip/treasure', {
        method: 'POST',
        body: JSON.stringify({
            rune_id: parseInt(runeId),
            treasure_id: parseInt(treasureId)
        })
    });
    const data = await response.json();

    if (response.ok) {
        alert(data.message);
        showRunes(); // 重新加载符文列表
        loadTreasuresForRune(); // 重新加载法宝列表
    } else {
        alert(data.message);
    }
}

// 丹药相关函数
let pillsCache = [];

async function showPills() {
    const response = await apiCall('/pill');
    const data = await response.json();
    if (response.ok) {
        pillsCache = data;
        const pillList = document.getElementById('pill-list');
        pillList.innerHTML = '';

        // 品质颜色映射
        const qualityColors = {
            '凡品': 'secondary',
            '黄品': 'warning',
            '玄品': 'info',
            '地品': 'success',
            '天品': 'primary',
            '无上': 'danger'
        };

        data.forEach(pill => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4 mb-3';

            const qualityColor = qualityColors[pill.quality] || 'secondary';

            col.innerHTML = `
                <div class="card h-100" onclick="showPillDetail(${pill.id})" style="cursor: pointer;">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title">${pill.name}</h6>
                            <span class="badge bg-${qualityColor}">${pill.quality}</span>
                        </div>
                        <p class="card-text small">
                            等级: ${pill.level}<br>
                            效果: ${pill.effect_type}<br>
                            成功率: ${(pill.success_rate * 100).toFixed(1)}%
                        </p>
                        <div class="mt-2">
                            <small class="text-muted">${pill.description || '暂无描述'}</small>
                        </div>
                    </div>
                </div>
            `;
            pillList.appendChild(col);
        });

        // 更新选择下拉框
        updatePillSelect();
    } else {
        alert(data.message);
    }
}

function updatePillSelect() {
    const select = document.getElementById('usePillSelect');
    select.innerHTML = '<option value="">请选择丹药</option>';
    pillsCache.forEach(pill => {
        const option = document.createElement('option');
        option.value = pill.id;
        option.textContent = `${pill.name} (${pill.quality}) - ${pill.effect_type}`;
        select.appendChild(option);
    });
}

function showRefinePillModal() {
    const modal = new bootstrap.Modal(document.getElementById('refinePillModal'));
    modal.show();
}

function showUsePillModal() {
    const modal = new bootstrap.Modal(document.getElementById('usePillModal'));
    modal.show();
}

async function refinePill() {
    const pillId = document.getElementById('refinePillSelect').value;
    if (!pillId) {
        alert('请选择要炼制的丹药');
        return;
    }

    const response = await apiCall(`/pill/refine/${pillId}`, { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n成功率: ${(data.success_rate * 100).toFixed(1)}%\n消耗灵石: ${data.cost}`);
    } else {
        alert(data.message);
    }

    // 关闭模态框
    const modal = bootstrap.Modal.getInstance(document.getElementById('refinePillModal'));
    if (modal) modal.hide();
}

async function usePill() {
    const pillId = document.getElementById('usePillSelect').value;
    if (!pillId) {
        alert('请选择要使用的丹药');
        return;
    }

    const response = await apiCall(`/pill/use/${pillId}`, { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n效果: ${data.effect_type}\n数值: ${data.effect_value}`);
        // 重新加载人物信息
        if (window.showCharacter) showCharacter();
    } else {
        alert(data.message);
    }

    // 关闭模态框
    const modal = bootstrap.Modal.getInstance(document.getElementById('usePillModal'));
    if (modal) modal.hide();
}

// 灵植相关函数
let lingzhisCache = [];
let lingtiansCache = [];
let currentLingzhiId = null;

async function showLingtians() {
    const response = await apiCall('/lingtian');
    const data = await response.json();
    if (response.ok) {
        lingtiansCache = data;
        const lingtianList = document.getElementById('lingtian-list');
        lingtianList.innerHTML = '';

        data.forEach(lt => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4 mb-3';

            const statusText = lt.is_occupied ? (lt.lingzhi ? '种植中' : '空闲') : '空闲';
            const statusColor = lt.is_occupied ? (lt.lingzhi ? 'success' : 'secondary') : 'secondary';

            col.innerHTML = `
                <div class="card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title">灵田 ${lt.slot}</h6>
                            <span class="badge bg-${statusColor}">${statusText}</span>
                        </div>
                        <p class="card-text small">
                            土壤品质: ${lt.soil_quality}<br>
                            灌溉等级: ${lt.irrigation_level}<br>
                            施肥等级: ${lt.fertilizer_level}
                        </p>
                        ${lt.lingzhi ? `
                            <div class="mt-2">
                                <small><strong>种植:</strong> ${lt.lingzhi.name} (${lt.lingzhi.quality})</small><br>
                                <small><strong>阶段:</strong> ${lt.lingzhi.growth_stage}</small><br>
                                <small><strong>进度:</strong> ${lt.lingzhi.growth_progress}%</small>
                                <div class="progress mt-1" style="height: 4px;">
                                    <div class="progress-bar" role="progressbar" style="width: ${lt.lingzhi.growth_progress}%"></div>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
            lingtianList.appendChild(col);
        });
    } else {
        alert(data.message);
    }
}

async function showLingzhis() {
    const response = await apiCall('/lingzhi');
    const data = await response.json();
    if (response.ok) {
        lingzhisCache = data;
        const lingzhiList = document.getElementById('lingzhi-list');
        lingzhiList.innerHTML = '';

        if (data.length === 0) {
            lingzhiList.innerHTML = '<p class="text-muted">暂无灵植</p>';
            return;
        }

        data.forEach(lz => {
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';

            const qualityColors = {
                '凡品': 'secondary',
                '黄品': 'warning',
                '玄品': 'info',
                '地品': 'success',
                '天品': 'primary',
                '无上': 'danger'
            };
            const qualityColor = qualityColors[lz.quality] || 'secondary';

            li.innerHTML = `
                <div>
                    <strong>${lz.name}</strong>
                    <span class="badge bg-${qualityColor} ms-2">${lz.quality}</span>
                    <br><small class="text-muted">等级: ${lz.level} | 阶段: ${lz.growth_stage} | 进度: ${lz.growth_progress}%</small>
                    ${lz.has_mutated ? `<br><small class="text-success">变异: ${lz.attribute_type} +${lz.attribute_value}</small>` : ''}
                </div>
                <div>
                    <button class="btn btn-sm btn-success me-1" onclick="careLingzhi(${lz.id})">照顾</button>
                    ${lz.growth_progress >= 100 ? `<button class="btn btn-sm btn-warning" onclick="harvestLingzhi(${lz.id})">收获</button>` : ''}
                </div>
            `;
            lingzhiList.appendChild(li);
        });

        // 更新选择下拉框
        updateLingzhiSelect();
    } else {
        alert(data.message);
    }
}

function updateLingzhiSelect() {
    const careSelect = document.getElementById('careLingzhiSelect');
    const harvestSelect = document.getElementById('harvestLingzhiSelect');

    [careSelect, harvestSelect].forEach(select => {
        select.innerHTML = '<option value="">请选择灵植</option>';
    });

    lingzhisCache.forEach(lz => {
        // 照顾选择
        const careOption = document.createElement('option');
        careOption.value = lz.id;
        careOption.textContent = `${lz.name} (${lz.quality}) - ${lz.growth_stage}`;
        careSelect.appendChild(careOption);

        // 收获选择（只显示成熟的）
        if (lz.growth_progress >= 100) {
            const harvestOption = document.createElement('option');
            harvestOption.value = lz.id;
            harvestOption.textContent = `${lz.name} (${lz.quality}) - ${lz.has_mutated ? '变异' : '普通'}`;
            harvestSelect.appendChild(harvestOption);
        }
    });
}

async function initLingtians() {
    const response = await apiCall('/lingtian/init', { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        alert(data.message);
        showLingtians(); // 重新加载灵田
    } else {
        alert(data.message);
    }
}

function showPlantModal() {
    const modal = new bootstrap.Modal(document.getElementById('plantModal'));
    modal.show();
}

function showCareModal() {
    const modal = new bootstrap.Modal(document.getElementById('careModal'));
    modal.show();
}

function showHarvestModal() {
    const modal = new bootstrap.Modal(document.getElementById('harvestModal'));
    modal.show();
}

async function plantLingzhi() {
    const name = document.getElementById('lingzhiName').value.trim();
    const quality = document.getElementById('lingzhiQuality').value;

    if (!name) {
        alert('请输入灵植名称');
        return;
    }

    const response = await apiCall('/lingzhi/plant', {
        method: 'POST',
        body: JSON.stringify({ name, quality })
    });
    const data = await response.json();

    if (response.ok) {
        alert(data.message);
        showLingtians(); // 重新加载灵田
        showLingzhis(); // 重新加载灵植
    } else {
        alert(data.message);
    }

    // 关闭模态框
    const modal = bootstrap.Modal.getInstance(document.getElementById('plantModal'));
    if (modal) modal.hide();
}

async function careLingzhi(lingzhiId) {
    const careType = document.getElementById('careType').value;
    if (!careType) {
        alert('请选择照顾方式');
        return;
    }

    const response = await apiCall(`/lingzhi/care/${lingzhiId}`, {
        method: 'POST',
        body: JSON.stringify({ type: careType })
    });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n消耗灵石: ${data.cost}\n${data.mutated ? `变异！获得${data.attribute_type} +${data.attribute_value}` : ''}`);
        showLingzhis(); // 重新加载灵植
        showLingtians(); // 重新加载灵田
    } else {
        alert(data.message);
    }

    // 关闭模态框
    const modal = bootstrap.Modal.getInstance(document.getElementById('careModal'));
    if (modal) modal.hide();
}

async function harvestLingzhi(lingzhiId) {
    const response = await apiCall(`/lingzhi/harvest/${lingzhiId}`, { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        alert(`${data.message}\n获得灵石: ${data.reward}\n品质: ${data.quality}${data.mutated ? '\n变异奖励！' : ''}`);
        showLingzhis(); // 重新加载灵植
        showLingtians(); // 重新加载灵田
    } else {
        alert(data.message);
    }

    // 关闭模态框
    const modal = bootstrap.Modal.getInstance(document.getElementById('harvestModal'));
    if (modal) modal.hide();
}
