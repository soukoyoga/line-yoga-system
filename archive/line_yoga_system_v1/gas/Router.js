/**
 * イベント振り分け
 */
function handlePostback_(ctx, data) {
  if (data.indexOf('MONTH_') === 0) {
    const month = parseInt(data.replace('MONTH_', ''), 10);
    if (!isNaN(month) && month >= 1 && month <= 12) {
      sendMonthlyReport_(ctx, month);
    }
    return;
  }

  if (data === CONFIG.REPAYMENT_CHOICE_LABEL) {
    showRepaymentSubOptions_(ctx);
    return;
  }

  if (data.indexOf('REV_') === 0) {
    const category = data.slice(4);
    if (CONFIG.REVENUE_LABELS.indexOf(category) !== -1) {
      clearExpenseDirectMode_();
      setLastCategory_(category);
      replyText_(ctx, CONFIG.MESSAGES.ASK_REVENUE_AMOUNT(category));
    }
    return;
  }

  if (isKnownCategory_(data, ctx.sheet)) {
    clearExpenseDirectMode_();
    setLastCategory_(data);
    if (CONFIG.REVENUE_LABELS.indexOf(data) !== -1) {
      replyText_(ctx, CONFIG.MESSAGES.ASK_REVENUE_AMOUNT(data));
    } else {
      replyText_(ctx, CONFIG.MESSAGES.ASK_AMOUNT(data));
    }
    return;
  }
}

function handleTextMessage_(ctx, text) {
  console.log('[Router] handleTextMessage: ' + text);

  if (/\d/.test(text)) {
    if (tryRecordFromText_(ctx, text)) return;
    replyText_(ctx, CONFIG.MESSAGES.INVALID_AMOUNT);
    return;
  }

  if (tryHandleKakeiboCommand_(ctx, text)) return;
  if (tryHandleBusinessCommand_(ctx, text)) return;

  replyText_(ctx, CONFIG.MESSAGES.UNKNOWN);
}
