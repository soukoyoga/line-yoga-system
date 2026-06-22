/**
 * 家計・ビジネスレポート
 */
function sendMonthSelection_(ctx) {
  const now = new Date();
  const options = [];
  for (var i = 0; i < 6; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const month = d.getMonth() + 1;
    options.push({
      label: month + '月',
      data: 'MONTH_' + month,
    });
  }
  replyQuickReply_(ctx, 'レポートを見る月を選んでください', options);
}

function sendMonthlyReport_(ctx, month) {
  const entries = getLedgerEntries_(ctx.sheet).filter(function (entry) {
    return entry.date.getMonth() + 1 === month;
  });

  if (entries.length === 0) {
    replyText_(ctx, month + '月の家計データはまだありません。');
    return;
  }

  const living = entries.filter(function (entry) {
    return (
      entry.accountType === CONFIG.ACCOUNT_TYPE.PRIVATE &&
      entry.label !== CONFIG.SAVINGS_LABEL
    );
  });
  const savings = entries.filter(function (entry) {
    return entry.label === CONFIG.SAVINGS_LABEL;
  });
  const repayment = entries.filter(function (entry) {
    return entry.accountType === CONFIG.ACCOUNT_TYPE.REPAYMENT;
  });

  if (living.length === 0 && savings.length === 0 && repayment.length === 0) {
    replyText_(ctx, month + '月の家計データはまだありません。');
    return;
  }

  const sections = [];
  var livingTotal = 0;
  const groupKeys = Object.keys(CONFIG.KAKEIBO_GROUPS);

  for (var g = 0; g < groupKeys.length; g++) {
    const groupName = groupKeys[g];
    const groupLabels = CONFIG.KAKEIBO_GROUPS[groupName];
    const groupEntries = living.filter(function (entry) {
      return groupLabels.indexOf(entry.label) !== -1;
    });
    if (groupEntries.length === 0) continue;

    const totals = sumByLabel_(groupEntries);
    const groupSum = sumAmounts_(groupEntries);
    livingTotal += groupSum;

    const displayName = groupName.replace(/入力$/, '');
    sections.push(
      '【' +
        displayName +
        '】\n' +
        formatLabelTotals_(totals) +
        '\n小計：' +
        groupSum.toLocaleString() +
        '円'
    );
  }

  const knownLivingLabels = []
    .concat(
      CONFIG.KAKEIBO_GROUPS['食費・外食入力'],
      CONFIG.KAKEIBO_GROUPS['娯楽・通信入力'],
      CONFIG.KAKEIBO_GROUPS['日用品・水ガス入力']
    );
  const otherLiving = living.filter(function (entry) {
    return knownLivingLabels.indexOf(entry.label) === -1;
  });
  if (otherLiving.length > 0) {
    const totals = sumByLabel_(otherLiving);
    const groupSum = sumAmounts_(otherLiving);
    livingTotal += groupSum;
    sections.push(
      '【その他の生活費】\n' +
        formatLabelTotals_(totals) +
        '\n小計：' +
        groupSum.toLocaleString() +
        '円'
    );
  }

  var message = '📊 ' + month + '月の家計レポート\n\n';

  if (sections.length > 0) {
    message += sections.join('\n\n');
    message += '\n\n━━━━━━━━━━\n';
    message += '💰 生活費 合計：' + livingTotal.toLocaleString() + '円';
  }

  if (savings.length > 0) {
    const savingsTotal = sumAmounts_(savings);
    message += '\n\n【貯金】\n';
    message += formatLabelTotals_(sumByLabel_(savings));
    message += '\n\n📌 貯金 合計：' + savingsTotal.toLocaleString() + '円';
  }

  if (repayment.length > 0) {
    const repaymentTotal = sumAmounts_(repayment);
    message += '\n\n【返済】\n';
    message += formatLabelTotals_(sumByLabel_(repayment));
    message += '\n\n📌 返済 合計：' + repaymentTotal.toLocaleString() + '円';
  }

  replyText_(ctx, message);
}

function sendBizReport_(ctx, detailed) {
  const now = new Date();
  const month = now.getMonth() + 1;
  const entries = getLedgerEntries_(ctx.sheet).filter(function (entry) {
    return (
      entry.date.getMonth() === now.getMonth() &&
      entry.date.getFullYear() === now.getFullYear()
    );
  });

  const revenue = entries.filter(function (e) {
    return e.accountType === CONFIG.ACCOUNT_TYPE.REVENUE;
  });
  const expense = entries.filter(function (e) {
    return e.accountType === CONFIG.ACCOUNT_TYPE.EXPENSE;
  });

  const revenueSum = sumAmounts_(revenue);
  const expenseSum = sumAmounts_(expense);
  const profit = revenueSum - expenseSum;

  if (revenue.length === 0 && expense.length === 0) {
    replyText_(ctx, month + '月のビジネスデータはまだありません。');
    return;
  }

  var message =
    '💼 ' +
    month +
    '月ビジネス' +
    (detailed ? '詳細' : '速報') +
    '\n\n' +
    '売上：' +
    revenueSum.toLocaleString() +
    '円\n' +
    '経費：' +
    expenseSum.toLocaleString() +
    '円\n' +
    '利益：' +
    profit.toLocaleString() +
    '円';

  if (detailed) {
    message += '\n\n【売上内訳】\n' + formatBreakdown_(revenue);
    message += '\n【経費内訳】\n' + formatBreakdown_(expense);
  }

  replyText_(ctx, message);
}

function sumByLabel_(entries) {
  const totals = {};
  entries.forEach(function (entry) {
    totals[entry.label] = (totals[entry.label] || 0) + entry.amount;
  });
  return totals;
}

function sumAmounts_(entries) {
  return entries.reduce(function (sum, entry) {
    return sum + entry.amount;
  }, 0);
}

function formatLabelTotals_(totals) {
  return Object.keys(totals)
    .sort(function (a, b) {
      return totals[b] - totals[a];
    })
    .map(function (label) {
      return '・' + label + '：' + totals[label].toLocaleString() + '円';
    })
    .join('\n');
}

function formatBreakdown_(entries) {
  if (entries.length === 0) return '（なし）';
  return formatLabelTotals_(sumByLabel_(entries));
}
