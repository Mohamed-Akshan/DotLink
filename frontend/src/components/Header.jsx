import { useEffect, useState } from 'react';
import { Search, Menu } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api';
import Modal from './Modal';

export default function Header({
    page,
    setPage,
    menuOpen,
    onMenu
}) {

    const { profile } = useAuth();

    const [open, setOpen] = useState(false);
    const [query, setQuery] = useState('');
    const [records, setRecords] = useState([]);
    const [error, setError] = useState('');

    useEffect(() => {

        function key(e) {

            if (
                (e.ctrlKey || e.metaKey) &&
                e.key.toLowerCase() === 'k'
            ) {

                e.preventDefault();
                setOpen(true);

            }
        }

        window.addEventListener('keydown', key);

        return () => {
            window.removeEventListener('keydown', key);
        };

    }, []);

    useEffect(() => {

        if (!open) return;

        setError('');

        Promise.all([

            ['Clients', '/clients'],
            ['Projects', '/projects'],
            ['Tasks', '/projects/tasks/all'],
            ['Services', '/services'],
            ['Finance', '/finance/documents'],
            ['Finance', '/expenses']

        ].map(async ([page, path]) => ({

            page,
            rows: await api(path)

        })))

            .then(groups => {

                const all = [];

                for (const group of groups) {

                    for (const record of group.rows) {

                        all.push({

                            page: group.page,
                            id: record.id,
                            label:
                                record.title ||
                                record.name ||
                                `${record.document_type} #${record.id}`

                        });

                    }

                }

                setRecords(all);

            })

            .catch(e => setError(e.message));

    }, [open]);

    return (

        <header className="header">

            <button
                className="mobile-menu-button icon-button"
                aria-label="Open navigation"
                aria-expanded={menuOpen}
                aria-controls="workspace-navigation"
                onClick={onMenu}
            >

                <Menu size={24} />

            </button>

            <h2>{page}</h2>

            <div className="header-right">

                <button
                    className="secondary global-search"
                    onClick={() => setOpen(true)}
                >

                    <Search size={16} />

                    Search

                    <small>Ctrl K</small>

                </button>

                <span>{profile.user.full_name}</span>

                <div className="avatar">

                    {profile.user.full_name
                        .slice(0, 1)
                        .toUpperCase()}

                </div>

            </div>

            {open && (

                <Modal
                    title="Search workspace"
                    onClose={() => setOpen(false)}
                >

                    <input
                        autoFocus
                        aria-label="Search workspace"
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                        placeholder="Search clients, tasks, projects and documents…"
                    />

                    {error && (
                        <p className="error">{error}</p>
                    )}

                    {records

                        .filter(record =>
                            query.trim() &&
                            record.label
                                .toLowerCase()
                                .includes(query.toLowerCase())
                        )

                        .slice(0, 30)

                        .map((record, index) => (

                            <button
                                className="history-item"
                                key={index}
                                onClick={() => {

                                    setPage(record.page);
                                    setOpen(false);

                                }}
                            >

                                <b>{record.label}</b>

                                <small> · {record.page}</small>

                            </button>

                        ))}

                </Modal>

            )}

        </header>

    );
}