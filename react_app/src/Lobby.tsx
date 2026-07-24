import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import SendIcon from "./components/icons/SendIcon";
import CogIcon from "./components/icons/CogIcon";
import CrownIcon from "./components/icons/CrownIcon";

export default function LobbyPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const lobbyId = location.search.substring(1);
  const myNickname = localStorage.getItem('oscillator_nickname');
  const ws = useRef<WebSocket | null>(null);
  const [playerMessages, setPlayerMessages] = useState<any[]>([]);
  const [chatMessages, setChatMessages] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [authorId, setAuthorId] = useState<string | null>(null);
  const [lobbyName, setLobbyName] = useState("");
  const [theme, setTheme] = useState("");
  const [description, setDescription] = useState("");
  const [password, setPassword] = useState("");
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [clickStartedOnOverlay, setClickStartedOnOverlay] = useState(false);
  const [selectedUser, setSelectedUser] = useState<{user: any, x: number, y: number} | null>(null);
  const [editingNickname, setEditingNickname] = useState(false);
  const [newNickname, setNewNickname] = useState("");

  const deleteLobby = async () => {
    if (!lobbyId) return;
    try {
      await fetch(`/api/delete_lobby?lobby_id=${lobbyId}`, { method: 'POST' });
      navigate("/lobby_list");
    } catch (err) {
      console.error("Failed to delete lobby", err);
    }
  };

  const saveSettings = () => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
          type: "update_lobby_settings",
          lobby_name: lobbyName,
          theme: theme,
          description: description,
          password: password
      }));
    }
    setShowSettings(false);
  };

  const playerChatRef = useRef<HTMLDivElement>(null);
  const lobbyChatRef = useRef<HTMLDivElement>(null);
  const [showPlayerScrollDown, setShowPlayerScrollDown] = useState(false);
  const [showLobbyScrollDown, setShowLobbyScrollDown] = useState(false);

  const handlePlayerScroll = () => {
    if (playerChatRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = playerChatRef.current;
      setShowPlayerScrollDown(scrollHeight - scrollTop > clientHeight + 100);
    }
  };

  const handleLobbyScroll = () => {
    if (lobbyChatRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = lobbyChatRef.current;
      setShowLobbyScrollDown(scrollHeight - scrollTop > clientHeight + 100);
    }
  };

  const scrollToBottomPlayer = () => {
    playerChatRef.current?.scrollTo({ top: playerChatRef.current.scrollHeight, behavior: 'smooth' });
  };

  const scrollToBottomLobby = () => {
    lobbyChatRef.current?.scrollTo({ top: lobbyChatRef.current.scrollHeight, behavior: 'smooth' });
  };

  useEffect(() => {
    if (playerChatRef.current && !showPlayerScrollDown) {
      playerChatRef.current.scrollTop = playerChatRef.current.scrollHeight;
    }
    if (lobbyChatRef.current && !showLobbyScrollDown) {
      lobbyChatRef.current.scrollTop = lobbyChatRef.current.scrollHeight;
    }
  }, [playerMessages, chatMessages]);

  useEffect(() => {
    const nickname = localStorage.getItem('oscillator_nickname');
    if (!lobbyId || !nickname) return;

    let isMounted = true;
    let socket: WebSocket | null = null;

    const checkLobby = async () => {
      try {
        const response = await fetch(`/api/lobby_details?lobby_id=${lobbyId}`);
        if (response.status === 404) {
          if (isMounted) setConnectionError("Lobby not found");
          return;
        }

        if (!isMounted) return;

        // If lobby exists, proceed with WebSocket
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        socket = new WebSocket(`${protocol}://${window.location.host}/api/join_lobby?lobby_id=${lobbyId}&user_name=${encodeURIComponent(nickname)}`);

        socket.onopen = () => {
          if (isMounted) {
            setPlayerMessages([]);
            setChatMessages([]);
            setIsConnected(true);
          }
        };

        socket.onmessage = (event) => {
          if (!isMounted) return;
          const data = JSON.parse(event.data);
          if (data.type === 'player_chat') {
            setPlayerMessages((prev) => [...prev, data]);
          } else if (data.type === 'lobby_chat') {
            setChatMessages((prev) => [...prev, data]);
          } else if (data.type === 'lobby_sync') {
            setUsers(data.users);
            setAuthorId(data.author_id);
            setLobbyName(data.lobby_name);
            setTheme(data.theme);
            setDescription(data.description);
          } else if (data.type === 'user_joined') {
            setUsers((prev) => {
              if (prev.some(u => u.user_id === data.user_id)) return prev;
              return [...prev, { user_id: data.user_id, user_name: data.user_name }];
            });
          } else if (data.type === 'user_left') {
            setUsers((prev) => prev.filter(u => u.user_id !== data.user_id));
          }
        };

        socket.onclose = (event) => {
          if (!isMounted) return;
          setIsConnected(false);
          if (event.code === 409) {
            setConnectionError("Already connected in another tab");
          }
          else if (event.code !== 1000) {
            setConnectionError("Connection failed");
          }
        };

        ws.current = socket;
      } catch (err) {
        if (isMounted) setConnectionError("Connection failed");

      }
    };

    checkLobby();

    return () => {
      isMounted = false;
      setIsConnected(false);
      if (socket) socket.close();
      ws.current = null;
    };
  }, [lobbyId]);

  const [playerMessageInput, setPlayerMessageInput] = useState("");
  const [chatMessageInput, setChatMessageInput] = useState("");

  const sendPlayerMessage = () => {
    if (ws.current?.readyState === WebSocket.OPEN && playerMessageInput.trim()) {
      ws.current.send(JSON.stringify({ type: "player_chat", body: playerMessageInput }));
      setPlayerMessageInput("");
    }
  };

  const sendChatMessage = () => {
    if (ws.current?.readyState === WebSocket.OPEN && chatMessageInput.trim()) {
      ws.current.send(JSON.stringify({ type: "lobby_chat", body: chatMessageInput }));
      setChatMessageInput("");
    }
  };

  const formatTime = (stamp: string) => {
    const date = new Date(parseFloat(stamp) * 1000);
    const time = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
    const timePart = time.replace(/[AaPp][Mm]/, '').trim();
    const amPmPart = time.match(/[AaPp][Mm]/)?.[0];

    if (amPmPart) {
      return (
        <>
          {timePart}
          <span className="text-[10px] ml-0.5">{amPmPart}</span>
        </>
      );
    }
    return time;
  };

  return (
    <div className="min-h-screen text-white p-20 relative">
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute inset-0 bg-[#101010] bg-[linear-gradient(to_right,#ffffff0f_1px,transparent_1px),linear-gradient(to_bottom,#ffffff0f_1px,transparent_1px)] bg-[size:300px_200px]" />
      </div>
      {connectionError ? (
        <div className="flex flex-col items-center justify-center h-full">
          <h1 className="text-2xl text-white-500">{connectionError}</h1>
        </div>
      ) : !isConnected ? (
        <div className="flex flex-col items-center justify-center h-full">
          <h1 className="text-2xl">Joining lobby...</h1>
        </div>
      ) : (
        <div className="grid grid-cols-5 gap-8 h-[calc(100vh-10rem)] bg-[#101010]/80">
          <div className="col-span-2 border-2 border-white/70 rounded-3xl flex flex-col min-h-0">
            <h2 className="text-2xl text-white/50 m-4 font-light">Music Player</h2>
            <div className="flex-grow relative min-h-0">
              <div className="absolute inset-0 overflow-y-auto overflow-x-hidden border-b-2 border-white/70 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent" ref={playerChatRef} onScroll={handlePlayerScroll}>
                {playerMessages.map((m, i) => {
                  const isMine = m.user_name === myNickname;
                  return (
                    <div key={i} className={`flex ${isMine ? 'justify-end' : 'justify-start'} p-2`}>
                      <div className="border border-white/70 rounded-2xl p-3 max-w-[80%]">
                        <div className={`flex items-baseline gap-2 ${isMine ? 'justify-end' : 'justify-start'}`}>
                          {isMine && m.stamp && (
                            <span className="text-xs text-white/50">
                              {formatTime(m.stamp)}
                            </span>
                          )}
                          <span className="text text-white/70">{m.user_name}</span>
                          {!isMine && m.stamp && (
                            <span className="text-xs text-white/50">
                              {formatTime(m.stamp)}
                            </span>
                          )}
                        </div>
                        <div className={isMine ? 'text-right' : 'text-left'}>{m.body}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
              {showPlayerScrollDown && (
                <button onClick={scrollToBottomPlayer} className="absolute bottom-4 left-1/2 -translate-x-1/2 border border-white text-white rounded-full p-2 text-xs">Scroll Down</button>
              )}
            </div>
            <div className="flex gap-2 p-2">
              <input
                type="text"
                value={playerMessageInput}
                onChange={(e) => setPlayerMessageInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && sendPlayerMessage()}
                placeholder="Url/file..."
                className="outline-none ml-4 flex-grow p-3 rounded-xl text-white bg-transparent"
              />
              <button onClick={sendPlayerMessage} className="text-white text-4xl px-6 py-2 rounded-xl cursor-pointer"><SendIcon className="w-8 h-8" /></button>
            </div>
          </div>

          {/* Chat 2 */}
          <div className="col-span-2 border-2 border-white/70 rounded-3xl flex flex-col min-h-0">
            <h2 className="text-2xl text-white/50 m-4 font-light">Chat</h2>
            <div className="flex-grow relative min-h-0">
              <div className="absolute inset-0 overflow-y-auto overflow-x-hidden border-b-2 border-white/70 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent" ref={lobbyChatRef} onScroll={handleLobbyScroll}>
                {chatMessages.map((m, i) => {
                  const isMine = m.user_name === myNickname;
                  return (
                    <div key={i} className={`flex ${isMine ? 'justify-end' : 'justify-start'} p-2`}>
                      <div className="border border-white/70 rounded-2xl p-3 max-w-[80%] bg-[#101010]">
                        <div className={`flex items-baseline gap-2 ${isMine ? 'justify-end' : 'justify-start'}`}>
                          {isMine && m.stamp && (
                            <span className="text-xs text-white/50">
                              {formatTime(m.stamp)}
                            </span>
                          )}
                          <span className="text text-white/70">{m.user_name}</span>
                          {!isMine && m.stamp && (
                            <span className="text-xs text-white/50">
                              {formatTime(m.stamp)}
                            </span>
                          )}
                        </div>
                        <div className={isMine ? 'text-right' : 'text-left'}>{m.body}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
              {showLobbyScrollDown && (
                <button onClick={scrollToBottomLobby} className="absolute bottom-4 left-1/2 -translate-x-1/2 border border-white text-white rounded-full p-2 text-xs">Scroll Down</button>
              )}
            </div>
            <div className="flex gap-2 p-2">
              <input
                type="text"
                value={chatMessageInput}
                onChange={(e) => setChatMessageInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && sendChatMessage()}
                placeholder="Type a message..."
                className="outline-none ml-4 flex-grow p-3 rounded-xl text-white bg-transparent"
              />
              <button onClick={sendChatMessage} className="text-white text-4xl px-6 py-2 rounded-xl cursor-pointer"><SendIcon className="w-8 h-8" /></button>
            </div>
          </div>
          <div className="col-span-1 border-2 border-white/70 rounded-3xl p-6 bg-[#101010]/80">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl text-white/50 font-light">Users</h2>
              <button onClick={() => setShowSettings(!showSettings)} className="text-white/50 hover:text-white">
                <CogIcon className="w-6 h-6" />
              </button>
            </div>
            <div className="overflow-y-auto">
              {users.map((u) => (
                <div
                  key={u.user_id}
                  className="text-white py-1 flex items-center justify-center gap-2 rounded transition cursor-pointer hover:bg-white/10 select-none"
                  onClick={(e) => {
                      setSelectedUser({ user: u, x: e.clientX, y: e.clientY });
                  }}
                >
                  {editingNickname && u.user_name === myNickname ? (
                        <input 
                        type="text" 
                        value={newNickname} 
                        onChange={(e) => setNewNickname(e.target.value)} 
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                                ws.current?.send(JSON.stringify({ type: 'update_nickname', new_nickname: newNickname }));
                                localStorage.setItem('oscillator_nickname', newNickname);
                                setEditingNickname(false);
                            }
                        }}
                        onBlur={() => {
                            ws.current?.send(JSON.stringify({ type: 'update_nickname', new_nickname: newNickname }));
                            localStorage.setItem('oscillator_nickname', newNickname);
                            setEditingNickname(false);
                        }}
                        className="bg-transparent border-b border-white outline-none text-center w-full"
                        autoFocus
                      />
                  ) : (
                    <>
                      {u.user_name}
                      {u.user_id === authorId && <CrownIcon className="w-4 h-4 text-white" />}
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      {selectedUser && (
        <div className="fixed inset-0 z-50" onClick={() => setSelectedUser(null)}>
          <div 
            className="absolute bg-[#101010] border border-white/70 rounded-xl p-2 w-fit min-w-[120px] flex flex-col items-center" 
            style={{ top: selectedUser.y, left: selectedUser.x }}
            onClick={e => e.stopPropagation()}
          >
            {selectedUser.user.user_name === myNickname ? (
                <button onClick={() => { 
                    setEditingNickname(true);
                    setNewNickname(myNickname || "");
                    setSelectedUser(null);
                }} className="w-full text-center p-2 hover:bg-white/10 rounded whitespace-nowrap">Change Nickname</button>
            ) : (
                <>
                    <button onClick={() => { console.log('Kick', selectedUser.user); setSelectedUser(null); }} className="w-full text-center p-2 hover:bg-white/10 rounded">Kick</button>
                    <button onClick={() => { console.log('Ban', selectedUser.user); setSelectedUser(null); }} className="w-full text-center p-2 hover:bg-white/10 rounded">Ban</button>
                    <button onClick={() => { 
                ws.current?.send(JSON.stringify({ type: 'set_owner', new_owner_id: selectedUser.user.user_id }));
                setSelectedUser(null); 
            }} className="w-full text-center p-2 hover:bg-white/10 rounded">Make Owner</button>
                </>
            )}
          </div>
        </div>
      )}
      {showSettings && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) {
              setClickStartedOnOverlay(true);
            }
          }}
          onMouseUp={(e) => {
            if (clickStartedOnOverlay && e.target === e.currentTarget) {
              saveSettings();
            }
            setClickStartedOnOverlay(false);
          }}
        >
          <div
            className="bg-[#101010] border-2 border-white/70 rounded-3xl p-8 w-80"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-2xl text-white mb-6">Settings</h2>
            <input type="text" value={lobbyName} onChange={e => setLobbyName(e.target.value)} placeholder="Lobby Name" className="w-full bg-transparent border border-white/20 p-2 mb-2 rounded text-white" />
            <input type="text" value={theme} onChange={e => setTheme(e.target.value)} placeholder="Theme" className="w-full bg-transparent border border-white/20 p-2 mb-2 rounded text-white" />
            <input type="text" value={description} onChange={e => setDescription(e.target.value)} placeholder="Description" className="w-full bg-transparent border border-white/20 p-2 mb-2 rounded text-white" />
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password (leave blank for none)" className="w-full bg-transparent border border-white/20 p-2 mb-4 rounded text-white" />

            <button
              onClick={deleteLobby}
              className="w-full text-red-500 hover:text-red-400 text-sm border border-red-500/50 rounded-lg px-3 py-2 mb-4"
            >
              Delete Lobby
            </button>
            <button
              onClick={saveSettings}
              className="w-full text-white/50 hover:text-white text-sm border border-white/20 rounded-lg px-3 py-2"
            >
              Save & Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
