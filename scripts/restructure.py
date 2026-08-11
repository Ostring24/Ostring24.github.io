#!/usr/bin/env python3
"""One-off: collapse 7 ad-hoc sections into 4 and make every post a page bundle.

Two problems are fixed at once:

1. Ten posts were a loose `foo.md` sitting next to their images. Hugo does not
   rewrite relative image paths for non-bundle pages, so `![](x.png)` on
   /posts/a/b/foo/ resolved to /posts/a/b/foo/x.png -> 404. Renaming the file
   to index.md turns the directory into a leaf bundle and the images become
   page resources that resolve correctly.

2. Sections were invented ad hoc (data_center, tech_news, invest, industry,
   solution, edge_computing, model) and only two were reachable from the nav.

Every moved post gets an `aliases` entry pointing at its old URL so existing
links keep working.

Run once, from the repo root. Delete afterwards.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path("content/posts")

# (source markdown, target section, target slug)
MOVES = [
    # ---------------------------------------------------------------- infra
    ("data_center/2026_0411_cpo_market_analysis/index.md", "infra", "cpo-market-analysis"),
    ("data_center/nvidia_fusion/nvdia_fusion.md", "infra", "nvlink-fusion"),
    ("data_center/server_cooling_evolution/server_cooling_evolution.md", "infra", "server-cooling-evolution"),
    ("edge_computing/edge_deploy_survey/index.md", "infra", "edge-deploy-survey"),
    ("ocs-deep-dive/index.md", "infra", "ocs-deep-dive"),
    ("scale-up-cpo-opportunities/index.md", "infra", "scale-up-cpo-opportunities"),

    # ----------------------------------------------------------------- tech
    ("tech_news/2025_0530_deepseek_newupdate/index.md", "tech", "deepseek-domestic-chips"),
    ("tech_news/2025_5takeaway_computex/2025_computex_5takeaway.md", "tech", "computex-2025-takeaways"),
    ("tech_news/2026-0422-how-gps-works/index.md", "tech", "how-gps-works"),
    ("tech_news/2026_0410_cpo_ubs_analysis/index.md", "tech", "cpo-ubs-analysis"),
    ("tech_news/2026_0418_claude_47_tokenizer_cost/index.md", "tech", "claude-tokenizer-cost"),
    ("tech_news/AI_illumination/A_illumination.md", "tech", "ai-hallucination"),
    ("tech_news/ai_agent/manus.md", "tech", "manus"),
    ("tech_news/ai_replace_human/index.md", "tech", "ai-replace-human"),
    ("tech_news/amd_buy_silicon_photonic_startup/index.md", "tech", "amd-silicon-photonics-acquisition"),
    ("tech_news/apple_intellegence_2025/apple_intellegence.md", "tech", "apple-intelligence-2025"),
    ("tech_news/apple_wwdc2025/16_Everything_Apple_Plans_to_Show_at_Its_iOS_26-Focus_zh.md", "tech", "apple-wwdc-2025"),
    ("tech_news/broadcomm_nvidia_compete/15_Big_Tech_Needs_a_Way_Out_of_Its_AI_Cost_Spiral._Th_zh.md", "tech", "broadcom-nvidia-ai-cost"),
    ("tech_news/cloud_storage/index.md", "tech", "cloud-storage-subscription"),
    ("tech_news/copper_fever/5_Copper_Fever_Is_Here._How_to_Play_It._zh.md", "tech", "copper-fever"),
    ("tech_news/google_deepmind_hassabis/3_The_Man_Who_A_G_I_-Pilled_Google_zh.md", "tech", "deepmind-hassabis-interview"),
    ("tech_news/meta_invest_EssilorLuxottica_smartglass/index.md", "tech", "meta-smart-glasses"),
    ("tech_news/mistral_ai/What_is_Mistral_AI__zh.md", "tech", "mistral-ai-update"),
    ("tech_news/openai_gpto3pro/gpto3_pro.md", "tech", "openai-o3-pro"),
    ("tech_news/tesla_robotaxi_launch/index.md", "tech", "tesla-robotaxi-launch"),
    ("tech_news/vision_pro2_latest/index.md", "tech", "vision-pro-2"),
    ("model/qwen3_next_80b_a3b_deepdive.md", "tech", "qwen3-next-80b-deep-dive"),
    ("lex-ffmpeg-podcast.md", "tech", "lex-ffmpeg-podcast"),

    # ------------------------------------------------------------- research
    ("invest/ai_agents/NBER_agent_suvery.md", "research", "nber-ai-agent-survey"),
    ("invest/ai_agents/the-coding-assistant-breakdown/index.md", "research", "coding-assistant-breakdown"),
    ("invest/cursor/cursor_analysis.md", "research", "cursor-analysis"),
    ("invest/m2_confusion.md/index.md", "research", "m2-confusion"),
    ("industry/2026_0409_ai_memory_market_boom/index.md", "research", "ai-memory-market-boom"),
    ("industry/2026_0409_cpo_trend_2026/index.md", "research", "cpo-trend-2026"),
    ("industry/2026_0416_cybersecurity_pow_shift/index.md", "research", "cybersecurity-pow-shift"),
    ("industry/applovin/index.md", "research", "applovin"),
    ("industry/trend/compile_to_generate.md", "research", "compile-to-generate"),

    # ------------------------------------------------------------ solutions
    ("solution/rag/index.md", "solutions", "rag-platform"),
    ("solution/search_recommendation_adv/index.md", "solutions", "search-recommendation-ads"),
]


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def old_url(src: Path) -> str:
    """The URL this file published at before the move."""
    rel = src.relative_to("content")
    parts = list(rel.parts)
    if parts[-1] == "index.md":
        parts.pop()
    else:
        parts[-1] = parts[-1][: -len(".md")]
    return "/" + "/".join(parts) + "/"


def dedicated_dir(src: Path) -> bool:
    """True if src's parent directory belongs solely to this post.

    A leaf bundle counts as dedicated even when it holds extra .md files:
    inside a bundle those are page resources, not separate pages. Missing this
    stranded the GPS post's nine images on the first run.
    """
    parent = src.parent
    if parent == ROOT:
        return False
    if src.name == "index.md":
        return True
    mds = [p for p in parent.rglob("*.md") if p.is_file()]
    return len(mds) == 1 and mds[0] == src


def add_alias(index_md: Path, url: str) -> None:
    text = index_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        print(f"  !! no front matter: {index_md}", file=sys.stderr)
        return
    end = text.index("\n---", 4)
    front, body = text[4:end], text[end:]
    if "aliases:" in front:
        return
    front += f'\naliases: ["{url}"]'
    index_md.write_text("---\n" + front + body, encoding="utf-8")


def main() -> int:
    if not ROOT.exists():
        print("run from the repo root", file=sys.stderr)
        return 2

    for rel_src, section, slug in MOVES:
        src = ROOT / rel_src
        if not src.exists():
            print(f"  skip (missing): {rel_src}")
            continue

        url = old_url(src)
        dst_dir = ROOT / section / slug
        dst_dir.parent.mkdir(parents=True, exist_ok=True)

        if dedicated_dir(src):
            # Move the whole directory so images travel with the post.
            run("git", "mv", str(src.parent), str(dst_dir))
            moved_md = dst_dir / src.name
            if moved_md.name != "index.md":
                run("git", "mv", str(moved_md), str(dst_dir / "index.md"))
        else:
            dst_dir.mkdir(parents=True, exist_ok=True)
            run("git", "mv", str(src), str(dst_dir / "index.md"))

        add_alias(dst_dir / "index.md", url)
        print(f"  {rel_src}\n      -> posts/{section}/{slug}/   (alias {url})")

    # Drop the two obsolete section pages and any now-empty directories.
    for stale in ("data_center/_index.md", "tech_news/_index.md"):
        p = ROOT / stale
        if p.exists():
            run("git", "rm", "-q", str(p))

    for d in sorted((p for p in ROOT.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)):
        if not any(d.iterdir()):
            d.rmdir()

    return 0


if __name__ == "__main__":
    sys.exit(main())
