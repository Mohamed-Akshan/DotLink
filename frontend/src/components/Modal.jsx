import { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';

export default function Modal({ title, onClose, children }) {
    const panel = useRef(null);

    useEffect(() => {
        const previous = document.activeElement;
        panel.current?.focus();

        return () => previous?.focus();
    }, []);

    function handleKey(event) {
        if(event.key==='Tab'){
            const items=panel.current?.querySelectorAll('button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href]');
            if(items?.length){const first=items[0],last=items[items.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}}
        }
        if (event.key === 'Escape') {
            event.stopPropagation();
            onClose();
        }
    }

    return createPortal(
        <div className="modal-backdrop" onClick={onClose}>
            <section
                ref={panel}
                tabIndex={-1}
                role="dialog"
                aria-modal="true"
                aria-label={title}
                className="modal"
                onClick={event => event.stopPropagation()}
                onKeyDown={handleKey}
            >
                <div className="modal-header">
                    <h2>{title}</h2>
                    <button type="button" className="icon-button" onClick={onClose} aria-label="Close">
                        <X size={20} />
                    </button>
                </div>
                {children}
            </section>
        </div>,
        document.body
    );
}
