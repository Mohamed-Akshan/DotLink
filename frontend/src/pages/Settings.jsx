import {useState} from 'react';
import {useAuth} from '../context/AuthContext';
import {api} from '../api';
import {Fields} from '../components/RecordPage';
import PasswordInput from '../components/PasswordInput';

export default function Settings(){
    const {profile,refresh}=useAuth();
    const w=profile.workspace;
    const [form,setForm]=useState({business_name:w.business_name,business_email:w.business_email,phone:w.phone,address:w.address});
    const [name,setName]=useState(profile.user.full_name);
    const [password,setPassword]=useState({current_password:'',password:'',confirm_password:''});
    const [message,setMessage]=useState('');
    const [error,setError]=useState('');
    const [busy,setBusy]=useState(false);

    async function save(e,path,data,success){
        e.preventDefault();setError('');setMessage('');setBusy(true);
        try{
            await api(path,'PUT',data);
            await refresh();
            setMessage(success);
            if(path==='/settings/password')setPassword({current_password:'',password:'',confirm_password:''});
        }catch(e){setError(e.message);}finally{setBusy(false);}
    }
    return <><div className="page-title"><div><h1>Settings</h1><p>Manage your profile and business information.</p></div></div>{message&&<p className="success">{message}</p>}{error&&<p className="error">{error}</p>}<section className="panel settings-panel"><h3>Account profile</h3><form onSubmit={e=>save(e,'/settings/profile',{full_name:name},'Profile saved.')}><label>Full name<input required value={name} onChange={e=>setName(e.target.value)}/></label><label>Email<input value={profile.user.email} readOnly/></label><button className="primary" disabled={busy}>Save profile</button></form></section><section className="panel settings-panel"><h3>Change password</h3><form onSubmit={e=>save(e,'/settings/password',password,'Password changed.')}><PasswordInput label="Current password" value={password.current_password} onChange={e=>setPassword({...password,current_password:e.target.value})} autoComplete="current-password"/><PasswordInput label="New password" value={password.password} onChange={e=>setPassword({...password,password:e.target.value})} autoComplete="new-password"/><PasswordInput label="Confirm new password" value={password.confirm_password} onChange={e=>setPassword({...password,confirm_password:e.target.value})} autoComplete="new-password"/><p className="muted">Use at least 8 characters, uppercase and lowercase letters, a number and a symbol.</p><button className="primary" disabled={busy}>Update password</button></form></section><section className="panel settings-panel"><h3>Business details</h3><form onSubmit={e=>save(e,'/settings',form,'Business settings saved.')}><Fields form={form} setForm={setForm} fields={[{key:'business_name',label:'Business name'},{key:'business_email',label:'Business email',type:'email',required:false},{key:'phone',label:'Phone',required:false},{key:'address',label:'Address',required:false}]}/><p className="muted">Currency: {w.currency} · Timezone: {w.timezone}</p><button className="primary" disabled={busy}>Save changes</button></form></section><section className="panel settings-panel"><h3>Dottie & privacy</h3><p className="muted">Dottie prepares changes for your review. Your business records are updated only after you approve.</p></section></>;
}
