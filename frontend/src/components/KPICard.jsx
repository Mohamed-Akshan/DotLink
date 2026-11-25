export default function KPICard({ label, value, featured=false }) { return <article className={'kpi '+(featured?'featured':'')}><small>{label}</small><strong>{value}</strong></article>; }
