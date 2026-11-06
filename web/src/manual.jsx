// @spec docs/BACKLOG.md#sls-062 | docs/CONSOLE_MANUAL.md | docs/manual.md | docs/DESIGN_SYSTEM_APP.md#manuel-dusage-sls-062
import React, {useEffect} from 'react';
import manual from 'virtual:usage-manual';

export function UsageManual() {
  useEffect(() => {
    function focusChapter() {
      const anchor = location.hash.slice(1);
      if (anchor === 'sommaire' || manual.chapters.some(chapter => chapter.id === anchor)) {
        const target = document.getElementById(anchor);
        target?.focus({preventScroll:true});target?.scrollIntoView();
      }
    }
    focusChapter();
    window.addEventListener('hashchange',focusChapter);
    return () => window.removeEventListener('hashchange',focusChapter);
  }, []);
  return <>
    <div className="page-title"><h1>{manual.title}</h1></div>
    <div className="manual-layout">
      <nav className="panel manual-toc" aria-labelledby="sommaire">
        <h2 id="sommaire" tabIndex={-1}>Sommaire</h2>
        <ol>{manual.chapters.map(chapter => <li key={chapter.id}><a href={'#'+chapter.id}>{chapter.label}</a></li>)}</ol>
      </nav>
      <div className="manual-reading">
        {/* This HTML is compiled only from the maintained manual with raw HTML disabled. */}
        <article className="panel manual-content" data-manual-sha256={manual.sha256} aria-label="Guide d’utilisation" dangerouslySetInnerHTML={{__html:manual.html}}/>
        <a className="button" href="#sommaire">Revenir au sommaire</a>
      </div>
    </div>
  </>;
}
