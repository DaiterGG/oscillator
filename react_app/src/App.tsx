import LobbyList from './LobbyList.tsx'
import Home from './Home.tsx'
import Lobby from './Lobby.tsx'
import { Routes, Route } from 'react-router-dom';



export default function App() {
  return (
    <div>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/lobby_list" element={<LobbyList />} />
        <Route path="/lobby" element={<Lobby />} />
      </Routes>
    </div>
  )
}
