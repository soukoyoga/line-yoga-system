/**
 * 「外食 3500 カフェ」「30000 パーソナル」などの入力解析
 */
function parseAmountInput_(text, sheet) {
  const normalized = normalizeInputText_(text);
  if (!normalized) return null;

  var result =
    tryParseCategoryAmountRemarks_(normalized, sheet) ||
    tryParseAmountFirst_(normalized, sheet) ||
    parseLegacyAmountInput_(normalized, sheet);

  console.log(
    '[InputParser] "' +
      normalized +
      '" -> ' +
      (result ? JSON.stringify(result) : 'null')
  );
  return result;
}

function normalizeInputText_(text) {
  return String(text)
    .replace(/,/g, '')
    .replace(/[\u3000\u00a0]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function buildParseResult_(category, amount, remarks) {
  const memo = remarks ? String(remarks).trim() : '';
  return {
    category: category,
    amount: amount,
    note: memo,
    remarks: memo,
  };
}

function tryParseCategoryAmountRemarks_(normalized, sheet) {
  const amountMatch = normalized.match(/(\d+)/);
  if (!amountMatch) return null;

  const amount = parseInt(amountMatch[1], 10);
  if (isNaN(amount) || amount <= 0) return null;

  const amountIndex = normalized.indexOf(amountMatch[0]);
  const before = normalized.slice(0, amountIndex).trim();
  const after = normalized.slice(amountIndex + amountMatch[0].length).trim();

  if (!before) return null;

  const category =
    findCategoryInText_(before, sheet) ||
    findCategoryInText_(normalized, sheet) ||
    before ||
    getLastCategory_();

  if (!category) {
    return { error: 'no_category' };
  }

  return buildParseResult_(category, amount, after);
}

function tryParseAmountFirst_(normalized, sheet) {
  const match = normalized.match(/^(\d+)(?:\s+(.*))?$/);
  if (!match) return null;

  const amount = parseInt(match[1], 10);
  const remarks = (match[2] || '').trim();

  if (isNaN(amount) || amount <= 0) return null;

  const category = getLastCategory_() || findCategoryInText_(normalized, sheet);
  if (!category) {
    return { error: 'no_category' };
  }

  return buildParseResult_(category, amount, remarks);
}

function parseLegacyAmountInput_(normalized, sheet) {
  const amountMatch = normalized.match(/(\d+)/);
  if (!amountMatch) return null;

  const amount = parseInt(amountMatch[1], 10);
  if (isNaN(amount) || amount <= 0) {
    return { error: 'invalid_amount' };
  }

  const categoryFromText = findCategoryInText_(normalized, sheet);
  const category = categoryFromText || getLastCategory_();

  if (!category) {
    return { error: 'no_category' };
  }

  var remarks = normalized;
  if (categoryFromText) {
    remarks = remarks.replace(categoryFromText, '');
  }
  remarks = remarks.replace(amountMatch[0], '').replace(/\s+/g, ' ').trim();

  return buildParseResult_(category, amount, remarks);
}
