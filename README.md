# whats-claude-doing.gif

> Claude Code 在 think 啥？这套表情包替它回答。

![Pondering](stickers/pondering.gif)

朋友问"在干嘛"，丢一个 `Vibing…`。老板问"做完没"，丢一个 `Marinating…`。

---

## 161 个搞笑动词，从 Claude Code 二进制里直接抠出来

词不是我编的——`strings` 抠的 Claude Code 二进制：

```bash
strings $(which claude) | grep -E "^[A-Z][a-z]+ing$" | sort -u
```

从 `Pondering` 到 `Flibbertigibbeting`，从 `Crystallizing` 到 `Whatchamacalliting`，Anthropic 工程师埋的彩蛋一个不漏。

---

## 8 类高频场景，对号入座挑词

| 场景 | 用哪个 |
|---|---|
| 工作时装样子 | `Pondering` `Cogitating` `Architecting` |
| 摸鱼被抓 | `Vibing` `Lollygagging` `Doodling` |
| 拖延截稿 | `Marinating` `Puttering` `Dithering` |
| 加班破防 | `Churning` `Crunching` `Wrangling` |
| 不想说话 | `Simmering` `Ebbing` `Misting` |
| 大干一场 | `Catapulting` `Bootstrapping` `Forging` |
| 装神弄鬼 | `Enchanting` `Manifesting` `Prestidigitating` |
| 纯粹胡闹 | `Razzmatazzing` `Tomfoolering` `Boondoggling` |

懒得挑？上面 24 个推荐词 + 3 个完成态 PNG 已经打包在 [`essentials/`](essentials/)，一次下完就够日常用。

想看全的：完整 161 词分类词汇表在 [`vocabulary.md`](vocabulary.md)。

---

## 下载 stickers/ 直接发，统一 920×140 字号不会乱跳

161 个 GIF 全部在 [`stickers/`](stickers/) 目录，文件名就是词的小写。

```
stickers/pondering.gif
stickers/vibing.gif
stickers/whatchamacalliting.gif
...
```

每张都是 **920×140 透明底**，统一尺寸——发到聊天里字号一致，不会一个大一个小。

支持微信、Telegram、iMessage、Discord、Slack 全平台。

---

## 配一组灰色 PNG，任务做完发收尾

任务结束发 `✻ Cooked for 58s` 这种灰色完成态。`stickers/` 里有 3 个示例：

| 文件 | 效果 |
|---|---|
| `stickers/cooked_for_58s.png` | `✻ Cooked for 58s` |
| `stickers/brewed_for_8m_43s.png` | `✻ Brewed for 8m 43s` |
| `stickers/recap.png` | `※ recap:` |

灰色字、静态 PNG、透明底，同样 920×140。

---

## 微信表情包专用版 240×60，直接拖进收藏

微信表情包对图片尺寸敏感——长矩形（920×140）导入后字会被缩很小。`wechat/` 文件夹是同样 161 个 GIF + 3 个完成态 PNG 的微信优化版：

- **240×60 横版**（微信表情包单边上限 240，这个尺寸字号最大）
- **字号统一 25px**（长词降到 24px + 字间距压缩，保持视觉一致）
- **左对齐**，左侧边距 0
- **4 阶橙色调色板假抗锯齿**（针对浅色聊天底色优化，深色模式会有微弱白边）

直接下载 [`wechat/`](wechat/) 目录里的文件，加入微信表情收藏即可。

---

## 一行命令出新词，自定义任何场景

`gen.py` 就是一个 CLI。

```bash
# 橙色闪烁动画 GIF（thinking 状态）
python3 gen.py gif Pondering
python3 gen.py gif "Whirring"

# 灰色静态 PNG（completed 状态）
python3 gen.py png "Cooked for 58s"
python3 gen.py png "Brewed for 8m 43s"
python3 gen.py png "recap:" --star ※

# 自定义路径
python3 gen.py gif Vibing -o ~/Desktop/vibing.gif

# 微信表情包版本 240×60
python3 gen.py wx Pondering
python3 gen.py wx "Cooked for 58s" --kind png
python3 gen.py wx "recap:" --kind png --star ※
```

依赖：`pip install Pillow numpy`。字体走 macOS 自带的 Menlo + Apple Symbols。

---

## 做这套表情包搞清楚的 5 件事

**1. 真实 spinner 序列**

Claude Code 那个星号不是简单旋转，是从无到有再到无的形态渐变：

```
· → ✢ → ✳ → ✶ → ✻ → ✽ → ✻ → ✶ → ✳ → ✢  (然后回到 ·)
```

10 帧首尾相接，2 秒一个完整周期。

**2. 像素重心对齐**

不同星形字符在字体里的位置差太多（`∗` 整体贴底，`·` 集中在中央，`✻` 占满字符 box），直接渲染上下乱跳。

用 `numpy` 算每个字符的**像素质量重心**（pixel-weighted centroid），偏移到同一锚点。这样视觉中心锁死，肉眼看不出抖。

**3. 颜色用 Claude 品牌橙 `#D97757`**

不是常见的亮橙 `#FF8C00`，是 Anthropic 品牌库里那个偏赤陶色的暖橙。

**4. 统一画布 920×140**

最长的词 `Whatchamacalliting` 占 912px，所有词补到 920。这样发到聊天里字号一致——否则短词被聊天软件放大、长词被缩小，看起来字号忽大忽小。

**5. 1-bit 透明 GIF + supersample**

GIF 只支持 1 位透明（要么完全透明要么不透明），抗锯齿边缘会变成空心字。3× supersample 渲染后下采样，再用 alpha 阈值二值化，得到边缘比较顺滑的透明 GIF。

---

## MIT 协议，词汇属于 Anthropic 工程师的脑洞

代码 MIT。词汇表版权属于 Anthropic 工程师的彩蛋，本仓库只是把它做成了能发的图。

Claude Code 是 Anthropic 的产品，这个项目和 Anthropic 无关。
