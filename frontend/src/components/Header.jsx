import {useEffect,useState} from 'react';
import {Search} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import {api} from '../api';
import Modal from './Modal';
export default function Header({page,setPage}) {
 const {profile}=useAuth();const [open,setOpen]=useState(false),[query,setQuery]=useState(''),[records,setRecords]=useState([]),[error,setError]=useState('');
 useEffect(()=>{function key(e){if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();setOpen(true)}}window.addEventListener('keydown',key);return()=>window.removeEventListener('keydown',key)},[]);
 useEffect(()=>{if(!open)return;setError('');Promise.all([['Clients','/clients'],['Projects','/projects'],['Tasks','/projects/tasks/all'],['Services','/services'],['Finance','/finance/documents'],['Finance','/expenses']].map(async([page,path])=>({page,rows:await api(path)}))).then(groups=>{const all=[];for(const g of groups)for(const r of g.rows)all.push({page:g.page,id:r.id,label:r.title||r.name||`${r.document_type} #${r.id}`});setRecords(all)}).catch(e=>setError(e.message))},[open]);
 return <header className="header"><h2>{page}</h2><div className="header-right"><button className="secondary global-search" onClick={()=>setOpen(true)}><Search size={16}/> Search <small>Ctrl K</small></button><span>{profile.user.full_name}</span><div className="avatar">{profile.user.full_name.slice(0,1).toUpperCase()}</div></div>{open&&<Modal title="Search workspace" onClose={()=>setOpen(false)}><input autoFocus aria-label="Search workspace" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search clients, tasks, projects and documents…"/>{error&&<p className="error">{error}</p>}{records.filter(r=>query.trim()&&r.label.toLowerCase().includes(query.toLowerCase())).slice(0,30).map((r,i)=><button className="history-item" key={i} onClick={()=>{setPage(r.page);setOpen(false)}}><b>{r.label}</b><small> · {r.page}</small></button>)}</Modal>}</header>;
}
