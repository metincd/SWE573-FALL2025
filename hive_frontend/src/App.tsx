import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Services from './pages/Services'
import ServiceDetail from './pages/ServiceDetail'
import CreateService from './pages/CreateService'
import Profile from './pages/Profile'
import Manifesto from './pages/Manifesto'
import Chat from './pages/Chat'
import Messages from './pages/Messages'
import UserProfile from './pages/UserProfile'
import Forum from './pages/Forum'
import ThreadDetail from './pages/ThreadDetail'
import CreateThread from './pages/CreateThread'
import AdminPanel from './pages/AdminPanel'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Register />} />
        <Route path="manifesto" element={<Manifesto />} />
        <Route path="services" element={<Services />} />
        <Route path="services/:id" element={<ServiceDetail />} />
        <Route path="services/create" element={<CreateService />} />
        <Route path="profile" element={<Profile />} />
        <Route path="messages" element={<Messages />} />
        <Route path="users/:userId" element={<UserProfile />} />
        <Route path="chat/:conversationId" element={<Chat />} />
        <Route path="forum" element={<Forum />} />
        <Route path="forum/create" element={<CreateThread />} />
        <Route path="forum/:threadId" element={<ThreadDetail />} />
        <Route path="admin" element={<AdminPanel />} />
      </Route>
    </Routes>
  )
}

export default App
