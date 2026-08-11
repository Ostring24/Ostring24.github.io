# 写作指南

这个站点的目标是：**你只管写，格式的事情交给脚本。**

不需要手写 front matter。标题、日期、摘要都会自动补全；忘了跑命令也没关系，
提交时的 git hook 会兜底。

---

## 最短路径

```bash
# 1. 开一篇新文章
make new S=tech SLUG=qwen3-deep-dive T="Qwen3-Next 模型深度解析"

# 2. 写。图片直接拖进那个文件夹，正文里写 ![说明](图片名.png)

# 3. 本地预览（含草稿）
make serve                  # http://localhost:1313

# 4. 发布：把 draft: true 改成 false，然后
make publish
```

`make publish` 之后 GitHub Actions 会自动构建并部署，大约 1–2 分钟上线。

不记得命令？直接敲 `make`，会列出全部。

---

## 四个栏目往哪放

| `S=` | 栏目 | 收什么 |
|------|------|--------|
| `infra` | Infrastructure | 数据中心、光互连、CPO/OCS、NVLink、液冷、边缘部署 |
| `tech` | Tech Watch | 模型、芯片、产品动向；技术拆解 |
| `research` | Research | 市场规模、竞争格局、个股、宏观 |
| `solutions` | Solutions | 偏工程的系统设计笔记 |

传错栏目名脚本会直接报错并列出合法值——这是刻意的，防止再长出无人访问的新栏目。

---

## Front matter 速查

`make new` 生成的模板长这样：

```yaml
---
title: "Qwen3-Next 模型深度解析"
date: 2026-08-11T16:04:26+08:00
draft: true
summary: ""
tags: []
---
```

| 字段 | 要不要手写 | 说明 |
|------|-----------|------|
| `title` | **自动** | `make new` 填好；也可以只在正文写 `# 标题`，脚本会提上来 |
| `date` | **自动** | 新文章用当前时间；老文章从 git 首次提交时间恢复 |
| `lastmod` | **自动** | 最后一次提交时间 |
| `summary` | **自动**（建议精修） | 自动取正文第一段。首页卡片显示的就是它，值得润色一下 |
| `draft` | 手动 | `true` 不上线。`make serve` 能看到，线上看不到 |
| `private` | 手动 | `true` 永不发布，连 `make serve` 都不显示。见下方 |
| `tags` | **建议手写** | 2–4 个。见下方词表 |
| `cover.image` | 可选 | 有封面图时写 |
| `aliases` | 极少用 | 改 URL 时保留旧链接 |

### 标题的两种写法，都不用管格式

**写法一**——用 `make new` 的 `T=` 参数，标题直接进 front matter：

```bash
make new S=tech SLUG=my-post T="我的标题"
```

**写法二**——front matter 里不写 title，正文顶部写 `# 我的标题`。
脚本会把它提到 front matter，**并从正文里删掉**（避免页面出现两个标题），
同时清理掉 `**加粗**` 和内嵌 HTML 这类脏东西。

> 站点原来 34 篇文章就是靠这个机制救回来的。曾经线上标题直接显示成
> `**苹果WWDC 2025 前瞻**`，星号裸奔。

---

## 不想发布的文章：`draft` 还是 `private`？

两种机制，区别只有一条：**你自己还看不看得到。**

| | 上线 | `make serve` 本地预览 | 用途 |
|---|:---:|:---:|---|
| `draft: true` | ❌ | ✅ **能看到** | 还没写完，想边写边预览 |
| `private: true` | ❌ | ❌ **也看不到** | 就是不打算发，只想留在仓库里 |

两者都不会产生页面、不进站内搜索、不进 RSS、不产生标签页。

```bash
# 直接创建一篇私密文章
./scripts/new-post.sh --private research my-notes "内部笔记"
```

或者给已有文章加一行：

```yaml
private: true
```

然后 `make sync`，脚本会自动展开成 Hugo 真正需要的形式：

```yaml
private: true
build:
  list: never
  render: never
```

> `private` 不是 Hugo 的内置字段，`build` 才是。写一行 `private: true` 就够了，
> 嵌套的 YAML 交给脚本，避免缩进写错导致文章意外上线。

**想改回发布**：删掉 `private: true` 和整个 `build` 块，再把 `draft` 设成 `false`。

### ⚠️ 「不发布」不等于「私密」

**这个 GitHub 仓库是公开的。** `private: true` 只是让文章不出现在网站上，
文件本身仍然可以被任何人在
`github.com/Ostring24/Ostring24.github.io` 里读到。

真正需要保密的内容，选一种：

1. **放在仓库外** —— 最简单可靠，比如 `~/notes/`
2. **加进 `.gitignore`** —— 文件留在本地，永远不推送（代价：换机器就没了，也没有备份）
3. **把仓库改成 private** —— 注意：从私有仓库发布 GitHub Pages 需要付费方案

---

## 图片

**规则只有一条：图片放在 `index.md` 旁边，正文里写文件名。**

```
content/posts/tech/my-post/
├── index.md
├── cover.png          ← 封面
└── arch.png           ← 正文图
```

```markdown
![架构图](arch.png)
```

不要写 `./`、不要写 `/images/`、不要放 `static/`。**直接写文件名。**

VS Code、Typora 拖拽粘贴图片的默认落点就是这里，无需配置。

封面图在 front matter 里声明：

```yaml
cover:
  image: "cover.png"
  alt: "封面说明"
```

> 为什么这样就行：每篇文章都是一个 Hugo **page bundle**（文件夹 + `index.md`），
> 同目录的图片自动成为 page resource，路径永远正确。
> 站点原来有 10 篇文章因为不是 bundle，图片全部 404。

外链图片（如 CSDN）也能用，但随时可能失效，建议下载到本地。

---

## Tags 词表

标签是现在**唯一**的跨栏目导航方式（`categories` 已移除，因为它和栏目完全重复）。
**尽量复用下面已有的标签**，不要造同义词——`NVIDIA` 和 `Nvidia` 会变成两个互不相通的页面。

**基础设施**
`AI 基础设施` · `数据中心` · `CPO` · `OCS` · `光网络` · `光通信` · `硅光` · `NVLink` · `互连` · `液冷` · `散热` · `边缘计算` · `供应链`

**芯片 / 存储**
`半导体` · `AI 芯片` · `国产芯片` · `HBM` · `DRAM` · `NAND` · `TSMC`

**模型 / AI**
`LLM` · `大模型` · `开源模型` · `推理模型` · `模型结构` · `MoE` · `推理优化` · `模型部署` · `Agent` · `Coding Agent` · `RAG` · `幻觉` · `端侧 AI` · `AGI` · `Tokenizer` · `AI 成本`

**公司**
`NVIDIA` · `AMD` · `Apple` · `Google` · `DeepMind` · `Meta` · `Tesla` · `OpenAI` · `Anthropic` · `DeepSeek` · `Qwen` · `Mistral AI` · `Broadcom` · `Cursor` · `AppLovin`

**投资 / 宏观**
`投资` · `宏观` · `M2` · `货币供应` · `中美对比` · `大宗商品` · `铜` · `广告` · `并购` · `经济影响` · `就业`

**其他**
`系统设计` · `搜广推` · `推荐系统` · `平台架构` · `自动驾驶` · `智能眼镜` · `空间计算` · `播客`

完整列表见 [/tags/](https://ostring24.github.io/tags/)。

避免用 `AI`、`技术`、`分析` 这种覆盖一切的词——等于没打标签。

---

## 全部命令

```bash
make                 # 帮助
make new S=… SLUG=… T="…"
make serve           # 本地预览，含草稿，改文件自动刷新
make sync            # 补齐所有缺失的 front matter
make check           # 只报告不修改（CI 用的就是它）
make build           # 生产构建到 public/
make publish         # sync + commit + push，触发自动部署
make publish M="自定义 commit message"
make clean
make install-hooks   # 启用 git hook（每个新 clone 需要跑一次）
```

---

## 自动化到底做了什么

**`make sync`（以及提交时的 hook）只补空缺，绝不覆盖你写的东西。**
跑一百遍结果都一样。

它会：

- 缺 `title` → 取正文第一个 `# `，清理格式，并从正文删掉那行
- 缺 `date` → 从 git 首次提交时间恢复（新文件用当天）
- 缺 `summary` → 取正文第一个真正的段落，在句号处截断
- 缺 `draft` → 补 `false`
- 正文 H1 和 title 重复 → 删掉正文那个

它**不会**自动生成 `tags`——自动打标签会产生大量近义词，反而毁掉标签体系。

> ⚠️ 它也**绝不碰 git 状态**。
> 老的 `add_frontmatter.py` 在每次构建后执行 `git restore content/posts`，
> 会静默删掉所有未提交的修改。那个脚本已经删除。

---

## 排错

**文章不显示**
1. `draft: true`？线上不显示草稿，`make serve` 才能看到
2. `private: true`？那是刻意的，连 `make serve` 都不会显示
3. `date` 是未来时间？`buildFuture = false`，未来日期的文章不会构建
4. 放在 `content/posts/<栏目>/<slug>/index.md` 了吗？文件名必须是 `index.md`

**构建报错 `The "_build" front matter key was deprecated`**
Hugo 0.145 起改名为 `build`。跑 `make sync` 会自动把 `_build:` 改成 `build:`。

**图片不显示**
1. 图片和 `index.md` 在同一个文件夹吗？
2. 正文里写的是纯文件名吗（`![](a.png)`，不是 `![](/a.png)` 或 `![](./img/a.png)`）？
3. 大小写对得上吗？macOS 本地不区分大小写，Linux 上的 CI 区分

**日期不对**
`date` 一旦写进文件就固定了。想改直接改 front matter，脚本不会覆盖。

**部署没反应**
1. 看 [Actions](https://github.com/Ostring24/Ostring24.github.io/actions)
2. 构建前会跑 `make check`，缺 front matter 会直接失败——本地先跑 `make check`
3. 只有推到 `main` 分支才会部署

**commit 被 hook 卡住**
`git commit --no-verify` 可以跳过一次。

---

## 新机器上 clone 之后

```bash
git clone --recurse-submodules git@github.com:Ostring24/Ostring24.github.io.git
cd Ostring24.github.io
make install-hooks
brew install hugo          # 需要 extended 版本
make serve
```

忘了 `--recurse-submodules` 的话：`git submodule update --init --recursive`。
主题是 submodule，没有它构建会缺少全部模板。
