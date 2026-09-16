# WeChat Link to Markdown for Codex

把公开的微信公众号文章链接交给 Codex，通过用户自己的 Chrome 会话读取原文，并保存为带本地图片的 Markdown 文档。

## 能力

- 接受公开的 `https://mp.weixin.qq.com/...` 文章链接。
- 保存经过校验的原文 Markdown，而不是搜索摘要或转载内容。
- 下载正文图片到本地 `images/` 目录。
- 遇到微信验证页时停止并提示用户在 Chrome 中完成验证。
- 在 Codex 中根据请求自动触发，也支持显式调用 `$wechat-link-to-markdown`。

## 前置条件

- Codex Desktop、Codex CLI 或 Codex IDE 扩展。
- Chrome。
- Node.js 20 或更高版本。
- Python 3.10 或更高版本。
- [OpenCLI Browser Bridge Chrome 扩展](https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk)。

本项目会安装并调用 [`@jackwener/opencli`](https://github.com/jackwener/opencli)，文章访问发生在用户自己的 Chrome 会话中。

## 安装

从仓库的 `dist/` 目录下载对应系统的压缩包并解压。

### Windows

在解压后的目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1
```

### macOS

在解压后的目录运行：

```bash
chmod +x install-macos.sh
./install-macos.sh
```

随后安装并启用 OpenCLI Chrome 扩展，保持 Chrome 打开，并运行：

```text
opencli doctor
```

看到 Browser Bridge 已连接即表示环境正常。Codex 通常会自动发现新 Skill；如果没有出现，重启一次 Codex。

## 使用

直接向 Codex 发送：

```text
把这篇公众号文章保存为原文 Markdown：
https://mp.weixin.qq.com/s/...
```

也可以说“保存后解析”“只归档原文”或显式使用：

```text
$wechat-link-to-markdown 把这个链接保存为原文 Markdown：<链接>
```

默认输出到当前工作区的：

```text
公众号原文/
└── 文章标题/
    ├── 文章标题.md
    └── images/
```

## 验证

Skill 会要求结果同时满足：

- `verified_original` 为 `true`；
- Markdown 包含足够的正文内容；
- 文档保留 `mp.weixin.qq.com` 来源链接；
- 内容不是登录、验证码或环境异常页面。

