
## Room Number (1)
Sent from server to web client as soon as socket is opened

```json
{
    "pkt_name": "new_room",
    "room_number": "room number (string)"
}
```

## Send Code (2)
Sent from iOS client to server when user types in code.

```json
{
    "pkt_name": "join_room",
    "room_number": "room number (string)",
    "user_name": "user name (string)",
    "screen_dim": {
        "width": "width in pixels (int)",
        "height": "height in pixels (int)"
    }
}
```

## Send Code (2\*)
Send from server to iOS client to indicate that it was a correct room code.
Emit a simple string with event name `join_room_status`


## Send Players (3)
Sent from server to web client when a player joins.
```json
{
    "pkt_name": "all_players",
    "players": [
        {"user_name": "user 1 name (string)"},
        {"user_name": "user 2 name (string)"}
    ]
}
```

## Send Start Game (4)
Sent from server to iOS client when the game starts

```json
{
    "pkt_name": "start_game_ios",
    "prompt": "Prompt (string)"
}
```
## Send Start Game (4*)
Sent from server to web when the game starts

```json
{
    "pkt_name": "start_game_web",
    "player_user_names": [ "name (String)", "..."],
}
```

## Send Draw Data iOS (5)
Sent from iOS client to server when line is drawn.
### Next Points in Current Line
```json
{
    "pkt_name": "draw_data_ios_move",
    "color": "color (string)",
    "points": [
        {"x": "x1 (int)", "y": "y1 (int)"},
        {"x": "x2 (int)", "y": "y2 (int)"},
    ],
}
```
### End the Current Line and Start New Line
```json
{
    "pkt_name": "draw_data_ios_end_line",
}
```

## Send Draw Data Web (5*)
Sent from server to web client to server when draw data is received

```json
{
    "pkt_name": "draw_data_web",
    "user_name": "user 1 name (string)",
    "screen_dim": {
        "width": "width in pixels (int)",
        "height": "height in pixels (int)"
    },
    "lines": [
        {
            "color": "color (string)",
            "points": [
                {"x": "x1 (int)", "y": "y1 (int)"},
                {"x": "x2 (int)", "y": "y2 (int)"},
            ]
        },
        {
            "color": "color (string)",
            "points": [
                {"x": "x1 (int)", "y": "y1 (int)"},
                {"x": "x2 (int)", "y": "y2 (int)"},
            ]
        },
    ]
}
```
