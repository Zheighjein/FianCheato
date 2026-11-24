import os
import cv2
import mss
import numpy as np

# Standard piece codes: uppercase = White, lowercase = Black
PIECE_FILES = {
    "P": "wP.png", "N": "wN.png", "B": "wB.png",
    "R": "wR.png", "Q": "wQ.png", "K": "wK.png",
    "p": "bP.png", "n": "bN.png", "b": "bB.png",
    "r": "bR.png", "q": "bQ.png", "k": "bK.png",
}


class BoardVision:
    def __init__(self, template_dir: str = "templates", threshold: float = 0.45):
        self.sct = mss.mss()
        self.template_dir = template_dir
        self.threshold = threshold
        self.templates = self._load_templates(template_dir)

    def _preprocess(self, img_gray: np.ndarray) -> np.ndarray:
        """Extract edges and blur slightly so 1-2px shifts still match cleanly."""
        edges = cv2.Canny(img_gray, 40, 120)
        return cv2.GaussianBlur(edges, (5, 5), 0)

    def _center_brightness(self, img_gray: np.ndarray) -> float:
        """Average brightness of the inner 40% of the piece (White vs Black check)."""
        h, w = img_gray.shape
        y1, y2 = int(h * 0.30), int(h * 0.70)
        x1, x2 = int(w * 0.30), int(w * 0.70)
        return float(np.mean(img_gray[y1:y2, x1:x2]))

    def _load_templates(self, template_dir: str) -> dict:
        loaded = {}
        for symbol, filename in PIECE_FILES.items():
            path = os.path.join(template_dir, filename)
            if os.path.exists(path):
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                loaded[symbol] = (
                    self._preprocess(img),
                    self._center_brightness(img),
                )
        return loaded

    def capture_board(self, region: dict) -> np.ndarray:
        """region = {'top': y, 'left': x, 'width': w, 'height': h}"""
        raw = np.array(self.sct.grab(region))
        return cv2.cvtColor(raw, cv2.COLOR_BGRA2GRAY)

    def detect_starting_perspective(self, board_gray: np.ndarray) -> str:
        """Auto-detects White vs Black on a starting board by comparing piece brightness."""
        h, w = board_gray.shape
        sq_h, sq_w = h / 8.0, w / 8.0

        def avg_rows_brightness(rows):
            vals = []
            for row in rows:
                for col in range(8):
                    y1, y2 = int(row * sq_h), int((row + 1) * sq_h)
                    x1, x2 = int(col * sq_w), int((col + 1) * sq_w)
                    vals.append(self._center_brightness(board_gray[y1:y2, x1:x2]))
            return float(np.mean(vals))

        top_bright = avg_rows_brightness([0, 1])
        bottom_bright = avg_rows_brightness([6, 7])
        return "w" if bottom_bright >= top_bright else "b"

    def detect_perspective_from_grid(self, grid: list[list[str]]) -> str:
        """Auto-detects perspective from recognized pieces (White lower = 'w', Black lower = 'b')."""
        white_rows = []
        black_rows = []
        for r, row in enumerate(grid):
            for cell in row:
                if cell.isupper():
                    white_rows.append(r)
                elif cell.islower():
                    black_rows.append(r)

        if white_rows and black_rows:
            return "w" if np.mean(white_rows) >= np.mean(black_rows) else "b"
        return "w"

    def capture_starting_templates(self, board_gray: np.ndarray, perspective: str = "auto"):
        """Auto-crops all 12 piece templates right-side up for either White or Black."""
        os.makedirs(self.template_dir, exist_ok=True)
        if perspective == "auto":
            perspective = self.detect_starting_perspective(board_gray)

        h, w = board_gray.shape
        sq_h, sq_w = h / 8.0, w / 8.0

        start_squares = {
            (0, 0): "bR.png", (0, 1): "bN.png", (0, 2): "bB.png",
            (0, 3): "bQ.png", (0, 4): "bK.png", (1, 0): "bP.png",
            (6, 0): "wP.png", (7, 0): "wR.png", (7, 1): "wN.png",
            (7, 2): "wB.png", (7, 3): "wQ.png", (7, 4): "wK.png",
        }

        for (row, col), filename in start_squares.items():
            # Flip square coordinates (not pixels) if Black is at the bottom
            r = 7 - row if perspective == "b" else row
            c = 7 - col if perspective == "b" else col

            y1, y2 = int(r * sq_h), int((r + 1) * sq_h)
            x1, x2 = int(c * sq_w), int((c + 1) * sq_w)
            my, mx = int((y2 - y1) * 0.15), int((x2 - x1) * 0.15)
            crop = board_gray[y1 + my : y2 - my, x1 + mx : x2 - mx]
            cv2.imwrite(os.path.join(self.template_dir, filename), crop)

        self.templates = self._load_templates(self.template_dir)
        return len(self.templates), perspective

    def _classify_square(self, sq_gray: np.ndarray) -> str:
        if not self.templates:
            return ""

        sq_proc = self._preprocess(sq_gray)

        # Quick empty-square check (almost no edges inside the square)
        if np.mean(sq_proc) < 3.5:
            return ""

        h, w = sq_proc.shape
        tw, th = max(10, int(w * 0.80)), max(10, int(h * 0.80))

        best_symbol = ""
        best_score = self.threshold

        for symbol, (tmpl_edges, tmpl_bright) in self.templates.items():
            resized = cv2.resize(tmpl_edges, (tw, th), interpolation=cv2.INTER_AREA)
            res = cv2.matchTemplate(sq_proc, resized, cv2.TM_CCOEFF_NORMED)
            _, edge_score, _, max_loc = cv2.minMaxLoc(res)

            # Compare interior brightness at the matched location to separate White vs Black
            mx, my = max_loc
            matched_patch = sq_gray[my : my + th, mx : mx + tw]
            patch_bright = self._center_brightness(matched_patch)
            color_penalty = 0.40 * (abs(patch_bright - tmpl_bright) / 255.0)

            final_score = edge_score - color_penalty
            if final_score > best_score:
                best_score = final_score
                best_symbol = symbol

        return best_symbol

    def board_to_fen(self, board_gray: np.ndarray, perspective: str = "auto") -> tuple[str, str]:
        """Converts an 8x8 grayscale board image into (FEN, detected_perspective)."""
        h, w = board_gray.shape
        sq_h, sq_w = h / 8.0, w / 8.0

        grid = []
        for row in range(8):
            row_pieces = []
            for col in range(8):
                y1, y2 = int(row * sq_h), int((row + 1) * sq_h)
                x1, x2 = int(col * sq_w), int((col + 1) * sq_w)
                my, mx = int((y2 - y1) * 0.05), int((x2 - x1) * 0.05)
                crop = board_gray[y1 + my : y2 - my, x1 + mx : x2 - mx]
                row_pieces.append(self._classify_square(crop))
            grid.append(row_pieces)

        if perspective == "auto":
            perspective = self.detect_perspective_from_grid(grid)

        if perspective == "b":
            grid = [row[::-1] for row in grid[::-1]]

        fen_rows = []
        for row in grid:
            empty = 0
            fen_row = ""
            for cell in row:
                if cell == "":
                    empty += 1
                else:
                    if empty:
                        fen_row += str(empty)
                        empty = 0
                    fen_row += cell
            if empty:
                fen_row += str(empty)
            fen_rows.append(fen_row)

        placement = "/".join(fen_rows)

        # Only grant castling rights if the King and Rook are on their home squares
        castling = ""
        if grid[7][4] == "K":
            if grid[7][7] == "R":
                castling += "K"
            if grid[7][0] == "R":
                castling += "Q"
        if grid[0][4] == "k":
            if grid[0][7] == "r":
                castling += "k"
            if grid[0][0] == "r":
                castling += "q"
        if not castling:
            castling = "-"

        return f"{placement} {perspective} {castling} - 0 1", perspective