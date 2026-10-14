'use strict';
const $=id=>document.getElementById(id), NS='http://www.w3.org/2000/svg';
const mix=(a,b,t)=>a+(b-a)*t, clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const ratios=[.5,.56,.65,.75,.85,.90,.95,1];
const slopes=[-570/1016,-.5,-.60,-.8,-.83,-.56,-.35,-.35];
const scales=[.46,.53,.59,.59,.59,.59,.59,.59];
const xs=[120,100,100,110,110,110,110,110];
let frames,active=false,p=0,dwell=0,inside=false,hover=false,px=508,py=285,originX=508,originY=285,angle=-.511,targetAngle=-.511,offset=0,slope=slopes[0],intercept=570,last=0;
function artwork(name,x,y,w,h,outlined=false){
 const spec=typography[name],e=document.createElementNS(NS,'svg');
 // 'meet' keeps the original letter proportions; overflow visible prevents glyph edges from being cut.
 for(const[k,v]of Object.entries({x,y,width:w,height:h,viewBox:spec.viewBox.join(' '),preserveAspectRatio:'xMinYMin meet',overflow:'visible'}))e.setAttribute(k,v);
 // 'rotate' = ordinary horizontal lines turned 90° clockwise (not vertical writing).
 const holder=spec.rotate?document.createElementNS(NS,'g'):e;if(spec.rotate){holder.setAttribute('transform','rotate(90)');e.append(holder);}
 spec.lines.forEach((line,i)=>{const text=document.createElementNS(NS,'text');text.textContent=line;
 text.setAttribute('x',0);text.setAttribute('y',i*110);text.setAttribute('font-family',spec.family);text.setAttribute('font-size',100);text.setAttribute('font-weight',400);
 text.setAttribute('fill',outlined?'none':(name==='courage'||name==='suffix'?'black':'#ffffff'));
 if(outlined){text.setAttribute('stroke','#aaa');text.setAttribute('stroke-width',.65);text.setAttribute('vector-effect','non-scaling-stroke');}
 holder.append(text);});return e;
}
$('bravery').replaceChildren(artwork('courage',0,0,309,115));
const suffixArtwork=artwork('suffix',75,-74,234,74);suffixArtwork.setAttribute('id','suffix');$('bravery').append(suffixArtwork);
const words=[
 ['increases',465,139,234,66,0.08],
 ['worry',104,269,193,137,0.10],
 ['top',350,32,271,59,.24],
 ['lost',112,429,337,108,.37],
 ['hesitate',522,233,457,58,.38],
 ['failure',522,300,300,57,.51],
 ['vertical',370,228,87,195,.66],
 ['hmm',522,369,264,60,.68],
 ['ambiguous',522,442,464,57,.82],
 ['more',522,145,371,68,.97]
].map(([name,x,y,w,h,at])=>{let e=artwork(name,x,y,w,h,!['increases','more'].includes(name));$('words').append(e);return{name,e,at,w};});
const chunks={top:['어떡하지','어떡하지 음…'],hesitate:['할까말까','할까말까 확신이','할까말까 확신이 안서긴 해'],hmm:['흠…','흠… 아닌가?'],ambiguous:['애매하긴 해','애매하긴 해 잘','애매하긴 해 잘 모르겠네..']};
let leftCache=-1,rightCache=-1;
function number(group,n,x,y,invert,size=28){
 group.replaceChildren();const e=document.createElementNS(NS,'text');e.textContent=String(n);e.setAttribute('x',0);e.setAttribute('y',size*.6);e.setAttribute('fill','white');e.setAttribute('font-size',size);e.setAttribute('font-family','Neurimbo');e.setAttribute('text-anchor',invert?'end':'start');group.append(e);group.setAttribute('transform',`translate(${x} ${y})`);
}
function area(m,b){let points=[[0,0],[1016,0],[1016,570],[0,570]],out=[];for(let i=0;i<4;i++){let a=points[i],c=points[(i+1)%4],fa=a[1]-m*a[0]-b,fc=c[1]-m*c[0]-b;if(fa<=0)out.push(a);if((fa<=0)!==(fc<=0)){let t=fa/(fa-fc);out.push([mix(a[0],c[0],t),mix(a[1],c[1],t)]);}}let sum=0;for(let i=0;i<out.length;i++){let a=out[i],c=out[(i+1)%out.length];sum+=a[0]*c[1]-c[0]*a[1];}return {fraction:Math.abs(sum)/2/(1016*570),points:out};}
function boundary(m,r){let lo=-1200,hi=2000;for(let i=0;i<34;i++){let b=(lo+hi)/2;if(area(m,b).fraction<r)lo=b;else hi=b;}return(lo+hi)/2;}
function path(a,b,t){return a.map((c,i)=>c[0]+c.slice(1).map((v,k)=>mix(v,b[i][k+1],t).toFixed(3)).join(' ')).join(' ');}
function fadeAt(x,at,width=.045){return clamp((x-at)/width);}
function draw(dt){const stage=p*7,i=Math.min(6,Math.floor(stage)),t=stage-i;
 slope=mix(slopes[i],slopes[i+1],t);
 const movement=active?clamp((slope*px+intercept-py)/570*.30,-.15,.15):0;
 offset=mix(offset,movement,1-Math.exp(-dt*4));
 const r=clamp(mix(ratios[i],ratios[i+1],t)+offset*(1-p),.35,1);
 intercept=boundary(slope,r);
 const shape=area(slope,intercept).points;const d='M'+shape.map(a=>a.join(' ')).join('L')+'Z';
 $('background').setAttribute('d',d);$('blackPath').setAttribute('d',d);
 $('whitePath').setAttribute('d',`M0 0H1016V570H0Z ${d}`);$('whitePath').setAttribute('clip-rule','evenodd');
 const fi=Math.min(5,stage),a=Math.min(4,Math.floor(fi)),ft=fi-a;
 if(frames){$('saeng').setAttribute('d',path(frames[a][0],frames[a+1][0],ft));$('gak').setAttribute('d',path(frames[a][1],frames[a+1][1],ft));}
 $('thought').setAttribute('transform',`translate(${mix(xs[i],xs[i+1],t)} ${mix(96,100,clamp(stage))}) scale(${mix(scales[i],scales[i+1],t)*(1+(tb-1)*(1-p))})`);
 words.forEach(({e,name,at})=>{let opacity=name==='more'?fadeAt(p,.96,.03):fadeAt(p,at);if(name==='increases')opacity*=1-fadeAt(p,.97,.03);e.setAttribute('opacity',opacity);
 if(name==='increases'){e.setAttribute('x',mix(465,522,clamp(stage-1)));e.setAttribute('y',mix(139,154,clamp(stage-1)));}
 if(name==='hesitate') e.setAttribute('width',457);});
 // Reveal longer thoughts in whole word chunks, so no letter is ever cut in half.
 const reveals={top:fadeAt(p,.5,.08),hesitate:fadeAt(p,.65,.06),hmm:fadeAt(p,.82,.06),ambiguous:fadeAt(p,.97,.03)};
 words.forEach(({name,e})=>{if(!(name in chunks))return;const c=chunks[name],k=Math.min(c.length-1,Math.floor(reveals[name]*c.length));const tx=e.querySelector('text');if(tx.textContent!==c[k])tx.textContent=c[k];});
 const courageScales=[1,.84,.70,.62,.43,.27,.25,0];let cs=mix(courageScales[i],courageScales[i+1],t);
 const bx=mix([574,650,695,716,775,817,825,930][i],[574,650,695,716,775,817,825,930][i+1],t);
 const by=mix([354,378,399,410,430,450,467,560][i],[354,378,399,410,430,450,467,560][i+1],t);
 cs*=cb;$('bravery').setAttribute('transform',`translate(${bx} ${by}) scale(${cs})`);$('suffix').setAttribute('opacity',fadeAt(p,.08));
 const n=Math.round(r*100);if(n!==leftCache){number($('leftNumber'),n,79,50,false,mix(28,64,clamp((n-35)/65)));leftCache=n;}if(100-n!==rightCache){number($('rightNumber'),100-n,900,495,true);rightCache=100-n;}
 $('rightNumber').setAttribute('transform',`translate(${clamp(bx+309*cs+47,70,937)} ${clamp(by+115*cs+26,30,537)})`);
 // Place the compass halfway along the visible dividing line.
 const hits=[];for(const x of[0,1016]){const y=slope*x+intercept;if(y>=0&&y<=570)hits.push([x,y]);}for(const y of[0,570]){const x=(y-intercept)/slope;if(x>=0&&x<=1016)hits.push([x,y]);}
 let cx=508,cy=285;if(hits.length>=2){cx=(hits[0][0]+hits[1][0])/2;cy=(hits[0][1]+hits[1][1])/2;}
 angle+=Math.atan2(Math.sin(targetAngle-angle),Math.cos(targetAngle-angle))*(1-Math.exp(-dt*8));
 $('compass').setAttribute('transform',`translate(${cx} ${cy}) rotate(${angle*180/Math.PI})`);$('compass').setAttribute('opacity',1-fadeAt(p,.975,.025));
 hover=inside&&py<slope*px+intercept;
}
// tb/cb: slow hover growth of the 생각 / 용기 typography (up to +25%), easing back when the pointer leaves.
let tb=1,cb=1;
function tick(time){const dt=Math.min(.05,(time-last)/1000||0);last=time;
 tb=active&&hover?Math.min(1.12,tb+dt*.04):Math.max(1,tb-dt*.15);
 cb=active&&inside&&!hover?Math.min(1.25,cb+dt*.06):Math.max(1,cb-dt*.15);
 if(active&&hover&&p<1){dwell+=dt;p=clamp(p+dt/8);}else if(!hover){dwell=0;if(active&&inside)p=clamp(p-dt/12);}draw(dt);requestAnimationFrame(tick);}
function move(e){const r=$('art').getBoundingClientRect(),nx=(e.clientX-r.left)/r.width*1016,ny=(e.clientY-r.top)/r.height*570;const dx=nx-px,dy=ny-py;if(Math.hypot(dx,dy)>.5)targetAngle=Math.atan2(dy,dx);px=nx;py=ny;inside=true;const dot=$('cursorDot');dot.style.left=e.clientX+'px';dot.style.top=e.clientY+'px';dot.style.opacity=e.pointerType==='touch'?'0':'1';}
$('art').addEventListener('pointermove',move);$('art').addEventListener('pointerleave',()=>{inside=false;hover=false;dwell=0;$('cursorDot').style.opacity=0;});
function start(){active=true;originX=px;originY=py;inside=true;$('start').hidden=true;$('help').style.opacity=0;}
function reset(){active=false;p=0;tb=1;cb=1;dwell=0;offset=0;leftCache=rightCache=-1;$('start').hidden=false;$('help').style.opacity=1;}
$('start').addEventListener('pointerdown',e=>{move(e);start();});$('start').addEventListener('click',()=>{if(!active){px=200;py=150;start();}});$('reset').addEventListener('click',reset);
document.addEventListener('keydown',e=>{if(e.key.toLowerCase()==='r'||e.key==='Escape')reset();});
document.addEventListener('visibilitychange',()=>{inside=false;hover=false;dwell=0;$('cursorDot').style.opacity=0;});
fetch('assets/frames.json').then(r=>{if(!r.ok)throw Error('SVG load');return r.json();}).then(data=>{frames=data;draw(0);}).catch(()=>{$('help').textContent='글자 파일을 불러오지 못했어요. 새로고침해 주세요.';});
requestAnimationFrame(tick);
