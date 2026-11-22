// @spec docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#console-et-manuel | docs/DESIGN_SYSTEM.md | docs/DESIGN_SYSTEM_APP.md | docs/manual.md
import React, {useEffect,useRef,useState} from 'react';
import {api} from './api';
import {DialogForm, ErrorMessage, Facts, Field, Resource, Section, Success, useResource} from './ui';
import {retentionResponse,incompleteJournalResponse} from './execution-journal-contract';

export function LogRetention({serviceId,serviceName}) {
  const endpoint=`/api/services/${serviceId}/log-policy`;
  const response=useResource(endpoint);
  let resource=response;
  if(Object.hasOwn(response,'data'))try{retentionResponse(response.data,serviceId);}catch(error){resource={...response,data:undefined,error,loading:false};}
  const heading=useRef(null),opener=useRef(null),focusAfterClose=useRef(false);
  const [editing,setEditing]=useState(false),[notice,setNotice]=useState('');
  // @spec docs/BACKLOG.md#sls-124 | docs/DESIGN_SYSTEM_APP.md#journaux-recherchables--contrat-sls-072-avant-code
  useEffect(()=>{
    if(editing || !focusAfterClose.current)return;
    focusAfterClose.current=false;
    if(document.activeElement===document.body || document.activeElement===opener.current)heading.current?.focus();
  },[editing]);
  return <Section title="Conservation des journaux" headingRef={heading} action={<button ref={opener} disabled={!resource.data || resource.loading || Boolean(resource.error)} onClick={() => {focusAfterClose.current=false;setEditing(true);}}>Modifier la conservation</button>}>
    <Success>{notice}</Success>
    <Resource resource={resource}>{row => <>
      <Facts values={[
        ['Durée de conservation',`${row.retention_minutes} min`],
        ['Version de la politique',row.version],
        ['Périmètre','Messages des fonctions et événements publics de ce service'],
      ]}/>
      <p className="muted">De 1 à 10080 minutes, soit sept jours au maximum. Un contenu expiré ne réapparaît pas si vous augmentez cette durée. La chronologie des invocations possède sa propre conservation.</p>
      {editing && <RetentionEditor endpoint={endpoint} initial={row} serviceName={serviceName} focusTarget={heading} onClose={() => {focusAfterClose.current=true;setEditing(false);resource.reload();}}
        onSaved={changed => setNotice(changed ? 'Conservation des journaux enregistrée.' : 'Cette durée est déjà enregistrée.')}/>}
    </>}</Resource>
  </Section>;
}

function RetentionEditor({endpoint,initial,serviceName,onClose,onSaved,focusTarget}) {
  const [base,setBase]=useState(initial),[conflict,setConflict]=useState(false),[uncertain,setUncertain]=useState(false);
  const [reading,setReading]=useState(false),[readError,setReadError]=useState(null),[readNotice,setReadNotice]=useState('');
  async function reread() {
    if(reading)return;
    setReading(true);setReadError(null);
    try {
      const current=retentionResponse(await api(endpoint),initial.service_id);
      setBase(current);setConflict(false);setUncertain(false);
      setReadNotice(`Politique relue : ${current.retention_minutes} min, version ${current.version}. Votre saisie est conservée.`);
    } catch(error) {setReadError(error);}
    finally {setReading(false);}
  }
  return <DialogForm title="Conservation des journaux" initial={{retention_minutes:String(initial.retention_minutes)}} focusTarget={focusTarget}
    submitDisabled={reading || uncertain || conflict} confirmationLabel="Confirmer la diminution" confirmationTone="danger"
    confirmationWhen={value => Number(value.retention_minutes)<base.retention_minutes}
    confirmation={value => `Réduire la conservation des journaux de « ${serviceName} » de ${base.retention_minutes} à ${value.retention_minutes} min ? Le contenu au-delà de cette durée expirera et ne pourra pas être récupéré.`}
    onClose={onClose} onSubmit={async value => {
      const minutes=Number(value.retention_minutes);
      if(!Number.isInteger(minutes) || minutes<1 || minutes>10080)throw new Error('Saisissez une durée entière entre 1 et 10080 minutes.');
      if(uncertain || conflict)throw new Error('Relisez la politique avant un nouvel enregistrement.');
      try {
        const result=await api(endpoint,{method:'PUT',headers:{'If-Match':String(base.version)},body:{retention_minutes:minutes}});
        retentionResponse(result,initial.service_id);
        if(typeof result.changed!=='boolean' || result.retention_minutes!==minutes || result.version!==base.version+(result.changed?1:0))throw incompleteJournalResponse();
        onSaved(result.changed);
      } catch(error) {
        if(error.status===409)setConflict(true);
        else if(!error.fromControl || error.status>=500)setUncertain(true);
        throw error;
      }
    }}>
    {(value,setValue) => <>
      <Field label="Conservation (minutes)" help="De 1 à 10080 minutes. Une diminution peut effacer du contenu déjà collecté.">
        <input required type="number" min={1} max={10080} step={1} value={value.retention_minutes}
          onChange={event => setValue({...value,retention_minutes:event.target.value})}/>
      </Field>
      {(uncertain || conflict) && <p role="status">{uncertain ? 'La réponse de l’enregistrement manque. Son résultat est inconnu ; relisez la politique avant toute autre écriture.' : 'La politique a changé dans une autre session. Relisez-la avant de poursuivre.'}</p>}
      {(uncertain || conflict) && <button type="button" disabled={reading} onClick={reread}>{reading ? 'Relecture…' : 'Relire la politique'}</button>}
      <Success>{readNotice}</Success><ErrorMessage error={readError}/>
    </>}
  </DialogForm>;
}
