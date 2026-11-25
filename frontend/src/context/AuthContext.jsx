import { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../api';

const AuthContext = createContext(null);
export function AuthProvider({ children }) {
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    function logout() { sessionStorage.removeItem('dotlink_token'); setProfile(null); }
    async function refresh() { const result = await api('/auth/me'); setProfile(result); return result; }
    async function signIn(path, data) {
        const result = await api('/auth/' + path, 'POST', data);
        sessionStorage.setItem('dotlink_token', result.access_token);
        return refresh();
    }
    useEffect(() => {
        if (sessionStorage.getItem('dotlink_token')) refresh().catch(logout).finally(() => setLoading(false));
        else setLoading(false);
        window.addEventListener('dotlink-expired', logout);
        return () => window.removeEventListener('dotlink-expired', logout);
    }, []);
    return <AuthContext.Provider value={{ profile, loading, signIn, logout, refresh }}>{children}</AuthContext.Provider>;
}
export const useAuth = () => useContext(AuthContext);
