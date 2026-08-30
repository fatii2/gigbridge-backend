import { useState, useEffect, useRef } from "react";

// ─── Palette & Globals ────────────────────────────────────────────────────────
const C = {
  bg:      "#07111F",
  card:    "#0D1E33",
  card2:   "#112240",
  border:  "#1A3050",
  muted:   "#243B55",
  text:    "#E0EAF4",
  sub:     "#6B89A8",
  orange:  "#E8700A",
  orangeL: "#FF8C2A",
  blue:    "#2D6BE4",
  blueL:   "#5B9AFF",
  green:   "#00C878",
  gold:    "#F0A500",
  red:     "#E84040",
};

const css = `
  @import url('https://fonts.googleapis.com/css2?family=Clash+Display:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
  *{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent;}
  html,body,#root{width:100%;height:100%;background:#000;}
  body{font-family:'Plus Jakarta Sans',sans-serif;color:${C.text};overflow:hidden;}
  input,textarea,select{font-family:inherit;outline:none;}
  button{cursor:pointer;font-family:inherit;border:none;outline:none;}
  ::-webkit-scrollbar{width:3px;}
  ::-webkit-scrollbar-thumb{background:${C.muted};border-radius:4px;}

  .app{
    width:100%;max-width:430px;height:100dvh;
    margin:0 auto;background:${C.bg};
    display:flex;flex-direction:column;
    position:relative;overflow:hidden;
  }

  /* Scrollable content area */
  .screen{flex:1;overflow-y:auto;overflow-x:hidden;padding-bottom:80px;}
  .screen-noscroll{flex:1;overflow:hidden;display:flex;flex-direction:column;}

  /* Typography */
  .font-display{font-family:'Clash Display',sans-serif;}

  /* Bottom Nav */
  .bottom-nav{
    position:absolute;bottom:0;left:0;right:0;
    height:68px;background:${C.card};
    border-top:1px solid ${C.border};
    display:flex;align-items:stretch;
    padding-bottom:env(safe-area-inset-bottom,0);
    z-index:100;
  }
  .nav-btn{
    flex:1;display:flex;flex-direction:column;align-items:center;
    justify-content:center;gap:3px;background:none;
    color:${C.sub};font-size:9px;font-weight:700;
    letter-spacing:.05em;text-transform:uppercase;
    transition:color .2s;
  }
  .nav-btn.active{color:${C.orange};}
  .nav-icon{font-size:20px;line-height:1;}

  /* Cards */
  .card{background:${C.card};border:1px solid ${C.border};border-radius:18px;padding:16px;}
  .card2{background:${C.card2};border:1px solid ${C.border};border-radius:14px;padding:14px;}

  /* Buttons */
  .btn-primary{
    width:100%;padding:15px;border-radius:14px;
    background:${C.orange};color:#fff;
    font-size:15px;font-weight:700;
    transition:all .2s;
  }
  .btn-primary:active{transform:scale(.97);background:${C.orangeL};}
  .btn-secondary{
    width:100%;padding:14px;border-radius:14px;
    background:transparent;color:${C.text};
    border:1.5px solid ${C.border};
    font-size:15px;font-weight:600;
    transition:all .2s;
  }
  .btn-secondary:active{background:${C.muted};}
  .btn-small{
    padding:8px 16px;border-radius:20px;
    background:${C.orange};color:#fff;
    font-size:12px;font-weight:700;
  }
  .btn-ghost{
    padding:8px 16px;border-radius:20px;
    background:${C.muted};color:${C.text};
    font-size:12px;font-weight:600;
  }

  /* Input */
  .inp{
    width:100%;padding:14px 16px;border-radius:12px;
    background:${C.card2};border:1.5px solid ${C.border};
    color:${C.text};font-size:14px;
    transition:border .2s;
  }
  .inp:focus{border-color:${C.orange};}
  .inp::placeholder{color:${C.sub};}

  /* Badge */
  .badge{
    display:inline-flex;align-items:center;gap:4px;
    padding:3px 9px;border-radius:20px;
    font-size:11px;font-weight:700;
  }

  /* Chip */
  .chip{
    display:inline-flex;align-items:center;gap:5px;
    padding:7px 14px;border-radius:20px;
    border:1.5px solid ${C.border};background:${C.card2};
    font-size:12px;font-weight:600;color:${C.sub};
    white-space:nowrap;cursor:pointer;transition:all .15s;
  }
  .chip.active{background:${C.orange};border-color:${C.orange};color:#fff;}
  .chip:active{opacity:.8;}

  /* Animations */
  @keyframes fadeUp{from{opacity:0;transform:translateY(20px);}to{opacity:1;transform:translateY(0);}}
  @keyframes fadeIn{from{opacity:0;}to{opacity:1;}}
  @keyframes pulse{0%,100%{opacity:1;}50%{opacity:.5;}}
  @keyframes shimmer{0%{background-position:-200% 0;}100%{background-position:200% 0;}}

  .fade-up{animation:fadeUp .4s ease both;}
  .fade-in{animation:fadeIn .3s ease both;}

  /* Skeleton */
  .skel{
    background:linear-gradient(90deg,${C.card} 25%,${C.card2} 50%,${C.card} 75%);
    background-size:200% 100%;
    animation:shimmer 1.5s infinite;
    border-radius:8px;
  }

  /* Chat bubbles */
  .bubble-bot{
    background:${C.card2};border:1px solid ${C.border};
    border-radius:18px 18px 18px 4px;
    padding:11px 14px;max-width:82%;
    font-size:13.5px;line-height:1.55;color:${C.text};
  }
  .bubble-user{
    background:${C.orange};
    border-radius:18px 18px 4px 18px;
    padding:11px 14px;max-width:78%;
    font-size:13.5px;line-height:1.55;color:#fff;
    margin-left:auto;
  }
`;

// ─── Seed Data ────────────────────────────────────────────────────────────────
const SEED_JOBS = [
  {id:1,title:"Social Media Manager",business:"BrewBox Café",location:"Clifton",salary:18000,type:"Part-time",skills:["Social Media","Canva","Content Writing"],urgent:true,remote:false,hours:"4 hrs/day",pay:"EasyPaisa",desc:"Manage Instagram, TikTok and Facebook. Create engaging content and grow following.",color:"#E8700A"},
  {id:2,title:"Junior Data Analyst",business:"TechHive Solutions",location:"DHA",salary:25000,type:"Part-time",skills:["Excel","SQL","Python"],urgent:false,remote:true,hours:"5 hrs/day",pay:"JazzCash",desc:"Analyze customer data, build Excel dashboards and present weekly reports.",color:"#2D6BE4"},
  {id:3,title:"Customer Support Rep",business:"TechHive Solutions",location:"DHA",salary:22000,type:"Part-time",skills:["Communication","CRM"],urgent:true,remote:false,hours:"5 hrs/day",pay:"EasyPaisa",desc:"Handle inbound queries via chat and phone. CRM training provided.",color:"#2D6BE4"},
  {id:4,title:"Content Writer",business:"MediaPulse PK",location:"Remote",salary:3000,type:"Part-time",skills:["Writing","SEO"],urgent:false,remote:true,hours:"Project-based",pay:"JazzCash",desc:"Write SEO blog articles in Urdu and English. Portfolio required.",color:"#7C3AED"},
  {id:5,title:"Weekend Barista",business:"BrewBox Café",location:"Clifton",salary:10000,type:"Part-time",skills:["Hospitality"],urgent:false,remote:false,hours:"Sat & Sun",pay:"EasyPaisa",desc:"Assist our head barista on weekends. No experience needed.",color:"#E8700A"},
  {id:6,title:"UI/UX Design Intern",business:"TechHive Solutions",location:"DHA",salary:15000,type:"Part-time",skills:["Figma","Canva","Design"],urgent:true,remote:true,hours:"3 hrs/day",pay:"JazzCash",desc:"Help design mobile app screens using Figma.",color:"#2D6BE4"},
];

const SKILLS_ONBOARD = [
  {icon:"🎨",label:"Graphic Design"},{icon:"📊",label:"Data Entry"},
  {icon:"📞",label:"Sales"},{icon:"📱",label:"Social Media"},
  {icon:"✍️",label:"Content Writing"},{icon:"🤝",label:"Customer Support"},
  {icon:"💻",label:"Web Dev"},{icon:"🎬",label:"Video Editing"},
  {icon:"📚",label:"Tutoring"},{icon:"🏢",label:"Admin Work"},
  {icon:"☕",label:"Food & Café"},{icon:"🚚",label:"Delivery"},
];

// ─── Helpers ──────────────────────────────────────────────────────────────────
const fmt = n => `PKR ${n.toLocaleString()}`;
const ini = n => n.split(" ").map(w=>w[0]).join("").toUpperCase().slice(0,2);
const COLORS = ["#E8700A","#2D6BE4","#7C3AED","#00C878","#F0A500","#E84040"];
const avc = name => COLORS[name.split("").reduce((a,c)=>a+c.charCodeAt(0),0)%COLORS.length];

function Avatar({name,size=40,fontSize=13}){
  return(
    <div style={{width:size,height:size,borderRadius:"50%",background:avc(name),
      display:"flex",alignItems:"center",justifyContent:"center",
      fontFamily:"'Clash Display',sans-serif",fontSize,fontWeight:700,color:"#fff",flexShrink:0}}>
      {ini(name)}
    </div>
  );
}

function LogoBadge({size=32}){
  return(
    <div style={{width:size,height:size,borderRadius:8,background:avc("BrewBox"),
      display:"flex",alignItems:"center",justifyContent:"center",
      fontFamily:"'Clash Display',sans-serif",fontSize:size*0.38,fontWeight:700,color:"#fff",flexShrink:0}}>
      BC
    </div>
  );
}

function BizAvatar({name,size=38}){
  const c = avc(name);
  return(
    <div style={{width:size,height:size,borderRadius:10,background:c,
      display:"flex",alignItems:"center",justifyContent:"center",
      fontFamily:"'Clash Display',sans-serif",fontSize:size*0.36,fontWeight:700,color:"#fff",flexShrink:0}}>
      {ini(name)}
    </div>
  );
}

// ─── Top Bar ──────────────────────────────────────────────────────────────────
function TopBar({title,onBack,right}){
  return(
    <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",
      padding:"14px 20px 10px",background:C.bg,flexShrink:0,
      borderBottom:`1px solid ${C.border}`}}>
      <div style={{width:36}}>
        {onBack&&<button onClick={onBack} style={{background:"none",border:"none",color:C.text,fontSize:22,display:"flex",alignItems:"center"}}>‹</button>}
      </div>
      <div style={{textAlign:"center"}}>
        <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:16,fontWeight:700,color:C.text}}>{title}</div>
      </div>
      <div style={{width:36,display:"flex",justifyContent:"flex-end"}}>{right}</div>
    </div>
  );
}

// ─── Nav Bar ─────────────────────────────────────────────────────────────────
const S_TABS=[
  {id:"home",icon:"🏠",label:"Home"},
  {id:"gigbot",icon:"🤖",label:"GigBot"},
  {id:"gigs",icon:"🔍",label:"Gigs"},
  {id:"applied",icon:"📋",label:"Applied"},
  {id:"profile",icon:"👤",label:"Profile"},
];
const B_TABS=[
  {id:"home",icon:"🏠",label:"Home"},
  {id:"post",icon:"➕",label:"Post"},
  {id:"applicants",icon:"👥",label:"Applicants"},
  {id:"profile",icon:"👤",label:"Profile"},
];

function BottomNav({tabs,active,onTab}){
  return(
    <div className="bottom-nav">
      {tabs.map(t=>(
        <button key={t.id} className={`nav-btn${active===t.id?" active":""}`} onClick={()=>onTab(t.id)}>
          <span className="nav-icon">{t.icon}</span>
          {t.label}
        </button>
      ))}
    </div>
  );
}

// ─── Job Card ─────────────────────────────────────────────────────────────────
function JobCard({job,onView}){
  return(
    <div className="card fade-up" style={{marginBottom:12,position:"relative",overflow:"hidden"}}>
      <div style={{position:"absolute",top:-30,right:-30,width:100,height:100,
        background:`radial-gradient(${job.color}30,transparent 70%)`,borderRadius:"50%"}}/>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:10}}>
        <div style={{display:"flex",gap:10,alignItems:"center",flex:1,minWidth:0}}>
          <BizAvatar name={job.business} size={40}/>
          <div style={{minWidth:0}}>
            <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:15,fontWeight:700,
              color:C.text,whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{job.title}</div>
            <div style={{color:C.sub,fontSize:12,marginTop:2}}>{job.business} · {job.location}</div>
          </div>
        </div>
        <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:14,fontWeight:700,
          color:C.orange,whiteSpace:"nowrap",marginLeft:8}}>{fmt(job.salary)}/mo</div>
      </div>
      <div style={{display:"flex",gap:6,flexWrap:"wrap",marginBottom:10}}>
        {job.urgent&&<span className="badge" style={{background:"rgba(232,112,10,.15)",color:C.orange}}>⚡ Urgent</span>}
        {job.remote&&<span className="badge" style={{background:"rgba(45,107,228,.15)",color:C.blueL}}>🌐 Remote</span>}
        <span className="badge" style={{background:C.muted,color:C.sub}}>{job.type}</span>
        {job.skills.slice(0,2).map(s=>(
          <span key={s} className="badge" style={{background:C.muted,color:C.sub}}>{s}</span>
        ))}
      </div>
      <div style={{color:C.sub,fontSize:12.5,lineHeight:1.5,marginBottom:12}}>
        {job.desc.slice(0,90)}…
      </div>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
        <div style={{fontSize:11.5,color:C.sub}}>⏱ {job.hours} · 💳 {job.pay}</div>
        <button className="btn-small" onClick={()=>onView(job)}>View & Apply →</button>
      </div>
    </div>
  );
}

// ─── SCREENS ─────────────────────────────────────────────────────────────────

// SPLASH
function SplashScreen({onDone}){
  useEffect(()=>{const t=setTimeout(onDone,2200);return()=>clearTimeout(t);},[]);
  return(
    <div style={{flex:1,display:"flex",flexDirection:"column",alignItems:"center",
      justifyContent:"center",background:C.bg,gap:16}}>
      <div className="fade-up" style={{textAlign:"center"}}>
        <div style={{fontSize:64,marginBottom:8}}>🌉</div>
        <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:42,fontWeight:700,
          color:C.text,letterSpacing:"-0.03em",lineHeight:1.1}}>
          Gig<span style={{color:C.orange}}>Bridge</span>
        </div>
        <div style={{color:C.sub,fontSize:13,marginTop:8,letterSpacing:"0.1em",textTransform:"uppercase"}}>
          Bridging Karachi's Students
        </div>
      </div>
      <div style={{marginTop:32,display:"flex",gap:6}}>
        {[0,1,2].map(i=>(
          <div key={i} style={{width:i===1?24:8,height:8,borderRadius:4,
            background:i===1?C.orange:C.muted,transition:"all .3s"}}/>
        ))}
      </div>
    </div>
  );
}

// ONBOARDING SLIDES
const SLIDES=[
  {icon:"⚡",title:"Find Part-Time Gigs",sub:"Browse hundreds of verified part-time jobs from real Karachi businesses — matched to your skills."},
  {icon:"🤖",title:"AI-Powered Matching",sub:"GigBot learns your interests and instantly matches you with the right opportunities."},
  {icon:"💳",title:"Get Paid Easily",sub:"Receive salary via EasyPaisa, JazzCash, or bank transfer — no hassle, no delays."},
];

function OnboardingScreen({onDone}){
  const [slide,setSlide]=useState(0);
  const next=()=>slide<SLIDES.length-1?setSlide(s=>s+1):onDone();
  const s=SLIDES[slide];
  return(
    <div style={{flex:1,display:"flex",flexDirection:"column",background:C.bg}}>
      {/* Skip */}
      <div style={{padding:"16px 20px",display:"flex",justifyContent:"flex-end"}}>
        <button onClick={onDone} style={{background:"none",color:C.sub,fontSize:13,fontWeight:600}}>Skip</button>
      </div>
      {/* Content */}
      <div style={{flex:1,display:"flex",flexDirection:"column",alignItems:"center",
        justifyContent:"center",padding:"0 32px",textAlign:"center",gap:24}}>
        <div className="fade-up" key={slide} style={{
          width:120,height:120,borderRadius:32,
          background:C.card2,border:`2px solid ${C.border}`,
          display:"flex",alignItems:"center",justifyContent:"center",
          fontSize:52}}>
          {s.icon}
        </div>
        <div className="fade-up" key={`t${slide}`} style={{animationDelay:".1s"}}>
          <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:28,fontWeight:700,
            color:C.text,lineHeight:1.2,marginBottom:12}}>{s.title}</div>
          <div style={{color:C.sub,fontSize:14,lineHeight:1.7}}>{s.sub}</div>
        </div>
      </div>
      {/* Dots + button */}
      <div style={{padding:"32px 24px 48px",display:"flex",flexDirection:"column",gap:20,alignItems:"center"}}>
        <div style={{display:"flex",gap:6}}>
          {SLIDES.map((_,i)=>(
            <div key={i} style={{width:i===slide?24:8,height:8,borderRadius:4,
              background:i===slide?C.orange:C.muted,transition:"all .3s"}}/>
          ))}
        </div>
        <button className="btn-primary" onClick={next}>
          {slide===SLIDES.length-1?"Get Started →":"Next →"}
        </button>
      </div>
    </div>
  );
}

// LANDING
function LandingScreen({onRole}){
  return(
    <div style={{flex:1,display:"flex",flexDirection:"column",background:C.bg}}>
      {/* Hero */}
      <div style={{padding:"48px 24px 32px",textAlign:"center",
        background:`radial-gradient(ellipse at 50% 0%, rgba(232,112,10,0.12), transparent 70%)`}}>
        <div style={{fontSize:48,marginBottom:12}}>🌉</div>
        <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:38,fontWeight:700,
          color:C.text,letterSpacing:"-0.04em",lineHeight:1.1,marginBottom:8}}>
          Gig<span style={{color:C.orange}}>Bridge</span>
        </div>
        <div style={{color:C.sub,fontSize:14,lineHeight:1.6,maxWidth:260,margin:"0 auto"}}>
          Pakistan's #1 platform connecting students with part-time jobs
        </div>
      </div>
      {/* Cards */}
      <div style={{padding:"0 20px",display:"flex",flexDirection:"column",gap:12,flex:1,justifyContent:"center"}}>
        <button onClick={()=>onRole("student")} style={{
          background:C.card,border:`1.5px solid ${C.border}`,borderRadius:20,
          padding:"20px 20px",textAlign:"left",width:"100%",
          transition:"all .2s",cursor:"pointer"}}>
          <div style={{display:"flex",alignItems:"center",gap:14}}>
            <div style={{width:52,height:52,borderRadius:16,
              background:"rgba(232,112,10,0.12)",border:`1.5px solid rgba(232,112,10,0.3)`,
              display:"flex",alignItems:"center",justifyContent:"center",fontSize:26}}>🎓</div>
            <div>
              <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:18,fontWeight:700,color:C.text}}>I'm a Student</div>
              <div style={{color:C.sub,fontSize:12.5,marginTop:2}}>Find part-time gigs · Free forever</div>
            </div>
            <div style={{marginLeft:"auto",color:C.orange,fontSize:20}}>›</div>
          </div>
        </button>
        <button onClick={()=>onRole("business")} style={{
          background:C.card,border:`1.5px solid ${C.border}`,borderRadius:20,
          padding:"20px 20px",textAlign:"left",width:"100%",cursor:"pointer"}}>
          <div style={{display:"flex",alignItems:"center",gap:14}}>
            <div style={{width:52,height:52,borderRadius:16,
              background:"rgba(45,107,228,0.12)",border:`1.5px solid rgba(45,107,228,0.3)`,
              display:"flex",alignItems:"center",justifyContent:"center",fontSize:26}}>🏢</div>
            <div>
              <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:18,fontWeight:700,color:C.text}}>I'm a Business</div>
              <div style={{color:C.sub,fontSize:12.5,marginTop:2}}>Post gigs · Hire verified talent</div>
            </div>
            <div style={{marginLeft:"auto",color:C.blueL,fontSize:20}}>›</div>
          </div>
        </button>
        {/* Stats row */}
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:8,marginTop:8}}>
          {[["500+","Students"],["50+","Businesses"],["PKR 0","For Students"]].map(([v,l])=>(
            <div key={l} style={{background:C.card,border:`1px solid ${C.border}`,
              borderRadius:12,padding:"12px 8px",textAlign:"center"}}>
              <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:16,fontWeight:700,color:C.orange}}>{v}</div>
              <div style={{fontSize:10,color:C.sub,marginTop:2}}>{l}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// AUTH
function AuthScreen({role,onLogin,onBack}){
  const [tab,setTab]=useState("signin");
  const [form,setForm]=useState({email:"",password:"",name:"",uni:"IBA Karachi",cnic:"",bname:"",industry:"Technology",city:"Karachi"});
  const [err,setErr]=useState("");
  const isS=role==="student";

  const DEMO = isS ? {email:"sara@iba.edu.pk",password:"password123"} : {email:"hr@brewbox.pk",password:"password123"};

  const handleLogin=()=>{
    if(!form.email||!form.password){setErr("Please fill all fields.");return;}
    onLogin({email:form.email,role,name:isS?"Sara Ahmed":"BrewBox Café",plan:"free"});
  };
  const handleSignup=()=>{
    if(isS&&(!form.name||!form.email||!form.password)){setErr("Fill all fields.");return;}
    if(!isS&&(!form.bname||!form.email||!form.password)){setErr("Fill all fields.");return;}
    onLogin({email:form.email,role,name:isS?form.name:form.bname,plan:"free"});
  };

  return(
    <div style={{flex:1,display:"flex",flexDirection:"column",background:C.bg}}>
      <TopBar title={isS?"Student Portal":"Business Portal"} onBack={onBack}/>
      <div className="screen" style={{padding:"24px 20px"}}>
        {/* Icon */}
        <div style={{textAlign:"center",marginBottom:24}}>
          <div style={{fontSize:44}}>{isS?"🎓":"🏢"}</div>
          <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:22,fontWeight:700,color:C.text,marginTop:8}}>
            Welcome to GigBridge
          </div>
        </div>
        {/* Tabs */}
        <div style={{display:"flex",background:C.card2,borderRadius:12,padding:4,marginBottom:24}}>
          {["signin","signup"].map(t=>(
            <button key={t} onClick={()=>{setTab(t);setErr("");}} style={{
              flex:1,padding:"10px",borderRadius:10,
              background:tab===t?C.orange:"transparent",
              color:tab===t?"#fff":C.sub,
              fontSize:13,fontWeight:700,transition:"all .2s"}}>
              {t==="signin"?"Sign In":"Sign Up"}
            </button>
          ))}
        </div>
        {err&&<div style={{background:"rgba(232,64,64,.12)",border:`1px solid ${C.red}`,
          borderRadius:10,padding:"10px 14px",marginBottom:14,fontSize:13,color:C.red}}>{err}</div>}

        {tab==="signin"?(
          <div style={{display:"flex",flexDirection:"column",gap:12}}>
            <input className="inp" placeholder="Email address" value={form.email}
              onChange={e=>setForm({...form,email:e.target.value})}/>
            <input className="inp" type="password" placeholder="Password" value={form.password}
              onChange={e=>setForm({...form,password:e.target.value})}/>
            <div style={{background:C.card2,borderRadius:10,padding:"10px 14px",fontSize:12.5,color:C.sub}}>
              Demo: <span style={{color:C.orange,fontWeight:700}}>{DEMO.email}</span> / <span style={{color:C.orange,fontWeight:700}}>{DEMO.password}</span>
            </div>
            <button className="btn-primary" onClick={handleLogin}>Sign In →</button>
          </div>
        ):(
          <div style={{display:"flex",flexDirection:"column",gap:12}}>
            {isS?(
              <>
                <input className="inp" placeholder="Full Name *" value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/>
                <input className="inp" placeholder="University Email *" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/>
                <input className="inp" placeholder="CNIC *" value={form.cnic} onChange={e=>setForm({...form,cnic:e.target.value})}/>
                <input className="inp" type="password" placeholder="Password *" value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/>
              </>
            ):(
              <>
                <input className="inp" placeholder="Business Name *" value={form.bname} onChange={e=>setForm({...form,bname:e.target.value})}/>
                <input className="inp" placeholder="Business Email *" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/>
                <input className="inp" type="password" placeholder="Password *" value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/>
              </>
            )}
            <button className="btn-primary" onClick={handleSignup}>
              {isS?"Create My Profile →":"Register Business →"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// SKILL ONBOARDING
function SkillOnboarding({onDone}){
  const [selected,setSelected]=useState(new Set());
  const toggle=l=>setSelected(s=>{const n=new Set(s);n.has(l)?n.delete(l):n.add(l);return n;});
  return(
    <div style={{flex:1,display:"flex",flexDirection:"column",background:C.bg}}>
      <div style={{padding:"24px 20px 16px",textAlign:"center",
        background:`radial-gradient(ellipse at 50% 0%,rgba(232,112,10,0.1),transparent 70%)`}}>
        <div style={{fontSize:36,marginBottom:8}}>🎯</div>
        <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:24,fontWeight:700,color:C.text,marginBottom:6}}>
          What can you do?
        </div>
        <div style={{color:C.sub,fontSize:13}}>Pick your skills for AI-powered gig matching</div>
      </div>
      <div className="screen" style={{padding:"16px 20px"}}>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:10,marginBottom:24}}>
          {SKILLS_ONBOARD.map(({icon,label})=>{
            const sel=selected.has(label);
            return(
              <button key={label} onClick={()=>toggle(label)} style={{
                background:sel?"rgba(232,112,10,.15)":C.card2,
                border:`1.5px solid ${sel?C.orange:C.border}`,
                borderRadius:14,padding:"14px 8px",
                display:"flex",flexDirection:"column",alignItems:"center",gap:6,
                cursor:"pointer",transition:"all .15s"}}>
                <span style={{fontSize:22}}>{icon}</span>
                <span style={{fontSize:11,fontWeight:600,color:sel?C.orange:C.sub,textAlign:"center",lineHeight:1.3}}>{label}</span>
              </button>
            );
          })}
        </div>
        {selected.size>0&&(
          <div style={{background:"rgba(232,112,10,.1)",border:`1px solid rgba(232,112,10,.3)`,
            borderRadius:10,padding:"10px 14px",marginBottom:16,textAlign:"center",
            fontSize:13,color:C.orange,fontWeight:600}}>
            {selected.size} skill{selected.size!==1?"s":""} selected ✓
          </div>
        )}
        <button className="btn-primary" onClick={()=>onDone([...selected])}>
          {selected.size>0?"Find My Gigs →":"Skip for now →"}
        </button>
      </div>
    </div>
  );
}

// STUDENT HOME
function StudentHome({user,onNav}){
  const apps=2,hired=0;
  return(
    <div className="screen" style={{padding:"20px 20px 0"}}>
      {/* Hero */}
      <div className="card fade-up" style={{marginBottom:16,
        background:`linear-gradient(135deg, ${C.card} 0%, #112240 100%)`,
        position:"relative",overflow:"hidden"}}>
        <div style={{position:"absolute",top:-40,right:-40,width:140,height:140,
          background:`radial-gradient(${C.orange}25,transparent 70%)`,borderRadius:"50%"}}/>
        <div style={{position:"relative"}}>
          <div style={{fontSize:12,color:C.sub,letterSpacing:"0.08em",textTransform:"uppercase",marginBottom:4}}>Welcome back 👋</div>
          <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:22,fontWeight:700,color:C.text,marginBottom:4}}>
            {user.name.split(" ")[0]}'s Dashboard
          </div>
          <div style={{display:"flex",gap:8,alignItems:"center"}}>
            <span className="badge" style={{background:"rgba(0,200,120,.15)",color:C.green}}>✓ Verified</span>
            <span style={{color:C.sub,fontSize:12}}>IBA Karachi</span>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:10,marginBottom:16}}>
        {[[apps,"Applied","#3B9EE8"],[hired,"Hired",C.green],["PKR 0","Earned",C.gold]].map(([v,l,c])=>(
          <div key={l} style={{background:C.card,border:`1px solid ${C.border}`,
            borderRadius:14,padding:"14px 10px",textAlign:"center"}}>
            <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:18,fontWeight:700,color:c}}>{v}</div>
            <div style={{fontSize:10.5,color:C.sub,marginTop:3,textTransform:"uppercase",letterSpacing:"0.05em"}}>{l}</div>
          </div>
        ))}
      </div>

      {/* Premium banner */}
      <div style={{background:"linear-gradient(135deg,rgba(240,165,0,0.1),rgba(91,127,232,0.1))",
        border:`1px solid rgba(240,165,0,0.3)`,borderRadius:16,padding:"14px 16px",marginBottom:16}}>
        <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:15,fontWeight:700,color:C.gold,marginBottom:4}}>
          ⭐ Unlock Student Premium
        </div>
        <div style={{fontSize:12.5,color:C.sub,lineHeight:1.5,marginBottom:12}}>
          AI CV Generator · Training Programs · Priority Profile — PKR 500/mo
        </div>
        <button className="btn-small" style={{background:C.gold}}>Upgrade Now</button>
      </div>

      {/* Quick actions */}
      <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:16,fontWeight:700,color:C.text,marginBottom:12}}>
        Quick Actions
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:20}}>
        <button onClick={()=>onNav("gigs")} style={{background:C.card,border:`1px solid ${C.border}`,
          borderRadius:14,padding:"16px",cursor:"pointer",textAlign:"left"}}>
          <div style={{fontSize:24,marginBottom:6}}>🔍</div>
          <div style={{fontSize:13,fontWeight:700,color:C.text}}>Browse Gigs</div>
          <div style={{fontSize:11,color:C.sub,marginTop:2}}>{SEED_JOBS.length} available</div>
        </button>
        <button onClick={()=>onNav("gigbot")} style={{background:C.card,border:`1px solid ${C.border}`,
          borderRadius:14,padding:"16px",cursor:"pointer",textAlign:"left"}}>
          <div style={{fontSize:24,marginBottom:6}}>🤖</div>
          <div style={{fontSize:13,fontWeight:700,color:C.text}}>Ask GigBot</div>
          <div style={{fontSize:11,color:C.sub,marginTop:2}}>AI matching</div>
        </button>
      </div>

      {/* Recent jobs */}
      <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:16,fontWeight:700,color:C.text,marginBottom:12}}>
        Urgent Gigs
      </div>
      {SEED_JOBS.filter(j=>j.urgent).slice(0,2).map(job=>(
        <JobCard key={job.id} job={job} onView={()=>onNav("gigs")}/>
      ))}
    </div>
  );
}

// GIGS SCREEN
function GigsScreen({onView}){
  const [filter,setFilter]=useState("All");
  const [search,setSearch]=useState("");
  const FILTERS=[{label:"All",icon:"🌐"},{label:"Part-time",icon:"⏰"},{label:"🤖 For You",icon:"🤖"}];

  const filtered=SEED_JOBS.filter(j=>{
    const q=search.toLowerCase();
    const matchSearch=!q||j.title.toLowerCase().includes(q)||j.business.toLowerCase().includes(q)||j.skills.some(s=>s.toLowerCase().includes(q));
    const matchFilter=filter==="All"||filter==="🤖 For You"||(filter==="Part-time"&&j.type==="Part-time");
    return matchSearch&&matchFilter;
  });

  return(
    <div style={{flex:1,display:"flex",flexDirection:"column",overflow:"hidden"}}>
      <TopBar title="Find Gigs"/>
      <div style={{padding:"12px 20px 0",flexShrink:0}}>
        <input className="inp" placeholder="🔍  Search gigs, skills, companies…"
          value={search} onChange={e=>setSearch(e.target.value)} style={{marginBottom:12}}/>
        <div style={{display:"flex",gap:8,overflowX:"auto",paddingBottom:12,scrollbarWidth:"none"}}>
          {FILTERS.map(f=>(
            <button key={f.label} className={`chip${filter===f.label?" active":""}`}
              onClick={()=>setFilter(f.label)}>
              {f.icon} {f.label}
            </button>
          ))}
        </div>
        <div style={{fontSize:12,color:C.sub,marginBottom:8}}>{filtered.length} gig{filtered.length!==1?"s":""} found</div>
      </div>
      <div style={{flex:1,overflowY:"auto",padding:"0 20px 80px"}}>
        {filtered.length===0?(
          <div style={{textAlign:"center",padding:"48px 20px"}}>
            <div style={{fontSize:40,marginBottom:12}}>🔭</div>
            <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:16,color:C.text}}>No gigs found</div>
            <div style={{color:C.sub,fontSize:13,marginTop:4}}>Try a different search</div>
          </div>
        ):filtered.map(job=>(
          <JobCard key={job.id} job={job} onView={onView}/>
        ))}
      </div>
    </div>
  );
}

// JOB DETAIL
function JobDetail({job,onBack,onApply}){
  const [applied,setApplied]=useState(false);
  const [cover,setCover]=useState("");
  return(
    <div style={{flex:1,display:"flex",flexDirection:"column",overflow:"hidden"}}>
      <TopBar title={job.title} onBack={onBack}/>
      <div className="screen" style={{padding:"20px 20px"}}>
        {/* Hero */}
        <div className="card" style={{marginBottom:14,
          background:`linear-gradient(135deg,${C.card},${C.card2})`,
          position:"relative",overflow:"hidden"}}>
          <div style={{position:"absolute",top:0,right:0,width:160,height:160,
            background:`radial-gradient(${job.color}20,transparent 70%)`,
            borderRadius:"50%",transform:"translate(50px,-50px)"}}/>
          <div style={{display:"flex",gap:12,alignItems:"center",marginBottom:14}}>
            <BizAvatar name={job.business} size={52}/>
            <div>
              <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:17,fontWeight:700,color:C.text}}>{job.title}</div>
              <div style={{color:C.sub,fontSize:13,marginTop:2}}>{job.business} · {job.location}</div>
            </div>
          </div>
          <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:24,fontWeight:700,color:C.orange}}>
            {fmt(job.salary)}<span style={{fontSize:14,color:C.sub}}>/mo</span>
          </div>
        </div>

        {/* Details */}
        <div className="card" style={{marginBottom:14}}>
          <div style={{fontSize:11,fontWeight:700,color:C.sub,letterSpacing:"0.08em",textTransform:"uppercase",marginBottom:12}}>About This Gig</div>
          <p style={{fontSize:13.5,color:C.sub,lineHeight:1.7,marginBottom:14}}>{job.desc}</p>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12,fontSize:13}}>
            {[["Type",job.type],["Hours",job.hours],["Payment",job.pay],["Location",job.remote?"Remote 🌐":job.location]].map(([k,v])=>(
              <div key={k}>
                <div style={{color:C.sub,fontSize:11,marginBottom:2}}>{k}</div>
                <div style={{color:C.text,fontWeight:600}}>{v}</div>
              </div>
            ))}
          </div>
          <div style={{marginTop:14,display:"flex",flexWrap:"wrap",gap:6}}>
            {job.skills.map(s=>(
              <span key={s} className="badge" style={{background:"rgba(45,107,228,.15)",color:C.blueL}}>{s}</span>
            ))}
          </div>
        </div>

        <div style={{background:"rgba(240,165,0,0.08)",border:`1px solid rgba(240,165,0,0.2)`,
          borderRadius:10,padding:"10px 14px",marginBottom:14,fontSize:12.5,color:C.gold}}>
          ⚡ 5% platform fee applies on salary payments
        </div>

        {applied?(
          <div style={{background:"rgba(0,200,120,.1)",border:`1px solid ${C.green}`,
            borderRadius:12,padding:"14px",textAlign:"center",fontWeight:700,color:C.green}}>
            ✓ Application Submitted!
          </div>
        ):(
          <>
            <div style={{fontSize:11,fontWeight:700,color:C.sub,letterSpacing:"0.08em",
              textTransform:"uppercase",marginBottom:8}}>Cover Note (optional)</div>
            <textarea className="inp" placeholder="Why are you a great fit?" rows={3}
              value={cover} onChange={e=>setCover(e.target.value)}
              style={{marginBottom:14,resize:"none"}}/>
            <button className="btn-primary" onClick={()=>{setApplied(true);onApply(job);}}>
              Apply Now →
            </button>
          </>
        )}
      </div>
    </div>
  );
}

// GIGBOT
function GigBotScreen(){
  const [msgs,setMsgs]=useState([
    {role:"bot",text:"Hey! 👋 I'm GigBot. Tell me what kind of work you're looking for — like 'social media', 'data entry', or 'sales' — and I'll find matching gigs instantly!"}
  ]);
  const [input,setInput]=useState("");
  const [recs,setRecs]=useState([]);
  const [selJob,setSelJob]=useState(null);
  const bottomRef=useRef(null);

  const QUICK=[["🎨","Design"],["📊","Data"],["📞","Sales"],["📱","Social"],["✍️","Writing"],["🤝","Support"]];

  const match=(q)=>{
    const kw=q.toLowerCase();
    const scored=SEED_JOBS.map(j=>{
      const hay=(j.title+" "+j.desc+" "+j.skills.join(" ")).toLowerCase();
      let s=0;
      kw.split(" ").forEach(w=>{if(w.length>2&&hay.includes(w))s+=2;});
      if(j.urgent)s+=1;
      return{s,j};
    }).filter(x=>x.s>0).sort((a,b)=>b.s-a.s).slice(0,3).map(x=>x.j);

    if(scored.length>0){
      const names=scored.map(j=>j.title+" at "+j.business).join(", ");
      return{text:`Great! Here are the best matches for "${q}": ${names}. Tap a card below to apply! 👇`,jobs:scored};
    }
    return{text:`No exact gigs for "${q}" right now, but check back soon! New gigs are posted daily. Try browsing All Gigs.`,jobs:[]};
  };

  const send=(text)=>{
    if(!text.trim())return;
    const newMsgs=[...msgs,{role:"user",text}];
    const {text:reply,jobs}=match(text);
    setMsgs([...newMsgs,{role:"bot",text:reply}]);
    setRecs(jobs);
    setInput("");
    setTimeout(()=>bottomRef.current?.scrollIntoView({behavior:"smooth"}),100);
  };

  if(selJob)return <JobDetail job={selJob} onBack={()=>setSelJob(null)} onApply={()=>{}}/>;

  return(
    <div style={{flex:1,display:"flex",flexDirection:"column",overflow:"hidden"}}>
      <TopBar title="GigBot" right={<span style={{background:"rgba(0,200,120,.15)",color:C.green,fontSize:11,fontWeight:700,padding:"4px 10px",borderRadius:20}}>● LIVE</span>}/>

      {/* Bot header */}
      <div style={{padding:"12px 20px",background:C.card2,borderBottom:`1px solid ${C.border}`,flexShrink:0}}>
        <div style={{display:"flex",alignItems:"center",gap:10}}>
          <div style={{width:38,height:38,borderRadius:"50%",
            background:"linear-gradient(135deg,#5B7FE8,#E8700A)",
            display:"flex",alignItems:"center",justifyContent:"center",fontSize:18}}>🤖</div>
          <div>
            <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:14,fontWeight:700,color:C.text}}>GigBot</div>
            <div style={{fontSize:11,color:C.sub}}>Matches you to live jobs · No AI fees · Instant</div>
          </div>
        </div>
      </div>

      {/* Quick chips */}
      <div style={{padding:"10px 16px",display:"flex",gap:8,overflowX:"auto",scrollbarWidth:"none",flexShrink:0,borderBottom:`1px solid ${C.border}`}}>
        {QUICK.map(([icon,label])=>(
          <button key={label} className="chip" onClick={()=>send(label)} style={{fontSize:12}}>
            {icon} {label}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div style={{flex:1,overflowY:"auto",padding:"16px 16px 8px"}}>
        {msgs.map((m,i)=>(
          <div key={i} style={{display:"flex",gap:8,marginBottom:12,
            justifyContent:m.role==="user"?"flex-end":"flex-start",alignItems:"flex-end"}}>
            {m.role==="bot"&&(
              <div style={{width:26,height:26,borderRadius:"50%",
                background:"linear-gradient(135deg,#5B7FE8,#E8700A)",
                display:"flex",alignItems:"center",justifyContent:"center",fontSize:13,flexShrink:0}}>🤖</div>
            )}
            <div className={m.role==="bot"?"bubble-bot":"bubble-user"}>{m.text}</div>
          </div>
        ))}
        {recs.length>0&&(
          <div style={{background:"rgba(91,127,232,0.08)",border:`1px solid rgba(91,127,232,0.2)`,
            borderRadius:14,padding:"12px",marginBottom:12}}>
            <div style={{fontSize:11,fontWeight:700,color:"#5B9AFF",letterSpacing:"0.07em",textTransform:"uppercase",marginBottom:10}}>
              🤖 Matched Gigs
            </div>
            {recs.map(j=>(
              <div key={j.id} style={{background:C.card,border:`1px solid ${C.border}`,
                borderRadius:12,padding:"10px 12px",marginBottom:8,
                display:"flex",alignItems:"center",gap:10,cursor:"pointer"}}
                onClick={()=>setSelJob(j)}>
                <BizAvatar name={j.business} size={34}/>
                <div style={{flex:1,minWidth:0}}>
                  <div style={{fontWeight:700,fontSize:13,color:C.text,whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{j.title}</div>
                  <div style={{color:C.sub,fontSize:11.5}}>{j.business} · {fmt(j.salary)}/mo</div>
                </div>
                <div style={{color:C.orange,fontSize:13}}>›</div>
              </div>
            ))}
          </div>
        )}
        <div ref={bottomRef}/>
      </div>

      {/* Input */}
      <div style={{padding:"10px 16px 16px",borderTop:`1px solid ${C.border}`,flexShrink:0,
        display:"flex",gap:10,alignItems:"center"}}>
        <input className="inp" style={{flex:1}} placeholder="Type a skill, e.g. sales, design…"
          value={input} onChange={e=>setInput(e.target.value)}
          onKeyDown={e=>e.key==="Enter"&&send(input)}/>
        <button onClick={()=>send(input)} style={{
          width:42,height:42,borderRadius:12,background:C.orange,
          color:"#fff",fontSize:18,display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0}}>
          →
        </button>
      </div>
    </div>
  );
}

// APPLIED
function AppliedScreen({applications}){
  const STATUS={pending:["#6B89A8","⏳ Pending"],hired:[C.green,"✅ Hired"],rejected:[C.red,"✗ Passed"]};
  return(
    <div style={{flex:1,display:"flex",flexDirection:"column",overflow:"hidden"}}>
      <TopBar title="My Applications"/>
      <div className="screen" style={{padding:"20px 20px"}}>
        <div style={{fontSize:12,color:C.sub,marginBottom:16}}>{applications.length} applications</div>
        {applications.length===0?(
          <div style={{textAlign:"center",padding:"48px 20px"}}>
            <div style={{fontSize:40,marginBottom:12}}>📋</div>
            <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:16,color:C.text}}>No applications yet</div>
            <div style={{color:C.sub,fontSize:13,marginTop:4}}>Find gigs and start applying!</div>
          </div>
        ):applications.map((a,i)=>{
          const [sc,sl]=STATUS[a.status]||STATUS.pending;
          return(
            <div key={i} className="card" style={{marginBottom:12}}>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:6}}>
                <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:14,fontWeight:700,color:C.text,flex:1,marginRight:8}}>{a.job.title}</div>
                <span className="badge" style={{background:`${sc}20`,color:sc,whiteSpace:"nowrap"}}>{sl}</span>
              </div>
              <div style={{color:C.sub,fontSize:12.5}}>{a.job.business} · {fmt(a.job.salary)}/mo</div>
              <div style={{color:C.sub,fontSize:12,marginTop:4}}>{a.job.type} · Applied just now</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// PROFILE
function ProfileScreen({user,onLogout}){
  const [interests,setInterests]=useState("Marketing, Social Media");
  const [payType,setPayType]=useState("wallet");
  return(
    <div style={{flex:1,display:"flex",flexDirection:"column",overflow:"hidden"}}>
      <TopBar title="My Profile"/>
      <div className="screen" style={{padding:"20px 20px"}}>
        {/* Avatar card */}
        <div className="card" style={{marginBottom:16,display:"flex",alignItems:"center",gap:14}}>
          <Avatar name={user.name} size={56} fontSize={18}/>
          <div>
            <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:17,fontWeight:700,color:C.text}}>{user.name}</div>
            <div style={{color:C.sub,fontSize:12.5,marginTop:2}}>IBA Karachi</div>
            <div style={{marginTop:6,display:"flex",gap:6}}>
              <span className="badge" style={{background:"rgba(0,200,120,.15)",color:C.green}}>✓ Verified</span>
              <span className="badge" style={{background:C.muted,color:C.sub}}>Free</span>
            </div>
          </div>
        </div>

        {/* Interests */}
        <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:15,fontWeight:700,color:C.text,marginBottom:10}}>Interests & Skills</div>
        <input className="inp" value={interests} onChange={e=>setInterests(e.target.value)}
          placeholder="Marketing, Design, Data Entry…" style={{marginBottom:16}}/>

        {/* Payment */}
        <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:15,fontWeight:700,color:C.text,marginBottom:10}}>💳 Payment Method</div>
        <div style={{display:"flex",gap:8,marginBottom:12}}>
          {["wallet","bank"].map(t=>(
            <button key={t} onClick={()=>setPayType(t)} style={{
              flex:1,padding:"10px",borderRadius:12,
              background:payType===t?C.orange:"transparent",
              color:payType===t?"#fff":C.sub,
              border:`1.5px solid ${payType===t?C.orange:C.border}`,
              fontSize:13,fontWeight:700,transition:"all .2s"}}>
              {t==="wallet"?"📱 Wallet":"🏦 Bank"}
            </button>
          ))}
        </div>
        {payType==="wallet"?(
          <div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:16}}>
            <select className="inp" style={{appearance:"none"}}>
              <option>EasyPaisa 🟢</option>
              <option>JazzCash 🔴</option>
            </select>
            <input className="inp" placeholder="03XX-XXXXXXX"/>
          </div>
        ):(
          <div style={{display:"flex",flexDirection:"column",gap:10,marginBottom:16}}>
            <select className="inp" style={{appearance:"none"}}>
              {["HBL","UBL","Meezan Bank","MCB","Bank Alfalah","Faysal Bank"].map(b=><option key={b}>{b}</option>)}
            </select>
            <input className="inp" placeholder="Account Title"/>
            <input className="inp" placeholder="IBAN / Account Number"/>
          </div>
        )}
        <button className="btn-primary" style={{marginBottom:12}}>Save Profile →</button>

        {/* Premium */}
        <div style={{background:"linear-gradient(135deg,rgba(240,165,0,0.1),rgba(91,127,232,0.1))",
          border:`1px solid rgba(240,165,0,0.3)`,borderRadius:16,padding:"16px",marginBottom:16}}>
          <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:16,fontWeight:700,color:C.gold,marginBottom:6}}>
            ⭐ Student Premium
          </div>
          <div style={{fontSize:12.5,color:C.sub,lineHeight:1.6,marginBottom:12}}>
            ✦ AI-Generated CV · ✦ Training Programs · ✦ Priority Profile
          </div>
          <button className="btn-small" style={{background:C.gold}}>Upgrade — PKR 500/mo</button>
        </div>

        <button className="btn-secondary" onClick={onLogout}>Sign Out</button>
      </div>
    </div>
  );
}

// BUSINESS HOME
function BusinessHome({user,onNav}){
  return(
    <div className="screen" style={{padding:"20px 20px 0"}}>
      <div className="card fade-up" style={{marginBottom:16,
        background:"linear-gradient(135deg,#0D1E33,#0D2040)",position:"relative",overflow:"hidden"}}>
        <div style={{position:"absolute",top:-30,right:-30,width:120,height:120,
          background:"radial-gradient(rgba(45,107,228,0.3),transparent 70%)",borderRadius:"50%"}}/>
        <div style={{position:"relative",display:"flex",alignItems:"center",gap:12}}>
          <Avatar name={user.name} size={48} fontSize={16}/>
          <div>
            <div style={{fontSize:11,color:C.sub,letterSpacing:"0.08em",textTransform:"uppercase",marginBottom:2}}>Business Dashboard</div>
            <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:18,fontWeight:700,color:C.text}}>{user.name}</div>
            <span className="badge" style={{background:"rgba(45,107,228,.15)",color:C.blueL,marginTop:4,display:"inline-flex"}}>PRO</span>
          </div>
        </div>
      </div>

      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:10,marginBottom:16}}>
        {[["6","Posted",C.blueL],["3","Hired",C.green],["PRO","Plan",C.orange]].map(([v,l,c])=>(
          <div key={l} style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:14,padding:"14px 10px",textAlign:"center"}}>
            <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:18,fontWeight:700,color:c}}>{v}</div>
            <div style={{fontSize:10.5,color:C.sub,marginTop:3,textTransform:"uppercase",letterSpacing:"0.05em"}}>{l}</div>
          </div>
        ))}
      </div>

      <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:16,fontWeight:700,color:C.text,marginBottom:12}}>Active Gigs</div>
      {SEED_JOBS.slice(0,3).map(j=>(
        <div key={j.id} className="card2" style={{marginBottom:10,display:"flex",justifyContent:"space-between",alignItems:"center"}}>
          <div>
            <div style={{fontWeight:700,fontSize:13.5,color:C.text}}>{j.title}</div>
            <div style={{color:C.sub,fontSize:12,marginTop:2}}>{fmt(j.salary)}/mo · {j.type}</div>
          </div>
          <span className="badge" style={{background:"rgba(0,200,120,.15)",color:C.green}}>OPEN</span>
        </div>
      ))}
    </div>
  );
}

// BUSINESS POST
function BusinessPost(){
  const [form,setForm]=useState({title:"",salary:"",hours:"",desc:"",skills:"",urgent:false,remote:false,pay:"easypaisa"});
  const [done,setDone]=useState(false);
  if(done)return(
    <div style={{flex:1,display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",padding:32,textAlign:"center"}}>
      <div style={{fontSize:56,marginBottom:16}}>🚀</div>
      <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:22,fontWeight:700,color:C.text,marginBottom:8}}>Gig Posted!</div>
      <div style={{color:C.sub,fontSize:14,marginBottom:24}}>Students can now see and apply to your gig.</div>
      <button className="btn-primary" onClick={()=>setDone(false)}>Post Another Gig</button>
    </div>
  );
  return(
    <div style={{flex:1,display:"flex",flexDirection:"column",overflow:"hidden"}}>
      <TopBar title="Post a Gig"/>
      <div className="screen" style={{padding:"20px 20px"}}>
        <div style={{display:"flex",flexDirection:"column",gap:12}}>
          <input className="inp" placeholder="Job Title *" value={form.title} onChange={e=>setForm({...form,title:e.target.value})}/>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10}}>
            <input className="inp" placeholder="Salary (PKR) *" type="number" value={form.salary} onChange={e=>setForm({...form,salary:e.target.value})}/>
            <input className="inp" placeholder="Hours/day" value={form.hours} onChange={e=>setForm({...form,hours:e.target.value})}/>
          </div>
          <textarea className="inp" rows={3} placeholder="Description *" value={form.desc} onChange={e=>setForm({...form,desc:e.target.value})} style={{resize:"none"}}/>
          <input className="inp" placeholder="Skills (comma separated)" value={form.skills} onChange={e=>setForm({...form,skills:e.target.value})}/>
          <select className="inp" value={form.pay} onChange={e=>setForm({...form,pay:e.target.value})} style={{appearance:"none"}}>
            <option value="easypaisa">EasyPaisa 🟢</option>
            <option value="jazzcash">JazzCash 🔴</option>
            <option value="bank">Bank Transfer 🏦</option>
          </select>
          <div style={{display:"flex",gap:16}}>
            {[["urgent","⚡ Mark Urgent"],["remote","🌐 Remote OK"]].map(([k,l])=>(
              <button key={k} onClick={()=>setForm({...form,[k]:!form[k]})} style={{
                flex:1,padding:"10px",borderRadius:12,cursor:"pointer",
                background:form[k]?"rgba(232,112,10,.15)":"transparent",
                border:`1.5px solid ${form[k]?C.orange:C.border}`,
                color:form[k]?C.orange:C.sub,fontSize:13,fontWeight:600}}>
                {l}
              </button>
            ))}
          </div>
          <button className="btn-primary" onClick={()=>{if(form.title&&form.salary)setDone(true);}}>Post This Gig →</button>
        </div>
      </div>
    </div>
  );
}

// BUSINESS APPLICANTS
function BusinessApplicants(){
  const [statuses,setStatuses]=useState({});
  const apps=SEED_JOBS.slice(0,4).map((j,i)=>({
    name:["Sara Ahmed","Hassan Raza","Aimen Siddiqui","Zara Khan"][i],
    uni:["IBA Karachi","FAST NUCES","NED University","SZABIST"][i],
    job:j,rating:4,
  }));
  return(
    <div style={{flex:1,display:"flex",flexDirection:"column",overflow:"hidden"}}>
      <TopBar title="Applicants"/>
      <div className="screen" style={{padding:"20px 20px"}}>
        <div style={{fontSize:12,color:C.sub,marginBottom:16}}>{apps.length} applicants</div>
        {apps.map((a,i)=>{
          const st=statuses[i];
          return(
            <div key={i} className="card" style={{marginBottom:12}}>
              <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:10}}>
                <Avatar name={a.name} size={42} fontSize={14}/>
                <div style={{flex:1}}>
                  <div style={{fontWeight:700,fontSize:14,color:C.text}}>{a.name}</div>
                  <div style={{color:C.sub,fontSize:12,marginTop:1}}>{a.uni}</div>
                  <div style={{color:C.gold,fontSize:12,marginTop:1}}>{"★".repeat(a.rating)}{"☆".repeat(5-a.rating)}</div>
                </div>
                {st&&<span className="badge" style={{background:st==="hired"?"rgba(0,200,120,.15)":"rgba(232,64,64,.15)",color:st==="hired"?C.green:C.red}}>{st==="hired"?"✅ Hired":"✗ Passed"}</span>}
              </div>
              <div style={{color:C.sub,fontSize:12.5,marginBottom:10}}>Applied for: <strong style={{color:C.text}}>{a.job.title}</strong></div>
              {!st&&(
                <div style={{display:"flex",gap:8}}>
                  <button onClick={()=>setStatuses({...statuses,[i]:"hired"})} style={{
                    flex:1,padding:"9px",borderRadius:10,background:"rgba(0,200,120,.12)",
                    border:`1px solid ${C.green}`,color:C.green,fontSize:13,fontWeight:700,cursor:"pointer"}}>
                    ✓ Hire
                  </button>
                  <button onClick={()=>setStatuses({...statuses,[i]:"rejected"})} style={{
                    flex:1,padding:"9px",borderRadius:10,background:"rgba(232,64,64,.1)",
                    border:`1px solid ${C.red}`,color:C.red,fontSize:13,fontWeight:700,cursor:"pointer"}}>
                    ✗ Pass
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// BUSINESS PROFILE
function BusinessProfile({user,onLogout}){
  return(
    <div style={{flex:1,display:"flex",flexDirection:"column",overflow:"hidden"}}>
      <TopBar title="Business Profile"/>
      <div className="screen" style={{padding:"20px 20px"}}>
        <div className="card" style={{marginBottom:16,display:"flex",alignItems:"center",gap:14}}>
          <Avatar name={user.name} size={56} fontSize={18}/>
          <div>
            <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:17,fontWeight:700,color:C.text}}>{user.name}</div>
            <div style={{color:C.sub,fontSize:12.5,marginTop:2}}>Technology · Karachi</div>
            <div style={{marginTop:6}}>
              <span className="badge" style={{background:"rgba(45,107,228,.15)",color:C.blueL}}>PRO</span>
            </div>
          </div>
        </div>
        <textarea className="inp" rows={3} placeholder="Business description…" style={{marginBottom:12,resize:"none"}}/>
        <input className="inp" placeholder="Website" style={{marginBottom:16}}/>
        <button className="btn-primary" style={{marginBottom:12}}>Save Profile →</button>
        <div style={{background:"linear-gradient(135deg,rgba(232,112,10,0.08),rgba(91,127,232,0.08))",
          border:`1px solid rgba(232,112,10,0.25)`,borderRadius:16,padding:"16px",marginBottom:16}}>
          <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:15,fontWeight:700,color:C.orange,marginBottom:6}}>Business Pro</div>
          <div style={{color:C.sub,fontSize:12.5,lineHeight:1.6,marginBottom:12}}>Unlimited gigs · Priority listing · Advanced filters</div>
          <div style={{fontFamily:"'Clash Display',sans-serif",fontSize:20,fontWeight:700,color:C.text,marginBottom:10}}>PKR 2,999<span style={{fontSize:13,color:C.sub}}>/mo</span></div>
          <div style={{display:"flex",gap:8}}>
            <button className="btn-small">EasyPaisa</button>
            <button className="btn-small" style={{background:C.muted,color:C.text}}>JazzCash</button>
          </div>
        </div>
        <button className="btn-secondary" onClick={onLogout}>Sign Out</button>
      </div>
    </div>
  );
}

// ─── ROOT APP ─────────────────────────────────────────────────────────────────
export default function App(){
  const [phase,setPhase]=useState("splash"); // splash > onboard > landing > auth > skill > main
  const [role,setRole]=useState(null);
  const [user,setUser]=useState(null);
  const [sTab,setSTab]=useState("home");
  const [bTab,setBTab]=useState("home");
  const [selJob,setSelJob]=useState(null);
  const [applications,setApplications]=useState([]);

  const handleLogin=(u)=>{
    setUser(u);
    if(u.role==="student") setPhase("skill");
    else setPhase("main");
  };

  const handleSkillDone=(skills)=>{
    setUser(u=>({...u,skills}));
    setPhase("main");
  };

  const handleApply=(job)=>{
    setApplications(a=>[...a,{job,status:"pending"}]);
    setSelJob(null);
    setSTab("applied");
  };

  return(
    <>
      <style>{css}</style>
      <div className="app">
        {phase==="splash"&&<SplashScreen onDone={()=>setPhase("onboard")}/>}
        {phase==="onboard"&&<OnboardingScreen onDone={()=>setPhase("landing")}/>}
        {phase==="landing"&&<LandingScreen onRole={r=>{setRole(r);setPhase("auth");}}/>}
        {phase==="auth"&&<AuthScreen role={role} onLogin={handleLogin} onBack={()=>setPhase("landing")}/>}
        {phase==="skill"&&<SkillOnboarding onDone={handleSkillDone}/>}

        {phase==="main"&&user?.role==="student"&&(
          <>
            {selJob?(
              <JobDetail job={selJob} onBack={()=>setSelJob(null)} onApply={handleApply}/>
            ):(
              <>
                {sTab==="home"&&<div className="screen"><StudentHome user={user} onNav={setSTab}/></div>}
                {sTab==="gigbot"&&<GigBotScreen/>}
                {sTab==="gigs"&&<GigsScreen onView={j=>{setSelJob(j);}}/>}
                {sTab==="applied"&&<AppliedScreen applications={applications}/>}
                {sTab==="profile"&&<ProfileScreen user={user} onLogout={()=>{setUser(null);setPhase("landing");}}/>}
              </>
            )}
            {!selJob&&<BottomNav tabs={S_TABS} active={sTab} onTab={setSTab}/>}
          </>
        )}

        {phase==="main"&&user?.role==="business"&&(
          <>
            {bTab==="home"&&<div className="screen"><BusinessHome user={user} onNav={setBTab}/></div>}
            {bTab==="post"&&<BusinessPost/>}
            {bTab==="applicants"&&<BusinessApplicants/>}
            {bTab==="profile"&&<BusinessProfile user={user} onLogout={()=>{setUser(null);setPhase("landing");}}/>}
            <BottomNav tabs={B_TABS} active={bTab} onTab={setBTab}/>
          </>
        )}
      </div>
    </>
  );
}
