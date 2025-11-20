"""
Character Management API - Track player characters and professions
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
from loguru import logger

router = APIRouter(prefix="/api/characters", tags=["Characters"])

# Data models
class Profession(BaseModel):
    name: str
    skill_level: int
    max_skill: int = 100
    specialization: Optional[str] = None

class Character(BaseModel):
    name: str
    realm: str
    faction: str
    level: int
    gold: int
    professions: List[Profession]

class CharacterDB:
    """Simple JSON-based character storage."""
    
    def __init__(self):
        self.db_path = "/app/ml/data/characters.json"
        self.characters = self._load()
        
    def _load(self) -> List[Dict]:
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                return json.load(f)
        return []
    
    def _save(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, 'w') as f:
            json.dump(self.characters, f, indent=2)
    
    def add(self, character: Character) -> Dict:
        char_dict = character.dict()
        # Check if exists
        existing = next((c for c in self.characters if c['name'] == character.name and c['realm'] == character.realm), None)
        if existing:
            raise ValueError(f"Character {character.name}-{character.realm} already exists")
        
        self.characters.append(char_dict)
        self._save()
        return char_dict
    
    def get(self, name: str, realm: str) -> Optional[Dict]:
        return next((c for c in self.characters if c['name'] == name and c['realm'] == realm), None)
    
    def update(self, name: str, realm: str, updates: Dict) -> Dict:
        char = self.get(name, realm)
        if not char:
            raise ValueError(f"Character {name}-{realm} not found")
        
        char.update(updates)
        self._save()
        return char
    
    def list_all(self) -> List[Dict]:
        return self.characters

# Initialize DB
char_db = CharacterDB()

# Endpoints
@router.post("/", response_model=Character)
async def create_character(character: Character):
    """Add a new character."""
    try:
        result = char_db.add(character)
        logger.info(f"Created character: {character.name}-{character.realm}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/", response_model=List[Character])
async def list_characters():
    """List all characters."""
    return char_db.list_all()

@router.get("/{name}/{realm}", response_model=Character)
async def get_character(name: str, realm: str):
    """Get specific character."""
    char = char_db.get(name, realm)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    return char

@router.put("/{name}/{realm}", response_model=Character)
async def update_character(name: str, realm: str, updates: Dict[str, Any]):
    """Update character details."""
    try:
        result = char_db.update(name, realm, updates)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{name}/{realm}/crafting-guide")
async def get_crafting_guide(name: str, realm: str, profession: str, target_skill: int = 100):
    """Generate profession leveling guide for character."""
    from ml.pipeline.leveling_guide import LevelingGuideGenerator
    
    char = char_db.get(name, realm)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Find profession
    prof = next((p for p in char['professions'] if p['name'].lower() == profession.lower()), None)
    if not prof:
        raise HTTPException(status_code=404, detail=f"Character doesn't have {profession}")
    
    # Generate guide
    generator = LevelingGuideGenerator()
    guide = generator.generate_guide(
        profession=profession,
        current_skill=prof['skill_level'],
        target_skill=target_skill,
        character_gold=char['gold']
    )
    
    return guide
