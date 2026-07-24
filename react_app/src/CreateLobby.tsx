import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function CreateLobby({ onClose }: { onClose: () => void }) {
  const [lobbyName, setLobbyName] = useState("");
  const [theme, setTheme] = useState("");
  const [description, setDescription] = useState("");
  const [isProtected, setIsProtected] = useState(false);
  const [password, setPassword] = useState("");
  const [passwordError, setPasswordError] = useState(false);

  const navigate = useNavigate();

  const handleCreate = async () => {
    if (isProtected && !password) {
        setPasswordError(true);
        return;
    }
    setPasswordError(false);
    
    const user_name = localStorage.getItem('oscillator_nickname') || 'Anonymous';

    // Send according to backend schema: NewLobby
    const response = await fetch('/api/create_lobby', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_name,
        lobby_name: lobbyName || "Lobby",
        lobby_theme: theme || "None",
        lobby_description: description || "None",
        lobby_password: isProtected ? password : null
      }),
    });

    if (response.ok) {
        const data = await response.json();
        localStorage.setItem('lobby_id', data.lobby_id);
        localStorage.setItem('lobby_secret', data.lobby_secret);
        navigate(`/lobby?${data.lobby_id}`);
        onClose();
    }
  };

  return (
    <div className="absolute inset-0 z-50 bg-black/80 flex items-center justify-center p-5">
      <div className="bg-[#101010] p-10 rounded-3xl border-2 border-white/70 w-full max-w-lg flex flex-col gap-4">
        <h2 className="text-white text-3xl font-light mb-2">Create Lobby</h2>

        <input
          type="text"
          placeholder="Lobby Name"
          value={lobbyName}
          onChange={(e) => setLobbyName(e.target.value)}
          className="w-full p-3 rounded-xl border-2 border-white/70 bg-[#101010] text-white"
        />
        <input
          type="text"
          placeholder="Theme/Genres"
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
          className="w-full p-3 rounded-xl border-2 border-white/70 bg-[#101010] text-white"
        />
        <input
          type="text"
          placeholder="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full p-3 rounded-xl border-2 border-white/70 bg-[#101010] text-white"
        />
        
        <label className="flex items-center gap-3 text-white/70 cursor-pointer group">
          <div className="relative">
            <input
              type="checkbox"
              checked={isProtected}
              onChange={(e) => setIsProtected(e.target.checked)}
              className="peer sr-only"
            />
            <div className="w-6 h-6 border-2 border-white/70 rounded-md peer-checked:bg-white peer-checked:border-white transition-all"></div>
            <svg className="absolute top-1 left-1 w-4 h-4 text-black hidden peer-checked:block" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <span className="peer-checked:text-white">Password protected</span>
        </label>

        {isProtected && (
          <div className="w-full flex flex-col gap-1">
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => {
                  setPassword(e.target.value);
                  if (passwordError) setPasswordError(false);
              }}
              autoComplete="new-password"
              className={`w-full p-3 rounded-xl border-2 ${passwordError ? 'border-red-500' : 'border-white/70'} bg-[#101010] text-white`}
            />
            {passwordError && <span className="text-red-500 text-sm">Password is required.</span>}
          </div>
        )}

        <div className="flex gap-4 mt-4">
          <button onClick={onClose} className="flex-1 py-3 text-white border border-white rounded-xl">cancel</button>
          <button onClick={handleCreate} className="flex-1 py-3 text-black bg-white rounded-xl">create</button>
        </div>
      </div>
    </div>
  );
}
