import httpx
from django.conf import settings
from accounts.models import SocialNetwork
from authlib.integrations.httpx_client import OAuth1Auth


def post_to_misskey(domain, token, content, files=None):
    with httpx.Client() as client:
        media_ids = []
        file_detail = []

        if files:
            for f in files:
                r = client.post(f'https://{domain}/api/drive/files/create', data={'i': token}, files={'file': f},
                               headers={
                                   'user-agent': 'fedicross/0.1',
                               }, timeout=1800)
                result = r.json()
                media_ids.append(result['id'])
                file_detail.append(result['thumbnailUrl'])

        data = {'text': content, 'i': token}
        if len(media_ids) > 0:
            data['fileIds'] = media_ids
        r = client.post(f'https://{domain}/api/notes/create',
                       json=data,
                       headers={
                           'user-agent': 'fedicross/0.1',
                       })
        result = r.json()['createdNote']

        return file_detail, result['id']


def post_to_mstdn(domain, token, content, files=None):
    with httpx.Client() as client:
        media_ids = []
        file_detail = []

        if files:
            for f in files:
                r = client.post(f'https://{domain}/api/v1/media', files={'file': f},
                               headers={
                                   'Authorization': f'Bearer {token}',
                                   'user-agent': 'fedicross/0.1',
                               }, timeout=1800)
                result = r.json()
                media_ids.append(result['id'])
                file_detail.append(result['preview_url'])

        r = client.post(f'https://{domain}/api/v1/statuses',
                       data={'status': content, 'media_ids[]': media_ids, 'visibility': 'direct'},
                       headers={
                           'Authorization': f'Bearer {token}',
                           'user-agent': 'fedicross/0.1',
                       })
        result = r.json()

        return file_detail, result['id']


def post_to_plurk(auth, content, file_detail, toot_url, is_sensitive=False):
    with httpx.Client() as client:
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
            token=auth.oauth_token,
            token_secret=auth.oauth_token_secret,
        )
        post_url = 'https://www.plurk.com/APP/Timeline/plurkAdd'
        uri, headers, body = cauth.sign(
            'POST',
            post_url,
            {'Content-Type': 'application/x-www-form-urlencoded'},
            {'content': post_content, 'qualifier': 'says'}
        )
        resp = client.post(uri, headers=headers, data=body, timeout=300)
        if resp.status_code == 200:
            return True, resp.text
        else:
            return False, resp.text


def crosspost(request, data, files=None):
    success = []
    fail = []
    detail = []

    user = request.user
    software = request.user.app.software
    username, domain = user.username.split('@')
    content = data['content']
    if software == 'misskey':
        file_detail, toot_id = post_to_misskey(domain, user.access_token, content, files)
        toot_url = f'https://{domain}/notes/{toot_id}'
    else:
        file_detail, toot_id = post_to_mstdn(domain, user.access_token, content, files)
        toot_url = f'https://{domain}/@{username}/{toot_id}'

    obj = user.socialaccount_set.all()
    plurk = obj.filter(social_network=SocialNetwork.PLURK)
    if plurk:
        result, err = post_to_plurk(plurk[0], content, file_detail, toot_url)
        if result:
            success.append('Plurk')
        else:
            fail.append('Plurk')
        if err:
            detail.append(err)
    return success, fail, detail


