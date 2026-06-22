/**
 * ユーザーごとの状態（直前カテゴリなど）
 */
function getLastCategory_() {
  return PropertiesService.getUserProperties().getProperty(
    CONFIG.USER_STATE_KEY.LAST_CATEGORY
  );
}

function setLastCategory_(category) {
  PropertiesService.getUserProperties().setProperty(
    CONFIG.USER_STATE_KEY.LAST_CATEGORY,
    category
  );
}

function isExpenseDirectMode_() {
  return (
    PropertiesService.getUserProperties().getProperty(
      CONFIG.USER_STATE_KEY.EXPENSE_DIRECT
    ) === '1'
  );
}

function setExpenseDirectMode_(enabled) {
  PropertiesService.getUserProperties().setProperty(
    CONFIG.USER_STATE_KEY.EXPENSE_DIRECT,
    enabled ? '1' : '0'
  );
}

function clearExpenseDirectMode_() {
  setExpenseDirectMode_(false);
}
