from authlib.integrations.httpx_client import OAuth1Auth
import httpx
from django.conf import settings
import dramatiq


@dramatiq.actor
def post_to_plurk(auth, content, file_detail, toot_url):
    mstdn_content = ''
    if file_detail:
        for i in file_detail:
            mstdn_content += f' {i}'
    mstdn_content += f' \n\n{toot_url}'
    #if len(content) > 360:
    #    mstdn_content = '... ' + mstdn_content
    #max_length = 360 - len(mstdn_content)
    content = content + mstdn_content
    cauth = OAuth1Auth(
        settings.PLURK_CONSUMER_KEY,
        settings.PLURK_CONSUMER_SECRET,
        token=auth.oauth_token,
        token_secret=auth.oauth_token_secret,
    )
    post_url = 'https://www.plurk.com/APP/Timeline/plurkAdd'
    uri, headers, body = cauth.sign(
        'POST',
        post_url,
        {'Content-Type': 'application/x-www-form-urlencoded'},
        {'content': content, 'qualifier': 'says'}
    )
    resp = httpx.post(uri, headers=headers, data=body, timeout=300)
    if resp.status_code == 200:
        return True, resp.text
    else:
        return False, resp.text