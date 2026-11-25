import { ListChecks, LayoutDashboard, Users, FolderOpen, Layers, Wallet, ClipboardCheck, Settings, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
export const pages = [['Overview',LayoutDashboard],['Clients',Users],['Projects',FolderOpen],['Tasks',ListChecks],['Services',Layers],['Finance',Wallet],['Approvals',ClipboardCheck],['Settings',Settings]];
export default function Sidebar({ page, setPage }) {
    const { logout, profile } = useAuth();
    return <aside className="sidebar"><img className="brand" src="/assets/dotlink-logo.png" alt="DotLink"/><span className="workspace-label">WORKSPACE</span><nav>{pages.map(([name,Icon])=><button key={name} className={page===name?'nav-item active':'nav-item'} onClick={()=>setPage(name)}><Icon size={19}/>{name}</button>)}</nav><div className="sidebar-bottom"><button className="sidebar-dottie" onClick={()=>window.dispatchEvent(new Event("dotlink-ask"))}><img src="/assets/dottie.png" alt=""/><span>Ask Dottie<small>Your business companion</small></span></button><div className="workspace-card"><b>{profile.workspace.business_name}</b><small>Your private workspace</small></div><button className="nav-item" onClick={logout}><LogOut size={18}/>Sign out</button></div></aside>;
}
