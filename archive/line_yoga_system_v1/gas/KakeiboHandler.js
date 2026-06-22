/**
 * 家計簿メニューの操作
 */
function tryHandleKakeiboCommand_(ctx, text) {
  clearExpenseDirectMode_();
  const groups = CONFIG.KAKEIBO_GROUPS;
  const keys = Object.keys(groups);
  for (var i = 0; i < keys.length; i++) {
    if (text === keys[i]) {
      replyQuickReply_(ctx, 'どちらを入力しますか？', groups[keys[i]]);
      return true;
    }
  }

  if (text === CONFIG.COMMANDS.DEBT_INPUT) {
    replyQuickReply_(ctx, 'どちらを入力しますか？', [
      CONFIG.REPAYMENT_CHOICE_LABEL,
      CONFIG.SAVINGS_LABEL,
    ]);
    return true;
  }

  if (text === CONFIG.REPAYMENT_CHOICE_LABEL) {
    showRepaymentSubOptions_(ctx);
    return true;
  }

  if (text === CONFIG.COMMANDS.KAKEIBO_REPORT) {
    sendMonthSelection_(ctx);
    return true;
  }

  return false;
}

function showRepaymentSubOptions_(ctx) {
  replyQuickReply_(
    ctx,
    '返済項目を選んでください',
    CONFIG.REPAYMENT_SUB_OPTIONS
  );
}
