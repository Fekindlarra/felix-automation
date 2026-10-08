#!/usr/bin/env python3
"""
FELIX Instagram Asset Generator
Generates 8 Instagram assets using OpenAI Dall-E 3 API
Includes: Logo, Profile Pic, Hero Post, 3 Carousel Slides, CTA, 5 Stories

Usage:
    python generate_instagram_assets.py --all
    python generate_instagram_assets.py --asset logo
    python generate_instagram_assets.py --all --accuracy 81.91 --uptime 99.9 --impact 618000

Author: Claude (FELIX Automation)
Last Updated: 2026-10-08
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import requests
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
ASSETS_DIR = Path(__file__).parent / "instagram_assets"
ASSETS_DIR.mkdir(exist_ok=True)

# Try to import OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("⚠️  OpenAI library not installed. Install with: pip install openai")

# Dall-E 3 Prompts (Optimized)
DALLE_PROMPTS = {
    "logo": """Create a minimalist, modern logo for "FELIX Audits" representing AI and marketing analysis.
Style: Geometric, clean lines, corporate.
Colors: Navy Blue (#001a4d) and Bright Blue (#1a73e8).
Design elements: Convergent data lines, or stylized "F" with network nodes.
Must work as a small icon (200×200px) and large format (1000×1000px).
No text, just symbol. Transparent background.
Final format: PNG with transparency.""",

    "profile_picture": """Create a professional Instagram profile picture (1080×1080px square).
Brand: FELIX Audits - AI-powered marketing analysis.
Colors: Navy Blue (#001a4d) to Bright Blue (#1a73e8) subtle gradient.
Style: Minimalist, tech-forward, professional B2B aesthetic.
Include: Subtle data/AI element (network lines, dashboard, or analysis symbol).
No photographs, pure design. Modern and trustworthy.
Transmit: Expertise, AI capability, professional marketing analysis.""",

    "hero_post": """Create an Instagram hero post image (1080×1350px vertical, mobile-first).
Headline: "Phase 3 Complete ✅"
Main metric: "81.91% ML Accuracy" in very large, bright blue text.
Background: Navy Blue with abstract data visualization lines.
Visual elements: Success checkmark, progress indicator, AI network.
CTA at bottom: "Comment AUDITORÍA for free resources"
Style: Clean, data-driven, modern dashboard aesthetic.
Colors: Navy, Bright Blue, White. High contrast for mobile viewing.
No photographs. Purely graphic design.""",

    "carousel_1_metrics": """Create an Instagram carousel slide (1080×1350px) showing 4 KPI metrics.
Title at top: "The Results" in large white text on navy background.
Display as 2×2 grid of metric cards showing:
- ML Accuracy: 81.91% ✅
- System Uptime: 99.9%+ ✅
- Error Rate: 0.26% ⚠️
- Manual Interventions: ZERO ✅
Style: Modern dashboard, minimalist metric display.
Colors: Navy background, Bright Blue for good metrics, yellow warning for caution.
Each card: Large number (60pt+), label (24pt), status icon.
Very clean, professional dashboard aesthetic.
No photographs. Graphic design only.""",

    "carousel_2_comparison": """Create an Instagram carousel slide (1080×1350px) comparing two approaches.
Title: "Machine Learning vs Traditional Rules"
Left side: "ML Accuracy" with 81.91% displayed as a long bright blue bar
Right side: "Rules-Based" with 75% displayed as a shorter gray bar
Highlight: "+6.91pp Advantage" in large bright blue text below comparison.
Visual: Horizontal bar chart, very clear comparison, easy to read on mobile.
Design: Minimalist, Navy background, data-driven aesthetics.
Include: Winner icon next to ML, visual gap between bars showing the difference.
Message: ML clearly outperforms traditional approach.
No photographs. Pure data visualization.""",

    "carousel_3_business_impact": """Create an Instagram carousel slide (1080×1350px) showing business impact.
Title: "Revenue Impact by Company Size"
Show 3 scenarios in separate boxes arranged vertically:
1. "$10M Company" with green arrow "↑" and "+$200K-300K annual"
2. "$50M Company" with green arrow "↑" and "+$1M-1.5M annual"
3. "$100M Company" with green arrow "↑" and "+$2M-3M annual"
Style: Financial/business oriented, green accents for positive impact.
Colors: Navy background, Green for positive growth arrows, Bright Blue for numbers.
Each box: Company size label, green upward arrow, impact amount in large text.
Message: Clear ROI across different company sizes, conservative estimates.
No photographs. Business dashboard style.""",

    "carousel_4_cta": """Create an Instagram carousel final slide (1080×1350px) - Call to Action.
Main text: "Get 10 FREE Prompts" in very large, bold white text (120pt+).
Subtitle: "SEO | SEM | Analytics Audits" in medium text.
Middle section: Large "10" number.
Lower section in bright blue box: "Comment AUDITORÍA Below" with downward arrow ↓
Small text: "We'll send PDF via DM"
Background: Bright Blue (#1a73e8) with white text for maximum contrast.
Include: PDF icon symbol, downward pointing arrows.
Style: Bold, motivational, irresistible offer with high contrast.
Message: Clear, simple action (comment), valuable offer (free).
No photographs. Pure graphic design with strong CTA.""",

    "story_1_complete": """Create Instagram story template (1080×1920px vertical).
Main text: "Phase 3 Complete ✅" in absolutely massive white text (150pt+).
Style: Celebration/success theme.
Background: Navy Blue (#001a4d) with Bright Blue (#1a73e8) gradient.
Visual elements: Large checkmark (✅), subtle confetti elements, celebratory vibe.
Bottom right corner: Small FELIX logo.
Full screen impact. Professional celebration, high energy.
Format: JPG for story posting.""",

    "story_2_accuracy": """Create Instagram story template (1080×1920px vertical).
Main: "81.91% Accuracy" in absolutely giant bright blue text (140pt+).
Small subtitle below: "vs 75% industry baseline"
Background: Bright Blue (#1a73e8) gradient to lighter blue.
Include: Subtle progress bar or data visualization.
Simple, impactful, high-contrast metric display.
Center text vertically. Professional technical presentation.
Format: JPG for story posting.""",

    "story_3_zero_interventions": """Create Instagram story template (1080×1920px vertical).
Main: "ZERO Manual Interventions 🛡️" in large white text.
Secondary text: "24h production testing" in medium size.
Small text: "Zero failures detected"
Background: Navy Blue (#001a4d) with security/shield visual element.
Include: Large shield icon or security element.
Convey: Reliability, zero errors, production-ready system.
Professional and reassuring tone.
Format: JPG for story posting.""",

    "story_4_impact": """Create Instagram story template (1080×1920px vertical).
Main: "$618K Annual Impact 💰" in very large green/blue text (120pt+).
Secondary: "Conservative Estimate" in smaller white text.
Small: "Real data, real results" at bottom.
Background: Navy Blue (#001a4d) with green accents (#00cc66).
Include: Upward arrow (↑) and money/dollar visual element.
Colors: Green for positive financial impact.
Style: Professional financial communication, optimistic but credible.
Format: JPG for story posting.""",

    "story_5_lead_offer": """Create Instagram story template (1080×1920px vertical).
Main: "Free PDF: 10 Prompts 📥" in very large white text.
Secondary: "Comenta AUDITORÍA" in bright blue text.
Bottom: Large downward arrow (↓) in bright blue.
Small text at very bottom: "Link in bio"
Background: Bright Blue (#1a73e8) with white text.
Style: Clear, direct lead capture CTA.
High contrast, easy to read on mobile, action-oriented.
Format: JPG for story posting.""",
}

# Asset configuration
ASSETS_CONFIG = {
    "logo": {
        "name": "FELIX Logo",
        "size": "1024x1024",
        "filename": "01_logo_felix.png",
        "description": "Professional logo for all branding materials"
    },
    "profile_picture": {
        "name": "Instagram Profile Picture",
        "size": "1024x1024",
        "filename": "02_profile_picture.jpg",
        "description": "1080×1080px Instagram profile image"
    },
    "hero_post": {
        "name": "Hero Announcement Post",
        "size": "1024x1280",
        "filename": "03_hero_post.jpg",
        "description": "Main announcement post for audit completion"
    },
    "carousel_1_metrics": {
        "name": "Carousel 1: Metrics",
        "size": "1024x1280",
        "filename": "04_carousel_1_metrics.jpg",
        "description": "Carousel slide showing KPI metrics"
    },
    "carousel_2_comparison": {
        "name": "Carousel 2: ML Comparison",
        "size": "1024x1280",
        "filename": "05_carousel_2_comparison.jpg",
        "description": "Carousel slide comparing ML vs traditional"
    },
    "carousel_3_business_impact": {
        "name": "Carousel 3: Business Impact",
        "size": "1024x1280",
        "filename": "06_carousel_3_impact.jpg",
        "description": "Carousel slide showing revenue impact"
    },
    "carousel_4_cta": {
        "name": "Carousel 4: CTA Lead Offer",
        "size": "1024x1280",
        "filename": "07_carousel_4_cta.jpg",
        "description": "Carousel final slide with lead magnet CTA"
    },
    "story_1_complete": {
        "name": "Story 1: Completion",
        "size": "1024x1920",
        "filename": "08_story_1_complete.jpg",
        "description": "Instagram story announcing completion"
    },
    "story_2_accuracy": {
        "name": "Story 2: Accuracy Metric",
        "size": "1024x1920",
        "filename": "09_story_2_accuracy.jpg",
        "description": "Instagram story highlighting accuracy"
    },
    "story_3_zero_interventions": {
        "name": "Story 3: Zero Interventions",
        "size": "1024x1920",
        "filename": "10_story_3_zero.jpg",
        "description": "Instagram story showing zero manual work"
    },
    "story_4_impact": {
        "name": "Story 4: Dollar Impact",
        "size": "1024x1920",
        "filename": "11_story_4_impact.jpg",
        "description": "Instagram story showing annual financial impact"
    },
    "story_5_lead_offer": {
        "name": "Story 5: Lead Offer",
        "size": "1024x1920",
        "filename": "12_story_5_offer.jpg",
        "description": "Instagram story with lead capture CTA"
    },
}

def get_api_key() -> str:
    """Get OpenAI API key from environment"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("❌ OPENAI_API_KEY environment variable not set")
        logger.info("Set it with: export OPENAI_API_KEY='sk-...'")
        sys.exit(1)
    return api_key

def generate_asset_dalle3(asset_type: str, api_key: str) -> Optional[str]:
    """Generate single asset using Dall-E 3"""

    if not OPENAI_AVAILABLE:
        logger.error("❌ OpenAI library required. Install: pip install openai")
        return None

    client = openai.OpenAI(api_key=api_key)
    config = ASSETS_CONFIG.get(asset_type)
    prompt = DALLE_PROMPTS.get(asset_type)

    if not config or not prompt:
        logger.error(f"❌ Unknown asset type: {asset_type}")
        return None

    logger.info(f"🎨 Generating {config['name']}...")

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",  # Dall-E 3 supports 1024x1024, 1792x1024, 1024x1792
            quality="hd",
            n=1,
        )

        image_url = response.data[0].url
        logger.info(f"✅ Generated: {image_url}")
        return image_url

    except Exception as e:
        logger.error(f"❌ Error generating {asset_type}: {str(e)}")
        return None

def download_image(url: str, filepath: Path) -> bool:
    """Download image from URL and save locally"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        logger.info(f"💾 Saved: {filepath}")
        return True

    except Exception as e:
        logger.error(f"❌ Error downloading image: {str(e)}")
        return False

def generate_all_assets(api_key: str, skip_existing: bool = False):
    """Generate all 12 Instagram assets"""

    logger.info("=" * 60)
    logger.info("🚀 FELIX Instagram Asset Generator")
    logger.info(f"📁 Output directory: {ASSETS_DIR}")
    logger.info("=" * 60)

    results = {
        "generated": [],
        "failed": [],
        "skipped": [],
        "timestamp": datetime.now().isoformat(),
    }

    for asset_type, config in ASSETS_CONFIG.items():
        output_path = ASSETS_DIR / config["filename"]

        if skip_existing and output_path.exists():
            logger.info(f"⏭️  Skipping {config['name']} (already exists)")
            results["skipped"].append(asset_type)
            continue

        image_url = generate_asset_dalle3(asset_type, api_key)

        if image_url and download_image(image_url, output_path):
            results["generated"].append({
                "asset": asset_type,
                "name": config["name"],
                "file": config["filename"],
                "url": image_url,
            })
        else:
            results["failed"].append(asset_type)

    # Save results summary
    results_path = ASSETS_DIR / "generation_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Generation Summary")
    logger.info("=" * 60)
    logger.info(f"✅ Generated: {len(results['generated'])}")
    logger.info(f"❌ Failed: {len(results['failed'])}")
    logger.info(f"⏭️  Skipped: {len(results['skipped'])}")
    logger.info(f"📁 Output: {ASSETS_DIR}")
    logger.info(f"📄 Results: {results_path}")
    logger.info("=" * 60)

    return results

def list_assets():
    """List all available assets to generate"""
    logger.info("\n📦 Available Instagram Assets:")
    logger.info("-" * 60)

    for asset_type, config in ASSETS_CONFIG.items():
        logger.info(f"\n  {config['name']}")
        logger.info(f"    Type: {asset_type}")
        logger.info(f"    File: {config['filename']}")
        logger.info(f"    {config['description']}")

    logger.info("\n" + "-" * 60)

def main():
    parser = argparse.ArgumentParser(
        description="FELIX Instagram Asset Generator (Dall-E 3)"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate all 12 assets"
    )

    parser.add_argument(
        "--asset",
        type=str,
        help="Generate specific asset (use --list to see options)"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available assets"
    )

    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip assets that already exist"
    )

    parser.add_argument(
        "--accuracy",
        type=float,
        default=81.91,
        help="ML accuracy percentage (default: 81.91)"
    )

    parser.add_argument(
        "--uptime",
        type=float,
        default=99.9,
        help="System uptime percentage (default: 99.9)"
    )

    parser.add_argument(
        "--impact",
        type=int,
        default=618000,
        help="Annual impact in dollars (default: 618000)"
    )

    args = parser.parse_args()

    # Handle --list
    if args.list:
        list_assets()
        return

    # Check for Dall-E 3 capability
    if not OPENAI_AVAILABLE:
        logger.error("❌ OpenAI library not installed")
        logger.info("Install with: pip install openai")
        return

    api_key = get_api_key()

    if args.all:
        generate_all_assets(api_key, skip_existing=args.skip_existing)
    elif args.asset:
        if args.asset not in ASSETS_CONFIG:
            logger.error(f"❌ Unknown asset: {args.asset}")
            logger.info("Use --list to see available assets")
            return

        config = ASSETS_CONFIG[args.asset]
        output_path = ASSETS_DIR / config["filename"]

        image_url = generate_asset_dalle3(args.asset, api_key)
        if image_url:
            download_image(image_url, output_path)
    else:
        logger.info("No action specified")
        logger.info("Use --all to generate all assets")
        logger.info("Use --asset <name> to generate specific asset")
        logger.info("Use --list to see available assets")

if __name__ == "__main__":
    main()
