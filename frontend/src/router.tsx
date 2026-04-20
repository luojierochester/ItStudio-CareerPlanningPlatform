import { createBrowserRouter } from 'react-router-dom';
import AppLayout from './layouts/AppLayout';
import Home from './pages/Home';
import Profile from './pages/Profile';
import Login from './pages/Login';
import AuthGuard from './components/AuthGuard';

export const router = createBrowserRouter([
    {
        path: '/login',
        element: <Login />,
    },
    {
        path: '/',
        element: <AuthGuard><AppLayout /></AuthGuard>,
        children: [
            { index: true, element: <Profile /> },
            { path: 'panorama', element: <Home /> },
        ],
    },
]);