## 這是什麼？
讓使用者可以在聯邦宇宙與社群網路同步發布貼文的系統。

## 支援的聯邦宇宙平台與社群網路
聯邦宇宙
- Mastodon
- Misskey（未測試能否支援其他分支）

社群網路
- Plurk（API不支援發布限制級的貼文）

不支援X是因為免費API呼叫的限制，Facebook則是太容易被佐。

## 安裝
強烈建議透過Docker Compose。也可以直接使用我建置的服務。

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