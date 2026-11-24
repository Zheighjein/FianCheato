import chess
import chess.engine


class EngineManager:
    def __init__(self, stockfish_path: str, time_limit: float = 0.25):
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        self.time_limit = time_limit

    def analyze(self, fen: str):
        """Returns (best_move_uci, eval_str) or (None, 'Invalid board')."""
        try:
            board = chess.Board(fen)
            if not board.is_valid():
                return None, "Invalid board"
            info = self.engine.analyse(
                board, chess.engine.Limit(time=self.time_limit)
            )
            pv = info.get("pv")
            if not pv:
                return None, "No move"

            best_move = pv[0].uci()  # e.g., "e2e4"
            score = info["score"].white()
            if score.is_mate():
                eval_str = f"M{score.mate()}"
            else:
                eval_str = f"{score.score() / 100.0:+.2f}"
            return best_move, eval_str
        except Exception as e:
            return None, f"Error: {e}"

    def close(self):
        self.engine.quit()