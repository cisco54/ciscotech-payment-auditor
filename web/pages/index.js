import {useEffect,useState} from 'react';

export default function Home(){
 const [url,setUrl]=useState('');
 const [project,setProject]=useState('');
 const [auth,setAuth]=useState('');
 const [audits,setAudits]=useState([]);
 const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000';

 const load=()=>fetch(API+'/api/audits').then(r=>r.json()).then(setAudits);

 useEffect(()=>{load();},[]);

 async function run(e){
   e.preventDefault();
   if(!url)return;
   await fetch(API+'/api/audits',{
     method:'POST',
     headers:{'Content-Type':'application/json'},
     body:JSON.stringify({
       url,project,authorization_id:auth,
       scope:['checkout','payment','webhooks']
     })
   });
   setUrl('');
   load();
 }

 return <main style={{fontFamily:'Arial',maxWidth:1000,margin:'40px auto',padding:20}}>
 <h1>CiscoTech Payment Auditor</h1>
 <p>Auditoría autorizada de checkout y pasarelas de pago.</p>
 <form onSubmit={run} style={{display:'grid',gap:12,background:'#f5f5f5',padding:20,borderRadius:12}}>
 <input placeholder="https://cliente.com/checkout" value={url} onChange={e=>setUrl(e.target.value)} />
 <input placeholder="Proyecto / cliente" value={project} onChange={e=>setProject(e.target.value)} />
 <input placeholder="ID de autorización / contrato" value={auth} onChange={e=>setAuth(e.target.value)} />
 <button>Iniciar auditoría</button></form>
 <h2>Auditorías</h2>
 {audits.map(a=><div key={a.id} style={{border:'1px solid #ddd',padding:15,margin:'10px 0',borderRadius:8}}>
 <b>{a.request?.project}</b> — {a.status}<br/><small>{a.request?.url}</small>
 {a.result&&<pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(a.result,null,2)}</pre>}
 </div>)}
 </main>
}
