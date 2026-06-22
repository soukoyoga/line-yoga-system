/**
 * リッチメニュー ID 解決・紐付け
 */
function normalizePostbackData_(raw) {
  if (raw === null || raw === undefined) return '';
  try {
    return decodeURIComponent(String(raw)).trim();
  } catch (err) {
    return String(raw).trim();
  }
}

function detectMenuSwitchIntent_(textOrData) {
  const d = normalizePostbackData_(textOrData);
  if (!d) return null;

  if (
    d === CONFIG.MENU_SWITCH.POSTBACK_TO_KAKEIBO ||
    d === CONFIG.MENU_SWITCH.TO_KAKEIBO ||
    d === '家計簿' ||
    d.indexOf('switch_to_kakeibo') !== -1 ||
    d.indexOf('kakeibo') !== -1
  ) {
    return 'kakeibo';
  }

  if (
    d === CONFIG.MENU_SWITCH.POSTBACK_TO_BUSINESS ||
    d === CONFIG.MENU_SWITCH.TO_BUSINESS ||
    d.indexOf('switch_to_business') !== -1 ||
    (d.indexOf('ビジネス') !== -1 &&
      d.indexOf('速報') === -1 &&
      d.indexOf('詳細') === -1 &&
      d.indexOf('レポート') === -1 &&
      d.indexOf('売上') === -1 &&
      d.indexOf('経費') === -1)
  ) {
    return 'business';
  }

  return null;
}

function listRichMenus_(token) {
  const res = UrlFetchApp.fetch('https://api.line.me/v2/bot/richmenu/list', {
    headers: { Authorization: 'Bearer ' + token },
    method: 'get',
    muteHttpExceptions: true,
  });
  if (res.getResponseCode() !== 200) return [];
  return JSON.parse(res.getContentText()).richmenus || [];
}

function getRichMenuDetail_(menuId, token) {
  const res = UrlFetchApp.fetch(
    'https://api.line.me/v2/bot/richmenu/' + menuId,
    {
      headers: { Authorization: 'Bearer ' + token },
      method: 'get',
      muteHttpExceptions: true,
    }
  );
  if (res.getResponseCode() !== 200) return null;
  return JSON.parse(res.getContentText());
}

function getRichMenuActionTexts_(menuId, token) {
  const detail = getRichMenuDetail_(menuId, token);
  if (!detail || !detail.areas) return [];

  const texts = [];
  detail.areas.forEach(function (area) {
    const action = area.action;
    if (!action) return;
    if (action.text) texts.push(String(action.text));
    if (action.data) texts.push(String(action.data));
    if (action.label) texts.push(String(action.label));
  });
  return texts;
}

function scoreMenuByActionTexts_(menuId, kind, token) {
  const joined = getRichMenuActionTexts_(menuId, token).join('|');
  const markers =
    kind === 'kakeibo'
      ? CONFIG.RICH_MENU_MARKERS.KAKEIBO
      : CONFIG.RICH_MENU_MARKERS.BUSINESS;
  const other =
    kind === 'kakeibo'
      ? CONFIG.RICH_MENU_MARKERS.BUSINESS
      : CONFIG.RICH_MENU_MARKERS.KAKEIBO;

  var score = 0;
  markers.forEach(function (m) {
    if (joined.indexOf(m) !== -1) score += 10;
  });
  other.forEach(function (m) {
    if (joined.indexOf(m) !== -1) score -= 8;
  });
  return score;
}

function findRichMenuIdByActions_(kind, token) {
  const menus = listRichMenus_(token);
  var best = null;
  var bestScore = 0;

  menus.forEach(function (menu) {
    const score = scoreMenuByActionTexts_(menu.richMenuId, kind, token);
    if (score > bestScore) {
      bestScore = score;
      best = menu;
    }
  });

  if (best && bestScore >= 10) {
    console.log(
      'findRichMenuIdByActions_: ' +
        kind +
        ' -> ' +
        best.richMenuId +
        ' (score=' +
        bestScore +
        ', name=' +
        best.name +
        ')'
    );
    return best.richMenuId;
  }
  return null;
}

function hasRichMenuImage_(menuId, token) {
  const res = UrlFetchApp.fetch(
    'https://api-data.line.me/v2/bot/richmenu/' + menuId + '/content',
    {
      method: 'get',
      headers: { Authorization: 'Bearer ' + token },
      muteHttpExceptions: true,
    }
  );
  return res.getResponseCode() === 200;
}

function buildAreaAt_(col, row, cols, rows, action) {
  const cellW = Math.floor(2500 / cols);
  const cellH = Math.floor(1686 / rows);
  return {
    bounds: {
      x: col * cellW,
      y: row * cellH,
      width: cellW,
      height: cellH,
    },
    action: action,
  };
}

function buildMessageAreas_(labels) {
  const cols = 3;
  const rows = Math.ceil(labels.length / cols);
  const areas = [];
  labels.forEach(function (label, i) {
    const col = i % cols;
    const row = Math.floor(i / cols);
    areas.push(
      buildAreaAt_(col, row, cols, rows, { type: 'message', text: label })
    );
  });
  return areas;
}

/**
 * ビジネスメニュー画像のボタン配置（3列×2行）
 * [売上][経費][予約確認]
 * [詳細レポート][速報][家計簿へ]
 */
function buildBusinessMenuAreas_() {
  const cols = 3;
  const rows = 2;
  const reservationUrl = getReservationSpreadsheetUrl_();
  const reservationAction = reservationUrl
    ? { type: 'uri', uri: reservationUrl, label: CONFIG.COMMANDS.RESERVATION_CHECK }
    : { type: 'message', text: CONFIG.COMMANDS.RESERVATION_CHECK };

  return [
    buildAreaAt_(0, 0, cols, rows, { type: 'message', text: '売上入力' }),
    buildAreaAt_(1, 0, cols, rows, { type: 'message', text: '経費入力' }),
    buildAreaAt_(2, 0, cols, rows, reservationAction),
    buildAreaAt_(1, 1, cols, rows, {
      type: 'message',
      text: CONFIG.COMMANDS.BIZ_QUICK,
    }),
    buildAreaAt_(0, 1, cols, rows, {
      type: 'message',
      text: CONFIG.COMMANDS.BIZ_DETAIL,
    }),
    buildAreaAt_(2, 1, cols, rows, {
      type: 'message',
      text: CONFIG.MENU_SWITCH.TO_KAKEIBO,
    }),
  ];
}

function getReservationSpreadsheetUrl_() {
  return CONFIG.RESERVATION.URL || '';
}

/**
 * 古い RESERVATION_SPREADSHEET_URL を削除し、ビジネスメニューを再作成
 */
function fixReservationUrl_() {
  const props = PropertiesService.getScriptProperties();
  const oldUrl = props.getProperty('RESERVATION_SPREADSHEET_URL') || '（未設定）';
  props.deleteProperty('RESERVATION_SPREADSHEET_URL');

  const newUrl = getReservationSpreadsheetUrl_();
  var lines = [
    'RESERVATION_SPREADSHEET_URL を削除しました。',
    '旧: ' + oldUrl,
    '現在使用URL: ' + newUrl,
  ];

  const token = props.getProperty('LINE_TOKEN');
  if (token) {
    const bizId = rebuildBusinessRichMenu_(token);
    const userId = 'Ud0f5e98f92f8eb9b04dacd61ad8add3c';
    linkRichMenuForce_(userId, bizId, token);
    lines.push('ビジネスメニュー再作成: ' + bizId);
    lines.push('予約確認URI: ' + getReservationSpreadsheetUrl_());
    lines.push('想子さんへの紐付け: 完了');
    lines.push('');
    lines.push('LINEを完全終了してから開き直してください。');
  }

  return lines.join('\n');
}

function isValidBusinessMenu_(menuId, token) {
  const detail = getRichMenuDetail_(menuId, token);
  if (!detail) return false;
  if ((detail.name || '').indexOf('_v2') !== -1) return true;
  const texts = getRichMenuActionTexts_(menuId, token).join('|');
  return texts.indexOf('予約確認') !== -1;
}

function createRichMenuWithMessages_(options, token) {
  const body = {
    size: { width: 2500, height: 1686 },
    selected: false,
    name: options.name,
    chatBarText: options.chatBarText,
    areas: options.areas || buildMessageAreas_(options.labels),
  };

  const res = UrlFetchApp.fetch('https://api.line.me/v2/bot/richmenu', {
    method: 'post',
    headers: {
      Authorization: 'Bearer ' + token,
      'Content-Type': 'application/json',
    },
    payload: JSON.stringify(body),
    muteHttpExceptions: true,
  });

  if (res.getResponseCode() !== 200) {
    throw new Error('リッチメニュー作成失敗: ' + res.getContentText());
  }
  return JSON.parse(res.getContentText()).richMenuId;
}

function createKakeiboRichMenu_(token) {
  return createRichMenuWithMessages_(
    {
      name: '家計簿メニュー_自動生成',
      chatBarText: CONFIG.MENU_SWITCH.TO_KAKEIBO,
      labels: [
        '食費・外食入力',
        '娯楽・通信入力',
        '日用品・水ガス入力',
        '返済・貯金入力',
        '家計レポート',
        CONFIG.MENU_SWITCH.TO_BUSINESS,
      ],
    },
    token
  );
}

function createBusinessRichMenu_(token) {
  return createRichMenuWithMessages_(
    {
      name: 'ビジネスメニュー_v2',
      chatBarText: CONFIG.MENU_SWITCH.TO_BUSINESS,
      areas: buildBusinessMenuAreas_(),
    },
    token
  );
}

function rebuildBusinessRichMenu_(token) {
  PropertiesService.getScriptProperties().deleteProperty(
    'RICH_MENU_ID_BUSINESS'
  );
  const bizId = createBusinessRichMenu_(token);
  uploadRichMenuImage_(bizId, CONFIG.RICH_MENU_IMAGE.BUSINESS, token);
  PropertiesService.getScriptProperties().setProperty(
    'RICH_MENU_ID_BUSINESS',
    bizId
  );
  return bizId;
}

/**
 * ボタン定義（areas）が正しいメニューを探す。無ければ新規作成
 */
function ensureProductionRichMenus_(token) {
  var kakeiboId = findRichMenuIdByActions_('kakeibo', token);
  var bizId = findRichMenuIdByActions_('business', token);
  var created = [];

  if (!kakeiboId) {
    kakeiboId = createKakeiboRichMenu_(token);
    uploadRichMenuImage_(kakeiboId, CONFIG.RICH_MENU_IMAGE.KAKEIBO, token);
    created.push('家計簿メニューを新規作成');
  }

  if (bizId && !isValidBusinessMenu_(bizId, token)) {
    bizId = null;
  }

  if (!bizId) {
    bizId = createBusinessRichMenu_(token);
    uploadRichMenuImage_(bizId, CONFIG.RICH_MENU_IMAGE.BUSINESS, token);
    created.push('ビジネスメニューを新規作成（v2・ボタン位置修正）');
  }

  if (kakeiboId && !hasRichMenuImage_(kakeiboId, token)) {
    uploadRichMenuImage_(kakeiboId, CONFIG.RICH_MENU_IMAGE.KAKEIBO, token);
  }
  if (bizId && !hasRichMenuImage_(bizId, token)) {
    uploadRichMenuImage_(bizId, CONFIG.RICH_MENU_IMAGE.BUSINESS, token);
  }

  cacheRichMenuIds_(kakeiboId, bizId);

  return {
    kakeiboId: kakeiboId,
    businessId: bizId,
    created: created,
  };
}

function resolveRichMenuId_(kind, token) {
  const key =
    kind === 'kakeibo' ? 'RICH_MENU_ID_KAKEIBO' : 'RICH_MENU_ID_BUSINESS';
  const cached = PropertiesService.getScriptProperties().getProperty(key);
  if (cached) return cached;

  const found = findRichMenuIdByActions_(kind, token);
  if (found) return found;

  return kind === 'kakeibo'
    ? CONFIG.RICH_MENU.KAKEIBO
    : CONFIG.RICH_MENU.BUSINESS;
}

function clearRichMenuIdCache_() {
  const props = PropertiesService.getScriptProperties();
  props.deleteProperty('RICH_MENU_ID_KAKEIBO');
  props.deleteProperty('RICH_MENU_ID_BUSINESS');
}

function cacheRichMenuIds_(kakeiboId, businessId) {
  const props = PropertiesService.getScriptProperties();
  if (kakeiboId) props.setProperty('RICH_MENU_ID_KAKEIBO', kakeiboId);
  if (businessId) props.setProperty('RICH_MENU_ID_BUSINESS', businessId);
}

function uploadRichMenuImage_(menuId, driveFileId, token) {
  const file = DriveApp.getFileById(driveFileId);
  const blob = file.getBlob();
  const res = UrlFetchApp.fetch(
    'https://api-data.line.me/v2/bot/richmenu/' + menuId + '/content',
    {
      method: 'post',
      headers: {
        Authorization: 'Bearer ' + token,
        'Content-Type': 'image/png',
      },
      payload: blob.getBytes(),
      muteHttpExceptions: true,
    }
  );
  return res.getResponseCode() === 200;
}

function uploadRichMenuImagesSwapped_(kakeiboId, businessId, token) {
  uploadRichMenuImage_(kakeiboId, CONFIG.RICH_MENU_IMAGE.BUSINESS, token);
  uploadRichMenuImage_(businessId, CONFIG.RICH_MENU_IMAGE.KAKEIBO, token);
}

function describeAllRichMenus_(token) {
  const menus = listRichMenus_(token);
  const lines = ['【LINEリッチメニュー一覧】', ''];

  menus.forEach(function (menu) {
    const id = menu.richMenuId;
    const actions = getRichMenuActionTexts_(id, token);
    const kScore = scoreMenuByActionTexts_(id, 'kakeibo', token);
    const bScore = scoreMenuByActionTexts_(id, 'business', token);
    lines.push(
      '名前: ' +
        menu.name +
        '\nchatBar: ' +
        menu.chatBarText +
        '\nID: ' +
        id +
        '\n家計簿スコア: ' +
        kScore +
        ' / ビジネススコア: ' +
        bScore +
        '\nボタン: ' +
        (actions.length ? actions.join(', ') : '（なし）') +
        '\n---'
    );
  });

  return lines.join('\n');
}

function unlinkRichMenu_(userId, token) {
  const res = UrlFetchApp.fetch(
    'https://api.line.me/v2/bot/user/' + userId + '/richmenu',
    {
      method: 'delete',
      headers: { Authorization: 'Bearer ' + token },
      muteHttpExceptions: true,
    }
  );
  const code = res.getResponseCode();
  return code === 200 || code === 404;
}

function linkRichMenuForce_(userId, richMenuId, token) {
  unlinkRichMenu_(userId, token);
  return linkRichMenu_(userId, richMenuId, token);
}

function getUserLinkedRichMenuId_(userId, token) {
  const res = UrlFetchApp.fetch(
    'https://api.line.me/v2/bot/user/' + userId + '/richmenu',
    {
      method: 'get',
      headers: { Authorization: 'Bearer ' + token },
      muteHttpExceptions: true,
    }
  );
  if (res.getResponseCode() !== 200) return null;
  return JSON.parse(res.getContentText()).richMenuId;
}
