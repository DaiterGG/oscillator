import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import CreateLobby from "./CreateLobby";
import RefreshIcon from "./components/icons/RefreshIcon";

export default function FindLobbyPage() {
  const navigate = useNavigate();
  const [nickname, setNickname] = useState("");
  const [lobbies, setLobbies] = useState<any[]>([]);
  const [showCreate, setShowCreate] = useState(false);

  const fetchLobbies = () => {
    fetch('/api/find_lobby')
      .then(res => res.json())
      .then(data => setLobbies(data.lobbies))
      .catch(err => console.error(err));
  };

  useEffect(() => {
    const storedNickname = localStorage.getItem('oscillator_nickname');
    if (storedNickname) {
      setNickname(storedNickname);
    } else {
      navigate("/");
    }

    fetchLobbies();
    const interval = setInterval(fetchLobbies, 10000);
    return () => clearInterval(interval);
  }, [navigate]);

  return (
    <div className="h-screen p-3 md:p-5 relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-[#101010] bg-[linear-gradient(to_right,#ffffff0f_1px,transparent_1px),linear-gradient(to_bottom,#ffffff0f_1px,transparent_1px)] bg-[size:300px_200px]" />
      </div>

      {showCreate && <CreateLobby onClose={() => setShowCreate(false)} />}
      <div className="relative z-10 h-screen flex justify-center flex-grow overflow-hidden">
        <div
          className="
      w-full
      max-w-7xl
      p-8
      relative
      flex
      flex-col
      flex-grow
      overflow-hidden
    "
        >
          {/* Top Bar */}
          <div className="flex justify-between items-center h-auto flex-shrink-0 pr-3 pl-3">
            <div className="flex items-center gap-2">
              <button className="px-4 h-10 rounded-xl border-2 border-white/70 text-white bg-[#101010] hover:bg-[#1a1a1a] transition">
                filters
              </button>
              <button
                onClick={fetchLobbies}
                className="px-4 h-10 rounded-xl border-2 border-white/70 text-white bg-[#101010] hover:bg-[#1a1a1a] transition flex items-center justify-center"
              >
                <RefreshIcon className="w-5 h-5 mb-1" />
              </button>
            </div>

            <div className="flex items-center gap-4">
              <input
                type="text"
                value={nickname}
                placeholder="John Oscillator"
                onChange={(e) => {
                  const newName = e.target.value;
                  setNickname(newName);
                  localStorage.setItem('oscillator_nickname', newName);
                }}
                className="px-3 h-10 rounded-xl border-2 border-white/70 text-white bg-[#101010] outline-none text-center placeholder:text-white/60"
              />

              <button
                onClick={() => setShowCreate(true)}
                className="px-5 h-10 rounded-xl border-2 border-white/70 text-white bg-[#101010] hover:bg-[#1a1a1a] transition"
              >
                create lobby
              </button>
            </div>
          </div>
          {/* Lobby List Container */}
          <div className="mt-4 border-2 border-white/70 rounded-3xl p-8 bg-[#101010] w-full flex-grow flex flex-col mb-8">
            {lobbies.length === 0 ? (
              <div className="text-center text-white/70 flex-grow flex items-center justify-center">
                <p className="text-xl">No lobbies found, create one!</p>
              </div>
            ) : (
              <div className="flex flex-col gap-6 overflow-y-auto pr-2">
                {lobbies.map((lobby) => (
                  <div
                    key={lobby.lobby_id}
                    className="
                          border-2
                          border-white/70
                          text-white bg-[#101010]
                          rounded-3xl
                          p-6
                          flex
                          justify-between
                          items-center
                        "
                  >
                    <div className="flex-1">
                      <h2 className="text-2xl text-white font-light">
                        {lobby.lobby_name}
                      </h2>
                      <p className="text-white/60 text-sm mt-1">
                        {lobby.lobby_description}
                      </p>

                      <div className="flex gap-6 mt-4 text-white/70 text-xs">
                        <span>Author: {lobby.author_name}</span>
                        <span>Theme/Genre: {lobby.lobby_theme}</span>
                        <span>Users: {lobby.user_count}</span>
                      </div>
                    </div>

                    <button
                      className="
                        px-6
                        h-11
                        rounded-xl
                        border-2
                        border-white/70
                        text-white
                        bg-[#101010]
                        hover:bg-[#1a1a1a]
                        transition
                      "
                      onClick={() => {
                        navigate(`/lobby?${lobby.lobby_id}`);
                      }}
                    >
                      Join
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

    </div>
  );
}
