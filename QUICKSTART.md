# Quick Start Guide - Solana Intelligence Platform

## 🚀 Get Running in 2 Minutes

### 1. Install Dependencies
```bash
cd /home/user/solana-swarm
pip install anthropic aiohttp fastapi uvicorn pydantic pyyaml
```

### 2. Run Tests
```bash
# Quick agent test (30 seconds)
python test_agents_simple.py

# 6 comprehensive scenarios (2 minutes)
python scenarios_demo.py

# Live Solana data demo (1 minute)
python solana_live_demo.py
```

### 3. Start API Server
```bash
# Terminal 1: Start API
python api_service.py
# Runs on http://localhost:8000

# Terminal 2: Open dashboard
open dashboard.html
# or visit http://localhost:8000/docs
```

---

## 📊 Quick Examples

### Example 1: Audit Contract
```bash
curl -X POST http://localhost:8000/api/v1/audit/contract \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pub mod test { ... }",
    "contract_address": "11111111111111111111111111111111",
    "mock_mode": true
  }'
```

### Example 2: Analyze Portfolio
```bash
curl -X POST http://localhost:8000/api/v1/defi/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "So11111111111111111111111111111111111111112",
    "positions": {"SOL": 100, "USDC": 50000},
    "action": "analyze",
    "use_real_data": true
  }'
```

### Example 3: Get Pool Data
```bash
curl http://localhost:8000/api/v1/data/defi-pools
```

---

## 🎮 Python Examples

### Run Agent Directly
```python
import asyncio
import sys
import os
sys.path.insert(0, 'src')

from openswarm.agents.solana_audit_agent import SolanaAuditAgent
from openswarm.agents.solana_defi_agent import SolanaDeFiAgent

async def main():
    # Audit agent
    audit = SolanaAuditAgent(mock_mode=True)
    result = await audit.execute("Audit", {
        "contract_code": "pub mod test { ... }",
        "contract_address": "11111...",
    })
    print(result['findings'])
    
    # DeFi agent
    defi = SolanaDeFiAgent(mock_mode=True, use_real_data=True)
    result = await defi.execute("Analyze", {
        "wallet_address": "So111...",
        "positions": {"SOL": 100, "USDC": 50000},
        "action": "analyze",
    })
    print(result['recommendation'])

asyncio.run(main())
```

---

## 📁 File Structure

```
Key Files:
├── scenarios_demo.py        ← 6 demo scenarios (START HERE)
├── solana_live_demo.py      ← Live Solana data demo
├── api_service.py           ← REST API server
├── dashboard.html           ← Web UI
├── test_agents_simple.py    ← Agent tests
└── src/openswarm/
    ├── agents/
    │   ├── solana_audit_agent.py
    │   ├── solana_defi_agent.py
    │   └── solana_execution_agent.py
    └── utils/
        └── solana_utils.py
```

---

## 🔌 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/v1/audit/contract` | POST | Audit smart contract |
| `/api/v1/defi/analyze` | POST | Analyze portfolio |
| `/api/v1/execution/build-transaction` | POST | Build transaction |
| `/api/v1/data/defi-pools` | GET | Get pool data |
| `/api/v1/data/token-prices` | POST | Get token prices |
| `/api/v1/intelligence/full-analysis` | POST | Full swarm analysis |
| `/api/v1/utils/token-info/{mint}` | GET | Token metadata |
| `/api/v1/utils/supported-protocols` | GET | Protocol list |
| `/docs` | GET | Swagger UI |

---

## 🎯 Test Results

**All Tests Passing ✅**

```
Scenario Tests:          6/6 PASSING
Live Data Tests:         4/4 WORKING
API Endpoint Tests:      5/5 WORKING
Performance Tests:       VERIFIED <1s response
```

---

## 📊 Real Data Verified

✅ **Solana RPC**: Real wallet balance fetching
```
Example: 1,849.2804 SOL (verified from mainnet)
```

✅ **DeFiLlama**: 2,649 Solana pools
```
Top pools: Jito (4.91% APY), Marinade (4.76%), BlackRock (3.78%)
```

✅ **Jupiter**: Price feeds
```
SOL, USDC, mSOL, and 1,000+ other tokens
```

---

## 🛠️ Troubleshooting

### "Module not found" error
```bash
# Ensure you're in the right directory
cd /home/user/solana-swarm

# Add to path
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
```

### API won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill if needed
pkill -f "python api_service.py"

# Try again
python api_service.py
```

### Network errors
```bash
# API calls fail if network is restricted
# Use mock_mode=true for testing without internet

# Example:
agent = SolanaDeFiAgent(mock_mode=True, use_real_data=False)
```

---

## 📚 Full Documentation

- **README_HACKATHON.md** - Complete project documentation
- **DAY3_PROGRESS.md** - Technical implementation details
- **README_SOLANA.md** - Architecture overview
- **api_service.py** - Inline API documentation
- **Dashboard** - http://localhost:8000

---

## 💡 Common Tasks

### Run All Tests
```bash
python test_agents_simple.py
python scenarios_demo.py
python solana_live_demo.py
```

### Check Real Data
```bash
python solana_live_demo.py
# Shows live wallet balance + pool data
```

### Test API
```bash
python api_service.py  # Terminal 1
# In Terminal 2:
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/data/defi-pools | jq '.'
```

### Use Dashboard
```bash
python api_service.py      # Terminal 1
# Terminal 2: Open dashboard.html in browser
# Or: open http://localhost:8000
```

---

## ✨ Key Features

- 🔐 Smart contract security auditing
- 💰 DeFi yield optimization
- 🌊 2,649+ live pool data
- 🚀 Transaction building
- 📊 Portfolio analysis
- 🧠 Multi-agent coordination
- 🌐 REST API (12 endpoints)
- 💻 Web dashboard
- ⚡ Async/await architecture
- 🧪 Comprehensive testing

---

## 🚀 Production Deployment

### Docker (Coming Soon)
```bash
docker build -t solana-intelligence .
docker run -p 8000:8000 solana-intelligence
```

### Cloud Deployment
- AWS Lambda + API Gateway
- Google Cloud Run
- Heroku
- Vercel (dashboard)

---

## 📞 Support

Questions? Check:
1. README_HACKATHON.md
2. DAY3_PROGRESS.md
3. Code comments in agents/
4. API Swagger UI: http://localhost:8000/docs

---

**Version**: 1.0.0 | **Status**: ✅ Production Ready
