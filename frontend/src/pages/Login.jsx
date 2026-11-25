import { useRef, useState } from 'react';

import {
    ArrowRight,
    CheckCircle2,
    LoaderCircle
} from 'lucide-react';

import { useAuth } from '../context/AuthContext';
import PasswordInput from '../components/PasswordInput';

export default function Login({
    signup = false,
    switchPage,
    goHome
}) {

    const { signIn } = useAuth();

    const [form, setForm] = useState({
        full_name: '',
        business_name: '',
        email: '',
        password: '',
        confirm_password: '',
        accept_terms: false
    });

    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);

    const submitting = useRef(false);

    const rules = [

        [
            '8 or more characters',
            form.password.length >= 8
        ],

        [
            'Uppercase & lowercase',
            /[A-Z]/.test(form.password) &&
            /[a-z]/.test(form.password)
        ],

        [
            'Number & symbol',
            /\d/.test(form.password) &&
            /[^\w\s]|_/.test(form.password)
        ],

        [
            'Passwords match',
            !!form.password &&
            form.password === form.confirm_password
        ]

    ];

    function field(key, value) {

        setForm(old => ({
            ...old,
            [key]: value
        }));

    }

    async function submit(event) {

        event.preventDefault();

        if (submitting.current) return;

        setError('');

        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {

            setError('Please enter a valid email address.');

            return;

        }

        submitting.current = true;

        setBusy(true);

        try {

            await signIn(

                signup ? 'signup' : 'login',

                signup ? form : {
                    email: form.email,
                    password: form.password
                }

            );

        } catch (e) {

            setError(e.message);

        } finally {

            submitting.current = false;

            setBusy(false);

        }
    }

    return (

        <main className="auth-layout">

            <section className="auth-main">

                <button
                    className="brand-home"
                    disabled={busy}
                    onClick={goHome}
                >

                    <img
                        className="brand"
                        src="/assets/dotlink-logo.png"
                        alt="DotLink — home"
                    />

                </button>

                <div className="auth-form">

                    <span className="eyebrow">
                        YOUR CREATIVE WORKSPACE
                    </span>

                    <h1>

                        {signup
                            ? 'Create your workspace'
                            : 'Welcome back.'
                        }

                    </h1>

                    <p className="muted">

                        {signup
                            ? 'A little less admin. A lot more creativity.'
                            : 'Sign in to manage your business with Dottie.'
                        }

                    </p>

                    <form
                        onSubmit={submit}
                        aria-busy={busy}
                    >

                        {signup && (

                            <div className="form-grid">

                                <label>

                                    Full name

                                    <input
                                        required
                                        value={form.full_name}
                                        onChange={e =>
                                            field('full_name', e.target.value)
                                        }
                                        placeholder="Your name"
                                    />

                                </label>

                                <label>

                                    Business name

                                    <input
                                        required
                                        value={form.business_name}
                                        onChange={e =>
                                            field('business_name', e.target.value)
                                        }
                                        placeholder="Studio name"
                                    />

                                </label>

                            </div>

                        )}

                        <label>

                            Email address

                            <input
                                required
                                type="email"
                                autoComplete="email"
                                value={form.email}
                                onChange={e =>
                                    field('email', e.target.value)
                                }
                                placeholder="you@example.com"
                            />

                        </label>

                        <PasswordInput
                            label="Password"
                            value={form.password}
                            onChange={e =>
                                field('password', e.target.value)
                            }
                            autoComplete={
                                signup
                                    ? 'new-password'
                                    : 'current-password'
                            }
                        />

                        {signup && (

                            <>

                                <PasswordInput
                                    label="Confirm password"
                                    value={form.confirm_password}
                                    onChange={e =>
                                        field(
                                            'confirm_password',
                                            e.target.value
                                        )
                                    }
                                    autoComplete="new-password"
                                />

                                <div className="rules">

                                    {rules.map(([text, ok]) => (

                                        <span
                                            key={text}
                                            className={ok ? 'valid' : ''}
                                        >

                                            <CheckCircle2 size={14} />

                                            {text}

                                        </span>

                                    ))}

                                </div>

                                <label className="checkbox">

                                    <input
                                        required
                                        type="checkbox"
                                        checked={form.accept_terms}
                                        onChange={e =>
                                            field(
                                                'accept_terms',
                                                e.target.checked
                                            )
                                        }
                                    />

                                    I agree to use this workspace for
                                    authorized business records.

                                </label>

                            </>

                        )}

                        {error && (

                            <p className="error" role="alert">
                                {error}
                            </p>

                        )}

                        <button
                            className="primary wide"
                            disabled={
                                busy ||
                                (
                                    signup &&
                                    (
                                        !rules.every(r => r[1]) ||
                                        !form.accept_terms
                                    )
                                )
                            }
                        >

                            {busy

                                ? (
                                    signup
                                        ? 'Creating your workspace…'
                                        : 'Signing you in…'
                                )

                                : (
                                    signup
                                        ? 'Create Account'
                                        : 'Sign In'
                                )

                            }

                            {busy ? (

                                <LoaderCircle
                                    className="auth-spinner"
                                    size={18}
                                />

                            ) : (

                                <ArrowRight size={18} />

                            )}

                        </button>

                        {busy && (

                            <div
                                className="auth-progress"
                                role="status"
                            >

                                <span className="auth-progress-track">

                                    <span />

                                </span>

                                <small>

                                    {signup
                                        ? 'Setting up your creative workspace.'
                                        : 'Preparing your creative workspace.'
                                    }

                                </small>

                            </div>

                        )}

                    </form>

                    <p className="auth-switch">

                        {signup
                            ? 'Already have an account?'
                            : 'New to DotLink?'
                        }

                        {' '}

                        <button
                            className="text-button"
                            disabled={busy}
                            onClick={switchPage}
                        >

                            {signup
                                ? 'Sign in'
                                : 'Create an account'
                            }

                        </button>

                    </p>

                </div>

                <small className="muted">

                    DotLink · Connect the dots. Focus on what matters.

                </small>

            </section>

            <aside className="auth-art">

                <div className="art-pill">

                    ✦ &nbsp; YOUR AI BUSINESS COMPANION

                </div>

                <img
                    src="/assets/dottie.png"
                    alt="Dottie, a friendly blue mascot"
                />

                <h2>
                    Make room for<br />
                    your best work.
                </h2>

                <p>

                    Clients, projects and finances — together in one
                    intelligent workspace.

                </p>

                <div className="art-bottom">

                    Meet Dottie <span>●</span> Here to help.

                </div>

            </aside>

        </main>

    );
}