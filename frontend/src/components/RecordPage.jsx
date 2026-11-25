import { useEffect, useState } from 'react';
import { Plus, Search } from 'lucide-react';
import { api } from '../api';
import Modal from './Modal';
import ConfirmDialog from './ConfirmDialog';

export function Fields({ fields, form, setForm }) {
    function change(field, value) {
        if (field.number) value = value === '' ? (field.required===false?null:'') : Number(value);
        setForm({...form, [field.key]:value});
    }

    return (
        <div className="form-grid">
            {fields.map(field => (
                <label key={field.key} className={field.multiline ? 'field-wide' : undefined}>
                    {field.label}{field.required !== false && <span className="required-mark"> *</span>}
                    {field.options ? (
                        <select required={field.required!==false} value={form[field.key]??''} onChange={event=>change(field,event.target.value)}>
                            <option value="">Select…</option>
                            {field.options.map(option=><option key={option.value??option} value={option.value??option}>{option.label??option}</option>)}
                        </select>
                    ) : field.multiline ? (
                        <textarea rows={3} required={field.required!==false} value={form[field.key]??''} onChange={event=>change(field,event.target.value)}/>
                    ) : (
                        <input type={field.type||'text'} pattern={field.type==='email'?"[^\\s@]+@[^\\s@]+\\.[^\\s@]+":undefined} required={field.required!==false} min={field.min} max={field.max} step={field.step} value={form[field.key]??''} onChange={event=>change(field,event.target.value)}/>
                    )}
                </label>
            ))}
        </div>
    );
}

export default function RecordPage({ title, singular, description, path, fields, columns, version, onChange, extraActions, extraContent, defaults={}, createLabel, deleteRecord=false }) {
    const [rows,setRows] = useState([]);
    const [search,setSearch] = useState('');
    const [sort,setSort]=useState(null);
    const [page,setPage]=useState(1);
    const [statusFilter,setStatusFilter]=useState("All");
    useEffect(()=>setPage(1),[search,sort,statusFilter]);
    const [form,setForm] = useState(null);
    const [id,setId] = useState(null);
    const [error,setError] = useState('');
    const [notice,setNotice] = useState('');
    const [busy,setBusy] = useState(false);
    const [confirm,setConfirm] = useState(null);

    async function load() {
        try {
            setRows(await api(path));
        } catch (error) {
            setError(error.message);
        }
    }

    useEffect(()=>{load();},[path,version]);

    function open(row) {
        setId(row?.id??null);
        const values = {};
        for (const field of fields) {
            values[field.key] = row?.[field.key]??defaults[field.key]??(field.number&&field.required===false?null:'');
        }
        setForm(values);
        setError('');
        setNotice('');
    }

    async function save(event) {
        event.preventDefault();
        setBusy(true);
        setError('');
        try {
            await api(id?`${path}/${id}`:path,id?'PUT':'POST',form);
            setForm(null);
            setNotice(`${singular} ${id?'updated':'created'} successfully.`);
            await load();
            onChange();
        } catch (error) {
            setError(error.message);
        } finally {
            setBusy(false);
        }
    }

    async function archive(row) {
        await api(`${path}/${row.id}/archive`,'POST');
        setNotice(`${singular} ${row.archived?'restored':'archived'} successfully.`);
        await load();
        onChange();
    }

    const filtered = rows.filter(row=>(statusFilter==='All'||(row.archived?'Archived':'Active')===statusFilter)&&JSON.stringify(row).toLowerCase().includes(search.toLowerCase()));
    if(sort) filtered.sort((a,b)=>String(a[sort.key]??'').localeCompare(String(b[sort.key]??''),undefined,{numeric:true})*sort.direction);
    const pageCount=Math.max(1,Math.ceil(filtered.length/15));
    const activePage=Math.min(page,pageCount);
    const visible=filtered.slice((activePage-1)*15,activePage*15);

    return <>
        <div className="page-title">
            <div><h1>{title}</h1><p>{description}</p></div>
            <button className="primary" onClick={()=>open()}><Plus size={17}/>{createLabel || `New ${singular}`}</button>
        </div>
        {notice && <p className="success" role="status">{notice}</p>}
        {extraContent?.(rows)}
        <section className="panel">
            <div className="table-toolbar">
                <h3>All {title.toLowerCase()}</h3>
                <div className="actions">{rows.some(r=>'archived' in r)&&<select aria-label="Archive filter" value={statusFilter} onChange={e=>setStatusFilter(e.target.value)}>{['All','Active','Archived'].map(v=><option key={v}>{v}</option>)}</select>}<div className="search"><Search size={16}/><input aria-label="Search records" placeholder="Search records" value={search} onChange={event=>setSearch(event.target.value)}/></div></div>
            </div>
            {error&&!form&&<p className="error">{error}</p>}
            <div className="table-scroll">
                <table>
                    <thead><tr>{columns.map(column=><th key={column.key}><button className="sort-label" onClick={()=>setSort({key:column.key,direction:sort?.key===column.key?-sort.direction:1})}>{column.label}{sort?.key===column.key?(sort.direction===1?" ↑":" ↓"):""}</button></th>)}<th>Actions</th></tr></thead>
                    <tbody>{visible.map(row=><tr key={row.id}>
                        {columns.map(column=><td key={column.key}>{column.render?column.render(row):String(row[column.key]??'—')}</td>)}
                        <td className="actions">
                            <button className="small" onClick={()=>open(row)}>Edit Details</button>
                            {'archived'in row&&<button className="small" onClick={()=>setConfirm(row)}>{row.archived?'Restore':'Archive'}</button>}
                            {deleteRecord&&<button className="small" onClick={()=>setConfirm(row)}>Delete {singular}</button>}{extraActions?.(row)}
                        </td>
                    </tr>)}</tbody>
                </table>
            </div>
            {pageCount>1&&<div className="pagination"><button className="secondary" disabled={activePage===1} onClick={()=>setPage(activePage-1)}>Previous</button><small>Page {activePage} of {pageCount}</small><button className="secondary" disabled={activePage===pageCount} onClick={()=>setPage(activePage+1)}>Next</button></div>}{!filtered.length&&<div className="empty"><h3>No {title.toLowerCase()} to display</h3><p>Create a record or ask Dottie to help.</p></div>}
        </section>
        {form&&<Modal title={`${id?'Edit':'New'} ${singular.toLowerCase()}`} onClose={()=>!busy&&setForm(null)}>
            <form onSubmit={save}>
                <Fields fields={fields} form={form} setForm={setForm}/>
                {error&&<p className="error" role="alert">{error}</p>}
                <div className="dialog-actions">
                    <button type="button" className="secondary" disabled={busy} onClick={()=>setForm(null)}>Cancel</button>
                    <button className="primary" disabled={busy}>{busy?'Saving…':id?'Save Changes':`Create ${singular}`}</button>
                </div>
            </form>
        </Modal>}
        {confirm&&<ConfirmDialog
            title={deleteRecord?`Delete ${singular}?`:`${confirm.archived?'Restore':'Archive'} this ${singular.toLowerCase()}?`}
            description={deleteRecord?"This record will be permanently deleted.":confirm.archived?'This record will be available for active business operations again.':'This record will be removed from active selection. Your existing history will be preserved.'}
            label={deleteRecord?`Delete ${singular}`:confirm.archived?'Restore':'Archive'}
            danger={!confirm.archived}
            onClose={()=>setConfirm(null)}
            onConfirm={async()=>{if(deleteRecord){await api(`${path}/${confirm.id}`,'DELETE');await load();onChange();}else await archive(confirm);}}
        />}
    </>;
}
