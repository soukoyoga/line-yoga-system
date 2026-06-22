/**
 * 記帳処理（家計簿・ビジネス共通）
 */
function recordEntry_(ctx, categoryLabel, amount, remarks, accountTypeOverride) {
  const sheet = ctx.sheet;
  const accountType =
    accountTypeOverride || toAccountType_(categoryLabel, sheet);
  const memo =
    remarks === undefined || remarks === null ? '' : String(remarks).trim();

  console.log(
    '[Ledger] record: ' +
      categoryLabel +
      ' / ' +
      amount +
      ' / memo=' +
      memo +
      ' / type=' +
      accountType
  );

  appendLedgerRow_(sheet, categoryLabel, amount, accountType, memo);
  setLastCategory_(categoryLabel);

  var message =
    '✅ ' +
    categoryLabel +
    'として記録しました！\n' +
    amount.toLocaleString() +
    '円';
  if (memo) {
    message += '\n備考: ' + memo;
  }

  if (isDebtCategory_(categoryLabel, sheet)) {
    const remaining = getDebtBalance_(sheet, categoryLabel);
    if (remaining !== null && remaining !== '') {
      message +=
        '\n\n📉 残高：あと ' + Number(remaining).toLocaleString() + '円';
    }
  }

  replyText_(ctx, message);
}

function tryRecordExpenseDirect_(ctx, text) {
  const normalized = normalizeInputText_(text);
  const match = normalized.match(/^(\d+)(?:\s+(.*))?$/);
  if (!match) {
    replyText_(ctx, CONFIG.MESSAGES.INVALID_EXPENSE_INPUT);
    return true;
  }

  const amount = parseInt(match[1], 10);
  const content = (match[2] || '').trim();

  if (isNaN(amount) || amount <= 0) {
    replyText_(ctx, CONFIG.MESSAGES.INVALID_EXPENSE_INPUT);
    return true;
  }
  if (!content) {
    replyText_(ctx, CONFIG.MESSAGES.EXPENSE_NEED_CONTENT);
    return true;
  }

  clearExpenseDirectMode_();
  recordEntry_(ctx, content, amount, '', CONFIG.ACCOUNT_TYPE.EXPENSE);
  return true;
}

function tryRecordFromText_(ctx, text) {
  if (isExpenseDirectMode_()) {
    return tryRecordExpenseDirect_(ctx, text);
  }

  const parsed = parseAmountInput_(text, ctx.sheet);
  if (!parsed) return false;

  if (parsed.error === 'no_category') {
    replyText_(ctx, CONFIG.MESSAGES.NO_CATEGORY);
    return true;
  }
  if (parsed.error === 'invalid_amount') {
    replyText_(ctx, CONFIG.MESSAGES.INVALID_AMOUNT);
    return true;
  }

  const remarks = parsed.remarks || parsed.note || '';
  recordEntry_(ctx, parsed.category, parsed.amount, remarks);
  return true;
}
