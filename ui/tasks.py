from authlib.integrations.httpx_client import OAuth1Auth
import httpx
from django.conf import settings
import dramatiq


@dramatiq.actor
def post_to_plurk(auth, content, file_detail, toot_url, is_sensitive=False):
    mstdn_content = ''
    if file_detail:
        for i in file_detail:
            mstdn_content += f' {i}'
    mstdn_content += f'\n\n{toot_url}'

    # plurk的url以31個字元計算，在貼文中前面會加上一個空白，所以是32
    plurk_url_length = 32
    # 33是toot_url的長度（31 + 2）
    url_length = len(file_detail) * plurk_url_length + 33
    content_length = len(content)
    total_length = content_length + url_length
    # plurk的內容長度限制是360個字元
    if total_length > 360:
        content_length = content_length - (total_length - 360 + 3)
        post_content = content[:content_length] + '...' + mstdn_content
    else:
        post_content = content + mstdn_content

    cauth = OAuth1Auth(
        settings.PLURK_CONSUMER_KEY,
        settings.PLURK_CONSUMER_SECRET,
        token=auth['oauth_token'],
        token_secret=auth['oauth_token_secret'],
    )
    post_url = 'https://www.plurk.com/APP/Timeline/plurkAdd'
    uri, headers, body = cauth.sign(
        'POST',
        post_url,
        {'Content-Type': 'application/x-www-form-urlencoded'},
        {'content': content, 'qualifier': 'says', 'porn': is_sensitive}
    )
    resp = httpx.post(uri, headers=headers, data=body, timeout=300)
    if resp.status_code == 200:
        return True, resp.text
    else:
        return False, resp.text