# whats-claude-doing.gif

> Claude Code 在 think 啥？这套表情包替它回答。

![Pondering](essentials/pondering.gif)

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

懒得挑？上面 24 个推荐词 + 3 个长得离谱的字典词（`Flibbertigibbeting` / `Hullaballooing` / `Whatchamacalliting`）+ 3 个完成态 PNG，**全部 240×60 微信表情包规格**已打包在 [`essentials/`](essentials/)，一次下完直接拖进微信收藏。

想看全的：完整 161 词分类词汇表在 [`vocabulary.md`](vocabulary.md)。

---

## 微信表情包专用版 240×60，是这套图的正式版

微信表情包对图片尺寸敏感——长矩形导入后字会被缩小。这套图的**正式版本就是 240×60 微信优化版**，单边贴 240（微信表情包单边上限），字号最大化：

- **240×60 横版透明底**
- **字号统一 25px**（长词降到 24px + 字间距压缩，保持视觉一致）
- **左对齐**，左侧边距 0
- **4 阶橙色调色板假抗锯齿**（针对浅色聊天底色优化，深色模式会有微弱白边）

全套 161 GIF + 3 完成态 PNG 在 [`WeChat stickers/`](WeChat%20stickers/) 目录，直接拖进微信表情收藏。

---

## 配一组灰色 PNG，任务做完发收尾

任务结束发 `✻ Cooked for 58s` 这种灰色完成态。`essentials/` 和 `WeChat stickers/` 里各有 3 个示例：

| 文件 | 效果 |
|---|---|
| `cooked_for_58s.png` | `✻ Cooked for 58s` |
| `brewed_for_8m_43s.png` | `✻ Brewed for 8m 43s` |
| `recap.png` | `※ recap:` |

灰色字、静态 PNG、透明底，同样 240×60。

---

## 一行命令出新词，自定义任何场景

`gen.py` 就是一个 CLI。

```bash
# 微信表情包版本 240×60（推荐）
python3 gen.py wx Pondering
python3 gen.py wx "Cooked for 58s" --kind png
python3 gen.py wx "recap:" --kind png --star ※

# 原始 920×140 长矩形（高分辨率版本，给设计师/打印）
python3 gen.py gif Pondering
python3 gen.py png "Cooked for 58s"

# 自定义路径
python3 gen.py wx Vibing -o ~/Desktop/vibing.gif
```

依赖：`pip install Pillow numpy`。字体走 macOS 自带的 Menlo + Apple Symbols。

原始 920×140 版本（高分辨率，给设计师二次创作用）也在仓库里：[`raw stickers 920x140/`](raw%20stickers%20920x140/)。

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

**4. 长词字间距压缩**

最长的词 `Whatchamacalliting`、`Flibbertigibbeting` 18 字符，240 宽度装不下原字号。降字号到 24px + 字间距收紧（最多 -3.58 px/字符），让所有 161 词都能单行装进 240×60。

**5. 假抗锯齿调色板**

GIF 只支持 1 位透明，边缘强行二值化后是空心字。这套图的调色板里放了 3 阶橙色（橙色 → 70% 橙混底 → 40% 橙混底），边缘像素按透明度分配不同阶，跟浅色聊天底色融合后视觉上接近抗锯齿。

---

## MIT 协议，词汇属于 Anthropic 工程师的脑洞

代码 MIT。词汇表版权属于 Anthropic 工程师的彩蛋，本仓库只是把它做成了能发的图。

Claude Code 是 Anthropic 的产品，这个项目和 Anthropic 无关。
