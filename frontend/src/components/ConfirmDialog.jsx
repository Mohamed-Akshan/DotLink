import { useState } from 'react';
import Modal from './Modal';

export default function ConfirmDialog({ title, description, label = 'Confirm', onConfirm, onClose, danger = true }) {
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');

    async function confirm() {
        setBusy(true);
        setError('');

        try {
            await onConfirm();
            onClose();
        } catch (error) {
            setError(error.message);
        } finally {
            setBusy(false);
        }
    }

    function close() {
        if (!busy) onClose();
    }

    return (
        <Modal title={title} onClose={close}>
            <div className="confirm-content">
                <p>{description}</p>
                {error && <p role="alert" className="error">{error}</p>}
                <div className="dialog-actions">
                    <button className="secondary" onClick={close} disabled={busy}>Cancel</button>
                    <button className={danger ? 'danger-button' : 'primary'} onClick={confirm} disabled={busy}>
                        {busy ? 'Working…' : label}
                    </button>
                </div>
            </div>
        </Modal>
    );
}
