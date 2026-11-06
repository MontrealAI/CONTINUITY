const vm=require('node:vm');const assert=require('node:assert/strict');const fs=require('node:fs');
const pages=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
function create(file,query='',hash=''){
 const winEvents={},docEvents={},prefEvents={};let loc=new URL('https://local.invalid/docs/research/'+file+query+hash);
 const elements=pages[file].elements.map(({tag,attrs})=>{
  const el={tag,attrs:{...attrs},dataset:{},listeners:{},disabled:'disabled'in attrs,hidden:'hidden'in attrs,value:attrs.value||'',defaultValue:attrs.value||'',textContent:'',min:attrs.min,max:attrs.max,step:attrs.step};
  for(const [k,v]of Object.entries(attrs))if(k.startsWith('data-'))el.dataset[k.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=v;
  el.getAttribute=k=>el.attrs[k]??null;el.setAttribute=(k,v)=>el.attrs[k]=String(v);
  el.addEventListener=(k,f)=>(el.listeners[k]??=[]).push(f);el.emit=(k,event={})=>(el.listeners[k]??[]).forEach(f=>f(event));
  el.classList={toggle:(name,on)=>{const c=new Set((el.attrs.class||'').split(' ').filter(Boolean));if(on)c.add(name);else c.delete(name);el.attrs.class=[...c].join(' ');}};
  Object.defineProperty(el,'src',{get:()=>el.attrs.src,set:x=>el.attrs.src=x});Object.defineProperty(el,'href',{get:()=>el.attrs.href,set:x=>el.attrs.href=x});return el;
 });
 const id=name=>elements.find(e=>e.attrs.id===name);const queryAll=sel=>{let m=sel.match(/^\[([^\]]+)\]$/);assert.ok(m,sel);return elements.filter(e=>m[1]in e.attrs);};
 const document={documentElement:elements.find(e=>e.tag==='html').attrs,getElementById:id,querySelectorAll:queryAll,visibilityState:'visible',addEventListener:(k,f)=>(docEvents[k]??=[]).push(f)};
 const window={location:loc,history:{replaceState:(_,__,url)=>{loc=new URL(url,loc);window.location=loc;}},addEventListener:(k,f)=>(winEvents[k]??=[]).push(f),matchMedia:()=>({addEventListener:(k,f)=>(prefEvents[k]??=[]).push(f)})};
 const emit=(table,event,data={})=>(table[event]??[]).forEach(f=>f(data));
 vm.runInNewContext(pages[file].script,{document,window,URLSearchParams,Intl},{filename:file,timeout:1000});
 return {elements,id,all:queryAll,window,document,win:(event,data)=>emit(winEvents,event,data),doc:(event,data)=>emit(docEvents,event,data),pref:matches=>emit(prefEvents,'change',{matches}),navigate:url=>{window.location=new URL(url,loc);}};
}
let combinations=0;
for(const [file,french] of [['continuity-omega.html',false],['continuity-omega-fr.html',true]]){
 let ctx=create(file,'','#pooling');const {id}=ctx;
 assert.equal(id('common-cost').disabled,false);assert.equal(id('capacity').disabled,false);for(const b of ctx.all('[data-cost]'))assert.equal(b.disabled,false);
 assert.equal(id('minimum').textContent,french?'3 acheteurs':'3 buyers');assert.equal(id('maximum').textContent,french?'2 acheteurs':'2 buyers');
 for(const button of ctx.all('[data-cost]')){
  button.emit('click');assert.equal(id('common-cost').value,button.dataset.cost);assert.equal(id('capacity').value,button.dataset.capacity);assert.equal(button.getAttribute('aria-pressed'),'true');
 }
 for(let cost=100;cost<=1800;cost+=50)for(let capacity=750;capacity<=4500;capacity+=250){
  id('common-cost').value=String(cost);id('capacity').value=String(capacity);id('common-cost').emit('input');
  assert.ok(id('minimum').textContent.startsWith(String(Math.ceil(cost/300))));assert.ok(id('maximum').textContent.startsWith(String(Math.floor(capacity/750))));
  assert.equal(id('pool-verdict').getAttribute('class').split(' ').includes('good'),Math.ceil(cost/300)<=Math.floor(capacity/750));
  for(const link of ctx.all('[data-language-switch]'))assert.equal(link.getAttribute('href'),link.dataset.languageSwitch+`?cost=${cost}&capacity=${capacity}#pooling`);
  assert.equal(ctx.window.location.search,`?cost=${cost}&capacity=${capacity}`);combinations++;
 }
 ctx.navigate('?cost=500&capacity=2000#reader');ctx.win('popstate');assert.equal(id('common-cost').value,'500');assert.equal(id('capacity').value,'2000');
 ctx.navigate('?cost=1500&capacity=3000#pooling');ctx.win('popstate');assert.equal(id('common-cost').value,'1500');assert.equal(id('capacity').value,'3000');
 ctx.navigate('#%zz');ctx.win('hashchange');for(const link of ctx.all('[data-language-switch]'))assert.ok(!link.getAttribute('href').includes('#'));
 for(const query of ['?cost=9999&capacity=1','?cost=500&cost=900&capacity=0999','?cost=550.0&capacity=nope','?cost=499&capacity=2001']){
  ctx=create(file,query,'#%zz');assert.equal(ctx.id('common-cost').value,'900');assert.equal(ctx.id('capacity').value,'2000');for(const l of ctx.all('[data-language-switch]'))assert.equal(l.getAttribute('href'),l.dataset.languageSwitch+'?cost=900&capacity=2000');
 }
 ctx=create(file,'?cost=100&capacity=4500&arbitrary=unsafe','#evidence');assert.equal(ctx.id('minimum').textContent,french?'1 acheteur':'1 buyer');assert.equal(ctx.id('maximum').textContent,french?'6 acheteurs':'6 buyers');assert.match(ctx.id('common-cost').getAttribute('aria-valuetext'),french?/unités monétaires hypothétiques/:/hypothetical monetary units/);for(const l of ctx.all('[data-language-switch]'))assert.ok(!l.getAttribute('href').includes('arbitrary'));
}
console.log('PASS EN/FR actual reader scripts: '+combinations+' valid slider combinations, presets, aria values, singular/plural, URL updates, language state, bounds/duplicate/step filtering, popstate and malformed fragments.');
for(const file of ['continuity-omega-media.html','continuity-omega-media-fr.html']){
 const ctx=create(file,'','#reveal');const buttons=ctx.all('[data-animation-control]');assert.equal(buttons.length,4);for(const b of buttons){assert.equal(b.hidden,false);assert.equal(b.getAttribute('aria-pressed'),'false');}
 for(const button of buttons){
  const image=ctx.id(button.dataset.animationControl);
  button.emit('click');assert.equal(image.src,button.dataset.gif);assert.equal(button.getAttribute('aria-pressed'),'true');assert.equal(button.textContent,button.dataset.stopLabel);
  button.emit('click');assert.equal(image.src,button.dataset.poster);assert.equal(button.getAttribute('aria-pressed'),'false');assert.equal(button.textContent,button.dataset.playLabel);
 }
 const stopCheck=()=>{for(const b of buttons){assert.equal(b.getAttribute('aria-pressed'),'false');assert.equal(ctx.id(b.dataset.animationControl).src,b.dataset.poster);}};
 buttons[0].emit('click');buttons[1].emit('click');assert.equal(buttons[0].getAttribute('aria-pressed'),'false');assert.equal(buttons[1].getAttribute('aria-pressed'),'true');
 ctx.pref(true);stopCheck();buttons[2].emit('click');ctx.win('pagehide');stopCheck();buttons[3].emit('click');ctx.document.visibilityState='hidden';ctx.doc('visibilitychange');stopCheck();
 for(const link of ctx.all('[data-language-switch]'))assert.equal(link.getAttribute('href'),link.dataset.languageSwitch+'#reveal');
 ctx.navigate('#unknown');ctx.win('hashchange');for(const link of ctx.all('[data-language-switch]'))assert.equal(link.getAttribute('href'),link.dataset.languageSwitch);
}
console.log('PASS EN/FR actual gallery scripts: localized Play/Stop and repeated clicks; single active animation; pagehide, visibility and reduced-motion stop; safe localized fragment links.');
for(const file of ['index.html','index-fr.html','help.html','help-fr.html']){
 const hash=file.startsWith('index')?'documentation':'accessibility';const ctx=create(file,'','#'+hash);for(const link of ctx.all('[data-language-switch]'))assert.equal(link.href,link.dataset.languageSwitch+'#'+hash);
 ctx.navigate('#%zz');ctx.win('hashchange');for(const link of ctx.all('[data-language-switch]'))assert.equal(link.href,link.dataset.languageSwitch);
}
console.log('PASS all four new library/help scripts: matching sections preserved in language links, malformed fragments rejected.');
for(const file of ['continuity-omega.html','continuity-omega-fr.html']){const el=pages[file].elements;assert.ok(el.filter(e=>e.tag==='input').every(e=>'disabled'in e.attrs));assert.ok(el.filter(e=>'data-cost'in e.attrs).every(e=>'disabled'in e.attrs));}
for(const file of ['continuity-omega-media.html','continuity-omega-media-fr.html'])assert.ok(pages[file].elements.filter(e=>'data-animation-control'in e.attrs).every(e=>'hidden'in e.attrs));
console.log('PASS static no-JavaScript disabled economics/hidden playback controls. No actual browser render or screen-reader audit was possible.');
