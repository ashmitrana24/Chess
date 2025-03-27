from flask import Flask, render_template, jsonify, request
import copy

app = Flask(__name__)

class ChessGame:
    def __init__(self):
        self.board = self.initialize_board()
        self.current_turn = 'w'  # w for white, b for black
        self.move_history = []
        self.white_king_pos = (7, 4)
        self.black_king_pos = (0, 4)
        self.castling_rights = {
            'w': {'kingside': True, 'queenside': True},
            'b': {'kingside': True, 'queenside': True}
        }
        self.en_passant_target = None
        
    def initialize_board(self):
        # Initialize the chess board with pieces
        board = [
            ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
            ['bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP'],
            ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR']
        ]
        return board

    def is_valid_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]
        
        # Check if it's the correct player's turn
        if piece[0] != self.current_turn:
            return False, "Not your turn"
            
        # Check if move is within board boundaries
        if not (0 <= to_row < 8 and 0 <= to_col < 8):
            return False, "Move outside board"
            
        # Can't capture own piece
        if self.board[to_row][to_col] != '--' and self.board[to_row][to_col][0] == piece[0]:
            return False, "Cannot capture own piece"
            
        piece_type = piece[1]
        
        # Validate move based on piece type
        if piece_type == 'P':
            valid = self.is_valid_pawn_move(from_pos, to_pos)
        elif piece_type == 'R':
            valid = self.is_valid_rook_move(from_pos, to_pos)
        elif piece_type == 'N':
            valid = self.is_valid_knight_move(from_pos, to_pos)
        elif piece_type == 'B':
            valid = self.is_valid_bishop_move(from_pos, to_pos)
        elif piece_type == 'Q':
            valid = self.is_valid_queen_move(from_pos, to_pos)
        elif piece_type == 'K':
            valid = self.is_valid_king_move(from_pos, to_pos)
        else:
            return False, "Invalid piece"
            
        if not valid:
            return False, "Invalid move for this piece"
            
        # Check if move puts/leaves own king in check
        test_board = copy.deepcopy(self)
        test_board.make_move(from_pos, to_pos, test=True)
        if test_board.is_in_check(self.current_turn):
            return False, "Move would put/leave king in check"
            
        return True, "Valid move"

    def is_valid_pawn_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]
        direction = -1 if piece[0] == 'w' else 1
        
        # Normal one square move
        if to_col == from_col and to_row == from_row + direction and self.board[to_row][to_col] == '--':
            return True
            
        # Initial two square move
        if ((piece[0] == 'w' and from_row == 6) or (piece[0] == 'b' and from_row == 1)):
            if to_col == from_col and to_row == from_row + 2*direction:
                if self.board[from_row + direction][from_col] == '--' and self.board[to_row][to_col] == '--':
                    self.en_passant_target = (from_row + direction, from_col)
                    return True
                    
        # Capture moves
        if abs(to_col - from_col) == 1 and to_row == from_row + direction:
            # Normal capture
            if self.board[to_row][to_col] != '--' and self.board[to_row][to_col][0] != piece[0]:
                return True
            # En passant
            if (to_row, to_col) == self.en_passant_target:
                return True
                
        return False

    def is_valid_rook_move(self, from_pos, to_pos):
        return self.is_clear_path_straight(from_pos, to_pos)

    def is_valid_knight_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        return (abs(to_row - from_row) == 2 and abs(to_col - from_col) == 1) or \
               (abs(to_row - from_row) == 1 and abs(to_col - from_col) == 2)

    def is_valid_bishop_move(self, from_pos, to_pos):
        return self.is_clear_path_diagonal(from_pos, to_pos)

    def is_valid_queen_move(self, from_pos, to_pos):
        return self.is_clear_path_straight(from_pos, to_pos) or \
               self.is_clear_path_diagonal(from_pos, to_pos)

    def is_valid_king_move(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Normal king move
        if abs(to_row - from_row) <= 1 and abs(to_col - from_col) <= 1:
            return True
            
        # Castling
        if from_row == to_row and abs(to_col - from_col) == 2:
            if not self.can_castle(from_pos, to_pos):
                return False
            return True
            
        return False

    def can_castle(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Check if king has moved
        if self.current_turn == 'w' and not self.castling_rights['w']['kingside'] and not self.castling_rights['w']['queenside']:
            return False
        if self.current_turn == 'b' and not self.castling_rights['b']['kingside'] and not self.castling_rights['b']['queenside']:
            return False
            
        # Check if king is in check
        if self.is_in_check(self.current_turn):
            return False
            
        # Kingside castling
        if to_col > from_col:
            if not self.castling_rights[self.current_turn]['kingside']:
                return False
            # Check if path is clear
            return self.is_clear_path_straight(from_pos, (from_row, 7)) and \
                   not self.is_square_attacked((from_row, from_col + 1), self.current_turn) and \
                   not self.is_square_attacked((from_row, from_col + 2), self.current_turn)
                   
        # Queenside castling
        else:
            if not self.castling_rights[self.current_turn]['queenside']:
                return False
            # Check if path is clear
            return self.is_clear_path_straight(from_pos, (from_row, 0)) and \
                   not self.is_square_attacked((from_row, from_col - 1), self.current_turn) and \
                   not self.is_square_attacked((from_row, from_col - 2), self.current_turn)

    def is_clear_path_straight(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        if from_row != to_row and from_col != to_col:
            return False
            
        row_step = 0 if from_row == to_row else (to_row - from_row) // abs(to_row - from_row)
        col_step = 0 if from_col == to_col else (to_col - from_col) // abs(to_col - from_col)
        
        current_row = from_row + row_step
        current_col = from_col + col_step
        
        while (current_row, current_col) != (to_row, to_col):
            if self.board[current_row][current_col] != '--':
                return False
            current_row += row_step
            current_col += col_step
            
        return True

    def is_clear_path_diagonal(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        if abs(to_row - from_row) != abs(to_col - from_col):
            return False
            
        row_step = (to_row - from_row) // abs(to_row - from_row)
        col_step = (to_col - from_col) // abs(to_col - from_col)
        
        current_row = from_row + row_step
        current_col = from_col + col_step
        
        while (current_row, current_col) != (to_row, to_col):
            if self.board[current_row][current_col] != '--':
                return False
            current_row += row_step
            current_col += col_step
            
        return True

    def is_in_check(self, color):
        king_pos = self.white_king_pos if color == 'w' else self.black_king_pos
        return self.is_square_attacked(king_pos, color)

    def is_square_attacked(self, pos, defending_color):
        for i in range(8):
            for j in range(8):
                piece = self.board[i][j]
                if piece != '--' and piece[0] != defending_color:
                    if self.is_valid_move((i, j), pos)[0]:
                        return True
        return False

    def is_checkmate(self, color):
        if not self.is_in_check(color):
            return False
            
        # Check all possible moves for all pieces
        for i in range(8):
            for j in range(8):
                piece = self.board[i][j]
                if piece != '--' and piece[0] == color:
                    for to_row in range(8):
                        for to_col in range(8):
                            if self.is_valid_move((i, j), (to_row, to_col))[0]:
                                # Try the move
                                test_board = copy.deepcopy(self)
                                test_board.make_move((i, j), (to_row, to_col), test=True)
                                if not test_board.is_in_check(color):
                                    return False
        return True

    def make_move(self, from_pos, to_pos, test=False):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]
        
        # Handle castling
        if piece[1] == 'K' and abs(to_col - from_col) == 2:
            # Kingside castling
            if to_col > from_col:
                self.board[to_row][to_col-1] = self.board[to_row][7]
                self.board[to_row][7] = '--'
            # Queenside castling
            else:
                self.board[to_row][to_col+1] = self.board[to_row][0]
                self.board[to_row][0] = '--'
                
        # Handle en passant capture
        if piece[1] == 'P' and (to_row, to_col) == self.en_passant_target:
            self.board[from_row][to_col] = '--'
            
        # Update king position
        if piece[1] == 'K':
            if piece[0] == 'w':
                self.white_king_pos = (to_row, to_col)
            else:
                self.black_king_pos = (to_row, to_col)
                
        # Update castling rights
        if piece[1] == 'K':
            self.castling_rights[piece[0]]['kingside'] = False
            self.castling_rights[piece[0]]['queenside'] = False
        elif piece[1] == 'R':
            if from_col == 0:  # Queenside rook
                self.castling_rights[piece[0]]['queenside'] = False
            elif from_col == 7:  # Kingside rook
                self.castling_rights[piece[0]]['kingside'] = False
                
        # Make the move
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = '--'
        
        # Handle pawn promotion
        if piece[1] == 'P' and (to_row == 0 or to_row == 7):
            self.board[to_row][to_col] = piece[0] + 'Q'  # Automatically promote to queen
            
        if not test:
            # Clear en passant target
            self.en_passant_target = None
            # Switch turns
            self.current_turn = 'b' if self.current_turn == 'w' else 'w'
            # Add move to history
            self.move_history.append((from_pos, to_pos))

game = ChessGame()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_board')
def get_board():
    return jsonify({
        'board': game.board,
        'current_turn': game.current_turn,
        'in_check': game.is_in_check(game.current_turn),
        'checkmate': game.is_checkmate(game.current_turn)
    })

@app.route('/move_piece', methods=['POST'])
def move_piece():
    data = request.get_json()
    from_pos = tuple(data['from'])
    to_pos = tuple(data['to'])
    
    valid, message = game.is_valid_move(from_pos, to_pos)
    
    if valid:
        game.make_move(from_pos, to_pos)
        is_check = game.is_in_check(game.current_turn)
        is_checkmate = game.is_checkmate(game.current_turn)
        
        return jsonify({
            'success': True,
            'board': game.board,
            'current_turn': game.current_turn,
            'in_check': is_check,
            'checkmate': is_checkmate,
            'message': 'Checkmate!' if is_checkmate else ('Check!' if is_check else 'Move successful')
        })
    
    return jsonify({
        'success': False,
        'message': message
    })

if __name__ == '__main__':
    app.run(debug=True)