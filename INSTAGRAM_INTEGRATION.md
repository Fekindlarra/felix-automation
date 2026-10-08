# FELIX Instagram Integration Guide
**How to Connect Dall-E 3, Generate Assets, and Offer Service to Clients**

---

## Quick Start (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set OpenAI API Key
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

Get your API key from: https://platform.openai.com/api/keys

### 3. Generate All Assets
```bash
python generate_instagram_assets.py --all
```

Assets will be saved to `instagram_assets/` directory.

---

## How It Works

### **Architecture Overview**

```
┌─────────────────────────────────────────────────────┐
│                   FELIX Dashboard                    │
│  (dashboard.html - User generates audit + requests) │
└──────────────────┬──────────────────────────────────┘
                   │ POST /api/reports/generate
                   │
┌──────────────────▼──────────────────────────────────┐
│              FELIX API Server                       │
│  - generate_audit_report()                          │
│  - generate_instagram_assets()  ← NEW               │
│  - send_email()                                     │
└──────────────────┬──────────────────────────────────┘
                   │
     ┌─────────────┴──────────────┐
     │                            │
     ▼                            ▼
┌──────────────┐        ┌──────────────────────┐
│ PDF Report   │        │ Instagram Assets     │
│ (WeasyPrint) │        │ (Dall-E 3)           │
└──────────────┘        │ - Logo               │
                        │ - Hero post          │
                        │ - Carousel (3 slides)│
                        │ - Stories (5 frames) │
                        │ - Lead magnet CTA    │
                        └──────────────────────┘
```

### **File Structure**
```
felix-automation/
├── api_server.py                      # Main Flask API
├── generate_audit_reports.py          # PDF generation
├── generate_instagram_assets.py       # Dall-E 3 generation ← NEW
├── dashboard.html                     # Web interface
├── requirements.txt                   # Dependencies (updated)
├── instagram_assets/                  # Generated assets ← NEW
│   ├── 01_logo_felix.png
│   ├── 02_profile_picture.jpg
│   ├── 03_hero_post.jpg
│   ├── 04_carousel_1_metrics.jpg
│   ├── 05_carousel_2_comparison.jpg
│   ├── 06_carousel_3_impact.jpg
│   ├── 07_carousel_4_cta.jpg
│   ├── 08_story_1_complete.jpg
│   ├── 09_story_2_accuracy.jpg
│   ├── 10_story_3_zero.jpg
│   ├── 11_story_4_impact.jpg
│   ├── 12_story_5_offer.jpg
│   └── generation_results.json
├── reports/                           # Audit PDFs
├── INSTAGRAM_INTEGRATION.md           # This file
└── ...
```

---

## Usage: Standalone Asset Generation

### **Generate All Assets**
```bash
python generate_instagram_assets.py --all
```

### **Generate Specific Asset**
```bash
# Generate only the logo
python generate_instagram_assets.py --asset logo

# Generate hero post
python generate_instagram_assets.py --asset hero_post

# Generate all carousel slides
python generate_instagram_assets.py --asset carousel_1_metrics
python generate_instagram_assets.py --asset carousel_2_comparison
python generate_instagram_assets.py --asset carousel_3_business_impact
```

### **List Available Assets**
```bash
python generate_instagram_assets.py --list
```

### **Skip Existing Assets**
```bash
# Regenerate only new assets, skip existing files
python generate_instagram_assets.py --all --skip-existing
```

---

## Integration with API Server (Extended)

### **Option 1: Standalone Asset Generation Workflow**

1. **Client gets audit report**
   ```bash
   POST http://localhost:5000/api/reports/generate
   {
       "client_name": "Tienda Online ABC",
       "client_email": "abc@example.com",
       "score": 81,
       "accuracy": 81.91,
       ...
   }
   ```

2. **Generate Instagram assets for their metrics**
   ```bash
   python generate_instagram_assets.py --all \
       --accuracy 81.91 \
       --uptime 99.9 \
       --impact 618000
   ```

3. **Assets ready in `instagram_assets/` for download/sharing**

### **Option 2: API Endpoint for Asset Generation**

Add this endpoint to `api_server.py`:

```python
@app.route("/api/instagram/generate", methods=["POST"])
def generate_instagram_assets_api():
    """
    Generate Instagram assets for a client audit
    
    POST /api/instagram/generate
    {
        "client_name": "Tienda Online ABC",
        "accuracy": 81.91,
        "uptime": 99.9,
        "impact": 618000,
        "assets": ["logo", "hero_post", "carousel_1_metrics"]
    }
    """
    try:
        data = request.json
        client_name = data.get("client_name", "FELIX_Client")
        assets_to_generate = data.get("assets", list(ASSETS_CONFIG.keys()))
        
        results = []
        
        for asset_type in assets_to_generate:
            if asset_type not in ASSETS_CONFIG:
                continue
            
            # Generate using subprocess (or direct import)
            url = generate_asset_dalle3(asset_type, api_key)
            config = ASSETS_CONFIG[asset_type]
            output_path = REPORTS_DIR / config["filename"]
            
            if url and download_image(url, output_path):
                results.append({
                    "asset": asset_type,
                    "status": "success",
                    "file": config["filename"],
                    "download_url": f"/api/instagram/download/{config['filename']}"
                })
        
        return jsonify({
            "status": "success",
            "client": client_name,
            "assets_generated": len(results),
            "results": results,
            "next_step": "Download assets and schedule on Instagram"
        }), 201
        
    except Exception as e:
        logger.error(f"Error generating Instagram assets: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/instagram/download/<filename>", methods=["GET"])
def download_instagram_asset(filename):
    """Download generated Instagram asset"""
    try:
        filepath = REPORTS_DIR / filename
        
        if not filepath.exists():
            return jsonify({"error": "Asset not found"}), 404
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

### **Option 3: Dashboard Integration**

Add Instagram assets section to `dashboard.html`:

```html
<!-- INSTAGRAM SERVICE TAB -->
<div class="tab-content" id="instagram-tab">
    <h2>📱 Instagram Assets</h2>
    <p>Generate branded Instagram assets for your audit campaign</p>
    
    <form id="instagram-form">
        <label>Generate Assets For:</label>
        <select id="instagram-client" required>
            <option value="">Select a client...</option>
        </select>
        
        <label>Assets to Generate:</label>
        <div class="checkbox-group">
            <label><input type="checkbox" name="assets" value="logo"> Logo</label>
            <label><input type="checkbox" name="assets" value="hero_post" checked> Hero Post</label>
            <label><input type="checkbox" name="assets" value="carousel_1_metrics" checked> Carousel 1</label>
            <label><input type="checkbox" name="assets" value="carousel_2_comparison" checked> Carousel 2</label>
            <label><input type="checkbox" name="assets" value="carousel_3_business_impact" checked> Carousel 3</label>
            <label><input type="checkbox" name="assets" value="carousel_4_cta" checked> Carousel 4 (CTA)</label>
        </div>
        
        <button type="submit">🎨 Generate Assets</button>
    </form>
    
    <div id="instagram-results"></div>
</div>

<script>
// Load client list for Instagram tab
async function loadClientsForInstagram() {
    const response = await fetch("/api/reports");
    const data = await response.json();
    const select = document.getElementById("instagram-client");
    
    data.reports.forEach(report => {
        const option = document.createElement("option");
        option.value = JSON.stringify({
            name: report.client_name,
            accuracy: report.score,
            uptime: 99.9,
            impact: 618000
        });
        option.text = report.client_name;
        select.appendChild(option);
    });
}

// Handle Instagram asset generation
document.getElementById("instagram-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const clientData = JSON.parse(document.getElementById("instagram-client").value);
    const selectedAssets = Array.from(document.querySelectorAll('input[name="assets"]:checked'))
        .map(cb => cb.value);
    
    const response = await fetch("/api/instagram/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            client_name: clientData.name,
            accuracy: clientData.accuracy,
            uptime: clientData.uptime,
            impact: clientData.impact,
            assets: selectedAssets
        })
    });
    
    const result = await response.json();
    
    if (result.status === "success") {
        // Display download links
        const resultsDiv = document.getElementById("instagram-results");
        resultsDiv.innerHTML = `
            <h3>✅ Assets Generated!</h3>
            <p>${result.assets_generated} assets ready for download:</p>
            <ul>
                ${result.results.map(r => `
                    <li>
                        <a href="${r.download_url}" download>${r.asset}</a>
                    </li>
                `).join("")}
            </ul>
            <p><strong>Next Step:</strong> Download and schedule on Instagram using Later, Buffer, or Meta Business Suite</p>
        `;
    }
});
</script>
```

---

## Customizing for Clients

### **Updating Metrics in Assets**

The `generate_instagram_assets.py` script accepts parameters:

```bash
python generate_instagram_assets.py --all \
    --accuracy 81.91 \
    --uptime 99.9 \
    --impact 618000
```

These values are used to customize asset generation prompts:

```python
# Example: Hero post with custom accuracy
prompt = f"""Create an Instagram hero post showing:
Accuracy: {args.accuracy}% ML Achievement
System Uptime: {args.uptime}%
Annual Impact: ${args.impact:,}
..."""
```

### **Batch Generation for Multiple Clients**

```bash
# Client 1: Tienda Online ABC
python generate_instagram_assets.py --all \
    --accuracy 81.91 --output tienda_online_abc

# Client 2: Tech Startup SaaS
python generate_instagram_assets.py --all \
    --accuracy 88.5 --output tech_startup

# Client 3: Agency
python generate_instagram_assets.py --all \
    --accuracy 79.2 --output marketing_agency
```

---

## Offering This Service to Clients

### **Pricing Tiers**

**Option 1: Standalone Instagram Design Service**
- 8 custom assets (logo, profile, hero, carousel ×3, CTA, stories ×5)
- Dall-E 3 generation + refinement
- Ready-to-post files
- **Investment:** $800-1,200 per project

**Option 2: Bundle with Audit Report**
- Comprehensive audit report (PDF)
- Complete Instagram visual system
- 10-day campaign plan
- Lead capture setup
- **Investment:** +$500 add-on to audit service

**Option 3: Recurring Social Service**
- Monthly Instagram content calendar
- 2 campaigns/month (20 assets)
- Dall-E 3 generation + design
- Scheduling + basic reporting
- **Investment:** $2,000/month

### **Sales Pitch for Clients**

> **"After your audit, you have data. You have proof. We create visual credibility."**
>
> Your FELIX audit uncovered:
> - 47 manual processes ready to automate
> - ML accuracy of 81.91% (vs 75% industry baseline)
> - $618K annual impact
>
> **But does your market know?**
>
> Our Instagram design service turns your audit findings into social proof:
> - Professional visual system (logo, hero post, carousel, stories)
> - Complete 10-day launch campaign
> - Lead capture funnel (free resources in exchange for email)
> - Positions you as AI-powered, data-driven, modern
>
> **Results:**
> - 12-20% engagement on B2B audiences
> - 5-15% of comments become qualified leads
> - Social proof that attracts investors, partners, customers
>
> **Ready to make your audit visible?**

---

## Environment Variables

### **.env File Setup**
```bash
# OpenAI API Configuration
OPENAI_API_KEY="sk-your-api-key"

# Instagram Service Settings
INSTAGRAM_ASSETS_DIR="./instagram_assets"
INSTAGRAM_QUALITY="hd"  # or "standard"

# Email for client support
SUPPORT_EMAIL="felix@enbuenamesa.com"
```

### **Loading Environment Variables**
```python
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INSTAGRAM_ASSETS_DIR = os.getenv("INSTAGRAM_ASSETS_DIR", "./instagram_assets")
```

---

## Troubleshooting

### **Issue: "OpenAI library not installed"**
```bash
pip install openai==1.3.0
```

### **Issue: "OPENAI_API_KEY not set"**
```bash
# Check key is exported
echo $OPENAI_API_KEY

# If empty, set it
export OPENAI_API_KEY="sk-your-key"

# Or add to .env file and load with python-dotenv
```

### **Issue: "Rate limited by Dall-E 3"**
- Free tier: 3 images/minute
- Paid tier: No strict limits

Solution: Batch requests with delays or generate during off-peak hours.

### **Issue: Generated assets have different aspect ratios**
Dall-E 3 supports:
- 1024×1024 (square)
- 1792×1024 (landscape)
- 1024×1792 (portrait)

Script resizes to correct Instagram dimensions:
- Posts: 1080×1350 (scale down from 1024×1280)
- Stories: 1080×1920 (scale down from 1024×1920)
- Profile: 1080×1080

---

## Next Steps

### **Immediate (This Week)**
1. ✅ Install requirements: `pip install -r requirements.txt`
2. ✅ Set OpenAI API key: `export OPENAI_API_KEY="sk-..."`
3. ✅ Test asset generation: `python generate_instagram_assets.py --all`
4. Review generated assets in `instagram_assets/`

### **Short Term (This Month)**
1. Integrate API endpoint into `api_server.py`
2. Add Instagram tab to dashboard
3. Create client campaign calendar template
4. Document in client onboarding materials

### **Long Term (Ongoing)**
1. Track client engagement metrics (likes, comments, leads)
2. Refine prompts based on performance
3. A/B test different designs
4. Expand to other platforms (LinkedIn, Twitter, TikTok)
5. Add video generation (Runway, Synthesia)

---

## API Reference

### **Asset Generation Script**
```bash
python generate_instagram_assets.py [OPTIONS]

Options:
  --all                    Generate all 12 assets
  --asset ASSET_TYPE       Generate specific asset
  --list                   List available assets
  --skip-existing          Skip assets that exist
  --accuracy FLOAT         ML accuracy % (default: 81.91)
  --uptime FLOAT           System uptime % (default: 99.9)
  --impact INT             Annual impact in dollars (default: 618000)
```

### **Available Assets**
```
logo                          - FELIX professional logo
profile_picture              - Instagram 1080×1080px profile pic
hero_post                    - Main announcement post
carousel_1_metrics           - KPI metrics dashboard
carousel_2_comparison        - ML vs Traditional comparison
carousel_3_business_impact   - Revenue impact by company size
carousel_4_cta              - Lead magnet call-to-action
story_1_complete            - "Phase 3 Complete" story
story_2_accuracy            - "81.91% Accuracy" story
story_3_zero_interventions  - "ZERO Manual Work" story
story_4_impact              - "$618K Impact" story
story_5_lead_offer          - Lead offer story
```

### **File Outputs**
All generated assets are saved to `instagram_assets/` directory:
- `01_logo_felix.png` - Transparent logo (use on any background)
- `02_profile_picture.jpg` - Instagram profile image
- `03_hero_post.jpg` - Main announcement post
- `04-07_carousel_*.jpg` - 4 carousel slides
- `08-12_story_*.jpg` - 5 story templates
- `generation_results.json` - Metadata and URLs

---

## Brand Guidelines Reminder

All generated assets follow FELIX brand standards:

| Element | Value |
|---------|-------|
| Primary Color | Navy Blue #001a4d |
| Secondary Color | Bright Blue #1a73e8 |
| Accent | Light Gray #f5f5f5 |
| Typography | Clean, sans-serif, bold headlines |
| Style | Minimalist, geometric, professional |
| Tone | Data-driven, B2B friendly, trustworthy |
| Format | Optimized for mobile-first viewing |

---

## Questions?

For issues or feature requests:
- **Email:** felix@enbuenamesa.com
- **Response Time:** < 4 hours
- **Support Hours:** Mon-Fri, 9am-6pm CT

---

**Ready to make your audit results visible on Instagram? Generate assets now! 🚀**

```bash
python generate_instagram_assets.py --all
```
