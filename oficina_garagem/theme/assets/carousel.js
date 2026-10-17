
(function(){
function init(){
const root=document.querySelector('.cd-source-hero-query');if(!root||root.dataset.carousel)return;
const track=root.querySelector('.wp-block-post-template');const slides=Array.from(track.children);if(slides.length<2)return;
root.dataset.carousel='true';root.setAttribute('role','region');root.setAttribute('aria-label','Matérias em destaque');
const controls=document.createElement('div');controls.className='cd-carousel-controls';
const dots=document.createElement('div');dots.className='cd-carousel-dots';
let current=0;
function go(n){current=(n+slides.length)%slides.length;track.scrollTo({left:slides[current].offsetLeft-track.offsetLeft,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});update();}
function update(){Array.from(dots.children).forEach((b,i)=>b.setAttribute('aria-current',String(i===current)));}
function button(label,text,fn){const b=document.createElement('button');b.type='button';b.setAttribute('aria-label',label);b.textContent=text;b.addEventListener('click',fn);return b;}
controls.append(button('Post anterior','‹',()=>go(current-1)),dots,button('Próximo post','›',()=>go(current+1)));
slides.forEach((s,i)=>{s.setAttribute('role','group');s.setAttribute('aria-label',(i+1)+' de '+slides.length);dots.append(button('Mostrar post '+(i+1),'',()=>go(i)));});
root.append(controls);update();
let autoplay;
function startAutoplay(){clearInterval(autoplay);if(!document.hidden)autoplay=setInterval(()=>go(current+1),5000);}
function stopAutoplay(){clearInterval(autoplay);}
root.addEventListener('mouseenter',stopAutoplay);
root.addEventListener('mouseleave',startAutoplay);
root.addEventListener('focusin',stopAutoplay);
root.addEventListener('focusout',e=>{if(!root.contains(e.relatedTarget))startAutoplay();});
root.addEventListener('pointerdown',stopAutoplay);
root.addEventListener('pointerup',()=>{if(!root.matches(':hover')&&!root.contains(document.activeElement))startAutoplay();});
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopAutoplay();else if(!root.matches(':hover')&&!root.contains(document.activeElement))startAutoplay();});
startAutoplay();

let timer;track.addEventListener('scroll',()=>{clearTimeout(timer);timer=setTimeout(()=>{current=slides.reduce((best,s,i)=>Math.abs(s.offsetLeft-track.offsetLeft-track.scrollLeft)<Math.abs(slides[best].offsetLeft-track.offsetLeft-track.scrollLeft)?i:best,0);update();},100);});
root.addEventListener('keydown',e=>{if(e.target.matches('input,textarea'))return;if(e.key==='ArrowRight'){e.preventDefault();go(current+1)}if(e.key==='ArrowLeft'){e.preventDefault();go(current-1)}});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
