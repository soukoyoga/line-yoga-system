/**
 * スプレッドシート読み書き
 * A:日付 B:項目 C:金額 D:備考 E:区分
 */
function getLedgerSheet_() {
  return SpreadsheetApp.getActiveSpreadsheet().getSheetByName(
    CONFIG.SHEET.LEDGER
  );
}

function getDebtNames_(sheet) {
  return sheet
    .getRange(CONFIG.SHEET.DEBT_NAMES_RANGE)
    .getValues()
    .flat()
    .filter(function (name) {
      return name !== '';
    });
}

function appendLedgerRow_(sheet, categoryLabel, amount, accountType, note) {
  const memo = note === undefined || note === null ? '' : String(note);
  const row = sheet.getLastRow() + 1;
  sheet
    .getRange(row, 1, 1, 5)
    .setValues([[new Date(), categoryLabel, amount, memo, accountType]]);
  console.log(
    '[Sheet] row ' +
      row +
      ' written: ' +
      categoryLabel +
      ' / ' +
      amount +
      ' / ' +
      memo
  );
}

function getDebtBalance_(sheet, debtName) {
  const debtNames = getDebtNames_(sheet);
  const index = debtNames.indexOf(debtName);
  if (index === -1) return null;
  return sheet.getRange(index + 2, CONFIG.SHEET.DEBT_BALANCE_COL).getValue();
}

function getLedgerEntries_(sheet) {
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];

  const numRows = lastRow - 1;
  const values = sheet.getRange(2, 1, numRows, 5).getValues();
  return values
    .map(function (row) {
      return {
        date: row[0] instanceof Date ? row[0] : new Date(row[0]),
        label: String(row[1] || ''),
        amount: Number(row[2]) || 0,
        note: String(row[3] || ''),
        accountType: String(row[4] || ''),
      };
    })
    .filter(function (entry) {
      return entry.amount > 0;
    });
}
