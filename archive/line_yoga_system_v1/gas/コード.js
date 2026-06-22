/**
 * LINE Webhook エントリポイント
 */

function doGet(e) {
  const token = PropertiesService.getScriptProperties().getProperty('LINE_TOKEN');

  if (e && e.parameter && e.parameter.action === 'listMenus' && token) {
    return ContentService.createTextOutput(describeAllRichMenus_(token));
  }

  if (e && e.parameter && e.parameter.action === 'reuploadImages' && token) {
    const key =
      PropertiesService.getScriptProperties().getProperty('ADMIN_KEY') ||
      'souko-fix-menu';
    if (e.parameter.key !== key) {
      return ContentService.createTextOutput('key が違います');
    }
    const menus = ensureProductionRichMenus_(token);
    uploadRichMenuImage_(menus.kakeiboId, CONFIG.RICH_MENU_IMAGE.KAKEIBO, token);
    uploadRichMenuImage_(menus.businessId, CONFIG.RICH_MENU_IMAGE.BUSINESS, token);
    return ContentService.createTextOutput(
      '画像を再アップロードしました。\n家計簿→' +
        menus.kakeiboId +
        '\nビジネス→' +
        menus.businessId
    );
  }

  if (e && e.parameter && e.parameter.action === 'reuploadImagesSwap' && token) {
    const key =
      PropertiesService.getScriptProperties().getProperty('ADMIN_KEY') ||
      'souko-fix-menu';
    if (e.parameter.key !== key) {
      return ContentService.createTextOutput('key が違います');
    }
    const menus = ensureProductionRichMenus_(token);
    uploadRichMenuImagesSwapped_(menus.kakeiboId, menus.businessId, token);
    return ContentService.createTextOutput(
      '画像を入れ替えてアップロードしました。\n家計簿→' +
        menus.kakeiboId +
        '\nビジネス→' +
        menus.businessId
    );
  }

  if (e && e.parameter && e.parameter.action === 'fixReservationUrl' && token) {
    const key =
      PropertiesService.getScriptProperties().getProperty('ADMIN_KEY') ||
      'souko-fix-menu';
    if (e.parameter.key !== key) {
      return ContentService.createTextOutput('key が違います');
    }
    return ContentService.createTextOutput(fixReservationUrl_());
  }

  if (e && e.parameter && e.parameter.action === 'fixBusinessMenu' && token) {
    const key =
      PropertiesService.getScriptProperties().getProperty('ADMIN_KEY') ||
      'souko-fix-menu';
    if (e.parameter.key !== key) {
      return ContentService.createTextOutput('key が違います');
    }
    const bizId = rebuildBusinessRichMenu_(token);
    const userId = 'Ud0f5e98f92f8eb9b04dacd61ad8add3c';
    linkRichMenuForce_(userId, bizId, token);
    return ContentService.createTextOutput(
      'ビジネスメニューを v2 に更新しました。\nID: ' +
        bizId +
        '\nボタン: ' +
        getRichMenuActionTexts_(bizId, token).join(', ') +
        '\n\nLINEを完全終了してから開き直してください。'
    );
  }

  if (e && e.parameter && e.parameter.action === 'fixMenu') {
    const key =
      PropertiesService.getScriptProperties().getProperty('ADMIN_KEY') ||
      'souko-fix-menu';
    if (e.parameter.key !== key) {
      return ContentService.createTextOutput('key が違います');
    }
    const result = fixMenuNow_();
    return ContentService.createTextOutput(result);
  }
  return ContentService.createTextOutput('line-yoga-bot ok (function-base-v1)');
}

/**
 * GASエディタで fixMenuNow を選んで実行（家計簿メニューを強制設定）
 */
function fixMenuNow() {
  Logger.log(fixMenuNow_());
}

function fixMenuNow_() {
  const token = PropertiesService.getScriptProperties().getProperty('LINE_TOKEN');
  if (!token) {
    throw new Error('LINE_TOKEN がスクリプトプロパティにありません');
  }

  clearRichMenuIdCache_();

  const userId = 'Ud0f5e98f92f8eb9b04dacd61ad8add3c';
  const menus = ensureProductionRichMenus_(token);
  const kakeiboId = menus.kakeiboId;
  const bizId = menus.businessId;

  const resDefault = UrlFetchApp.fetch(
    'https://api.line.me/v2/bot/user/all/richmenu/' + kakeiboId,
    {
      method: 'post',
      headers: { Authorization: 'Bearer ' + token },
      muteHttpExceptions: true,
    }
  );

  const ok = linkRichMenuForce_(userId, kakeiboId, token);

  const kakeiboActions = getRichMenuActionTexts_(kakeiboId, token).join(', ');
  const msg =
    '【ボタン定義ベースで再設定しました】\n\n' +
    (menus.created.length ? menus.created.join('\n') + '\n\n' : '') +
    '家計簿ID: ' +
    kakeiboId +
    '\n  ボタン: ' +
    kakeiboActions +
    '\nビジネスID: ' +
    bizId +
    '\n  ボタン: ' +
    getRichMenuActionTexts_(bizId, token).join(', ') +
    '\nデフォルト設定: HTTP ' +
    resDefault.getResponseCode() +
    '\n想子さんへの紐付け: ' +
    (ok ? '成功' : '失敗') +
    '\n\n※LINEを完全終了→再起動。\n' +
    '画像だけ逆なら reuploadImagesSwap も試してください。';
  Logger.log(msg);
  return msg;
}

function doPost(e) {
  try {
    console.log('[doPost] start');

    if (!e || !e.postData || !e.postData.contents) {
      console.log('[doPost] no postData, skip');
      return;
    }

    const token = PropertiesService.getScriptProperties().getProperty('LINE_TOKEN');
    if (!token) {
      console.error('[doPost] LINE_TOKEN が Script Properties に設定されていません');
      return;
    }

    const body = JSON.parse(e.postData.contents);
    if (!body.events || body.events.length === 0) {
      console.log('[doPost] no events, skip');
      return;
    }

    const event = body.events[0];
    if (!event || !event.source || !event.replyToken) {
      console.log('[doPost] invalid event, skip');
      return;
    }

    console.log('[doPost] event type: ' + event.type);

    const ctx = {
      replyToken: event.replyToken,
      userId: event.source.userId,
      token: token,
      sheet: null,
      event: event,
    };

    if (event.type === 'postback' && event.postback) {
      const data = normalizePostbackData_(event.postback.data);
      console.log('[doPost] postback: ' + data);
      if (tryHandleMenuSwitchPostback_(ctx, data)) return;
    }

    if (
      event.type === 'message' &&
      event.message &&
      event.message.type === 'text' &&
      event.message.text
    ) {
      const text = event.message.text.trim();
      console.log('[doPost] message: ' + text);
      if (tryHandleMenuSwitch_(ctx, text)) return;
    }

    const sheet = getLedgerSheet_();
    if (!sheet) {
      console.error('[doPost] シート「' + CONFIG.SHEET.LEDGER + '」が見つかりません');
      replyText_(
        ctx,
        'スプレッドシートに接続できません。GASとシートの紐付けを確認してください。'
      );
      return;
    }
    ctx.sheet = sheet;

    if (event.type === 'postback' && event.postback) {
      handlePostback_(ctx, normalizePostbackData_(event.postback.data));
      return;
    }

    if (
      event.type === 'message' &&
      event.message &&
      event.message.type === 'text' &&
      event.message.text
    ) {
      handleTextMessage_(ctx, event.message.text.trim());
    }

    console.log('[doPost] done');
  } catch (err) {
    console.error('[doPost] FAILED: ' + err.message + '\n' + err.stack);
    try {
      if (e && e.postData) {
        const body = JSON.parse(e.postData.contents);
        const event = body.events && body.events[0];
        const token = PropertiesService.getScriptProperties().getProperty('LINE_TOKEN');
        if (event && event.replyToken && token) {
          replyText_(
            { replyToken: event.replyToken, token: token },
            'エラーが発生しました。しばらくしてからもう一度お試しください。'
          );
        }
      }
    } catch (replyErr) {
      console.error('[doPost] reply failed: ' + replyErr.message);
    }
  }
}
