# HoloPet — Blue Maid Lite / 蓝毛女仆精简版

Fork of [chicochol/dsh-holopet](https://github.com/chicochol/dsh-holopet), based on upstream 583123d.

## 精简内容

- 仅保留蓝毛女仆 114 个标准速度动作、114 个 B 页小动画、3 个标准速度镜像，以及字体、音效和运行模块。
- 移除鲸鱼娘（含旧版回退资源）、快慢速度 GIF 和对应镜像。安装文件从约 61.23 MiB 减少到约 27.11 MiB。
- 默认皮肤 pc2005，旧配置迁移到标准速度；旧皮肤动作配置清空。
- 修正走动/转身列表重复追加；保留 SELECT/HOME 退出，忽略断开的手柄残留状态。
- 资源按当前应用 ID 定位，网页重启不再写死 dsh_fish。
- 中英文 info.html 内嵌原始 main.png 的 Base64 data URI，无外部资源依赖。

## 架构与安装

DSH Desktop 插件（Node.js）监听任务事件，通过局域网 HTTP/SSE 推送状态；设备端 Lua/LVGL 播放 SD 卡本地 GIF。

1. 在 DSH 中安装启用 dsh-pet-holocubic 插件，默认端口 17890。
2. 将 app/ **内部文件**复制到 /sd/apps/dsh_fish/，重扫并启动。
3. 打开设备 /dsh_fish/ 配置页，填写 DSH 电脑的局域网 IP。仅用于可信局域网，不要暴露到公网。

支持安装到 /sd/apps/<id>/，配置页为 /<id>/。
左右倾斜/方向键切换两页；设备 HOME 短按退出。手柄需要 hidpad 服务发布 ble-main，SELECT=4096、HOME=32768。

**升级：**覆盖上传不会清除旧文件。备份 config.lua、skin.json 等个人配置后，以精简包替换原应用资源；不要删除全局 /sd/apps/settings.json。

## 验证与打包

- python tools/test_slim.py （需要 lupa）
- powershell -File tools/build_slim.ps1 （输出 dist/dsh_fish-1.5.1.zip）

## English

This fork ships only Blue Maid at normal speed, retaining all 114 actions, B-page thumbnails and movement mirrors. Whale assets and fast/slow variants are removed. Existing settings migrate to pc2005/normal. Copy app contents to /sd/apps/<id>/ and configure the DSH host at /<id>/. Device HOME and connected gamepad SELECT/HOME exit. Replace old resources to reclaim storage when upgrading.

## License

Code: GPL-3.0. Blue Maid assets: CC BY-NC-SA 4.0 (**non-commercial**). Framework and font notices retain their licenses. See LICENSE and CREDITS.md. Historical whale attribution remains for provenance; those assets are no longer shipped.
