/**
 * セットアップ・メンテ用（Webhook からは呼ばない）
 * リッチメニュー ID は Config.js の CONFIG.RICH_MENU を参照
 */

function createTwoMenus() {
  const token = PropertiesService.getScriptProperties().getProperty('LINE_TOKEN');
  const url = 'https://api.line.me/v2/bot/richmenu';

  const bodyK = {
    size: { width: 2500, height: 1686 },
    selected: false,
    name: '家計簿メニュー_New',
    chatBarText: CONFIG.MENU_SWITCH.TO_KAKEIBO,
    areas: [
      {
        bounds: { x: 0, y: 0, width: 2500, height: 1686 },
        action: { type: 'postback', data: 'switch_to_business' },
      },
    ],
  };
  const resK = UrlFetchApp.fetch(url, {
    method: 'post',
    headers: {
      Authorization: 'Bearer ' + token,
      'Content-Type': 'application/json',
    },
    payload: JSON.stringify(bodyK),
  });
  const idK = JSON.parse(resK.getContentText()).richMenuId;

  const bodyB = {
    size: { width: 2500, height: 1686 },
    selected: false,
    name: 'ビジネスメニュー_New',
    chatBarText: CONFIG.MENU_SWITCH.TO_BUSINESS,
    areas: [
      {
        bounds: { x: 0, y: 0, width: 2500, height: 1686 },
        action: { type: 'postback', data: 'switch_to_kakeibo' },
      },
    ],
  };
  const resB = UrlFetchApp.fetch(url, {
    method: 'post',
    headers: {
      Authorization: 'Bearer ' + token,
      'Content-Type': 'application/json',
    },
    payload: JSON.stringify(bodyB),
  });
  const idB = JSON.parse(resB.getContentText()).richMenuId;

  console.log('新しい家計簿ID: ' + idK);
  console.log('新しいビジネスID: ' + idB);
}

function uploadImages() {
  const token = PropertiesService.getScriptProperties().getProperty('LINE_TOKEN');
  const menus = ensureProductionRichMenus_(token);
  uploadRichMenuImage_(menus.kakeiboId, CONFIG.RICH_MENU_IMAGE.KAKEIBO, token);
  uploadRichMenuImage_(menus.businessId, CONFIG.RICH_MENU_IMAGE.BUSINESS, token);
  console.log('家計簿: ' + menus.kakeiboId + ' / ビジネス: ' + menus.businessId);
}

function sendImageToLine_(menuId, fileId, token) {
  const file = DriveApp.getFileById(fileId);
  const blob = file.getBlob();
  const url =
    'https://api-data.line.me/v2/bot/richmenu/' + menuId + '/content';
  const res = UrlFetchApp.fetch(url, {
    method: 'post',
    headers: {
      Authorization: 'Bearer ' + token,
      'Content-Type': 'image/png',
    },
    payload: blob.getBytes(),
  });
  console.log(menuId + ' 画像アップロード: ' + res.getContentText());
}

function setInitialMenu() {
  const token = PropertiesService.getScriptProperties().getProperty('LINE_TOKEN');
  const userId = 'Ud0f5e98f92f8eb9b04dacd61ad8add3c';
  linkRichMenu_(userId, CONFIG.RICH_MENU.KAKEIBO, token);
}

function forceShowMenu() {
  setInitialMenu();
}

function checkImageStatus() {
  const token = PropertiesService.getScriptProperties().getProperty('LINE_TOKEN');
  const url =
    'https://api-data.line.me/v2/bot/richmenu/' +
    CONFIG.RICH_MENU.KAKEIBO +
    '/content';
  const res = UrlFetchApp.fetch(url, {
    method: 'get',
    headers: { Authorization: 'Bearer ' + token },
    muteHttpExceptions: true,
  });
  const code = res.getResponseCode();
  console.log(
    code === 200
      ? '✅ 家計簿メニューに画像があります'
      : '❌ 画像なし（' + code + '）'
  );
}

function checkRealIds() {
  const token = PropertiesService.getScriptProperties().getProperty('LINE_TOKEN');
  const res = UrlFetchApp.fetch('https://api.line.me/v2/bot/richmenu/list', {
    headers: { Authorization: 'Bearer ' + token },
    method: 'get',
  });
  const data = JSON.parse(res.getContentText());
  data.richmenus.forEach(function (menu) {
    console.log('名前: ' + menu.name + ' / ID: ' + menu.richMenuId);
  });
}

function setDefaultMenu() {
  const token = PropertiesService.getScriptProperties().getProperty('LINE_TOKEN');
  const url =
    'https://api.line.me/v2/bot/user/all/richmenu/' + CONFIG.RICH_MENU.KAKEIBO;
  const res = UrlFetchApp.fetch(url, {
    method: 'post',
    headers: { Authorization: 'Bearer ' + token },
  });
  console.log('デフォルトメニュー設定: ' + res.getContentText());
}

function resetUserMenu() {
  const token = PropertiesService.getScriptProperties().getProperty('LINE_TOKEN');
  const userId = 'Ud0f5e98f92f8eb9b04dacd61ad8add3c';
  const menus = ensureProductionRichMenus_(token);
  linkRichMenuForce_(userId, menus.kakeiboId, token);
  console.log('家計簿メニューを再紐付け: ' + menuId);
}

/**
 * GASエディタで実行: LINE上のメニュー一覧と想子さんの紐付け状態をログ出力
 */
function diagnoseRichMenus() {
  const token = PropertiesService.getScriptProperties().getProperty('LINE_TOKEN');
  const userId = 'Ud0f5e98f92f8eb9b04dacd61ad8add3c';

  listRichMenus_(token).forEach(function (menu) {
    console.log(
      'メニュー: ' + menu.name + ' / chatBar: ' + menu.chatBarText + ' / ID: ' + menu.richMenuId
    );
  });

  const linked = getUserLinkedRichMenuId_(userId, token);
  console.log('想子さんに紐付いているID: ' + (linked || '（なし＝デフォルトメニュー表示）'));
  console.log('解決ID 家計簿: ' + resolveRichMenuId_('kakeibo', token));
  console.log('解決ID ビジネス: ' + resolveRichMenuId_('business', token));
}

/**
 * 全ユーザーのデフォルトを家計簿にし、想子さんにも家計簿を強制紐付け
 */
function fixDefaultAndSoukoMenu() {
  const token = PropertiesService.getScriptProperties().getProperty('LINE_TOKEN');
  const userId = 'Ud0f5e98f92f8eb9b04dacd61ad8add3c';
  const kakeiboId = resolveRichMenuId_('kakeibo', token);

  UrlFetchApp.fetch(
    'https://api.line.me/v2/bot/user/all/richmenu/' + kakeiboId,
    {
      method: 'post',
      headers: { Authorization: 'Bearer ' + token },
      muteHttpExceptions: true,
    }
  );

  linkRichMenuForce_(userId, kakeiboId, token);
  console.log('デフォルト＋想子さんを家計簿に設定: ' + kakeiboId);
}
