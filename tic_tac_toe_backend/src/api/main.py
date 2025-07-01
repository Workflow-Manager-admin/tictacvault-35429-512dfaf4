from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import jwt, JWTError
import uuid
import os

from .models import UserCreate, UserOut, TokenOut, GameCreate, MovePlay, GameState, GameHistoryOut
from .db import hash_password, verify_password

# --- JWT & Auth Config ---
SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey-for-demo-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(
    title="Tic Tac Toe Backend API",
    version="1.0.0",
    description="A RESTful API backend for Tic Tac Toe game with user management and persistent games."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# In-memory users/games for POC; replace with DB ops
_fake_users = {}
_fake_games = {}

def get_current_user(token: str = Depends(oauth2_scheme)) -> UserOut:
    """User authentication dependency."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user = _fake_users.get(user_id)
        if not user:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

# --- Health ---
@app.get("/")
def health_check():
    """API health check"""
    return {"message": "Healthy"}

# --- Sign up ---
@app.post("/signup", response_model=UserOut, summary="User Sign Up", tags=["Auth & Users"])
def signup(user: UserCreate):
    """Create a user account with username & password."""
    if any(u.username == user.username for u in _fake_users.values()):
        raise HTTPException(status_code=400, detail="Username already registered")
    uid = str(uuid.uuid4())
    _fake_users[uid] = UserOut(id=uid, username=user.username)
    _fake_users[uid].hashed_password = hash_password(user.password)
    return _fake_users[uid]

# --- Login (Token) ---
@app.post("/token", response_model=TokenOut, summary="User Login, returns JWT token", tags=["Auth & Users"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and provide JWT token."""
    user = next((u for u in _fake_users.values() if u.username == form_data.username), None)
    if not user or not verify_password(form_data.password, getattr(user, "hashed_password", "")):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token(data={"sub": str(user.id)})
    return TokenOut(access_token=token)

# --- Start New Game ---
@app.post("/games", response_model=GameState, summary="Start new Tic Tac Toe game", tags=["Game"])
def start_game(game: GameCreate, user: UserOut = Depends(get_current_user)):
    """Creates a new game for the authenticated user."""
    game_id = uuid.uuid4()
    state = GameState(
        id=game_id,
        board=[[None, None, None], [None, None, None], [None, None, None]],
        next_player=user.username,
        winner=None,
        status="in_progress",
        created_at=datetime.utcnow(),
    )
    _fake_games[str(game_id)] = {
        "state": state,
        "players": [user.username],
        "moves": [],
    }
    return state

# --- Play Move ---
@app.post("/games/{game_id}/move", response_model=GameState, summary="Play a move", tags=["Game"])
def play_move(game_id: uuid.UUID, move: MovePlay, user: UserOut = Depends(get_current_user)):
    """Play a move (x, y) as the current user."""
    game = _fake_games.get(str(game_id))
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    state: GameState = game["state"]
    if state.status != "in_progress":
        raise HTTPException(status_code=400, detail="Game is over")
    if state.board[move.x][move.y] is not None:
        raise HTTPException(status_code=400, detail="Cell already occupied")
    symbol = "X" if (len(game["moves"]) % 2 == 0) else "O"
    state.board[move.x][move.y] = symbol
    game["moves"].append(move)
    # Check for win/draw here (simplified)
    if check_winner(state.board, symbol):
        state.status = "won"
        state.winner = user.username
    elif all(cell for row in state.board for cell in row):
        state.status = "draw"
    else:
        state.next_player = user.username if symbol == "O" else game["players"][0]
    return state

def check_winner(board, symbol):
    # Check rows, cols, diags for winner
    for i in range(3):
        if all(board[i][j] == symbol for j in range(3)) or all(board[j][i] == symbol for j in range(3)):
            return True
    if all(board[i][i] == symbol for i in range(3)) or all(board[i][2 - i] == symbol for i in range(3)):
        return True
    return False

# --- Game State ---
@app.get("/games/{game_id}", response_model=GameState, summary="Get game state", tags=["Game"])
def get_game_state(game_id: uuid.UUID, user: UserOut = Depends(get_current_user)):
    """Fetch a specific game's state."""
    game = _fake_games.get(str(game_id))
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game["state"]

# --- Game History By ID ---
@app.get("/games/{game_id}/history", response_model=GameHistoryOut, summary="View game history", tags=["Game"])
def get_game_history(game_id: uuid.UUID, user: UserOut = Depends(get_current_user)):
    """View move-by-move history for a game by ID."""
    game = _fake_games.get(str(game_id))
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return GameHistoryOut(
        id=game_id,
        created_at=game["state"].created_at,
        players=game["players"],
        moves=game["moves"],
        status=game["state"].status,
        winner=game["state"].winner,
    )
