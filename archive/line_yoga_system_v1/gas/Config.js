/**
 * 設定・定数（変更はここだけ）
 */
const CONFIG = {
  SHEET: {
    LEDGER: 'シート1',
    DEBT_NAMES_RANGE: 'P2:P4',
    DEBT_BALANCE_COL: 19,
  },

  RESERVATION: {
    URL: 'https://docs.google.com/spreadsheets/d/1xmws_P9LDCT5fY8F_KM7_AG3qEUJsuaqwNT5BuYLsDg/edit#gid=0',
  },

  RICH_MENU: {
    KAKEIBO: 'richmenu-a7f6bd0e0af5d1c0b7ad2a2853bf60a2',
    BUSINESS: 'richmenu-23f64c5287fbc132a90f784b5e65a48a',
  },

  RICH_MENU_IMAGE: {
    KAKEIBO: '18UmfmlMJFSIHWvVQULH9ytlZ3cim-F8k',
    BUSINESS: '1qki1_QyKHFMJbIvxBfdXB8LSjGBCYsX9',
  },

  RICH_MENU_MARKERS: {
    KAKEIBO: [
      '食費・外食入力',
      '娯楽・通信入力',
      '日用品・水ガス入力',
      '返済・貯金入力',
      '家計レポート',
    ],
    BUSINESS: [
      '売上入力',
      '経費入力',
      '予約確認',
      'ビジネス速報',
      'ビジネス詳細レポート',
    ],
  },

  MENU_SWITCH: {
    TO_KAKEIBO: '家計簿メニュー',
    TO_BUSINESS: 'ビジネスメニュー',
    POSTBACK_TO_KAKEIBO: 'switch_to_kakeibo',
    POSTBACK_TO_BUSINESS: 'switch_to_business',
  },

  ACCOUNT_TYPE: {
    PRIVATE: 'プライベート',
    REVENUE: '売上',
    EXPENSE: '経費',
    REPAYMENT: '返済',
  },

  REVENUE_LABELS: ['ヨガ', '古着', 'プログラミング', 'アルバイト', 'その他'],
  EXPENSE_LABELS: ['会場費', '交通費', '備品・消耗品', '広告費', '経費'],

  KAKEIBO_GROUPS: {
    '食費・外食入力': ['食費', '外食'],
    '娯楽・通信入力': ['娯楽費', '通信費'],
    '日用品・水ガス入力': ['日用品', '水ガス電気'],
  },

  SAVINGS_LABEL: '貯金',
  REPAYMENT_CHOICE_LABEL: '返済',
  OTHER_REPAYMENT_LABEL: 'その他',
  REPAYMENT_SUB_OPTIONS: ['想ちゃん', '奨学金', 'その他'],

  BUSINESS_GROUPS: {
    '売上入力': ['ヨガ', '古着', 'プログラミング', 'アルバイト', 'その他'],
  },

  COMMANDS: {
    REVENUE_INPUT: '売上入力',
    EXPENSE_INPUT: '経費入力',
    DEBT_INPUT: '返済・貯金入力',
    KAKEIBO_REPORT: '家計レポート',
    BIZ_QUICK: 'ビジネス速報',
    BIZ_DETAIL: 'ビジネス詳細レポート',
    RESERVATION_CHECK: '予約確認',
  },

  USER_STATE_KEY: {
    LAST_CATEGORY: 'LAST_CATEGORY',
    EXPENSE_DIRECT: 'EXPENSE_DIRECT',
  },

  MESSAGES: {
    MENU_SWITCH_NOTE:
      '（※画像が変わらない場合は、一度トーク一覧に戻ってから開き直してください）',
    ASK_AMOUNT: function (category) {
      return '【' + category + '】の金額を入力してください。';
    },
    ASK_REVENUE_AMOUNT: function (category) {
      return (
        '【' +
        category +
        '】金額と備考を入力してください。\n例: 30000 パーソナル'
      );
    },
    ASK_EXPENSE_AMOUNT:
      '【経費】金額と内容を入力してください。\n例: 4500 ヨガ場所代',
    NO_CATEGORY:
      '先にメニューから項目を選ぶか、「食費 1000」「外食 3500 〇〇カフェ」のように送ってください。',
    INVALID_AMOUNT:
      '金額を正しく入力してください（例: 1000 または 外食 3500 備考）。',
    INVALID_EXPENSE_INPUT:
      '金額と内容を入力してください（例: 4500 ヨガ場所代）',
    EXPENSE_NEED_CONTENT:
      '内容も入力してください（例: 4500 ヨガ場所代）',
    UNKNOWN:
      'メニューのボタンから操作するか、「家計簿メニュー」「ビジネスメニュー」で切り替えてください。',
  },
};
