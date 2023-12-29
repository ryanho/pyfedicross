import json

import httpx
from django.conf import settings
from accounts.models import SocialNetwork
from api.models import PostArticleLog
from api.utils import get_ip_address
from authlib.integrations.httpx_client import OAuth1Auth
from requests_oauthlib import OAuth1Session
# import pytumblr


def post_to_mstdn(domain, token, content, files=None):
    media_ids = []
    file_detail = []
    if files:
        for f in files:
            r = httpx.post(f'https://{domain}/api/v1/media', files={'file': f},
                           headers={
                               'Authorization': f'Bearer {token}',
                               'user-agent': 'social-crosspost/0.1',
                           }, timeout=1800)
            result = r.json()
            media_ids.append(result['id'])
            file_detail.append(result)

    r = httpx.post(f'https://{domain}/api/v1/statuses',
                   data={'status': content, 'media_ids[]': media_ids, 'visibility': 'direct'},
                   headers={
                       'Authorization': f'Bearer {token}',
                       'user-agent': 'social-crosspost/0.1',
                   })
    result = r.json()

    return file_detail, result['id']


def post_to_plurk(auth, content, file_detail, toot_url):
    mstdn_content = ''
    if file_detail:
        for i in file_detail:
            mstdn_content += f' {i["preview_url"]}'
    mstdn_content += f' \n\n查看原文 {toot_url}'
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


# def post_to_twitter(auth, content, file_detail, toot_url):
#     mstdn_content = ''
#     if file_detail:
#         for i in file_detail:
#             mstdn_content += f' {i["preview_url"]}'
#     mstdn_content += f' \n\n查看原文 {toot_url}'
#     if len(content) > 280:
#         mstdn_content = '... ' + mstdn_content
#     max_length = 280 - len(mstdn_content)
#     content = content[:max_length] + mstdn_content
#     client = OAuth1Session(
#         settings.TWITTER_CONSUMER_KEY,
#         settings.TWITTER_CONSUMER_SECRET,
#         resource_owner_key=auth.oauth_token,
#         resource_owner_secret=auth.oauth_token_secret,
#     )
#     post_url = 'https://api.twitter.com/2/tweets'
#     payload = {'text': content}
#     resp = client.post(post_url, json=payload)
#     if resp.status_code == 201:
#         return True, resp.text
#     else:
#         print(f"Request returned an error: {resp.status_code} {resp.text}")
#         return False, resp.text


# def post_to_tumblr(auth, content, file_detail, toot_url):
#     client = pytumblr.TumblrRestClient(
#         settings.TUMBLR_CONSUMER_KEY,
#         settings.TUMBLR_CONSUMER_SECRET,
#         auth.oauth_token,
#         auth.oauth_token_secret,
#     )
#
#     body = f'{content}<br><a href="{toot_url}">查看原文</a><br>'
#
#     if file_detail:
#         for f in file_detail:
#             body += f'<img src={f["preview_url"]}><br>'
#
#     r = client.create_text(
#         auth.pref["blog_identifier"],
#         state="published",
#         body=body,
#         format='html'
#     )
#
#     if r['state'] == 'published':
#         return True, json.dumps(r)
#     else:
#         return False, json.dumps(r)


def crosspost(request, data, files=None, api=False):
    success = []
    fail = []
    detail = []

    user = request.user
    username, domain = user.username.split('@')
    user_ip = get_ip_address(request)
    if api:
        content = data.content
        file_detail = data.file_detail
        toot_id = data.toot_id
    else:
        content = data['content']
        file_detail, toot_id = post_to_mstdn(domain, user.mastodon_token, content, files)
    toot_url = f'https://{domain}/@{username}/{toot_id}'

    obj = user.socialaccount_set.all()
    plurk = obj.filter(social_network=SocialNetwork.PLURK)
    if plurk:
        result, err = post_to_plurk(plurk[0], content, file_detail, toot_url)
        if result:
            PostArticleLog(user=user, ip_addr=user_ip, account=plurk[0].detail['name'],
                           network=SocialNetwork.PLURK, detail=result)
            success.append('Plurk')
        else:
            fail.append('Plurk')
        if err:
            detail.append(err)

    # twitter = obj.filter(social_network=SocialNetwork.TWITTER)
    # if twitter:
    #     result, err = post_to_twitter(twitter[0], content, file_detail, toot_url)
    #     if result:
    #         PostArticleLog(user=user, ip_addr=user_ip, account=twitter[0].detail['name'],
    #                        network=SocialNetwork.TWITTER, detail=result)
    #         success.append('Twitter')
    #     else:
    #         fail.append('Twitter')
    #     if err:
    #         detail.append(err)

    # tumblr = obj.filter(social_network=SocialNetwork.TUMBLR)
    # if tumblr:
    #     result, err = post_to_tumblr(tumblr[0], content, file_detail, toot_url)
    #     if result:
    #         PostArticleLog(user=user, ip_addr=user_ip, account=tumblr[0].detail['name'],
    #                        network=SocialNetwork.TUMBLR, detail=result)
    #         success.append('Tumblr')
    #     else:
    #         fail.append('Tumblr')
    #         detail.append('token失效，無法更新取得新的token')
    #     if err:
    #         detail.append(err)

    return success, fail, detail


