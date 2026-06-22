/**
 * カテゴリ判定・一覧
 */
function getAllCategoryLabels_(sheet) {
  const debtNames = getDebtNames_(sheet);
  const fixed = []
    .concat(
      CONFIG.KAKEIBO_GROUPS['食費・外食入力'],
      CONFIG.KAKEIBO_GROUPS['娯楽・通信入力'],
      CONFIG.KAKEIBO_GROUPS['日用品・水ガス入力'],
      [CONFIG.SAVINGS_LABEL],
      debtNames,
      CONFIG.REPAYMENT_SUB_OPTIONS,
      CONFIG.REVENUE_LABELS,
      CONFIG.EXPENSE_LABELS
    );
  return fixed.filter(function (v, i, arr) {
    return arr.indexOf(v) === i;
  });
}

function toAccountType_(categoryLabel, sheet) {
  if (CONFIG.REVENUE_LABELS.indexOf(categoryLabel) !== -1) {
    return CONFIG.ACCOUNT_TYPE.REVENUE;
  }
  if (CONFIG.EXPENSE_LABELS.indexOf(categoryLabel) !== -1) {
    return CONFIG.ACCOUNT_TYPE.EXPENSE;
  }
  if (categoryLabel === CONFIG.OTHER_REPAYMENT_LABEL) {
    return CONFIG.ACCOUNT_TYPE.REPAYMENT;
  }
  if (getDebtNames_(sheet).indexOf(categoryLabel) !== -1) {
    return CONFIG.ACCOUNT_TYPE.REPAYMENT;
  }
  if (CONFIG.REPAYMENT_SUB_OPTIONS.indexOf(categoryLabel) !== -1) {
    return CONFIG.ACCOUNT_TYPE.REPAYMENT;
  }
  return CONFIG.ACCOUNT_TYPE.PRIVATE;
}

function isDebtCategory_(categoryLabel, sheet) {
  return getDebtNames_(sheet).indexOf(categoryLabel) !== -1;
}

function findCategoryInText_(text, sheet) {
  const labels = getAllCategoryLabels_(sheet).sort(function (a, b) {
    return b.length - a.length;
  });
  for (var i = 0; i < labels.length; i++) {
    if (text.indexOf(labels[i]) !== -1) {
      return labels[i];
    }
  }
  return null;
}

function isKnownCategory_(data, sheet) {
  if (data.indexOf('MONTH_') === 0) return false;
  return getAllCategoryLabels_(sheet).indexOf(data) !== -1;
}
