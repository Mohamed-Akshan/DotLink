import {useEffect,useState} from 'react';
import {api} from '../api';
import ApprovalCard from '../components/ApprovalCard';
export default function Approvals({version,onChange}){
    const [rows,setRows]=useState([]),[filter,setFilter]=useState('Pending'),[error,setError]=useState('');
    async function load(){try{setRows(await api('/approvals'));}catch(e){setError(e.message);}}
    useEffect(()=>{load();},[version]);
    const items=rows.filter(r=>filter==='All'||r.status===filter);
    return <><div className="page-title"><div><h1>Approvals</h1><p>Review Dottie's proposed actions before any business data changes.</p></div></div><div className="tabs">{['Pending','Executed','Rejected','All'].map(t=><button key={t} className={filter===t?'selected':''} onClick={()=>setFilter(t)}>{t==='Executed'?'Approved':t} ({rows.filter(r=>t==='All'||r.status===t).length})</button>)}</div>{error&&<p className="error">{error}</p>}<div className="approval-grid">{items.map(i=><ApprovalCard key={i.id} item={i} onChange={async()=>{await load();onChange();}}/>)}</div>{!items.length&&<section className="panel empty">No {filter.toLowerCase()} requests.</section>}</>;
}
