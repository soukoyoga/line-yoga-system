/**
 * リッチメニュー切り替え
 */
function switchToKakeibo_(ctx) {
  const menuId = resolveRichMenuId_('kakeibo', ctx.token);
  const ok = linkRichMenuForce_(ctx.userId, menuId, ctx.token);
  if (!ok) {
    replyText_(
      ctx,
      'メニューの切り替えに失敗しました。しばらくしてからもう一度お試しください。'
    );
    return;
  }
  replyText_(
    ctx,
    '🏠 家計簿モードに切り替えました。\n' + CONFIG.MESSAGES.MENU_SWITCH_NOTE
  );
}

function switchToBusiness_(ctx) {
  const menuId = resolveRichMenuId_('business', ctx.token);
  const ok = linkRichMenuForce_(ctx.userId, menuId, ctx.token);
  if (!ok) {
    replyText_(
      ctx,
      'メニューの切り替えに失敗しました。しばらくしてからもう一度お試しください。'
    );
    return;
  }
  replyText_(
    ctx,
    '💼 ビジネスモードに切り替えました。\n' + CONFIG.MESSAGES.MENU_SWITCH_NOTE
  );
}

function tryHandleMenuSwitchPostback_(ctx, data) {
  const intent = detectMenuSwitchIntent_(data);
  if (intent === 'kakeibo') {
    switchToKakeibo_(ctx);
    return true;
  }
  if (intent === 'business') {
    switchToBusiness_(ctx);
    return true;
  }
  return false;
}

function tryHandleMenuSwitch_(ctx, text) {
  const intent = detectMenuSwitchIntent_(text);
  if (intent === 'kakeibo') {
    switchToKakeibo_(ctx);
    return true;
  }
  if (intent === 'business') {
    switchToBusiness_(ctx);
    return true;
  }
  return false;
}
