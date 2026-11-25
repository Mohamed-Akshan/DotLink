import { useEffect, useState } from 'react';
import { api, money } from '../api';
import Modal from './Modal';
import { Fields } from './RecordPage';

const projectStatuses = ['Pending', 'In progress', 'Completed', 'On hold'];
const taskStatuses = ['Pending', 'In progress', 'Completed'];

export default function ApprovalEditor({ item, onClose, onSaved }) {
    const [form, setForm] = useState(() => structuredClone(item.payload));
    const [clients, setClients] = useState([]);
    const [projects, setProjects] = useState([]);
    const [services, setServices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');

    const action = item.action;
    const isDocument = ['create_quotation', 'update_quotation', 'create_invoice', 'update_invoice'].includes(action);
    const isConversion = action === 'convert_quotation_to_invoice';
    const isQuotationStatus = action === 'set_quotation_status';
    const isProject = ['create_project','update_project'].includes(action);
    const isExpense = ['create_expense','update_expense'].includes(action);
    const isQuoteProject=action==='create_project_from_quotation';
    const isQuoteLink=action==='link_quotation_to_project';
    const isTask = action.endsWith('_task');

    useEffect(() => {
        async function loadOptions() {
            try {
                if (isProject || isDocument) {
                    setClients(await api('/clients'));
                }
                if (isTask || isDocument || isExpense || isQuoteLink) {
                    setProjects(await api('/projects'));
                }
                if (isDocument) {
                    setServices(await api('/services'));
                }
            } catch (error) {
                setError(error.message);
            } finally {
                setLoading(false);
            }
        }
        loadOptions();
    }, [action]);

    function fieldsForAction() {
        if (isConversion) {
            return [
                {key:'issue_date', label:'Invoice issue date', type:'date'},
                {key:'due_date', label:'Payment due date', type:'date'},
            ];
        }

        if (isQuotationStatus) {
            const options = item.before?.status === 'Draft' ? ['Sent','Accepted','Rejected'] : ['Accepted','Rejected'];
            return [{key:'status', label:'Quotation status', options}];
        }

        if (action.endsWith('_client')) {
            return [
                {key:'name', label:'Client name'},
                {key:'company', label:'Company (optional)', required:false},
                {key:'email', label:'Email address', type:'email'},
                {key:'phone', label:'Phone number', type:'tel'},
                {key:'address', label:'Address (optional)', required:false},
                {key:'notes', label:'Notes (optional)', required:false, multiline:true},
            ];
        }

        const clientOptions = [];
        for (const client of clients) {
            if (!client.archived || client.id === Number(form.client_id)) {
                clientOptions.push({value:client.id, label:client.name});
            }
        }

        if (isProject) {
            return [
                {key:'client_id', label:'Client', number:true, options:clientOptions},
                {key:'title', label:'Project title'},
                {key:'description', label:'Scope and deliverables', multiline:true},
                {key:'start_date', label:'Start date', type:'date'},
                {key:'deadline', label:'Deadline', type:'date'},
                {key:'priority', label:'Priority', options:['Low','Medium','High']},
                {key:'status', label:'Status', options:projectStatuses},
            ];
        }

        const projectOptions = [];
        for (const project of projects) {
            if (project.archived && project.id !== Number(form.project_id)) continue;
            if (isDocument && project.client_id !== Number(form.client_id)) continue;
            projectOptions.push({value:project.id, label:project.title});
        }

        if(isExpense) return [{key:'title',label:'Expense title'},{key:'category',label:'Category'},{key:'amount',label:'Amount (LKR)',type:'number',min:.01,step:.01},{key:'expense_date',label:'Date paid',type:'date'},{key:'method',label:'Payment method',options:['Cash','Bank transfer','Card','Other']},{key:'project_id',label:'Project (optional)',number:true,required:false,options:projectOptions},{key:'notes',label:'Notes',required:false,multiline:true}];
        if(isQuoteProject) return [{key:'title',label:'Project title'},{key:'start_date',label:'Start date',type:'date'},{key:'deadline',label:'Deadline',type:'date'},{key:'priority',label:'Priority',options:['Low','Medium','High']}];
        if(isQuoteLink) return [{key:'project_id',label:'Project',number:true,options:projectOptions.filter(p=>projects.find(x=>x.id===p.value)?.client_id===item.before?.client_id)}];
        if (isTask) {
            return [
                {key:'project_id', label:'Project (optional)', number:true, required:false, options:projectOptions},
                {key:'title', label:'Task title'},
                {key:'description', label:'Description (optional)', required:false, multiline:true},
                {key:'due_date', label:'Due date', type:'date'},
                {key:'priority', label:'Priority', options:['Low','Medium','High']},
                {key:'status', label:'Status', options:taskStatuses},
            ];
        }

        if (action.endsWith('_service')) {
            return [
                {key:'name', label:'Service name'},
                {key:'category', label:'Category'},
                {key:'unit_price', label:'Unit price (LKR)', type:'number', min:0, step:'.01'},
                {key:'pricing_unit', label:'Pricing unit', options:['design','hour','package','item']},
                {key:'description', label:'Description (optional)', required:false, multiline:true},
            ];
        }

        if (isDocument) {
            return [
                {key:'client_id', label:'Client', number:true, options:clientOptions},
                {key:'project_id', label:'Project (optional)', number:true, options:projectOptions, required:false},
                {key:'issue_date', label:'Issue date', type:'date'},
                {key:'due_date', label:form.document_type === 'quotation' ? 'Valid until' : 'Payment due date', type:'date'},
                {key:'discount', label:'Discount (%)', type:'number', min:0, max:100, step:'.01'},
                {key:'notes', label:'Notes (optional)', required:false, multiline:true},
            ];
        }

        if (action === 'record_payment') {
            return [
                {key:'amount', label:'Amount received (LKR)', type:'number', min:'.01', step:'.01'},
                {key:'payment_date', label:'Payment date', type:'date'},
                {key:'method', label:'Payment method', options:['Cash','Bank transfer','Card','Other']},
                {key:'reference', label:'Transaction reference (optional)', required:false},
                {key:'notes', label:'Notes (optional)', required:false, multiline:true},
            ];
        }

        return [];
    }

    function updateForm(next) {
        if (isDocument && next.client_id !== form.client_id) {
            next.project_id = null;
        }
        setForm(next);
    }

    function changeItem(index, key, value) {
        const items = [...form.items];
        items[index] = {...items[index], [key]:value};
        setForm({...form, items});
    }

    function removeItem(index) {
        const items = [...form.items];
        items.splice(index, 1);
        setForm({...form, items});
    }

    function estimatedTotal() {
        let total = 0;
        for (const item of form.items || []) {
            const service = services.find(service => service.id === Number(item.service_id));
            total += Number(service?.unit_price || 0) * Number(item.quantity || 0);
        }
        return total * (100 - Number(form.discount || 0)) / 100;
    }

    async function save(event) {
        event.preventDefault();
        setBusy(true);
        setError('');

        try {
            const payload = {...form};
            if (isDocument) {
                payload.project_id = payload.project_id ? Number(payload.project_id) : null;
                payload.client_id = Number(payload.client_id);
                payload.items = [];
                for (const item of form.items) {
                    payload.items.push({service_id:Number(item.service_id), quantity:item.quantity});
                }
            }
            const updated = await api(`/approvals/${item.id}`, 'PUT', {payload});
            await onSaved(updated);
        } catch (error) {
            setError(error.message);
        } finally {
            setBusy(false);
        }
    }

    return (
        <Modal title={`Edit ${item.title.toLowerCase()} proposal`} onClose={() => !busy && onClose()}>
            <p className="muted proposal-help">Make your changes below. Saving this form updates the proposal only; nothing is applied to your business until you approve it.</p>
            {action === 'record_payment' && <p className="proposal-help">Invoice: INV-{String(form.invoice_id).padStart(5,'0')}</p>}
            {isConversion && <p className="proposal-help">The original quotation's services, quantities, prices and discount will be preserved. Only the invoice dates can be changed here.</p>}
            {loading ? <p>Loading available records…</p> : (
                <form onSubmit={save}>
                    <Fields fields={fieldsForAction()} form={form} setForm={updateForm} />
                    {isDocument && <>
                        <h3>Services and quantities</h3>
                        {form.items.map((line, index) => (
                            <div className="approval-line-editor" key={index}>
                                <label>Service
                                    <select required value={line.service_id} onChange={event => changeItem(index,'service_id',event.target.value)}>
                                        <option value="">Select a service</option>
                                        {services.filter(service => !service.archived).map(service => (
                                            <option key={service.id} value={service.id}>{service.name} · {money(service.unit_price)}</option>
                                        ))}
                                    </select>
                                </label>
                                <label>Quantity
                                    <input required type="number" min="0.01" step=".01" value={line.quantity} onChange={event => changeItem(index,'quantity',event.target.value)} />
                                </label>
                                <button type="button" className="small" disabled={form.items.length === 1} onClick={() => removeItem(index)}>Remove</button>
                            </div>
                        ))}
                        <button type="button" className="secondary" onClick={() => setForm({...form,items:[...form.items,{service_id:'',quantity:1}]})}>+ Add service</button>
                        <div className="total-row"><span>Estimated total</span><strong>{money(estimatedTotal())}</strong></div>
                        <p className="muted">The server recalculates the final total using your current rate card.</p>
                    </>}
                    {error && <p className="error" role="alert">{error}</p>}
                    <div className="dialog-actions">
                        <button type="button" className="secondary" disabled={busy} onClick={onClose}>Cancel</button>
                        <button className="primary" disabled={busy || !fieldsForAction().length}>{busy?'Saving…':'Save proposal'}</button>
                    </div>
                </form>
            )}
        </Modal>
    );
}
