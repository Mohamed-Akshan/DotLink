import {useEffect,useState} from 'react';
import {useAuth} from './context/AuthContext';
import Landing from './pages/Landing';
import Tasks from './pages/Tasks';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import DottieChat from './components/DottieChat';
import Overview from './pages/Overview';
import Clients from './pages/Clients';
import Projects from './pages/Projects';
import Services from './pages/Services';
import Finance from './pages/Finance';
import Approvals from './pages/Approvals';
import Settings from './pages/Settings';

const pages={Overview,Clients,Projects,Tasks,Services,Finance,Approvals,Settings};
export default function App(){
    const {profile,loading}=useAuth();
    const [authPage,setAuthPage]=useState('landing'),[context,setContext]=useState({}),[page,setPage]=useState('Overview'),[version,setVersion]=useState(0);
    useEffect(()=>{setPage('Overview');setContext({});setAuthPage('landing')},[profile?.workspace?.id]);
    if(loading)return <main className="loading">Loading DotLink…</main>;
    if(!profile)return authPage==='landing'?<Landing onSignIn={()=>setAuthPage('login')} onSignup={()=>setAuthPage('signup')}/>:authPage==='signup'?<Signup key="signup" switchPage={()=>setAuthPage('login')} goHome={()=>setAuthPage('landing')}/>:<Login key="login" switchPage={()=>setAuthPage('signup')} goHome={()=>setAuthPage('landing')}/>;
    const Component=pages[page];
    function changed(){setVersion(v=>v+1);}
    return <div className="app-shell"><Sidebar page={page} setPage={p=>{setContext({});setPage(p)}}/><main className="workspace"><Header page={page} version={version} setPage={p=>{setContext({});setPage(p)}}/><div className="page-content"><Component key={page} version={version} onChange={changed} setContext={setContext} setPage={p=>{setContext({});setPage(p)}}/></div></main><DottieChat key={profile.workspace.id} page={page} context={context} onChange={changed}/></div>;
}
