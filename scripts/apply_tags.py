#!/usr/bin/env python3
"""One-off: tag the untagged posts and normalise the tag vocabulary.

Dropping the categories taxonomy left tags as the only cross-cutting way to
move between posts, but 25 of 39 posts had none — and the 14 that did had
split spellings (NVIDIA/Nvidia, AI 基础设施/AI基础设施/AI-Infrastructure) that
fragment the tag index into near-duplicate terms.

Run once from the repo root, then delete.
"""

import re
import sys
from pathlib import Path

ROOT = Path("content/posts")

# Existing spelling -> canonical spelling. Anything mapped to None is dropped
# for being too generic to aid navigation.
NORMALISE = {
    "AI-Infrastructure": "AI 基础设施",
    "AI基础设施": "AI 基础设施",
    "Nvidia": "NVIDIA",
    "Silicon-Photonics": "硅光",
    "Networking": "光网络",
    "光学网络": "光网络",
    "Coding Agents": "Coding Agent",
    "Invest": "投资",
    "供应链": "供应链",
    "AI": None,          # every post here is about AI
    "Analysis": None,    # says nothing
    "技术分析": None,
}

# Post slug -> tags. Chinese for concepts, English for proper nouns.
TAGS = {
    "infra/edge-deploy-survey": ["边缘计算", "模型部署", "推理优化"],
    "infra/nvlink-fusion": ["NVIDIA", "NVLink", "互连", "AI 基础设施"],
    "infra/server-cooling-evolution": ["液冷", "数据中心", "散热", "供应链"],
    "research/applovin": ["AppLovin", "广告", "投资"],
    "research/compile-to-generate": ["LLM", "应用形态", "产品设计"],
    "research/cursor-analysis": ["Cursor", "Coding Agent", "投资"],
    "research/nber-ai-agent-survey": ["Agent", "经济影响", "研究报告"],
    "solutions/rag-platform": ["RAG", "平台架构"],
    "solutions/search-recommendation-ads": ["搜广推", "推荐系统", "系统设计"],
    "tech/ai-hallucination": ["幻觉", "LLM", "Agent"],
    "tech/ai-replace-human": ["就业", "经济影响", "AI 与社会"],
    "tech/amd-silicon-photonics-acquisition": ["AMD", "硅光", "并购"],
    "tech/apple-intelligence-2025": ["Apple", "端侧 AI"],
    "tech/apple-wwdc-2025": ["Apple", "WWDC"],
    "tech/broadcom-nvidia-ai-cost": ["Broadcom", "NVIDIA", "AI 成本", "投资"],
    "tech/computex-2025-takeaways": ["Computex", "台湾", "AI 芯片"],
    "tech/copper-fever": ["铜", "大宗商品", "投资"],
    "tech/deepmind-hassabis-interview": ["Google", "DeepMind", "AGI"],
    "tech/deepseek-domestic-chips": ["DeepSeek", "国产芯片", "大模型"],
    "tech/meta-smart-glasses": ["Meta", "智能眼镜", "并购"],
    "tech/mistral-ai-update": ["Mistral AI", "开源模型"],
    "tech/openai-o3-pro": ["OpenAI", "推理模型"],
    "tech/qwen3-next-80b-deep-dive": ["Qwen", "MoE", "模型结构", "推理优化"],
    "tech/tesla-robotaxi-launch": ["Tesla", "自动驾驶", "Robotaxi"],
    "tech/vision-pro-2": ["Apple", "Vision Pro", "空间计算"],
}

TAGS_LINE = re.compile(r"^tags:\s*\[(.*)\]\s*$", re.MULTILINE)


def fmt(tags: list[str]) -> str:
    return "tags: [" + ", ".join(f'"{t}"' for t in tags) + "]"


def main() -> int:
    if not ROOT.exists():
        print("run from the repo root", file=sys.stderr)
        return 2

    added = normalised = 0

    for path in sorted(ROOT.rglob("index.md")):
        slug = str(path.parent.relative_to(ROOT))
        text = path.read_text(encoding="utf-8")
        m = TAGS_LINE.search(text)

        if m:
            current = [t.strip().strip('"\'') for t in m.group(1).split(",")]
            current = [t for t in current if t]
            out: list[str] = []
            for t in current:
                canon = NORMALISE.get(t, t)
                if canon and canon not in out:
                    out.append(canon)
            if out != current:
                path.write_text(text[: m.start()] + fmt(out) + text[m.end():], encoding="utf-8")
                print(f"  normalise {slug}: {current} -> {out}")
                normalised += 1
            continue

        if slug not in TAGS:
            continue

        # Insert tags just before the closing front-matter delimiter.
        end = text.index("\n---", 4)
        path.write_text(text[:end] + "\n" + fmt(TAGS[slug]) + text[end:], encoding="utf-8")
        print(f"  tag {slug}: {TAGS[slug]}")
        added += 1

    print(f"\ntagged {added}, normalised {normalised}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
