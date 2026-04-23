# Quick Start Guide - AI Research Project

Get up and running in under 10 minutes!

## 🚀 Option 1: Automated Full Setup

Run everything automatically:

```bash
# Complete pipeline (setup + data collection + demo + testing)
python run_research.py --phase full

# Or step by step:
python run_research.py --phase setup      # 1. Setup environment
python run_research.py --phase collect    # 2. Collect data
python run_research.py --phase demo       # 3. Run demos
python run_research.py --phase test       # 4. Test against baselines
```

## 🛠️ Option 2: Manual Setup

### Step 1: Environment Setup (2 minutes)

```bash
# Automated setup
python scripts/setup.py --full

# This will:
# - Check Python version
# - Create directory structure
# - Install dependencies
# - Create .env template
# - Verify installation
```

### Step 2: Configure API Keys (1 minute)

```bash
# Copy template
cp .env.template .env

# Edit .env and add your keys (optional for demo mode):
# - ALPHA_VANTAGE_KEY (free: https://www.alphavantage.co/support/#api-key)
# - OPENAI_API_KEY (for baseline comparisons)
# - ANTHROPIC_API_KEY (for baseline comparisons)
```

### Step 3: Collect Data (5-30 minutes depending on datasets)

```bash
# Collect data for all projects
python scripts/collect_all_data.py --projects all

# Or specific projects:
python scripts/collect_all_data.py --projects finance game_dev

# Downloaded data goes to:
# - data/          (raw datasets)
# - databases/     (processed for fine-tuning)
```

### Step 4: Run Demos (1 minute)

Test each AI system:

```bash
# Finance AI
python finance_ai.py --mode analyze --ticker AAPL
python finance_ai.py --mode learn --topic "pe_ratio"

# Game Development AI
python game_development_ai.py --mode generate --type character --genre platformer

# Music AI
python music_ai.py --mode generate --genre "lo-fi" --duration 30

# Creativity AI
python creativity_ai.py --mode ideate --problem "New mobile app ideas" --count 10

# Video AI
python video_ai.py --mode create --style tutorial
```

### Step 5: Run Baseline Comparisons (5-10 minutes)

Compare fine-tuned models vs GPT-4/Claude:

```bash
# Test finance system
python scripts/baseline_comparison.py --project finance --models gpt4 finetuned --test-cases 5

# Results saved to: test_results/
```

## 📊 What Gets Created

```
project/
├── data/                    # Raw datasets
│   ├── cybersecurity/
│   ├── finance/
│   ├── game_dev/
│   ├── music/
│   ├── video/
│   └── creativity/
├── databases/               # Processed data for fine-tuning
│   ├── cybersecurity/
│   ├── finance/
│   ├── ...
│   └── metadata.json
├── models/                  # Fine-tuned models (after training)
├── output/                  # Generated outputs
├── test_results/            # Comparison results
└── logs/                    # System logs
```

## 🎯 Quick Commands Reference

### Setup
```bash
python scripts/setup.py --full          # Full setup
python scripts/setup.py --minimal       # Minimal (no ML libs)
```

### Data Collection
```bash
python scripts/collect_all_data.py --projects all          # All projects
python scripts/collect_all_data.py --projects finance      # Single project
```

### Testing
```bash
python scripts/baseline_comparison.py --project finance --test-cases 10
```

### Demos
```bash
python run_research.py --phase demo --project finance
```

## 📋 Data Collection Results

After running data collection, check:

```bash
# View summary
cat databases/collection_summary.json

# Check each project
cat databases/finance/metadata.json
cat databases/game_dev/metadata.json
# etc.
```

## ✅ Verification Checklist

After setup, verify:

- [ ] All dependencies installed: `pip list | grep torch`
- [ ] Directory structure created: `ls -la data/`
- [ ] Data collected: `cat databases/collection_summary.json`
- [ ] Systems run in demo mode: `python finance_ai.py --mode learn --topic pe_ratio`
- [ ] (Optional) API keys configured: `cat .env`

## 🔧 Troubleshooting

### Issue: ModuleNotFoundError

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Permission denied downloading data

```bash
# Check internet connection
# Some datasets may be blocked or moved - check URLs in DATASET_SOURCES_AND_URLS.md
```

### Issue: Out of disk space

```bash
# Check disk usage
du -sh data/

# Remove large datasets you don't need
rm -rf data/music/fma_small.zip  # 8GB
```

### Issue: API rate limits

```bash
# Use --skip-large flag
python scripts/collect_all_data.py --projects all --skip-large

# Or collect in batches with delays
```

## 🎓 Next Steps After Quick Start

1. **Review collected data**: Explore `data/` and `databases/` directories

2. **Read the roadmap**: See `RESEARCH_ROADMAP.md` for 22-week research plan

3. **Review PRDs**: Each project has detailed documentation

4. **Begin fine-tuning**: Follow Week 9-14 in roadmap

5. **Run comprehensive tests**: Increase test case count:
   ```bash
   python scripts/baseline_comparison.py --project all --test-cases 100
   ```

6. **Customize systems**: Edit Python files to add your specific logic

## 📖 Documentation

- **RESEARCH_ROADMAP.md** - Complete 22-week research plan
- **DATASET_SOURCES_AND_URLS.md** - All dataset links and instructions
- **PRD_*.md** - Detailed requirements for each project
- **PROJECT_README.md** - Complete project documentation

## 💡 Tips

1. **Start small**: Test with finance project first (smallest data requirements)
2. **Demo mode works**: All systems have demo mode - no API keys needed for testing
3. **Parallel collection**: Data collection runs in parallel where possible
4. **Save costs**: Use demo mode and minimal test cases initially
5. **Check logs**: All errors are logged with clear messages

## 🚦 Status Indicators

When running scripts, look for:
- **[INFO]** 🔵 - Informational message
- **[SUCCESS]** ✅ - Operation completed successfully
- **[WARNING]** ⚠️ - Warning, but continuing
- **[ERROR]** ❌ - Operation failed

## ⏱️ Time Estimates

| Task | Minimal | Full |
|------|---------|------|
| Setup | 2 min | 5 min |
| Data Collection | 5 min | 30-60 min |
| Demo Testing | 1 min | 5 min |
| Baseline Comparison | 3 min | 10-30 min |
| **Total** | **~10 min** | **~45-100 min** |

## 🎉 You're Ready!

After completing this guide, you have:
- ✅ Working AI systems for 5+ domains
- ✅ Datasets collected and organized
- ✅ Baseline comparisons configured
- ✅ Development environment ready
- ✅ Ready to begin fine-tuning

Start experimenting and building! 🚀
