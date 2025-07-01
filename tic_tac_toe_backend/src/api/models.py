from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

# PUBLIC_INTERFACE
class UserCreate(BaseModel):
    """Model for user sign up."""
    username: str = Field(..., description="The unique username")
    password: str = Field(..., description="User password (plaintext; will be hashed)")

# PUBLIC_INTERFACE
class UserOut(BaseModel):
    """Model returned for user info."""
    id: uuid.UUID
    username: str

# PUBLIC_INTERFACE
class TokenOut(BaseModel):
    """Model for login/signup response with token."""
    access_token: str
    token_type: str = "bearer"

# PUBLIC_INTERFACE
class GameCreate(BaseModel):
    """Request model for starting a new game."""
    opponent: Optional[str] = Field(None, description="Opponent's username (optional, for future extension)")

# PUBLIC_INTERFACE
class MovePlay(BaseModel):
    """Request model for playing a move."""
    x: int = Field(..., description="Row index (0-2)")
    y: int = Field(..., description="Column index (0-2)")

# PUBLIC_INTERFACE
class GameState(BaseModel):
    """Current game state."""
    id: uuid.UUID
    board: List[List[Optional[str]]]
    next_player: str
    winner: Optional[str]
    status: str
    created_at: datetime

# PUBLIC_INTERFACE
class GameHistoryOut(BaseModel):
    """Model for single game history."""
    id: uuid.UUID
    created_at: datetime
    players: List[str]
    moves: List[MovePlay]
    status: str
    winner: Optional[str]
