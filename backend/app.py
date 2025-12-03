import os
import json
import uuid
import logging
import hashlib
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import google.generativeai as genai

# --- Configuration & Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO)

MODEL = os.getenv("MODEL", "gemini-2.5-flash-preview-09-2025")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    logging.error("GEMINI_API_KEY is not set.")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        logging.info("Gemini client configured.")
    except Exception as e:
        logging.error(f"Failed to configure Gemini client: {e}")

# --- MYSTERY TRUTH SYSTEM ---
MYSTERY_TRUTH = {
    "crime": {
        "what": "The Celestial Compass was stolen from Dumbledore's office",
        "when": "Last night between 10 PM and midnight",
        "where": "Dumbledore's Office",
        "who": "Draco Malfoy",
        "how": "Used Evelyn's stolen master key",
        "why": "Family pressure and jealousy of the artifact's power"
    },
    
    "clues": {
        "great hall": {
            "shimmer": {
                "description": "Magical trace of the missing artifact",
                "reveals": "Someone with magical artifact passed through recently",
                "points_to": []
            }
        },
        "library": {
            "torn_page": {
                "description": "Page torn from book about Celestial Compass",
                "reveals": "Someone researched the compass before stealing it",
                "points_to": ["draco"]
            },
            "dropped_key": {
                "description": "Evelyn's master key on the floor near Slytherin section",
                "reveals": "Evelyn's key was stolen here",
                "points_to": ["draco"]
            }
        },
        "courtyard": {
            "wet_footprints": {
                "description": "Fresh footprints leading to fountain, matches Draco's shoe size",
                "reveals": "Someone was at fountain recently",
                "points_to": ["draco"]
            },
            "compass": {
                "description": "The Celestial Compass, hidden behind fountain stones",
                "reveals": "CASE SOLVED - This is the stolen artifact",
                "solves_case": True,
                "points_to": ["draco"]
            }
        },
        "dumbledore's office": {
            "portrait_testimony": {
                "description": "Portrait saw a blonde student enter last night",
                "reveals": "Witness testimony of blonde student",
                "points_to": ["draco"]
            }
        }
    },
    
    "npc_knowledge": {
        "professor dumbledore": {
            "knows": ["crime.what", "crime.when", "crime.where"],
            "will_reveal": ["portrait_testimony"],
            "personality": "Guides with questions, never directly accuses"
        },
        "draco": {
            "knows": ["ALL"],
            "will_lie_about": ["whereabouts", "compass_knowledge"],
            "confess_threshold": 3,
            "personality": "Defensive, deflects blame, nervous when pressed"
        },
        "evelyn": {
            "knows": ["key_stolen", "saw_draco_in_library"],
            "will_reveal": ["dropped_key", "draco_suspicious"],
            "personality": "Nervous, needs encouragement to speak"
        }
    }
}

# --- RESPONSE CACHE SYSTEM ---
class ResponseCache:
    """Ensures consistent answers to identical questions."""
    
    def __init__(self):
        self.cache: Dict[str, Dict] = {}
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, npc_key: str, question: str, evidence_count: int) -> str:
        """Generate cache key from NPC, question, and evidence state."""
        # Normalize question
        q_normalized = question.lower().strip()
        # Key includes evidence count so answers change as player progresses
        key_string = f"{npc_key}:{q_normalized}:evidence_{evidence_count}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, npc_key: str, question: str, evidence_count: int) -> Optional[Dict]:
        """Get cached response if exists."""
        key = self._generate_key(npc_key, question, evidence_count)
        if key in self.cache:
            self.hits += 1
            logging.info(f"Cache HIT for {npc_key} (hit rate: {self.get_hit_rate():.1%})")
            return self.cache[key]
        self.misses += 1
        return None
    
    def set(self, npc_key: str, question: str, evidence_count: int, response: Dict):
        """Cache a response."""
        key = self._generate_key(npc_key, question, evidence_count)
        self.cache[key] = response
        logging.info(f"Cached response for {npc_key}")
    
    def get_hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def get_stats(self) -> Dict:
        return {
            "cache_hits": self.hits,
            "cache_misses": self.misses,
            "hit_rate": self.get_hit_rate(),
            "cached_entries": len(self.cache)
        }

# Global cache instance
response_cache = ResponseCache()

# --- EVALUATION FRAMEWORK ---
class EvaluationMetrics:
    """Tracks metrics for evaluation."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.total_interactions = 0
        self.contradictions = 0
        self.knowledge_violations = 0
        self.hallucinated_locations = 0
        self.hallucinated_npcs = 0
        self.premature_revelations = 0
        self.coherence_scores = []
        self.relevance_scores = []
    
    def record_interaction(self, npc_key: str, question: str, response: Dict, 
                          evidence_count: int, validation_result: Dict):
        """Record metrics from an interaction."""
        self.total_interactions += 1
        
        # Story consistency metrics
        if validation_result.get("knowledge_violation"):
            self.knowledge_violations += 1
        if validation_result.get("hallucinated_location"):
            self.hallucinated_locations += 1
        if validation_result.get("hallucinated_npc"):
            self.hallucinated_npcs += 1
        if validation_result.get("premature_revelation"):
            self.premature_revelations += 1
        
        # Response quality metrics (would use LLM-as-judge in production)
        coherence = validation_result.get("coherence_score", 5)  # 1-5 scale
        relevance = validation_result.get("relevance_score", 5)   # 1-5 scale
        
        self.coherence_scores.append(coherence)
        self.relevance_scores.append(relevance)
    
    def calculate_consistency_score(self) -> float:
        """Test → Measurement → Metric: Story Consistency."""
        if self.total_interactions == 0:
            return 1.0
        
        # Measurement: Count errors
        errors = (
            self.knowledge_violations + 
            self.hallucinated_locations + 
            self.hallucinated_npcs
        )
        
        # Metric: Calculate score
        consistency_score = 1 - (errors / self.total_interactions)
        return max(0.0, consistency_score)
    
    def calculate_quality_score(self) -> float:
        """Test → Measurement → Metric: Response Quality."""
        if not self.coherence_scores:
            return 1.0
        
        # Measurement: Average scores
        avg_coherence = sum(self.coherence_scores) / len(self.coherence_scores)
        avg_relevance = sum(self.relevance_scores) / len(self.relevance_scores)
        
        # Metric: Normalize to 0-1 scale
        quality_score = (avg_coherence + avg_relevance) / 10  # Both out of 5, so /10
        return quality_score
    
    def calculate_progression_score(self) -> float:
        """Test → Measurement → Metric: Mystery Progression."""
        if self.total_interactions == 0:
            return 1.0
        
        # Measurement: Count premature revelations
        premature_rate = self.premature_revelations / self.total_interactions
        
        # Metric: Penalize premature revelations
        progression_score = 1 - premature_rate
        return max(0.0, progression_score)
    
    def calculate_overall_accuracy(self) -> float:
        """Weighted combination of all metrics."""
        consistency = self.calculate_consistency_score()
        quality = self.calculate_quality_score()
        progression = self.calculate_progression_score()
        
        # Weighted average: consistency=40%, quality=30%, progression=30%
        overall = (consistency * 0.4) + (quality * 0.3) + (progression * 0.3)
        return overall
    
    def generate_report(self) -> Dict:
        """Generate full evaluation report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_interactions": self.total_interactions,
            
            "story_consistency": {
                "test": "dialogue_consistency_test + knowledge_boundary_test",
                "measurements": {
                    "knowledge_violations": self.knowledge_violations,
                    "hallucinated_locations": self.hallucinated_locations,
                    "hallucinated_npcs": self.hallucinated_npcs,
                    "total_errors": self.knowledge_violations + self.hallucinated_locations + self.hallucinated_npcs
                },
                "metric": {
                    "consistency_score": round(self.calculate_consistency_score(), 3),
                    "pass_threshold": 0.90,
                    "passed": self.calculate_consistency_score() >= 0.90
                }
            },
            
            "response_quality": {
                "test": "response_coherence_test + relevance_test",
                "measurements": {
                    "avg_coherence": round(sum(self.coherence_scores) / len(self.coherence_scores), 2) if self.coherence_scores else 5.0,
                    "avg_relevance": round(sum(self.relevance_scores) / len(self.relevance_scores), 2) if self.relevance_scores else 5.0,
                },
                "metric": {
                    "quality_score": round(self.calculate_quality_score(), 3),
                    "pass_threshold": 0.75,
                    "passed": self.calculate_quality_score() >= 0.75
                }
            },
            
            "mystery_progression": {
                "test": "clue_revelation_test + pacing_test",
                "measurements": {
                    "premature_revelations": self.premature_revelations,
                    "premature_rate": round(self.premature_revelations / self.total_interactions, 3) if self.total_interactions > 0 else 0
                },
                "metric": {
                    "progression_score": round(self.calculate_progression_score(), 3),
                    "pass_threshold": 0.80,
                    "passed": self.calculate_progression_score() >= 0.80
                }
            },
            
            "overall": {
                "accuracy": round(self.calculate_overall_accuracy(), 3),
                "pass_threshold": 0.80,
                "passed": self.calculate_overall_accuracy() >= 0.80
            },
            
            "cache_performance": response_cache.get_stats()
        }

# Global metrics instance
eval_metrics = EvaluationMetrics()

# --- System Instruction ---
SYSTEM_INSTRUCTION_BASE = """You are an NPC in a magical-school murder mystery game. 

CRITICAL RULES:
1. Stay strictly in character
2. Maximum 3 sentences per response
3. Only mention locations that exist: Great Hall, Library, Courtyard, Dumbledore's Office
4. Only mention NPCs that exist: Professor Dumbledore, Draco Malfoy, Evelyn
5. Follow your knowledge constraints exactly

Output ONLY valid JSON with these keys:
- "npc_reply": your dialogue (no speaker name)
- "mentions": list of new clues/suspects you reveal
- "tone": one word (nervous/calm/defensive/helpful/arrogant/fearful)
- "thinking": brief reasoning for your response (for debugging)
"""

llm_model = None
try:
    llm_model = genai.GenerativeModel(
        model_name=MODEL, 
        system_instruction=SYSTEM_INSTRUCTION_BASE
    )
    logging.info(f"LLM model prepared: {MODEL}")
except Exception as e:
    logging.error(f"Could not instantiate GenerativeModel: {e}")

# --- Game Data ---
SESSIONS: Dict[str, Dict] = {}

LOCATIONS = {
    "great hall": {
        "display": "The Great Hall",
        "description": "Floating candles illuminate the enchanted ceiling. A cold chill lingers."
    },
    "library": {
        "display": "The Library",
        "description": "Thousands of dusty books. Madam Pince watches suspiciously."
    },
    "courtyard": {
        "display": "The Courtyard",
        "description": "Cold open space with a stone fountain. Students rush by."
    },
    "dumbledore's office": {
        "display": "Dumbledore's Office",
        "description": "Circular room with ancient instruments and a sleeping phoenix."
    },
}

NPCS = {
    "professor dumbledore": {
        "display": "Professor Dumbledore",
        "avatar": "purple",
        "persona": "Wise, calm, enigmatic. Guides with questions.",
        "aliases": ["dumbledore", "professor dumbledore", "professor"]
    },
    "draco": {
        "display": "Draco Malfoy",
        "avatar": "green",
        "persona": "Sly, arrogant, easily panicked. Denies everything.",
        "aliases": ["draco", "malfoy", "draco malfoy"]
    },
    "evelyn": {
        "display": "Evelyn",
        "avatar": "brown",
        "persona": "Studious, quiet Ravenclaw. Observant but nervous.",
        "aliases": ["evelyn"]
    },
}

# --- Pydantic Models ---
class Action(BaseModel):
    session_id: str
    text: str

class Message(BaseModel):
    speaker: str
    text: str
    avatar_type: str

class State(BaseModel):
    location: str
    clues_found: int
    timeline: List[Message]
    evidence: List[str]
    npcs: Dict[str, Dict]

# --- FastAPI Setup ---
app = FastAPI(title="Hogwarts Mystery Backend with Evaluation")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Session Management ---
def create_initial_session(player_name: str = "You"):
    sid = str(uuid.uuid4())
    timeline = [
        Message(
            speaker="Professor Dumbledore",
            text="Welcome, young wizard. A mysterious artifact has gone missing from the castle. Your journey begins here in the Great Hall. What would you like to do?",
            avatar_type="purple"
        ).dict()
    ]
    doc = {
        "session_id": sid,
        "player_name": player_name,
        "location": "great hall",
        "clues_found": 0,
        "timeline": timeline,
        "evidence": [],
        "evidence_against": {"draco": 0, "evelyn": 0},
        "npcs": {k: v for k, v in NPCS.items()},
        "locations": {k: v for k, v in LOCATIONS.items()},
    }
    SESSIONS[sid] = doc
    return sid, doc

def get_current_state(session: Dict) -> State:
    return State(
        location=session["locations"][session["location"]]["display"],
        clues_found=session["clues_found"],
        timeline=session["timeline"],
        evidence=session["evidence"],
        npcs=session["npcs"],
    )

def add_message(session: Dict, speaker: str, text: str, avatar_type: str):
    session["timeline"].append(Message(speaker=speaker, text=text, avatar_type=avatar_type).dict())

# --- Evidence Tracking ---
def count_evidence_against(suspect: str, evidence_list: List[str]) -> int:
    """Count how many pieces of evidence point to a suspect."""
    count = 0
    for location_clues in MYSTERY_TRUTH["clues"].values():
        for clue_data in location_clues.values():
            if suspect in clue_data.get("points_to", []):
                if clue_data["description"] in evidence_list:
                    count += 1
    return count

# --- Strategic Prompt Builder ---
def build_strategic_prompt(session: Dict, npc_key: str, player_text: str) -> str:
    """Builds context-aware prompt with knowledge boundaries."""
    
    npc_data = NPCS[npc_key]
    npc_knowledge = MYSTERY_TRUTH["npc_knowledge"][npc_key]
    player_evidence = session["evidence"]
    
    evidence_against = count_evidence_against(npc_key, player_evidence)
    session["evidence_against"][npc_key] = evidence_against
    
    knowledge_section = build_knowledge_constraints(npc_key, npc_knowledge)
    revelation_section = build_revelation_logic(npc_key, evidence_against, npc_knowledge)
    
    evidence_text = "\n- ".join(player_evidence) if player_evidence else "None"
    
    history = "\n".join([
        f"{msg['speaker']}: {msg['text']}" 
        for msg in session["timeline"][-5:]
    ])
    
    prompt = f"""--- YOUR CHARACTER IDENTITY ---
You are: {npc_data['display']}
Personality: {npc_data['persona']}

--- YOUR KNOWLEDGE CONSTRAINTS ---
{knowledge_section}

--- REVELATION LOGIC (When to reveal info) ---
{revelation_section}

--- CURRENT GAME STATE ---
Player Location: {session['locations'][session['location']]['display']}
Evidence Player Has: 
- {evidence_text}

Evidence Pointing to You: {evidence_against} pieces

--- RECENT CONVERSATION ---
{history}

--- PLAYER'S QUESTION ---
{player_text}

--- RESPOND AS {npc_data['display']} ---
Consider your personality, knowledge, and the pressure from evidence.
Output valid JSON only."""
    
    return prompt

def build_knowledge_constraints(npc_key: str, npc_knowledge: Dict) -> str:
    """Define what NPC knows and doesn't know."""
    
    knows = npc_knowledge.get("knows", [])
    
    if "ALL" in knows:
        will_lie = npc_knowledge.get("will_lie_about", [])
        threshold = npc_knowledge.get("confess_threshold", 999)
        
        return f"""You are the CULPRIT. You know everything about the crime.
- You MUST LIE about: {', '.join(will_lie)}
- You will only confess if player has {threshold}+ pieces of evidence against you
- Act defensive and deflect blame until then"""
    
    else:
        will_reveal = npc_knowledge.get("will_reveal", [])
        return f"""You know limited information:
- You know: {', '.join(knows)}
- You can reveal these clues if asked: {', '.join(will_reveal)}
- You DON'T know who the culprit is (don't guess)"""

def build_revelation_logic(npc_key: str, evidence_count: int, npc_knowledge: Dict) -> str:
    """Define when NPC should reveal information."""
    
    if npc_key == "draco":
        threshold = npc_knowledge.get("confess_threshold", 3)
        
        if evidence_count >= threshold:
            return f"""⚠️ CRITICAL: Player has {evidence_count} pieces of evidence against you!
- Show FEAR and PANIC
- Admit guilt: "Fine! I took it! My family pressured me!"
- Reveal location: "It's hidden in the courtyard fountain!"
- Be remorseful"""
        elif evidence_count >= 2:
            return f"""⚠️ WARNING: Player has {evidence_count} evidence pieces.
- Show NERVOUSNESS
- Admit small details but deny theft
- Example: "I was in the library, but I didn't steal anything!"
- Don't reveal compass location yet"""
        else:
            return """✓ Stay CONFIDENT and DEFENSIVE
- Deny everything
- Deflect blame to others
- Act offended by accusations"""
    
    elif npc_key == "evelyn":
        return """✓ You're helpful but shy
- If player asks about your key, reveal you noticed it missing from library
- If player asks about Draco, mention you saw him acting suspicious in library
- Don't volunteer info unless asked"""
    
    else:  # Dumbledore
        return """✓ You guide with wisdom
- Ask probing questions
- Hint at examining evidence more closely
- Suggest talking to portraits in your office
- Never directly accuse anyone"""

# --- LLM Call with Caching ---
def call_gemini_llm(user_prompt: str) -> str:
    if llm_model is None:
        raise RuntimeError("LLM model not configured. Set GEMINI_API_KEY.")
    
    try:
        logging.info("Calling Gemini API...")
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json"
        )
        response = llm_model.generate_content(user_prompt, generation_config=generation_config)
        
        if response.candidates and response.candidates[0].content.parts:
            api_response_text = response.candidates[0].content.parts[0].text
            logging.info("Gemini API success.")
            return api_response_text
        else:
            raise Exception("Gemini returned no content.")
    except Exception as e:
        logging.error(f"Gemini API failed: {e}")
        raise

def parse_llm_response(raw_text: str) -> Tuple[str, List[str], str]:
    try:
        data = json.loads(raw_text)
        reply = data.get("npc_reply", "I can't answer that right now.")
        mentions = data.get("mentions", [])
        tone = data.get("tone", "neutral")
        thinking = data.get("thinking", "")
        
        logging.info(f"NPC thinking: {thinking}")
        
        return reply, mentions, tone
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON: {e}")
        logging.error(f"Raw: {raw_text}")
        raise ValueError(f"Invalid JSON from LLM: {e}")

# --- Validation Layer ---
def validate_npc_response(npc_key: str, reply: str, evidence_count: int) -> Dict:
    """
    Validate response and return metrics for evaluation.
    Returns dict with validation results and quality scores.
    """
    
    validation = {
        "knowledge_violation": False,
        "hallucinated_location": False,
        "hallucinated_npc": False,
        "premature_revelation": False,
        "coherence_score": 5,  # Default high score
        "relevance_score": 5,   # Default high score
    }
    
    reply_lower = reply.lower()
    
    # Check for hallucinated locations
    valid_location_names = [loc["display"].lower() for loc in LOCATIONS.values()]
    location_keywords = ["room", "chamber", "dungeon", "tower", "passage"]
    
    for keyword in location_keywords:
        if keyword in reply_lower:
            # Check if it's not one of our valid locations
            is_valid = any(loc_name in reply_lower for loc_name in valid_location_names)
            if not is_valid:
                validation["hallucinated_location"] = True
                validation["coherence_score"] = 2  # Penalize
                logging.warning(f"Possible hallucinated location in: {reply}")
    
    # Check for hallucinated NPCs
    valid_npc_names = [npc["display"].lower() for npc in NPCS.values()]
    # Simple check: if mentions a person-like name not in our NPC list
    if "professor" in reply_lower or "student" in reply_lower:
        mentioned_valid = any(npc_name in reply_lower for npc_name in valid_npc_names)
        # This is a simple heuristic - in production would use NER
    
    # Check for premature revelation (compass location revealed too early)
    if npc_key == "draco":
        reveals_compass_location = ("fountain" in reply_lower and "compass" in reply_lower) or \
                                  ("courtyard" in reply_lower and "hidden" in reply_lower)
        
        if reveals_compass_location and evidence_count < 3:
            validation["premature_revelation"] = True
            validation["relevance_score"] = 2  # Penalize
            logging.warning(f"Premature revelation at evidence_count={evidence_count}")
    
    # Check knowledge boundaries
    npc_knowledge = MYSTERY_TRUTH["npc_knowledge"][npc_key]
    knows = npc_knowledge.get("knows", [])
    
    if "ALL" not in knows:
        # NPC shouldn't reveal culprit if they don't know
        if "draco" in reply_lower and "took" in reply_lower and npc_key != "draco":
            # Check if this NPC should know Draco is guilty
            if npc_key == "evelyn":
                # Evelyn only suspects, doesn't know for sure
                if "guilty" in reply_lower or "thief" in reply_lower:
                    validation["knowledge_violation"] = True
                    validation["coherence_score"] = 2
    
    return validation

# --- Deterministic Actions ---
def handle_deterministic_action(session: Dict, player_action: str) -> Optional[Message]:
    action = player_action.lower().strip()
    
    # GO TO [LOCATION]
    if action.startswith("go to "):
        target_loc = action[6:].strip()
        for key, loc in LOCATIONS.items():
            if key in target_loc:
                if session["location"] == key:
                    return Message(speaker="Narrator", text=f"You are already in {loc['display']}.", avatar_type="brown")
                
                session["location"] = key
                add_message(session, "Narrator", f"You travel to **{loc['display']}**.", "brown")
                return Message(speaker="Narrator", text=loc["description"], avatar_type="brown")
        
        return Message(speaker="Narrator", text=f"Can't find '{target_loc}'. Try: great hall, library, courtyard, dumbledore's office", avatar_type="brown")
    
    # INSPECT [OBJECT]
    if action.startswith("inspect ") or action.startswith("examine "):
        item = action.split(maxsplit=1)[1].strip()
        current_loc = session["location"]
        
        if current_loc in MYSTERY_TRUTH["clues"]:
            location_clues = MYSTERY_TRUTH["clues"][current_loc]
            
            for clue_id, clue_data in location_clues.items():
                if clue_id in item or item in clue_id:
                    if clue_data["description"] not in session["evidence"]:
                        session["evidence"].append(clue_data["description"])
                        session["clues_found"] += 1
                        
                        for suspect in clue_data.get("points_to", []):
                            session["evidence_against"][suspect] += 1
                        
                        if clue_data.get("solves_case"):
                            msg = f"🎉 **CASE SOLVED!** You found {clue_data['description']}! {clue_data['reveals']}"
                            return Message(speaker="Narrator", text=msg, avatar_type="brown")
                        
                        msg = f"📝 **New Evidence:** {clue_data['description']}. {clue_data['reveals']}"
                        return Message(speaker="Narrator", text=msg, avatar_type="brown")
                    else:
                        return Message(speaker="Narrator", text="You've already examined this thoroughly.", avatar_type="brown")
        
        return Message(speaker="Narrator", text=f"You inspect the **{item}** but find nothing unusual.", avatar_type="brown")
    
    return None

# --- Dialogue Detection ---
DIALOGUE_TRIGGERS = ["talk to ", "speak with ", "speak to ", "ask "]

def find_npc_in_text(player_text: str) -> Optional[Tuple[str, str]]:
    text_lower = player_text.lower()
    
    for npc_key, npc_data in NPCS.items():
        aliases = npc_data.get("aliases", [npc_key])
        for alias in aliases:
            if alias in text_lower:
                return (npc_key, npc_data["display"])
    
    return None

def is_dialogue_command(player_text: str) -> bool:
    text_lower = player_text.lower()
    return any(trigger in text_lower for trigger in DIALOGUE_TRIGGERS)

# --- API Endpoints ---
@app.post("/session/start")
def start_game_session():
    sid, doc = create_initial_session()
    return {"session_id": sid, "state": get_current_state(doc).dict()}

@app.post("/session/action")
def process_player_action(action: Action):
    sid = action.session_id
    if sid not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    session = SESSIONS[sid]
    player_text = action.text.strip()
    player_name = session.get("player_name", "You")
    
    add_message(session, player_name, player_text, "blue")
    
    # Handle deterministic actions first
    deterministic_reply = handle_deterministic_action(session, player_text)
    if deterministic_reply:
        return {"reply": [deterministic_reply.dict()], "state": get_current_state(session).dict()}
    
    # Handle NPC dialogue with caching
    if is_dialogue_command(player_text):
        npc_result = find_npc_in_text(player_text)
        if npc_result:
            npc_key, npc_name = npc_result
            
            # Check cache first
            evidence_count = session["evidence_against"].get(npc_key, 0)
            cached_response = response_cache.get(npc_key, player_text, evidence_count)
            
            if cached_response:
                # Use cached response
                reply = cached_response["npc_reply"]
                mentions = cached_response.get("mentions", [])
                tone = cached_response.get("tone", "neutral")
            else:
                # Generate new response
                try:
                    prompt = build_strategic_prompt(session, npc_key, player_text)
                    raw_response = call_gemini_llm(prompt)
                    reply, mentions, tone = parse_llm_response(raw_response)
                    
                    # Cache the response
                    response_data = {
                        "npc_reply": reply,
                        "mentions": mentions,
                        "tone": tone
                    }
                    response_cache.set(npc_key, player_text, evidence_count, response_data)
                    
                except Exception as e:
                    logging.error(f"LLM error: {e}")
                    reply = "I... I need a moment to gather my thoughts."
                    mentions = []
                    tone = "confused"
                    response_data = {"npc_reply": reply, "mentions": mentions, "tone": tone}
            
            # Validate response and record metrics
            validation_result = validate_npc_response(npc_key, reply, evidence_count)
            eval_metrics.record_interaction(
                npc_key=npc_key,
                question=player_text,
                response={"npc_reply": reply, "mentions": mentions, "tone": tone},
                evidence_count=evidence_count,
                validation_result=validation_result
            )
            
            # Add NPC response to timeline
            add_message(session, npc_name, reply, NPCS[npc_key]["avatar"])
            
            # Add newly revealed clues to evidence
            for mention in mentions:
                if mention not in session["evidence"]:
                    session["evidence"].append(mention)
                    session["clues_found"] += 1
            
            npc_message = Message(
                speaker=npc_name,
                text=reply,
                avatar_type=NPCS[npc_key]["avatar"]
            )
            
            return {
                "reply": [npc_message.dict()],
                "state": get_current_state(session).dict()
            }
        
        # NPC not found in dialogue attempt
        feedback = "I don't see that person here. Try talking to: Professor Dumbledore, Draco, or Evelyn."
        add_message(session, "Narrator", feedback, "brown")
        return {
            "reply": [Message(speaker="Narrator", text=feedback, avatar_type="brown").dict()],
            "state": get_current_state(session).dict()
        }
    
    # Default fallback for unrecognized commands
    feedback = "I don't understand that command. Try: 'go to [location]', 'inspect [object]', or 'talk to [NPC]'."
    add_message(session, "Narrator", feedback, "brown")
    return {
        "reply": [Message(speaker="Narrator", text=feedback, avatar_type="brown").dict()],
        "state": get_current_state(session).dict()
    }

@app.get("/")
def read_root():
    """Health check and API info."""
    return {
        "message": "Hogwarts Mystery Game Backend with Evaluation Framework",
        "status": "running",
        "llm_configured": llm_model is not None,
        "version": "v2.0-evaluation-framework",
        "endpoints": {
            "POST /session/start": "Start new game session",
            "POST /session/action": "Send player action",
            "GET /evaluation/report": "Get evaluation metrics report",
            "POST /evaluation/reset": "Reset evaluation metrics"
        }
    }

@app.get("/evaluation/report")
def get_evaluation_report():
    """
    Get comprehensive evaluation report showing Test → Measurement → Metric reconciliation.
    
    This endpoint demonstrates the evaluation framework:
    - Tests: What we're testing (dialogue consistency, knowledge boundaries, etc.)
    - Measurements: Raw data collected (violation counts, scores)
    - Metrics: Calculated scores and pass/fail determinations
    """
    return eval_metrics.generate_report()

@app.post("/evaluation/reset")
def reset_evaluation_metrics():
    """Reset all evaluation metrics and cache for fresh testing."""
    eval_metrics.reset()
    
    # Also clear cache for clean slate
    response_cache.cache.clear()
    response_cache.hits = 0
    response_cache.misses = 0
    
    return {
        "message": "Evaluation metrics and response cache have been reset",
        "metrics_reset": True,
        "cache_reset": True
    }

@app.get("/session/{session_id}/state")
def get_session_state(session_id: str):
    """Get current state of a session."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    session = SESSIONS[session_id]
    return {
        "session_id": session_id,
        "state": get_current_state(session).dict(),
        "evidence_against": session["evidence_against"]
    }

@app.get("/debug/mystery-truth")
def get_mystery_truth():
    """
    Debug endpoint to view the ground truth (only for testing/evaluation).
    In production, this should be removed or protected.
    """
    return MYSTERY_TRUTH

@app.get("/debug/cache-stats")
def get_cache_stats():
    """Get cache performance statistics."""
    return response_cache.get_stats()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

