import { useEffect, useRef, useState } from 'react';

import {
    Send,
    Plus,
    History,
    Minus,
    ArrowUpRight,
    ChevronLeft,
    X
} from 'lucide-react';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { api, download } from '../api';
import ApprovalCard from './ApprovalCard';

const suggestionsByPage = {

    Tasks: [
        'Show my overdue tasks',
        'Help me create a task'
    ],

    Clients: [
        'Help me add a new client',
        'Show my clients'
    ],

    Projects: [
        'Help me create a new project',
        'Which projects are due soon?'
    ],

    Finance: [
        'Prepare a quotation for a client',
        'Show my outstanding invoices',
        'Record an expense'
    ],

    Services: [
        'Help me add a new service',
        'Show my service prices'
    ],

    Overview: [
        'Help me create a new project',
        'Add a new client',
        'Prepare a quotation',
        'How is my business doing?'
    ]

};

export default function DottieChat({
    onChange,
    page,
    context = {}
}) {

    const [expanded, setExpanded] = useState(false);
    const [open, setOpen] = useState(false);
    const [wave, setWave] = useState(false);
    const [seen, setSeen] = useState(false);

    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState([]);
    const [conversation, setConversation] = useState(null);

    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const [history, setHistory] = useState(null);

    const [approvals, setApprovals] = useState([]);
    const [downloads, setDownloads] = useState([]);

    const end = useRef(null);
    const input = useRef(null);
    const sending = useRef(false);

    useEffect(() => {

        end.current?.scrollIntoView({
            behavior: 'smooth',
            block: 'nearest'
        });

    }, [messages, busy, approvals, downloads]);

    useEffect(() => {

        if (!wave) return;

        const timer = setTimeout(
            () => setWave(false),
            1800
        );

        return () => clearTimeout(timer);

    }, [wave]);

    useEffect(() => {

        function show() {

            setOpen(true);
            setWave(true);

        }

        window.addEventListener('dotlink-ask', show);

        return () => {
            window.removeEventListener('dotlink-ask', show);
        };

    }, []);

    useEffect(() => {

        if (!open) return;

        const close = e => {

            if (
                e.key === 'Escape' &&
                !document.querySelector('.modal-backdrop')
            ) {

                setOpen(false);

            }

        };

        window.addEventListener('keydown', close);

        return () => {
            window.removeEventListener('keydown', close);
        };

    }, [open]);

    function toggle() {

        setOpen(!open);

        if (!seen) {

            setSeen(true);
            setWave(true);

        }

    }

    function reset() {

        setConversation(null);
        setMessages([]);
        setApprovals([]);
        setDownloads([]);
        setHistory(null);
        setMessage('');
        setError('');

    }

    async function send(text) {

        const question = text.trim();

        if (!question || sending.current) return;

        sending.current = true;

        setBusy(true);
        setError('');
        setMessage('');
        setHistory(null);

        setMessages(old => [

            ...old,

            {
                role: 'user',
                content: question
            }

        ]);

        try {

            const result = await api(

                '/chat',

                'POST',

                {
                    message: question,
                    conversation_id: conversation,
                    page,
                    ...context
                }

            );

            setConversation(result.conversation_id);

            setMessages(old => [

                ...old,

                {
                    role: 'assistant',
                    content: result.answer
                }

            ]);

            setApprovals(result.approvals || []);

            setDownloads(result.downloads || []);

            if (result.approvals?.length) {

                onChange();

            }

        } catch (error) {

            setError(
                'I couldn’t connect right now. ' +
                error.message
            );

            setMessage(question);

        } finally {

            sending.current = false;

            setBusy(false);

            if (window.matchMedia('(min-width: 701px)').matches) {

                input.current?.focus();

            }

        }

    }

    async function showHistory() {

        try {

            setHistory(
                history
                    ? null
                    : await api('/chat/conversations')
            );

        } catch (error) {

            setError(error.message);

        }

    }

    async function refreshApprovals(id) {

        const all = await api('/approvals');

        const pending = [];

        for (const item of all) {

            if (
                item.conversation_id === id &&
                item.status === 'Pending'
            ) {

                pending.push(item);

            }

        }

        setApprovals(pending);

    }

    async function select(id) {

        try {

            setMessages(
                await api(`/chat/conversations/${id}`)
            );

            setConversation(id);
            setHistory(null);
            setDownloads([]);
            setError('');

            await refreshApprovals(id);

        } catch (error) {

            setError(error.message);

        }

    }

    async function afterApproval() {

        try {

            await refreshApprovals(conversation);

            setMessages(
                await api(`/chat/conversations/${conversation}`)
            );

            onChange();

        } catch (error) {

            setError(error.message);

        }

    }

    const suggestions =
        suggestionsByPage[page] ||
        suggestionsByPage.Overview;

    return (

        <>

            <button
                className="dottie-float"
                aria-label="Open Dottie assistant"
                aria-expanded={open}
                onClick={toggle}
            >

                <img
                    src="/assets/dottie.png"
                    alt="Dottie"
                />

            </button>

            {open && (

                <section
                    className={
                        'chat-panel' +
                        (expanded ? ' expanded' : '')
                    }
                    aria-label="Dottie business assistant"
                >

                    <header className="chat-header">

                        <img
                            src="/assets/dottie.png"
                            alt=""
                        />

                        <div>

                            <b>Dottie</b>

                            <small>
                                Your personal business companion
                            </small>

                        </div>

                        <button
                            aria-label="New chat"
                            title="New chat"
                            onClick={reset}
                            disabled={busy}
                        >

                            <Plus size={18} />

                        </button>

                        <button
                            aria-label="Conversation history"
                            title="Conversation history"
                            onClick={showHistory}
                            disabled={busy}
                        >

                            <History size={18} />

                        </button>

                        <button
                            className="chat-expand"
                            aria-label="Expand assistant"
                            title="Expand assistant"
                            onClick={() => setExpanded(v => !v)}
                        >

                            ⤢

                        </button>

                        <button
                            aria-label="Minimize assistant"
                            onClick={() => setOpen(false)}
                        >

                            <Minus
                                className="chat-desktop-close"
                                size={18}
                            />

                            <X
                                className="chat-mobile-close"
                                size={21}
                            />

                        </button>

                    </header>

                    <div
                        className="chat-body"
                        aria-live="polite"
                    >

                        {(context.project_id || context.client_id) && (

                            <div className="context-pill">

                                Using selected {

                                    context.project_id
                                        ? 'project'
                                        : 'client'

                                } context

                            </div>

                        )}

                        {history ? (

                            <div>

                                <button
                                    className="small"
                                    onClick={() => setHistory(null)}
                                >

                                    <ChevronLeft size={15} />

                                    Back to chat

                                </button>

                                <h3 className="history-title">
                                    Your conversations
                                </h3>

                                {history.length ? (

                                    history.map(item => (

                                        <button
                                            className="history-item"
                                            key={item.id}
                                            onClick={() => select(item.id)}
                                        >

                                            {item.title}

                                        </button>

                                    ))

                                ) : (

                                    <p className="muted">
                                        No previous conversations yet.
                                    </p>

                                )}

                            </div>

                        ) : (

                            <>

                                {!messages.length && (

                                    <div className="chat-welcome">

                                        <img
                                            className={
                                                wave
                                                    ? 'mascot-entrance'
                                                    : ''
                                            }
                                            src="/assets/dottie.png"
                                            alt="Dottie greeting you"
                                        />

                                        <h2>
                                            Hi, I'm Dottie!
                                        </h2>

                                        <p>

                                            I'm your personal business
                                            companion. From managing clients
                                            and projects to preparing
                                            quotations and tracking payments
                                            and expenses, I'm here to make
                                            your day a little easier.

                                        </p>

                                        <h3>
                                            What would you like to work on today?
                                        </h3>

                                        {suggestions.map(suggestion => (

                                            <button
                                                className="suggestion"
                                                key={suggestion}
                                                onClick={() => send(suggestion)}
                                            >

                                                {suggestion}

                                                <ArrowUpRight size={15} />

                                            </button>

                                        ))}

                                    </div>

                                )}

                                {messages.map((item, index) => (

                                    <div
                                        key={
                                            item.id
                                                ? 'saved-' + item.id
                                                : 'local-' + index
                                        }
                                        className={
                                            'message ' + item.role
                                        }
                                    >

                                        <ReactMarkdown
                                            remarkPlugins={[remarkGfm]}
                                            components={{
                                                a: ({ children }) => (
                                                    <span>{children}</span>
                                                ),
                                                img: () => null
                                            }}
                                        >

                                            {item.content}

                                        </ReactMarkdown>

                                    </div>

                                ))}

                                {busy && (

                                    <div className="typing-indicator">

                                        <span />
                                        <span />
                                        <span />

                                        <small>
                                            Dottie is thinking…
                                        </small>

                                    </div>

                                )}

                                {approvals.map(item => (

                                    <ApprovalCard
                                        key={item.id}
                                        item={item}
                                        onChange={afterApproval}
                                    />

                                ))}

                                {downloads.map((item, index) => (

                                    <button
                                        className="secondary"
                                        key={index}
                                        onClick={() =>
                                            download(
                                                item.path,
                                                item.label
                                            ).catch(error =>
                                                setError(error.message)
                                            )
                                        }
                                    >

                                        Download {item.label}

                                    </button>

                                ))}

                                {error && (

                                    <p
                                        className="error"
                                        role="alert"
                                    >

                                        {error}

                                    </p>

                                )}

                                <div ref={end} />

                            </>

                        )}

                    </div>

                    <form
                        className="chat-input"
                        onSubmit={event => {

                            event.preventDefault();

                            send(message);

                        }}
                    >

                        <input
                            ref={input}
                            aria-label="Ask Dottie"
                            placeholder="Ask Dottie about your business…"
                            value={message}
                            onChange={event =>
                                setMessage(event.target.value)
                            }
                            maxLength={5000}
                        />

                        <button
                            className="primary"
                            disabled={busy || !message.trim()}
                            aria-label="Send message"
                        >

                            <Send size={17} />

                        </button>

                    </form>

                    <small className="chat-footer">

                        You're always in control.
                        Dottie asks before making changes.

                    </small>

                </section>

            )}

        </>

    );
}