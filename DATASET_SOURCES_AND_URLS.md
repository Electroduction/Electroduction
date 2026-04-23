# Comprehensive Dataset Sources & URLs

## How to Use This Document
Each section contains:
- **Dataset Name**: What it contains
- **URL**: Working download link
- **Access Method**: API, direct download, or scraping
- **Installation Commands**: Ready-to-run code
- **Data Format**: File types and structure

---

## 🎮 GAME DEVELOPMENT AI - Datasets

### Visual Assets

**1. OpenGameArt**
- **URL**: https://opengameart.org/
- **Access**: Web scraping (no official API)
- **Content**: 20,000+ game assets (sprites, textures, 3D models)
- **License**: Various open licenses
```bash
# Manual download or use scraper
pip install beautifulsoup4 requests
python scripts/scrape_opengameart.py
```

**2. Kenney Assets**
- **URL**: https://kenney.nl/assets
- **Access**: Direct download (bulk download available)
- **Content**: 40,000+ CC0 game assets
```bash
wget https://kenney.nl/data/kenney-game-assets.zip
unzip kenney-game-assets.zip
```

**3. itch.io Asset Packs**
- **URL**: https://itch.io/game-assets/free
- **Access**: Manual download (filter by free)
- **Content**: Thousands of game assets

**4. LAION-5B (filtered for game art)**
- **URL**: https://laion.ai/blog/laion-5b/
- **Access**: Download via img2dataset
```bash
pip install img2dataset
# Download subset with game-related tags
img2dataset --url_list laion_game_art.txt --output_folder ./game_art_data
```

### Animation & Movement

**5. Mixamo**
- **URL**: https://www.mixamo.com/
- **Access**: Free with Adobe account (manual download)
- **Content**: 2,000+ character animations
- **Note**: No bulk download API, manual per-asset

**6. CMU Graphics Lab Motion Capture Database**
- **URL**: http://mocap.cs.cmu.edu/
- **Access**: Direct download
- **Content**: 2,500+ motion capture recordings
```bash
# Download all BVH files
wget -r -np -nH --cut-dirs=3 -R index.html http://mocap.cs.cmu.edu/subjects/
```

**7. DeepMimic Dataset**
- **URL**: https://github.com/xbpeng/DeepMimic
- **Access**: GitHub repository
```bash
git clone https://github.com/xbpeng/DeepMimic.git
cd DeepMimic/data
```

### Audio & Sound Effects

**8. Freesound**
- **URL**: https://freesound.org/
- **API**: https://freesound.org/docs/api/
- **Content**: 500,000+ sound effects
```bash
pip install freesound-python
# Get API key from: https://freesound.org/apiv2/apply/
python scripts/download_freesound.py --api-key YOUR_KEY
```

**9. NSynth Dataset (Google)**
- **URL**: https://magenta.tensorflow.org/datasets/nsynth
- **Access**: Cloud storage download
```bash
# Requires gsutil
gsutil -m cp -r gs://magentadata/datasets/nsynth/nsynth-train.jsonwav.tar.gz .
tar -xzf nsynth-train.jsonwav.tar.gz
```

**10. BBC Sound Effects**
- **URL**: https://sound-effects.bbcrewind.co.uk/
- **Access**: Web download (requires account)
- **Content**: 16,000+ BBC sound effects

### Game Design & Metadata

**11. IGDB API**
- **URL**: https://api.igdb.com/
- **Access**: Free API (requires Twitch app registration)
- **Docs**: https://api-docs.igdb.com/
```python
pip install requests
# Register at: https://dev.twitch.tv/console/apps
# Use Client ID and Secret for API access
```

**12. Steam Games Dataset (Kaggle)**
- **URL**: https://www.kaggle.com/datasets/fronkongames/steam-games-dataset
- **Access**: Kaggle API
```bash
pip install kaggle
kaggle datasets download -d fronkongames/steam-games-dataset
unzip steam-games-dataset.zip
```

---

## 💰 FINANCE AI - Datasets

### Market Data

**1. Yahoo Finance (yfinance)**
- **URL**: https://finance.yahoo.com/
- **API**: Python library
```bash
pip install yfinance pandas
python -c "import yfinance as yf; yf.download('SPY', start='2010-01-01').to_csv('spy_data.csv')"
```

**2. Alpha Vantage**
- **URL**: https://www.alphavantage.co/
- **API Key**: https://www.alphavantage.co/support/#api-key (FREE)
```bash
pip install alpha_vantage
# Get free API key, 500 requests/day
python scripts/download_alphavantage.py --api-key YOUR_KEY
```

**3. Quandl (Nasdaq Data Link)**
- **URL**: https://data.nasdaq.com/
- **API**: https://docs.data.nasdaq.com/
```bash
pip install quandl
# Free tier available
quandl.ApiConfig.api_key = 'YOUR_KEY'
```

**4. FRED (Federal Reserve Economic Data)**
- **URL**: https://fred.stlouisfed.org/
- **API**: https://fred.stlouisfed.org/docs/api/fred/
```bash
pip install fredapi
# Get API key: https://fred.stlouisfed.org/docs/api/api_key.html
from fredapi import Fred
fred = Fred(api_key='YOUR_KEY')
gdp = fred.get_series('GDP')
```

### Fundamental Data

**5. SEC EDGAR**
- **URL**: https://www.sec.gov/edgar/searchedgar/companysearch.html
- **API**: https://www.sec.gov/edgar/sec-api-documentation
- **Content**: All public company filings
```bash
pip install sec-edgar-downloader
# No API key needed
python -c "from sec_edgar_downloader import Downloader; dl = Downloader('.'); dl.get('10-K', 'AAPL', limit=5)"
```

**6. Financial Modeling Prep**
- **URL**: https://financialmodelingprep.com/
- **API**: https://financialmodelingprep.com/developer/docs/
- **Free Tier**: 250 requests/day
```bash
# Get free API key
# https://financialmodelingprep.com/developer/docs/pricing/
python scripts/fmp_download.py --api-key YOUR_KEY
```

**7. SimFin**
- **URL**: https://simfin.com/
- **Access**: Free bulk downloads
```bash
# Download bulk data (free registration required)
# https://simfin.com/data/bulk
wget https://simfin.com/api/bulk?dataset=income&variant=annual&market=us
```

### Kaggle Datasets

**8. S&P 500 Stock Data**
- **URL**: https://www.kaggle.com/datasets/camnugent/sandp500
```bash
kaggle datasets download -d camnugent/sandp500
```

**9. Huge Stock Market Dataset**
- **URL**: https://www.kaggle.com/datasets/borismarjanovic/price-volume-data-for-all-us-stocks-etfs
```bash
kaggle datasets download -d borismarjanovic/price-volume-data-for-all-us-stocks-etfs
```

**10. Financial Sentiment Analysis**
- **URL**: https://www.kaggle.com/datasets/ankurzing/sentiment-analysis-for-financial-news
```bash
kaggle datasets download -d ankurzing/sentiment-analysis-for-financial-news
```

---

## 🎵 MUSIC AI - Datasets

### Music Datasets

**1. Free Music Archive (FMA)**
- **URL**: https://github.com/mdeff/fma
- **Download**: https://os.unil.cloud.switch.ch/fma/
```bash
# Small (8GB), Medium (25GB), Large (93GB), Full (879GB)
wget https://os.unil.cloud.switch.ch/fma/fma_small.zip
unzip fma_small.zip
```

**2. MAESTRO Dataset**
- **URL**: https://magenta.tensorflow.org/datasets/maestro
- **Content**: 200 hours of piano performances with MIDI
```bash
wget https://storage.googleapis.com/magentadata/datasets/maestro/v3.0.0/maestro-v3.0.0.zip
unzip maestro-v3.0.0.zip
```

**3. Lakh MIDI Dataset**
- **URL**: https://colinraffel.com/projects/lmd/
- **Content**: 176,581 MIDI files
```bash
wget http://hog.ee.columbia.edu/craffel/lmd/lmd_full.tar.gz
tar -xzf lmd_full.tar.gz
```

**4. MusicNet**
- **URL**: https://zenodo.org/record/5120004
- **Content**: 330 classical music recordings with annotations
```bash
wget https://zenodo.org/record/5120004/files/musicnet.tar.gz
tar -xzf musicnet.tar.gz
```

**5. NSynth (already listed above)**

**6. Million Song Dataset**
- **URL**: http://millionsongdataset.com/
- **Note**: Audio features only (no actual audio files)
```bash
# Download subset
wget http://millionsongdataset.com/sites/default/files/AdditionalFiles/msd_summary_file.h5
```

### Voice/Speech Datasets

**7. VCTK Corpus**
- **URL**: https://datashare.ed.ac.uk/handle/10283/3443
- **Content**: 110 English speakers, 400+ utterances each
```bash
wget https://datashare.ed.ac.uk/bitstream/handle/10283/3443/VCTK-Corpus-0.92.zip
unzip VCTK-Corpus-0.92.zip
```

**8. LibriSpeech**
- **URL**: https://www.openslr.org/12/
- **Content**: 1,000 hours of English audiobooks
```bash
# Download clean speech (100 hours)
wget https://www.openslr.org/resources/12/train-clean-100.tar.gz
tar -xzf train-clean-100.tar.gz
```

**9. Common Voice (Mozilla)**
- **URL**: https://commonvoice.mozilla.org/en/datasets
- **Content**: 18,000+ hours, multiple languages
```bash
# Requires account, then download from web interface
# Or use CV API
pip install mozilla-commonvoice-downloader
```

### Music Theory

**10. Hooktheory Database**
- **URL**: https://www.hooktheory.com/theorytab
- **Access**: Web scraping (no official API)
- **Content**: Chord progressions from popular songs

**11. McGill Billboard Dataset**
- **URL**: http://ddmal.music.mcgill.ca/research/The_McGill_Billboard_Project
- **Content**: Chord annotations for Billboard hits
```bash
wget http://ddmal.music.mcgill.ca/research/The_McGill_Billboard_Project_(Chord_Analysis)/billboard-2.0-chords.tar.gz
tar -xzf billboard-2.0-chords.tar.gz
```

---

## 🎥 VIDEO CONTENT CREATION AI - Datasets

### Large Video Datasets

**1. YouTube-8M**
- **URL**: https://research.google.com/youtube8m/
- **Content**: 8 million YouTube videos (features, not raw video)
```bash
gsutil -m cp -r gs://us.data.yt8m.org/2/frame/train .
```

**2. Kinetics-400/600/700**
- **URL**: https://github.com/cvdfoundation/kinetics-dataset
- **Content**: 650,000+ video clips
```bash
# Use official downloader
git clone https://github.com/cvdfoundation/kinetics-dataset.git
cd kinetics-dataset
pip install -r requirements.txt
python download.py
```

**3. WebVid-10M**
- **URL**: https://github.com/m-bain/webvid
- **Content**: 10 million video-text pairs
```bash
# Download metadata
wget https://www.robots.ox.ac.uk/~maxbain/webvid/results_2M_train.csv
# Videos downloaded via youtube-dl
pip install yt-dlp
```

**4. ActivityNet**
- **URL**: http://activity-net.org/download.html
- **Content**: 20,000 videos with temporal annotations
```bash
# Download via provided scripts
# Requires YouTube API access
```

### Stock Footage

**5. Pexels Videos**
- **URL**: https://www.pexels.com/api/
- **API**: Free API access
```bash
pip install requests
# Get API key: https://www.pexels.com/api/
python scripts/download_pexels_videos.py --api-key YOUR_KEY
```

**6. Pixabay Videos**
- **URL**: https://pixabay.com/api/docs/
- **API**: Free API
```bash
# Get API key: https://pixabay.com/api/docs/
python scripts/download_pixabay.py --api-key YOUR_KEY
```

### Video Analysis

**7. YouTube Trending Dataset (Kaggle)**
- **URL**: https://www.kaggle.com/datasets/datasnaek/youtube-new
```bash
kaggle datasets download -d datasnaek/youtube-new
```

**8. TED Talks Dataset**
- **URL**: https://www.kaggle.com/datasets/miguelcorraljr/ted-ultimate-dataset
```bash
kaggle datasets download -d miguelcorraljr/ted-ultimate-dataset
```

**9. DAVIS (Video Segmentation)**
- **URL**: https://davischallenge.org/
- **Content**: Densely annotated video segmentation
```bash
wget https://data.vision.ee.ethz.ch/csergi/share/davis/DAVIS-2017-trainval-480p.zip
unzip DAVIS-2017-trainval-480p.zip
```

---

## 🎨 ART & CREATIVITY AI - Datasets

### Creative Writing

**1. WritingPrompts (Reddit)**
- **URL**: https://www.kaggle.com/datasets/ratthachat/writing-prompts
```bash
kaggle datasets download -d ratthachat/writing-prompts
```

**2. Project Gutenberg**
- **URL**: https://www.gutenberg.org/
- **Content**: 70,000+ free books
```bash
# Use Gutenberg API
pip install gutenbergpy
# Or bulk download
wget -r -np -k https://www.gutenberg.org/robot/harvest?filetypes[]=txt
```

**3. CMU Movie Summary Corpus**
- **URL**: http://www.cs.cmu.edu/~ark/personas/
```bash
wget http://www.cs.cmu.edu/~ark/personas/data/MovieSummaries.tar.gz
tar -xzf MovieSummaries.tar.gz
```

**4. TV Tropes**
- **URL**: https://tvtropes.org/
- **Access**: Web scraping
```bash
pip install beautifulsoup4
python scripts/scrape_tvtropes.py
```

### Innovation & Products

**5. USPTO Patent Database**
- **URL**: https://www.uspto.gov/learning-and-resources/bulk-data-products
- **API**: https://developer.uspto.gov/
```bash
# Bulk download
wget https://bulkdata.uspto.gov/data/patent/grant/redbook/fulltext/2023/
```

**6. Kickstarter Projects**
- **URL**: https://www.kaggle.com/datasets/kemical/kickstarter-projects
```bash
kaggle datasets download -d kemical/kickstarter-projects
```

**7. Crunchbase (Limited Free Data)**
- **URL**: https://www.crunchbase.com/
- **API**: Paid API (free tier very limited)
- **Alternative**: Kaggle Crunchbase datasets

### Visual Art

**8. WikiArt**
- **URL**: https://www.wikiart.org/
- **Access**: Web scraping (no official API)
```bash
pip install wikiart
python scripts/download_wikiart.py
```

**9. LAION-Aesthetics**
- **URL**: https://laion.ai/blog/laion-aesthetics/
```bash
# Download aesthetic subset
pip install img2dataset
wget https://github.com/LAION-AI/laion-datasets/blob/main/laion-aesthetic.md
# Follow instructions for subset download
```

**10. Behance/Dribbble** (Scraping required)
- **Behance URL**: https://www.behance.net/
- **Dribbble URL**: https://dribbble.com/
- **Note**: No official bulk download, requires scraping

### Cultural & Trends

**11. Google Trends**
- **API**: PyTrends (unofficial)
```bash
pip install pytrends
python scripts/fetch_trends.py
```

**12. Reddit Datasets**
- **URL**: https://www.reddit.com/r/datasets/
- **Access**: Pushshift API or PRAW
```bash
pip install praw
# Get API credentials: https://www.reddit.com/prefs/apps
python scripts/scrape_reddit.py
```

**13. Common Crawl News**
- **URL**: https://commoncrawl.org/
```bash
# Download news subset
wget https://data.commoncrawl.org/crawl-data/CC-NEWS/
```

---

## 🔧 Setup Instructions

### Install Core Dependencies

```bash
# Create virtual environment
python3 -m venv ai_research_env
source ai_research_env/bin/activate  # On Windows: ai_research_env\Scripts\activate

# Install essential packages
pip install --upgrade pip
pip install pandas numpy scikit-learn
pip install torch torchvision torchaudio
pip install transformers datasets
pip install beautifulsoup4 requests selenium
pip install kaggle youtube-dl yt-dlp
pip install librosa opencv-python moviepy
pip install chromadb langchain openai
```

### Setup API Keys

Create a `.env` file:
```bash
# .env file
ALPHA_VANTAGE_KEY=your_key_here
FRED_API_KEY=your_key_here
FREESOUND_API_KEY=your_key_here
PEXELS_API_KEY=your_key_here
YOUTUBE_API_KEY=your_key_here
REDDIT_CLIENT_ID=your_id_here
REDDIT_CLIENT_SECRET=your_secret_here
OPENAI_API_KEY=your_key_here  # For baseline comparisons
```

### Kaggle Setup

```bash
# Install Kaggle CLI
pip install kaggle

# Setup credentials
mkdir ~/.kaggle
# Download kaggle.json from: https://www.kaggle.com/settings
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

---

## 📊 Data Processing Pipeline

After downloading datasets, use this structure:

```
/data
├── game_dev/
│   ├── raw/
│   ├── processed/
│   └── embeddings/
├── finance/
│   ├── raw/
│   ├── processed/
│   └── embeddings/
├── music/
│   ├── raw/
│   ├── processed/
│   └── embeddings/
├── video/
│   ├── raw/
│   ├── processed/
│   └── embeddings/
└── creativity/
    ├── raw/
    ├── processed/
    └── embeddings/
```

Run data processing:
```bash
python scripts/process_all_datasets.py --project game_dev
python scripts/process_all_datasets.py --project finance
python scripts/process_all_datasets.py --project music
python scripts/process_all_datasets.py --project video
python scripts/process_all_datasets.py --project creativity
```

---

## 🎯 Priority Download Order

**Start here for quick prototyping:**

1. **Game Dev**: Kenney Assets + FreeSounnd + CMU MoCap
2. **Finance**: yfinance + FRED + SEC EDGAR
3. **Music**: FMA Small + MAESTRO + VCTK
4. **Video**: Pexels API + YouTube Trending (Kaggle) + TED Talks
5. **Creativity**: WritingPrompts + Project Gutenberg + Kickstarter

**Total storage needed**: ~150GB for quick start, ~1TB+ for full datasets

---

## 📝 Notes

- Most APIs have rate limits (check documentation)
- Some datasets require academic/research registration
- Always check license compatibility for your use case
- Use `wget -c` for resumable downloads
- Set up parallel downloads where possible to save time

For any issues, check the official documentation links provided with each dataset.
