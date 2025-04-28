## 這是什麼？
讓使用者可以在聯邦宇宙與社群網路同步發布貼文的系統。

## 支援的聯邦宇宙平台與社群網路
聯邦宇宙
- Mastodon
- Misskey（未測試能否支援其他分支）

社群網路
- Plurk

不支援X是因為免費API呼叫的限制，Facebook則是太容易被佐。

## 安裝
強烈建議透過Docker Compose。也可以直接使用我建置的服務。

複製這個 repo

`git clone https://github.com/ryanho/pyfedicross.git`

`cd pyfedicross`

`mkdir data; cp pyfedicross/.env.example ./data/.env`

根據需求修改 ./data/.env 的內容

```aiignore
DEBUG=off # Debug 模式
SECRET_KEY= # Django 的加密金鑰
ALLOWED_HOSTS= # 此服務綁定的網域，使用逗號分隔
DATABASE_URL=sqlite:///db.sqlite
TIME_ZONE=UTC # 時區
LANGUAGE_CODE=en-us # 語系
CACHE_URL=filecache:////tmp/django_cache # 快取位置，通常不需要更改
PLURK_CONSUMER_KEY= # Plurk 的 Oauth 金鑰
PLURK_CONSUMER_SECRET= # Plurk 的 Oauth 密鑰
CSRF_TRUSTED_ORIGINS= # 允許跨站存取的來源網址，使用逗號分隔，格式為 https://domain.tld
DRAMATIQ_BROKER_URL=localhost:6379 # 工作排程器使用的 redis 位址，通常不需要更改
```

修改 app.template，拿掉開頭的註解，把 .example.com 修改為符合上面 ALLOWED_HOSTS 的值。  

`#server_name .example.com;`


打包容器

`docker compose build`

啟動服務

`docker compose up -d`

## 使用
在fedicross首頁輸入要登入的實例網域（例如mastodon.social或misskey.io），確認要提供的權限並按下同意，接著會轉回fedicross首頁。

從網頁下方點擊要登入的社群網路（目前只支援Plurk），同樣也是確認要提供的權限並按下同意。

完成後就可以從上方的表單同步發布貼文到聯邦宇宙與社群網路。

## 使用Misskey的Webhook來同步發貼文到社群網路
如果登入的聯邦宇宙平台是Misskey，在首頁下方Misskey名稱的旁邊會出現一個齒輪圖示，點擊可以設置webhook secret與取得webhook url。

取得webhook secret與url後，到Misskey頁面上，點擊左邊選單的「設定/其他設定/Webhook」，點擊「建立webhook」，名稱可以輸入「fedicross」，然後輸入剛剛取得的secret與url。在「何時運行webhook」，只打開「當發布貼文時」這個選項，其他關閉。到此就設定完成，之後可以在此開啟或關閉webhook。

啟用Webhook後會停用fedicross首頁上方的表單，因為可以在登入的Misskey站台直接同步發布。

在什麼情況會同步發布：發布新貼文、轉發與引用有附件的貼文或引用無附件的貼文但有加上自己的內容，符合前述條件而且可見性是「公開」。

只要貼文使用內容警告或媒體檔案有設定敏感，就會使用Plurk的「成人內容」設定。