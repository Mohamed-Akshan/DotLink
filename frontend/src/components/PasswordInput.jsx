import { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
export default function PasswordInput({ label, value, onChange, autoComplete }) {
    const [visible, setVisible] = useState(false);
    return <label>{label}<div className="password-wrap"><input required type={visible ? 'text' : 'password'} value={value} onChange={onChange} autoComplete={autoComplete} maxLength={128}/><button type="button" className="icon-button" aria-label={visible ? 'Hide password' : 'Show password'} onClick={() => setVisible(!visible)}>{visible ? <EyeOff size={18}/> : <Eye size={18}/>}</button></div></label>;
}
