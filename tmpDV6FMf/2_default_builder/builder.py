'''A bot which builds and climbs a tower.
It builds before it climbs, because building is fun.

Call with "$ python builder.py <input>"'''

def bot(board):
    symbol = 's' if board.count('s') else 'S'
    if symbol == 'S':
        return 'move up'
    else:
        return 'drop down'
    return
    #trying a new algorithm that doesn't care about surroundings
    
    board = board.splitlines()
    #find self
    for y, row in enumerate(board):
        x = row.find(symbol)
        if x >= 0:
            break
    else:
        return 'rest' #can't find self? better stand still.
    if y == 0: #this shouldn't really happen, but whatev
        return 'rest'
    else:
        return {'@': 'rest', #yikes don't move
                '&': 'move up', #climb the tower
                'e': 'throw up 1', #haters tryna climb my tower
                'E': 'throw up 1',
                '#': 'rest', #at the top
                '.': 'drop up' #build the tower
                }[board[y-1][x]]
    

if __name__ == "__main__":
    import sys
    print bot(sys.argv[1])
