# Daily_Fudan
> 本项目修改自：[k652/daily_fudan](https://github.com/k652/daily_fudan)

## 部署

### 1. 点击右上角`Fork`到自己的账号下, 将仓库默认分支设置为 master 分支

### 2. 添加 账号密码 至 Secrets

- 回到项目页面，依次点击`Settings`-->`Secrets`-->`New repository secret`

- 建立名为`UIS`的 secret，值为`学号`+`空格`+`密码`，最后点击`Add secret`

- 建立名为`EMAIL`的 secret，值为`发件邮箱`+`空格`+`密码`+`空格`+`收件邮箱`，最后点击`Add secret`
> 仅支持网易yeah.net邮箱, 其他邮箱请自行修改mail_host字段及端口

### 3. 启用 Actions

> Actions 默认为关闭状态，Fork 之后需要手动执行一次，若成功运行其才会激活。

返回项目主页面，点击上方的`Actions`，再点击左侧的`Daily Fudan`，再点击`Run workflow`
