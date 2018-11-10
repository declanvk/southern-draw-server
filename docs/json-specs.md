
## Room Number (1)
Sent from server to web client as soon as socket is opened

```json
{
   "pkt_name": "room_number",
   "room_number": room number (string)
}
```

## Send Code (2)
Sent from iOS client to server when user types in code.

```json
{
   "pkt_name": "code",
   "room_number": room number (string),
   "user_name": user name (string)
}
```

## Send Players (3)
Sent from server to web client when a player joins.
```json
{
   "pkt_name": "players",
   "players": [
      {"user_name": user 1 name (string)},
      {"user_name": user 2 name (string)}
   ]
}
```

## Send Start Game (4)
Sent from server to iOS client and web client when game starts.

```json
{
   "pkt_name": "start_game",
   "prompts": [
      {
         "user_name": user 1 name (string),
         "prompt": prompt 1 (string)
      },
      {
         "user_name": user 2 name (string),
         "prompt": prompt 2 (string)
      }
   ]
}
```

## Send Draw Data iOS (5)
Sent from iOS client to server when line is drawn.

```json
{
   "pkt_name": "draw_data_ios",
   "color": color (string)
   "points": [
      {"x": x1 (int), "y": y1 (int)},
      {"x": x2 (int), "y": y2 (int)},
   ]
}
```

## Send Draw Data Web (5*)
Sent from server to web client to server when draw data is received

```json
{
   "pkt_name": "draw_data_web",
   "color": color (string)
   "draw_data": [
      { 
         "user_name": user 1 name (string)
         "points": [
            {"x": x1 (int), "y": y1 (int)},
            {"x": x2 (int), "y": y2 (int)},
         ]
      }
   ]
}
```