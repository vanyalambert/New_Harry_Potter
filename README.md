# 🧙‍♂️ Hogwarts Mystery Game - Complete System

## Quick Start

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


**Enjoy your mystery adventure! 🧙‍♂️**
