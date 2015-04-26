# aBOTcalypse
A bot king-of-the-hill game for PPCG.

Design a bot to compete in a King-of-the-Hill challenge! [Here's a replay of a default bot game.](http://gfycat.com/AnnualBestBrontosaurus)

A valid bot must accept a multiline string representation of the region of the board it can see, and output a move for the bot.

### Mechanics
This is a survival game. The apocalypse has come, and only bots remain. A bot's total score is equal to the number of turns it survives, accumulated over X games (X is probably 10). Each bot is given a random starting location, at elevation 0. In a given move, a bot can rest, move, throw a rock, or drop a rock. Bots can share space with stationary rocks, but a bot that collides with another bot or a meteor is killed , as is a bot hit by a thrown rock.
+ Gravity: bots and rocks must rest on top of the floor of the board or on top of another rock. Unsupported bots or rocks will fall until they are supported; a fall of greater than one space will kill a bot, and a bot underneath a falling rock or bot is also killed. This means that trying to move or drop up will only work if the bot is currently sharing a space with a rock (otherwise the bot/rock will fall back down 1 space).
+ Meteors: Each turn a meteor enters the board from the top. A meteor has a velocity of magnitude 2, with a random angle and starting position. Meteors fall in a straight line until they hit something, at which point they disappear.
+ Projectiles: A bot can choose to throw a rock any distance up to its elevation. A thrown rock moves in a straight line until it hits something (all in one turn, unlike a meteor; thrown rocks don't appear on the board), at a slope of `- elevation / max distance`. **Note that thrown rocks begin their trajectory at x +- 1 square.** For example, if a bot is at an elevation of 5, and throws left a distance of 1, the rock will begin at `(x-1,5)` and end at `(x-2,0)`. Collision is only checked in steps of `dx=1`.

### Input
Each bot can see a square 20 pixels in each direction (Chebyshev distance = 20), up to the boundaries of the board. There are 8 different characters in each input string:
+ `'#'` (board boundary)
+ `'.'` (air)
+ `'@`' (meteor)
+ `'&'` (rock)
+ `'e'`/`'s'` (an enemy bot, or itself)
+ `'E'`/`'S'` (an enemy bot, or itself, sharing a space with a rock)

Here's an example input (line breaks will be `\n`):
```
..............................#
..............................#
..............................#
..............................#
..............................#
..............................#
..............................#
..............................#
..............................#
..............................#
..............................#
..............................#
..............................#
..............@...............#
.....................E........#
.....................&........#
.....................&........#
.....................&........#
.....................&........#
...........@.........&........#
....................s&........#
###############################
```

### Output
There are four actions that a bot can take each turn.
+ `rest` (literally sit and do nothing)
+ `move <direction>` moves the bot one space in any of the four directions, `up`, `down`, `left`, or `right`. Movement causes the bot to fall if the new space is not supported by the floor or a rock (`fall > 1 = bot.kill()`).
+ `drop <direction>` drops a rock in the indicated direction. Dropping a rock up or to the side causes it to fall until supported (possibly falling onto the bot during `drop up`). `drop down` places a rock in the same position as the bot, if there is not a rock there already.
+ `throw <direction> <distance>` throws a rock as per the "projectiles" mechanics above, with the indicated max distance. Max distance is irrelevant for throwing upward or downward - the projectile collides with the square below (for `down`), or attempts to collide with the square above (for `up`) and then with the bot's square if it doesn't hit anything (killing the bot).

A bot in the contest must output a scalar string with its action upon receiving the input string.

### Interface
A bot must consist of a single program which can be called via a python 2 subprocess. Any commands should be indicated, and will be saved in a file called `command.txt `; before a game begins, the controller will execute each command in `command.txt`, in order, and then the final command will be used to pass input to the bot.

A bot may have a single storage file called `storage.txt` in its folder; the "Default Thrower" bot shows an example implementation, using json to save its state during various turns. In addition, feel free to include debugging output in a write-only "errlog.txt", which I'll pass along in case your bot fails during a run. I'll make sure to run several tests with each bot, to try and find any errors beforehand.
