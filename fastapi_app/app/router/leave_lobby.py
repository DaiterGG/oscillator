from fastapi import APIRouter, HTTPException, Request
from ..model.lobbies import lobbies
from ..model.connected_user import ConnectedUser

router = APIRouter()

@router.post("/api/leave_lobby")
async def leave_lobby(request: Request):
    lobby_id = request.query_params.get("lobby_id")
    if not lobby_id:
        raise HTTPException(status_code=400, detail="lobby_id is required")

    u_id = request.cookies.get("user_id")
    if not u_id:
        raise HTTPException(status_code=400, detail="user_id cookie is required")

    lobby = lobbies.get_or_status(lobby_id, 404)
    
    if u_id not in lobby.users:
        raise HTTPException(status_code=404, detail="user not in lobby")

    user = lobby.users[u_id]
    
    # Cancel reconnect task if exists
    if user.reconnect_task:
        user.reconnect_task.cancel()
        user.reconnect_task = None
        
    # Perform immediate cleanup
    if u_id == lobby.author.author_id:
        result = lobby.get_new_owner()
        if result:
            new_owner_id, new_owner_user, new_secret = result
            lobby.transfer_ownership(new_owner_id, new_secret)
            
            # Notify
            for other_id, other_user in lobby.users.items():
                await other_user.socket.send_json({
                    "type": "owner_changed",
                    "old_owner_id": u_id,
                    "new_owner_id": new_owner_id
                })
            
            await new_owner_user.socket.send_json({
                "type": "owner_promoted",
                "new_secret": new_secret
            })

    # Notify other users
    for other_id, other_user in lobby.users.items():
        if other_id != u_id:
            try:
                await other_user.socket.send_json({
                    "type": "user_left",
                    "user_id": u_id,
                    "user_name": user.user_name
                })
            except Exception as e:
                print(f"Failed to notify user {other_user.user_name} of leave: {e}")
                
    await lobbies.disconnect_user(lobby_id, u_id)
    
    return {"status": "ok"}
