/**
 * ビジネスメニューの操作
 */
function getRevenueQuickReplyOptions_() {
  return CONFIG.REVENUE_LABELS.map(function (label) {
    return { label: label, data: 'REV_' + label };
  });
}

function tryHandleBusinessCommand_(ctx, text) {
  if (text === CONFIG.COMMANDS.REVENUE_INPUT) {
    clearExpenseDirectMode_();
    replyQuickReply_(ctx, '種類を選んでください', getRevenueQuickReplyOptions_());
    return true;
  }

  if (text === CONFIG.COMMANDS.EXPENSE_INPUT) {
    clearExpenseDirectMode_();
    setExpenseDirectMode_(true);
    replyText_(ctx, CONFIG.MESSAGES.ASK_EXPENSE_AMOUNT);
    return true;
  }

  if (text === CONFIG.COMMANDS.RESERVATION_CHECK) {
    const url = getReservationSpreadsheetUrl_();
    if (url) {
      replyText_(ctx, '予約ページはこちらです。\n' + url);
    } else {
      replyText_(ctx, '予約スプレッドシートのURLが未設定です。');
    }
    return true;
  }

  if (
    text === CONFIG.COMMANDS.BIZ_QUICK ||
    text === CONFIG.COMMANDS.BIZ_DETAIL
  ) {
    sendBizReport_(ctx, text === CONFIG.COMMANDS.BIZ_DETAIL);
    return true;
  }

  return false;
}
