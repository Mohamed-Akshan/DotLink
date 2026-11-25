import { useEffect, useState } from 'react';
import { CheckCircle2, ClipboardCheck } from 'lucide-react';
import { api, money } from '../api';
import ApprovalEditor from './ApprovalEditor';
import ConfirmDialog from './ConfirmDialog';

export default function ApprovalCard({ item, onChange }) {
    const [current, setCurrent] = useState(item);
    const [editing, setEditing] = useState(false);
    const [rejecting, setRejecting] = useState(false);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const [notice, setNotice] = useState('');

    useEffect(() => setCurrent(item), [item]);

    async function review(decision) {
        setBusy(true);
        setError('');
        try {
            const result = await api(`/approvals/${current.id}/review`, 'POST', {decision});
            setCurrent(result);
            setNotice(decision === 'approve' ? 'Approved. Your changes are saved.' : 'Proposal cancelled. No changes were made.');
            await onChange(result);
        } catch (error) {
            setError(error.message);
            if (decision === 'reject') throw error;
        } finally {
            setBusy(false);
        }
    }

    async function saved(updated) {
        setCurrent(updated);
        setEditing(false);
        setNotice('Proposal updated. Please review the revised details before approving.');
        await onChange(updated);
    }

    const statusLabel = current.status === 'Executed' ? 'Approved' : current.status;

    return (
        <article className="approval-card">
            <div className="approval-heading">
                <span className="approval-icon"><ClipboardCheck size={18}/></span>
                <div><h3>{current.title || 'Business proposal'}</h3><small>Prepared by Dottie</small></div>
                <span className="status">{statusLabel}</span>
            </div>
            {current.status === 'Pending' && <p className="muted proposal-help">Review the details before saving these changes to your business.</p>}
            <dl className="proposal-details">
                {(current.details || []).map((detail, index) => (
                    <div key={index}><dt>{detail.label}</dt><dd>{detail.value}</dd></div>
                ))}
            </dl>
            {current.preview?.items?.length > 0 && (
                <div className="proposal-preview">
                    <b>Line items</b>
                    {current.preview.items.map((line, index) => (
                        <div className="proposal-line" key={index}>
                            <span>{line.description} × {line.quantity}</span>
                            <strong>{money(Number(line.unit_price) * Number(line.quantity))}</strong>
                        </div>
                    ))}
                </div>
            )}
            {current.preview?.total !== undefined && <div className="total-row"><span>Total</span><strong>{money(current.preview.total)}</strong></div>}
            {notice && <p className="proposal-notice" role="status"><CheckCircle2 size={16}/>{notice}</p>}
            {error && <p className="error" role="alert">{error}</p>}
            {current.status === 'Pending' && (
                <div className="actions proposal-actions">
                    {!['issue_invoice','delete_expense','delete_task','void_invoice','reverse_payment','archive_client','archive_project','archive_service'].includes(current.action) && <button className="small" disabled={busy} onClick={() => {setError('');setEditing(true);}}>Edit details</button>}
                    <button className="secondary" disabled={busy} onClick={() => setRejecting(true)}>Decline Request</button>
                    <button className="primary" disabled={busy} onClick={() => review('approve')}>{busy?'Working…':'Approve & Execute'}</button>
                </div>
            )}
            {editing && <ApprovalEditor item={current} onClose={() => setEditing(false)} onSaved={saved}/>}
            {rejecting && <ConfirmDialog title="Reject this proposal?" description="Dottie's proposed changes will be cancelled. No business records will be changed." label="Reject proposal" onClose={() => setRejecting(false)} onConfirm={() => review('reject')}/>}
        </article>
    );
}
