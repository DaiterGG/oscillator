import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom';
import CreateLobby from './CreateLobby';


export default function Home() {
  const [nickname, setNickname] = useState(localStorage.getItem('oscillator_nickname') || '');
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => {
    fetch('/api/ping');
  }, []);

  const navigate = useNavigate();
  const find_lb = () => {
    const finalNickname = nickname.trim() || "John Oscillator";

    // Store nickname for client-side persistence
    localStorage.setItem('oscillator_nickname', finalNickname);

    navigate("/lobby_list");
  };
  return (
    <div className="min-h-screen p-3 md:p-5">
      {/* Outer Frame */}
      {/* Gradient background */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute inset-0 bg-[#101010] bg-[linear-gradient(to_right,#ffffff0f_1px,transparent_1px),linear-gradient(to_bottom,#ffffff0f_1px,transparent_1px)] bg-[size:300px_200px]" />
      </div>

      {showCreate && <CreateLobby onClose={() => setShowCreate(false)} />}

      {/* Content */}
      <div className="relative z-10 h-full flex flex-col items-center">
        {/* Logo Area */}
        <div className="mt-24 md:mt-28 text-center">
          <h1
            className="
                text-white
                text-4xl
                md:text-5xl
                font-light
                tracking-wide
              "
            style={{
              fontFamily: "cursive",
            }}
          >
            Oscillator
          </h1>

          <p
            className="
                text-xs
                md:text-lg
                text-white/90
                mt-3
                tracking-wide
              "
            style={{
              fontFamily: "@fontsource/inter",
            }}
          >
            brings humans into music discovery
          </p>
        </div>
        {/* Form Area */}
        <div className="mt-28 flex flex-col items-center">
          <input
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            placeholder="John Oscillator"
            autoFocus
            type="text"
            className="
        w-[300px]
        md:w-[340px]
        h-[56px]
        rounded-[12px]
        border-2
        border-white/70
        bg-[#101010]
        text-center
        text-white
        placeholder:text-white/60
        outline-none
        text-lg
      "
            style={{
              fontFamily: "@fontsource/inter",
            }}
          />
          {/* Buttons */}
          <div className="flex gap-10 mt-5">
            <button
              className="
                  px-6
                  h-[48px]
                  rounded-[12px]
                  border-2
                  border-white/70
                  text-white/90
                  bg-[#101010]
                  hover:bg-[#1a1a1a]
                  transition
                "
              style={{
                fontFamily: "@fontsource/inter",
              }}
              onClick={find_lb}
            >
              find lobby
            </button>
            <button
              className="
                  px-6
                  h-[48px]
                  rounded-[12px]
                  border-2
                  border-white/70
                  text-white/90
                  bg-[#101010]
                  hover:bg-[#1a1a1a]
                  transition
                "
              style={{
                fontFamily: "@fontsource/inter",
              }}
              onClick={() => setShowCreate(true)}
            >
              create lobby
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
