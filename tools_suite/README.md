# Tools Suite - Comprehensive IT & Development Toolkit

A collection of pure Python tools for IT, cybersecurity, data science, and software development.
**No external dependencies required** - uses only Python standard library.

---

## Quick Start

```bash
# Run any tool directly
python3 tools_suite/data_science/statistics_toolkit.py
python3 tools_suite/finance/financial_toolkit.py
python3 tools_suite/network/network_analyzer.py

# Or use the master runner
python3 tools_suite/run_tools.py --list
python3 tools_suite/run_tools.py --tool statistics
```

---

## Tool Categories

### 1. Data Science (`data_science/`)

**Statistics Toolkit** - Statistical analysis and data processing

```python
from tools_suite.data_science.statistics_toolkit import StatisticsToolkit, DataFrame

# Basic statistics
toolkit = StatisticsToolkit()
data = [23, 45, 67, 89, 12, 34, 56, 78, 90, 11]

stats = toolkit.describe(data)
print(f"Mean: {stats['mean']}, Std Dev: {stats['std']:.2f}")

# Correlation analysis
x = [1, 2, 3, 4, 5]
y = [2, 4, 5, 4, 5]
r, p_value = toolkit.correlation(x, y)
print(f"Correlation: {r:.4f}, P-value: {p_value:.4f}")

# DataFrame operations
df = DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'salary': [50000, 60000, 70000]
})
print(df.describe())

# Linear regression
from tools_suite.data_science.statistics_toolkit import LinearRegression
model = LinearRegression()
model.fit(x, y)
predictions = model.predict([6, 7, 8])
```

**Run Demo:**
```bash
python3 tools_suite/data_science/statistics_toolkit.py
```

---

### 2. Finance (`finance/`)

**Financial Toolkit** - Investment analysis and financial calculations

```python
from tools_suite.finance.financial_toolkit import FinancialToolkit

toolkit = FinancialToolkit()

# Time Value of Money
fv = toolkit.future_value(principal=10000, rate=0.08, periods=10)
pv = toolkit.present_value(future_value=21589, rate=0.08, periods=10)
print(f"Future Value: ${fv:,.2f}")

# Investment Analysis
cash_flows = [-100000, 25000, 30000, 35000, 40000, 45000]
npv = toolkit.net_present_value(rate=0.10, cash_flows=cash_flows)
irr = toolkit.internal_rate_of_return(cash_flows)
print(f"NPV: ${npv:,.2f}, IRR: {irr*100:.2f}%")

# Risk Metrics
returns = [0.05, -0.02, 0.08, 0.03, -0.01, 0.06]
sharpe = toolkit.sharpe_ratio(returns, risk_free_rate=0.02)
var = toolkit.value_at_risk(returns, confidence=0.95)
print(f"Sharpe Ratio: {sharpe:.4f}, VaR (95%): {var*100:.2f}%")

# Black-Scholes Option Pricing
call, put = toolkit.black_scholes(S=100, K=100, T=1, r=0.05, sigma=0.2)
print(f"Call: ${call:.2f}, Put: ${put:.2f}")

# Loan Calculations
monthly = toolkit.loan_payment(principal=250000, annual_rate=0.045, years=30)
print(f"Monthly Payment: ${monthly:,.2f}")
```

**Run Demo:**
```bash
python3 tools_suite/finance/financial_toolkit.py
```

---

### 3. Research (`research/`)

**Research Toolkit** - Text analysis, citations, and data extraction

```python
from tools_suite.research.research_toolkit import ResearchToolkit

toolkit = ResearchToolkit()

# Text Analysis
text = """
Machine learning has revolutionized artificial intelligence.
Deep learning enables breakthroughs in natural language processing.
"""
analysis = toolkit.analyzer.analyze(text)
print(f"Word Count: {analysis['word_count']}")
print(f"Flesch Reading Ease: {analysis['flesch_reading_ease']}")
print(f"Sentiment: {analysis['sentiment']['label']}")

# Citation Management
toolkit.citations.add_citation(
    author="Smith, John and Doe, Jane",
    title="Deep Learning for NLP",
    year=2024,
    journal="Journal of AI"
)
print(toolkit.citations.format_citation("smith2024", style="apa"))

# Data Extraction
sample = "Contact: john@example.com, Call: 555-1234, Visit: https://example.com"
extracted = toolkit.extractor.extract_all(sample)
print(f"Emails: {extracted['emails']}")
print(f"URLs: {extracted['urls']}")

# Document Comparison
similarity = toolkit.compare_documents(text1, text2)
print(f"Cosine Similarity: {similarity['cosine_similarity']:.4f}")
```

**Run Demo:**
```bash
python3 tools_suite/research/research_toolkit.py
```

---

### 4. Network (`network/`)

**Network Analyzer** - Packet parsing and network analysis

```python
from tools_suite.network.network_analyzer import NetworkAnalyzer, PacketParser

analyzer = NetworkAnalyzer()

# Parse raw packets
raw_packet = bytes([...])  # Raw Ethernet frame
parsed = analyzer.parse_packet(raw_packet)
print(f"Source IP: {parsed.get('src_ip')}")
print(f"Protocol: {parsed.get('protocol')}")

# Network scanning utilities
scanner = analyzer.scanner
ip = scanner.resolve_hostname("example.com")
hosts = scanner.calculate_network_range("192.168.1.0/24")

# Check if port is open
is_open, service = scanner.check_port("192.168.1.1", 80)
print(f"Port 80: {'Open' if is_open else 'Closed'} - {service}")

# Traffic analysis
analyzer.traffic.process_packet({'src_ip': '10.0.0.1', 'protocol': 'TCP'}, 1500)
stats = analyzer.traffic.get_statistics()
print(f"Total Packets: {stats['summary']['total_packets']}")
```

**Run Demo:**
```bash
python3 tools_suite/network/network_analyzer.py
```

---

### 5. Code Analysis (`code_analysis/`)

**Code Analyzer** - Metrics, quality checks, and static analysis

```python
from tools_suite.code_analysis.code_analyzer import CodeAnalyzer

analyzer = CodeAnalyzer()

# Analyze Python code
code = '''
def calculate_total(items):
    """Calculate the total price of items."""
    total = 0
    for item in items:
        if item.price > 0:
            total += item.price * item.quantity
    return total
'''

result = analyzer.analyze_code(code, "shopping.py")

# Metrics
print(f"Lines of Code: {result['metrics'].code_lines}")
print(f"Cyclomatic Complexity: {result['metrics'].avg_complexity}")
print(f"Maintainability Index: {result['metrics'].maintainability_index}")

# Quality issues
for issue in result['issues']:
    print(f"[{issue['severity']}] Line {issue['lineno']}: {issue['message']}")

# Analyze entire directory
report = analyzer.analyze_directory("/path/to/project", "*.py")
print(f"Total Files: {report['summary']['total_files']}")
print(f"Total Functions: {report['summary']['total_functions']}")
```

**Run Demo:**
```bash
python3 tools_suite/code_analysis/code_analyzer.py
```

---

### 6. Data Gathering (`data_gathering/`)

**Data Collector** - Web scraping and data collection

```python
from tools_suite.data_gathering.data_collector import DataCollector

collector = DataCollector(rate_limit=1.0)  # 1 request per second

# Fetch webpage
response = collector.fetch("https://example.com")
print(f"Status: {response.status_code}")

# Parse HTML
html = "<html><head><title>Test</title></head><body>...</body></html>"
parsed = collector.parser.parse(html)
print(f"Title: {parsed['title']}")

# Extract content
metadata = collector.extractor.extract_metadata(html)
links = collector.extractor.extract_links(html, base_url="https://example.com")
images = collector.extractor.extract_images(html)
tables = collector.extractor.extract_tables(html)

# Parse various formats
json_data = collector.data_parser.parse_json('{"key": "value"}')
csv_data = collector.data_parser.parse_csv("name,age\nJohn,30")
xml_data = collector.data_parser.parse_xml("<root><item>value</item></root>")

# Export data
collector.exporter.to_json(data, "output.json")
collector.exporter.to_csv(data, "output.csv")
```

**Run Demo:**
```bash
python3 tools_suite/data_gathering/data_collector.py
```

---

### 7. Database (`database/`)

**Database Toolkit** - SQLite ORM and query building

```python
from tools_suite.database.database_toolkit import Database

# Connect to database
db = Database("myapp.db")  # or ":memory:" for in-memory

# Create table
db.create_table("users", lambda t: (
    t.id(),
    t.string("name", nullable=False),
    t.string("email", unique=True),
    t.integer("age"),
    t.boolean("active", default=True),
    t.timestamps()
))

# Insert data
users = db.table("users")
user_id = users.insert({
    "name": "John Doe",
    "email": "john@example.com",
    "age": 30
})

# Query with fluent interface
active_users = (users
    .select("id", "name", "email")
    .where("active", "=", True)
    .where("age", ">", 18)
    .order_by("name")
    .limit(10)
    .all())

# Update
users.where("id", "=", user_id).update({"age": 31})

# Delete
users.where("active", "=", False).delete()

# Raw SQL
results = db.fetch_all("SELECT * FROM users WHERE age > ?", [25])

# Transactions
with db.transaction() as conn:
    conn.execute("INSERT INTO users (name) VALUES (?)", ["Jane"])
    conn.execute("UPDATE users SET active = ?", [True])

db.close()
```

**Run Demo:**
```bash
python3 tools_suite/database/database_toolkit.py
```

---

### 8. API (`api/`)

**API Toolkit** - REST client and testing utilities

```python
from tools_suite.api.api_toolkit import APIClient, RESTClient, APIMock

# Basic API client
client = APIClient("https://api.example.com")
client.auth_bearer("your-token")
client.enable_rate_limiting(requests_per_second=10)
client.enable_caching(default_ttl=300)

response = client.get("/users", params={"page": 1})
if response.ok:
    users = response.json()

# REST resource client
rest = RESTClient("https://api.example.com")
rest.auth_bearer("token")

users_resource = rest.resource("users")
all_users = users_resource.list()
user = users_resource.get(1)
new_user = users_resource.create({"name": "John"})
users_resource.update(1, {"name": "Jane"})
users_resource.delete(1)

# Request builder
from tools_suite.api.api_toolkit import RequestBuilder

response = (RequestBuilder("https://api.example.com")
    .post("/users")
    .json({"name": "John", "email": "john@example.com"})
    .header("X-Request-ID", "12345")
    .bearer("token")
    .timeout(30)
    .send())

# Mock API for testing
mock = APIMock()
mock.register_json("GET", "/users", [{"id": 1, "name": "John"}])
mock.register_json("POST", "/users", {"id": 2, "name": "Jane"}, status=201)

response = mock.handle("GET", "/users")
assert mock.assert_called("GET", "/users", times=1)

# Response validation
from tools_suite.api.api_toolkit import ResponseValidator

validator = ResponseValidator()
validator.expect_success()
validator.expect_json()
validator.expect_json_key("id", int)
validator.expect_json_key("name", str)

is_valid, errors = validator.validate(response)
```

**Run Demo:**
```bash
python3 tools_suite/api/api_toolkit.py
```

---

## Additional Tools

### 9. System Administration (`sysadmin/`)
- Process management
- Disk usage monitoring
- Service management
- Log rotation

### 10. Cryptography (`crypto/`)
- Hashing (MD5, SHA family)
- Encryption/Decryption (AES, Fernet)
- Password generation
- Key derivation

### 11. Automation (`automation/`)
- Task scheduling
- File watching
- Batch processing
- Workflow automation

### 12. File Processing (`file_processing/`)
- CSV/JSON/XML converters
- File comparison
- Batch renaming
- Archive management

---

## Running All Demos

```bash
# Run all tool demos
python3 tools_suite/run_tools.py --all

# Run specific tool
python3 tools_suite/run_tools.py --tool statistics
python3 tools_suite/run_tools.py --tool finance
python3 tools_suite/run_tools.py --tool network

# List available tools
python3 tools_suite/run_tools.py --list
```

---

## Directory Structure

```
tools_suite/
├── __init__.py
├── README.md
├── run_tools.py              # Master runner script
│
├── data_science/
│   ├── __init__.py
│   └── statistics_toolkit.py
│
├── finance/
│   ├── __init__.py
│   └── financial_toolkit.py
│
├── research/
│   ├── __init__.py
│   └── research_toolkit.py
│
├── network/
│   ├── __init__.py
│   └── network_analyzer.py
│
├── code_analysis/
│   ├── __init__.py
│   └── code_analyzer.py
│
├── data_gathering/
│   ├── __init__.py
│   └── data_collector.py
│
├── database/
│   ├── __init__.py
│   └── database_toolkit.py
│
├── api/
│   ├── __init__.py
│   └── api_toolkit.py
│
├── sysadmin/
│   ├── __init__.py
│   └── sysadmin_toolkit.py
│
├── crypto/
│   ├── __init__.py
│   └── crypto_toolkit.py
│
├── automation/
│   ├── __init__.py
│   └── automation_toolkit.py
│
└── file_processing/
    ├── __init__.py
    └── file_toolkit.py
```

---

## Requirements

- **Python 3.7+**
- No external dependencies (uses only standard library)

---

## License

MIT License - Free for personal and commercial use.

---

## Author

Electroduction Security Team
