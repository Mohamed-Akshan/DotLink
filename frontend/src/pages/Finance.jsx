import {useEffect,useState} from 'react';
import {api,money} from '../api';
import KPICard from '../components/KPICard';
import Quotations from '../components/finance/Quotations';
import Invoices from '../components/finance/Invoices';
import Expenses from '../components/finance/Expenses';
import Payments from '../components/finance/Payments';
export default function Finance({version,onChange}){
    const [tab,setTab]=useState('Quotations'),[data,setData]=useState(null),[error,setError]=useState('');
    async function load(){try{const [documents,clients,services,projects,payments,summary]=await Promise.all(['/finance/documents','/clients','/services','/projects','/finance/payments','/overview'].map(p=>api(p)));setData({documents,clients,services,projects,payments,summary});}catch(e){setError(e.message);}}
    useEffect(()=>{load();},[version]);
    if(!data)return <p>{error||'Loading finance…'}</p>;
    const Component={Quotations,Invoices,Payments,Expenses}[tab];
    return <><div className="page-title"><div><h1>Finance</h1><p>Manage quotations, invoices, payments and expenses.</p></div></div><div className="kpi-grid three"><KPICard featured label="Total invoiced" value={money(data.summary.invoiced)}/><KPICard label="Outstanding" value={money(data.summary.outstanding)}/><KPICard label="Overdue amount" value={money(data.summary.overdue)}/></div><div className="tabs">{['Quotations','Invoices','Payments','Expenses'].map(t=><button key={t} className={t===tab?'selected':''} onClick={()=>setTab(t)}>{t}</button>)}</div>{error&&<p className="error">{error}</p>}<Component key={tab} version={version} {...data} reload={()=>{load();onChange();}}/></>;
}
