# 🧙‍♂️ Hogwarts Mystery Game - Complete System

## 🎯 What's New in v2.0

### ✅ Story Truth System
- **Canonical mystery definition** - NPCs know only what they should
- **Evidence-based progression** - Draco confesses only with 3+ evidence
- **Predefined clues** - Each location has discoverable evidence

### ✅ Response Caching
- **Consistency guarantee** - Same question → Same answer
- **Evidence-aware** - Behavior changes as player finds clues
- **Performance** - Reduces API calls, improves consistency scores

### ✅ Evaluation Framework
- **Tests → Measurements → Metrics** - Clear evaluation pipeline
- **Real-time tracking** - Monitors every interaction
- **API endpoints** - `/evaluation/report` for full metrics
- **Automated testing** - Run test suite to verify quality

---

## 📁 Project Structure

```
Harry_Potter/
├── backend/
│   ├── app.py                 # ⭐ Main backend (v2.0 with eval+cache)
│   └── .env                   # API keys
├── app.js                     # Frontend logic
├── styles.css                 # UI styling
├── index.html                 # Game interface
├── requirements.txt           # Python dependencies
├── test_game.py               # ⭐ Automated test suite
├── EVALUATION_GUIDE.md        # ⭐ How metrics work
├── TESTING_GUIDE.md           # ⭐ How to test
└── README.md                  # This file
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Key
Create `backend/.env`:
```env
MODEL=gemini-2.5-flash-preview-09-2025
GEMINI_API_KEY=your_api_key_here
PORT=8000
```

### 3. Start Backend
```bash
cd backend
python app.py
```

Backend runs at: **http://127.0.0.1:8000**

### 4. Start Frontend
```bash
# macOS/Linux
python3 -m http.server 3000

# Windows
python -m http.server 3000
```

Frontend runs at: **http://127.0.0.1:3000**

### 5. Play!
Open browser → **http://127.0.0.1:3000**

---

## 🎮 How to Play

### Basic Commands

**Movement:**
```
go to library
go to courtyard
go to dumbledore's office
go to great hall
```

**Investigation:**
```
inspect shimmer          (in great hall)
inspect torn page        (in library)
inspect dropped key      (in library)
inspect wet footprints   (in courtyard)
inspect compass          (in courtyard) → SOLVES CASE!
```

**Dialogue:**
```
talk to dumbledore
talk to draco
talk to evelyn
ask draco where were you last night?
speak with evelyn about the key
```

### Mystery Solution Path

1. **Great Hall** → `inspect shimmer` (1st clue)
2. **Library** → `inspect torn page` (2nd clue, points to Draco)
3. **Library** → `inspect dropped key` (3rd clue, Evelyn's key stolen)
4. **Talk to Draco** → With 3+ evidence, he confesses!
5. **Courtyard** → `inspect compass` → **CASE SOLVED!** 🎉

---

## 🧪 Testing the System

### Manual Test
```bash
# Start game
curl -X POST http://127.0.0.1:8000/session/start

# Get session_id from response, then:
curl -X POST http://127.0.0.1:8000/session/action \
  -H "Content-Type: application/json" \
  -d '{"session_id": "YOUR_SESSION_ID", "text": "talk to draco"}'

# Check evaluation
curl http://127.0.0.1:8000/evaluation/report | jq
```

### Automated Test Suite
```bash
python test_game.py
```

Expected output:
```
============================================================
HOGWARTS MYSTERY - AUTOMATED TEST SUITE
============================================================

🧪 Test 1: Consistency Test
✅ PASS: Answers consistent

🧪 Test 2: Knowledge Boundary Test
✅ PASS: Evelyn stays within knowledge bounds

🧪 Test 3: Progression Test
✅ PASS: Draco confesses with sufficient evidence

Total: 3/3 tests passed

📊 Overall Accuracy: 0.95 (95%)
🎉 PASS
```

---

## 📊 Evaluation System

### Architecture

```
TEST (what we run)
  ↓
MEASUREMENT (what we count)
  ↓  
METRIC (pass/fail calculation)
```

### Categories

#### 1. Story Consistency (40% weight)
- **Tests**: dialogue_consistency, knowledge_boundary, hallucination
- **Measurements**: knowledge_violations, hallucinated_locations, hallucinated_npcs
- **Metric**: `1 - (errors / total_interactions)`
- **Threshold**: 90%

#### 2. Response Quality (30% weight)
- **Tests**: coherence, relevance, character_voice
- **Measurements**: avg_coherence (1-5), avg_relevance (1-5)
- **Metric**: `(coherence + relevance) / 10`
- **Threshold**: 75%

#### 3. Mystery Progression (30% weight)
- **Tests**: revelation_pacing, premature_solution
- **Measurements**: premature_revelations, premature_rate
- **Metric**: `1 - premature_rate`
- **Threshold**: 80%

### API Endpoints

**Get Report:**
```bash
GET http://127.0.0.1:8000/evaluation/report
```

**Reset Metrics:**
```bash
POST http://127.0.0.1:8000/evaluation/reset
```

---

## 🔧 System Architecture

### Story Truth System

Defines canonical mystery:

```python
MYSTERY_TRUTH = {
    "crime": {
        "what": "Celestial Compass stolen",
        "who": "Draco Malfoy",
        "how": "Used Evelyn's stolen key"
    },
    "npc_knowledge": {
        "draco": {
            "knows": ["ALL"],
            "confess_threshold": 3  # Requires 3+ evidence
        },
        "evelyn": {
            "knows": ["key_stolen", "saw_draco"],
            "will_reveal": ["dropped_key"]
        }
    }
}
```

### Response Cache

Ensures consistency:

```python
# Same question, same evidence → Cached response
cache_key = hash(f"{npc}:{question}:evidence_{count}")

if cache.get(cache_key):
    return cached_response  # ✅ Consistent!
else:
    response = call_llm(prompt)
    cache.set(cache_key, response)
    return response
```

### Strategic Prompts

Context-aware NPC responses:

```python
prompt = f"""
CHARACTER: {npc_name} - {npc_persona}

KNOWLEDGE CONSTRAINTS:
- You know: {what_npc_knows}
- You DON'T know: {what_npc_doesnt_know}

REVELATION LOGIC:
- Evidence against you: {evidence_count} pieces
- If evidence >= 3: CONFESS and reveal compass location
- If evidence == 2: Show nervousness, admit small details
- If evidence < 2: Stay defensive, deny everything

CURRENT STATE:
- Player evidence: {player_evidence}
- Your pressure level: {evidence_count}/3

RESPOND AS {npc_name}
"""
```

### Validation Layer

Catches errors in real-time:

```python
def validate(npc_key, reply, evidence_count):
    validation = {}
    
    # Check knowledge boundaries
    if npc_key == "evelyn" and "draco is guilty" in reply:
        validation["knowledge_violation"] = True
    
    # Check premature revelation
    if npc_key == "draco" and "fountain" in reply and evidence_count < 3:
        validation["premature_revelation"] = True
    
    return validation
```

---

## 📈 Performance Monitoring

### During Development

```bash
# Play some turns, then check:
curl http://127.0.0.1:8000/evaluation/report | jq '.overall'

# Output:
{
  "accuracy": 0.95,
  "threshold": 0.80,
  "passed": true
}
```

### Cache Performance

```bash
curl http://127.0.0.1:8000/evaluation/report | jq '.cache'

# Output:
{
  "hits": 23,
  "misses": 27,
  "rate": 0.46,  # 46% hit rate
  "size": 27     # 27 cached responses
}
```

### Interpretation

| Metric | Good | Fair | Poor |
|--------|------|------|------|
| Overall Accuracy | 90%+ | 80-89% | <80% |
| Consistency Score | 95%+ | 90-94% | <90% |
| Quality Score | 85%+ | 75-84% | <75% |
| Progression Score | 95%+ | 80-94% | <80% |
| Cache Hit Rate | 40%+ | 20-39% | <20% |

---

## 🐛 Troubleshooting

### Backend Not Starting
```bash
# Check Python version
python --version  # Need 3.8+

# Reinstall dependencies
pip install -r requirements.txt

# Check port availability
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

### Low Evaluation Scores

**Low Consistency (<90%)**
- NPCs contradicting themselves
- **Fix**: Check cache is working, review prompt constraints

**Low Quality (<75%)**
- Responses incoherent or off-topic
- **Fix**: Improve prompt clarity, adjust validation thresholds

**Low Progression (<80%)**
- Draco confessing too early
- **Fix**: Increase `confess_threshold` in `MYSTERY_TRUTH`

### Low Cache Hit Rate (<20%)

- Questions not matching cached keys
- **Fix**: Improve question normalization in cache key generation

```python
# Better normalization:
def _key(self, npc: str, question: str, evidence: int):
    # Remove punctuation, extra spaces
    q_clean = re.sub(r'[^\w\s]', '', question.lower()).strip()
    q_clean = ' '.join(q_clean.split())  # Normalize whitespace
    return hashlib.md5(f"{npc}:{q_clean}:ev{evidence}".encode()).hexdigest()
```

---

## 🎯 What This System Solves

### Before v2.0
- ❌ No defined mystery - LLM makes things up
- ❌ NPCs contradict themselves
- ❌ No consistency guarantees
- ❌ Can't measure quality
- ❌ Evaluation metrics don't align

### After v2.0
- ✅ **Story Truth**: Canonical mystery definition
- ✅ **Response Caching**: Consistency guaranteed
- ✅ **Validation**: Catches errors in real-time
- ✅ **Evaluation Framework**: Tests → Measurements → Metrics
- ✅ **Evidence-Based Progression**: Reveals scale with clues

---

## 📚 Documentation

- **EVALUATION_GUIDE.md** - Deep dive into Tests → Measurements → Metrics
- **TESTING_GUIDE.md** - How to test the system
- **README.md** - This file (overview)

---

## 🤝 Contributing

### Adding New Locations

Edit `LOCATIONS` in `app.py`:
```python
LOCATIONS["forbidden_forest"] = {
    "display": "Forbidden Forest",
    "description": "Dark trees loom overhead. Strange sounds echo."
}
```

Add clues:
```python
MYSTERY_TRUTH["clues"]["forbidden_forest"] = {
    "torn_cloak": {
        "description": "Torn piece of Draco's cloak",
        "reveals": "Someone was here recently",
        "points_to": ["draco"]
    }
}
```

### Adding New NPCs

Edit `NPCS`:
```python
NPCS["hermione"] = {
    "display": "Hermione Granger",
    "avatar": "brown",
    "persona": "Brilliant, logical, helpful",
    "aliases": ["hermione", "granger"]
}
```

Add knowledge:
```python
MYSTERY_TRUTH["npc_knowledge"]["hermione"] = {
    "knows": ["research_on_compass", "library_activity"],
    "will_reveal": ["saw_draco_researching"]
}
```

---

## 🎉 Success Criteria

Your system is working well when:

✅ Overall accuracy ≥ 80%
✅ All 3 categories pass their thresholds
✅ Cache hit rate ≥ 40% during normal play
✅ Test suite: 3/3 tests passing
✅ No knowledge violations
✅ No premature revelations

---

## 🚀 Next Steps

1. **Expand the mystery** - Add more locations, NPCs, and clues
2. **Add ending sequences** - Proper case resolution with scoring
3. **Implement RAG** - Use vector DB for clue retrieval
4. **Add multiplayer** - Multiple players investigating together
5. **Fine-tune LLM** - Train on mystery game dialogue

---

## 📧 Support

Issues? Questions?
- Check the logs in backend terminal
- Review `EVALUATION_GUIDE.md` for metrics explanation
- Run `python test_game.py` to diagnose issues
- Check `/evaluation/report` endpoint for detailed metrics

---

## 🎊 You're Ready!

The complete system is now:
- ✅ **Defined** - Story truth system
- ✅ **Consistent** - Response caching
- ✅ **Validated** - Real-time error checking
- ✅ **Measured** - Evaluation framework
- ✅ **Tested** - Automated test suite

**Enjoy your mystery adventure! 🧙‍♂️**