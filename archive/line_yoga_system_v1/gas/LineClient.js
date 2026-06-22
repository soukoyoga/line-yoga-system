/**
 * LINE Messaging API
 */
function replyText_(ctx, message) {
  const url = 'https://api.line.me/v2/bot/message/reply';
  UrlFetchApp.fetch(url, {
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      Authorization: 'Bearer ' + ctx.token,
    },
    payload: JSON.stringify({
      replyToken: ctx.replyToken,
      messages: [{ type: 'text', text: message }],
    }),
    muteHttpExceptions: true,
  });
}

function replyQuickReply_(ctx, text, options) {
  const items = options.map(function (opt) {
    const label = typeof opt === 'string' ? opt : opt.label;
    const data = typeof opt === 'string' ? opt : opt.data;
    return {
      type: 'action',
      action: {
        type: 'postback',
        label: label,
        data: data,
        displayText: label + 'を入力します',
      },
    };
  });

  const url = 'https://api.line.me/v2/bot/message/reply';
  UrlFetchApp.fetch(url, {
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      Authorization: 'Bearer ' + ctx.token,
    },
    payload: JSON.stringify({
      replyToken: ctx.replyToken,
      messages: [
        {
          type: 'text',
          text: text,
          quickReply: { items: items },
        },
      ],
    }),
    muteHttpExceptions: true,
  });
}

function linkRichMenu_(userId, richMenuId, token) {
  const url =
    'https://api.line.me/v2/bot/user/' + userId + '/richmenu/' + richMenuId;
  const res = UrlFetchApp.fetch(url, {
    method: 'post',
    headers: { Authorization: 'Bearer ' + token },
    muteHttpExceptions: true,
  });
  const code = res.getResponseCode();
  const body = res.getContentText();
  console.log('メニュー切り替え [' + richMenuId + '] HTTP ' + code + ': ' + body);
  return code === 200;
}
