const base = import.meta.env.VITE_API_URL || '/api';

export async function api(path, method = 'GET', data) {
    const token = sessionStorage.getItem('dotlink_token');
    const response = await fetch(base + path, {
        method,
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: data === undefined ? undefined : JSON.stringify(data),
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        if (response.status === 401 && token) window.dispatchEvent(new Event('dotlink-expired'));
        throw new Error(typeof error.detail === 'string' ? error.detail : 'Request failed. Please try again.');
    }
    return response.json();
}

export async function download(path, name) {
    const token = sessionStorage.getItem('dotlink_token');
    const response = await fetch(base + path, { headers: { Authorization: `Bearer ${token}` } });
    if (!response.ok) throw new Error('Unable to download document.');
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement('a');
    link.href = url;
    link.download = name;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const money = value => new Intl.NumberFormat('en-LK', { style: 'currency', currency: 'LKR', maximumFractionDigits: 2 }).format(Number(value || 0));
export const today = () => new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Colombo', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());

export async function preview(path) {
    const tab = window.open('', '_blank');
    if (!tab) throw new Error('Allow pop-ups to preview the PDF.');
    try {
        const response = await fetch(base + path, {headers:{Authorization:`Bearer ${sessionStorage.getItem('dotlink_token')}`}});
        if (!response.ok) throw new Error('Unable to preview document.');
        const url = URL.createObjectURL(await response.blob());
        tab.location.href = url;
        setTimeout(()=>URL.revokeObjectURL(url),60000);
    } catch (error) {tab.close();throw error;}
}
