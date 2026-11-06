// @spec docs/DESIGN_SYSTEM.md | docs/BACKLOG.md#sls-020 | docs/CONTROL.md#console-du-contrôle | docs/DESIGN_SYSTEM_APP.md
import React, {useEffect, useLayoutEffect, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {ArrowRight, FolderTree, Menu, X} from 'lucide-react';
import {api,sessionToken} from './api';
import {Confirm,ErrorMessage,Resource,useResource} from './ui';
import {Namespace,Namespaces,Service} from './management';
import {FunctionPage} from './function';
import './style.css';

const brand = <div className="brand"><img src="/favicon.svg" alt=""/><div>P2Enjoy<small>Serverless</small></div></div>;

function Login({error}) {
  return <main className="login-page"><div className="login-card">{brand}<div className="stack"><h1>Votre console serverless</h1><p className="muted">Administration des services et des fonctions.</p></div>
    <ErrorMessage error={error}/><a className="button primary" href="/auth/login">Se connecter avec le SSO<ArrowRight aria-hidden="true"/></a>
  </div></main>;
}

function App() {
  const session = useResource('/api/session');
  const [authError] = useState(() => {
    const value = new URLSearchParams(location.hash.slice(1)).get('auth-error') || document.body.dataset.authError;
    if (value) {history.replaceState(null,'',location.pathname); return new Error(value);}
    return null;
  });
  useEffect(() => {sessionToken(session.data?.csrf_token);}, [session.data]);
  if (session.loading) return <main className="login-page"><div className="login-card">{brand}<p role="status">Vérification de la session…</p></div></main>;
  if (session.error || !session.data?.authenticated) return <Login error={session.error || authError}/>;
  return <Shell user={session.data.user}/>;
}

function Shell({user}) {
  const [menu,setMenu] = useState(false);
  const menuButton = useRef(null), closeButton = useRef(null), sidebar = useRef(null);
  const menuWasOpen = useRef(false);
  useEffect(() => {
    const desktop = matchMedia('(min-width:1024px)');
    function changed() {if (desktop.matches) setMenu(false);}
    desktop.addEventListener('change',changed);
    return () => desktop.removeEventListener('change',changed);
  }, []);
  useLayoutEffect(() => {
    if (menu) {closeButton.current?.focus(); document.body.classList.add('dialog-open');}
    else {
      document.body.classList.remove('dialog-open');
      if (menuWasOpen.current) {
        const target = matchMedia('(min-width:1024px)').matches ? sidebar.current?.querySelector('nav a') : menuButton.current;
        target?.focus();
      }
    }
    menuWasOpen.current = menu;
    return () => document.body.classList.remove('dialog-open');
  }, [menu]);
  function closeMenu() {setMenu(false);}
  const parts = location.pathname.split('/').filter(Boolean);
  let view = <Namespaces/>;
  if (parts[0] === 'console' && parts[1] === 'namespaces' && parts[2]) view = <Namespace id={parts[2]}/>;
  else if (parts[0] === 'console' && parts[1] === 'services' && parts[2]) view = <Service id={parts[2]} tab={parts[3] || 'functions'}/>;
  else if (parts[0] === 'console' && parts[1] === 'functions' && parts[2]) view = <FunctionPage id={parts[2]}/>;
  else if (parts.length) view = <><h1>Page introuvable</h1><a href="/">Revenir aux namespaces</a></>;
  return <><a className="skip-link" href="#main">Aller au contenu</a>
    {menu && <div className="nav-veil" onClick={closeMenu} aria-hidden="true"/>}
    <aside ref={sidebar} className={`sidebar ${menu ? 'visible' : ''}`} aria-label="Navigation principale" onKeyDown={event => {
      if (!menu) return;
      if (event.key === 'Escape') {event.preventDefault(); closeMenu();}
      if (event.key === 'Tab') {
        const nodes = [...sidebar.current.querySelectorAll('a,button,input')].filter(node => !node.disabled && node.getClientRects().length);
        if (event.shiftKey && document.activeElement === nodes[0]) {event.preventDefault(); nodes.at(-1).focus();}
        else if (!event.shiftKey && document.activeElement === nodes.at(-1)) {event.preventDefault(); nodes[0].focus();}
      }
    }}>
      <div className="stack">{brand}<button className="close-nav" ref={closeButton} onClick={closeMenu}><X aria-hidden="true"/>Fermer le menu</button></div>
      <nav><a href="/" aria-current="page"><FolderTree aria-hidden="true"/>Namespaces</a></nav>
      <footer><div><small>Compte connecté</small><p>{user.name}</p></div>
        <Confirm label="Se déconnecter" message={`Fermer la session de « ${user.name} » ?`} action={async () => {await api('/auth/logout',{method:'POST'}); sessionToken(''); location.assign('/');}}/>
      </footer>
    </aside>
    <div className="shell" inert={menu ? true : undefined}><header className="topbar"><div className="actions"><button ref={menuButton} className="mobile-menu" onClick={() => setMenu(true)} aria-expanded={menu}><Menu aria-hidden="true"/>Menu</button><span>Console d’administration</span></div></header>
      <main id="main" tabIndex={-1}>{view}</main>
    </div>
  </>;
}

createRoot(document.getElementById('root')).render(<App/>);
