// @spec docs/BACKLOG.md#sls-122 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
// @verifies docs/BACKLOG.md#sls-122 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
// @spec docs/BACKLOG.md#sls-072 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
// @verifies docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
// Real SSH operators; every traced process remains owned until its joined exit.
import assert from 'node:assert/strict';
import {randomUUID} from 'node:crypto';
import {spawn,execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {createInterface} from 'node:readline';
import {performance} from 'node:perf_hooks';
import {setTimeout as pauseForProbe} from 'node:timers/promises';
import {until,diagnosis} from './execution-journal-harness.mjs';

const execute=promisify(execFile);
const connection=['-o','BatchMode=yes','-o','ConnectTimeout=10','-J','ubuntu@51.158.54.202','root@10.77.0.24'];
const directory='/srv/p2enjoy-serverless/e2e/';
const uuid=value=>assert.match(value,/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/);

export async function inspectJournal(campaign,mode='namespace') {
  assert(['baseline','namespace','cleanup'].includes(mode));
  const args=['python3','-B',directory+'execution-journal-inspect.py',mode];
  if(mode!=='baseline'){uuid(campaign.namespace.id);args.push(campaign.namespace.id);}
  const result=JSON.parse((await execute('ssh',[...connection,args.join(' ')],{timeout:30000,maxBuffer:16*1024**2})).stdout);
  if(mode==='cleanup')assert(result.physical_cleanup_confirmed);
  return result;
}

export class JournalSqlBarrier {
  constructor(campaign,image,count=1,barrier='read',{recovery='operator'}={}) {
    uuid(campaign.namespace.id);assert.match(image,/^sha256:[0-9a-f]{64}$/);
    assert([1,2].includes(count) && ['read','reader-start','read-result','read-decision','policy-commit','sqlite-reservation','fault','write'].includes(barrier));
    assert(['operator','independent_guard'].includes(recovery));this.recoveryMode=recovery;
    this.campaign=campaign;this.namespace=campaign.namespace.id;this.image=image;this.count=count;this.barrier=barrier;
    this.unit='serverless-restore-journal-sql-'+randomUUID().replaceAll('-','');
    this.events=[];this.closed=false;this.exit=null;this.nativeFailure=null;
  }

  async start() {
    assert(!this.process);this.startedMonotonic=performance.now();
    const command=['python3','-B',directory+'execution-journal-sql-operator.py','hold',this.namespace,this.image,String(this.count),this.unit,this.barrier].join(' ');
    this.process=spawn('ssh',[...connection,command],{stdio:['pipe','pipe','pipe']});
    // SSH/Python errors are not copied: they can contain a request's context.
    this.stderrBytes=0;this.process.stderr.on('data',chunk=>{this.stderrBytes+=chunk.length;});
    const lines=createInterface({input:this.process.stdout});
    lines.on('line',line=>{
      try {const value=JSON.parse(line);assert(value.unit===this.unit);this.events.push(value);}
      catch(error){this.nativeFailure=diagnosis(error);}
    });
    this.exited=new Promise(resolve=>{
      this.process.once('error',error=>{this.nativeFailure=diagnosis(error);});
      this.process.once('close',(code,signal)=>{lines.close();this.exit={code,signal};resolve(this.exit);});
    });
    this.campaign.nativeSqlBarriers??=[];this.campaign.nativeSqlBarriers.push(this);
    await this.event('armed');return this;
  }

  async event(name,seconds=45) {
    return until(async()=>{
      assert(!this.nativeFailure,'native_reader_message_invalid');
      const value=this.events.find(row=>row.event===name);if(value)return value;
      assert(!this.exit,'native_reader_exited_before_'+name);return null;
    },'native_reader_event_missing_'+name,seconds);
  }

  async held() {return this.event('held');}

  async action(mode,{timeout=70000}={}) {
    assert(['kill','suspend','recover','finish','evidence'].includes(mode));
    const command=['python3','-B',directory+'execution-journal-sql-operator.py',mode,this.namespace,this.unit].join(' ');
    const result=JSON.parse((await execute('ssh',[...connection,command],{timeout,maxBuffer:1024**2})).stdout);
    if(mode==='kill')this.helperLoss=result;return result;
  }

  async close({release=true,allowKilled=false,deadline}={}) {
    if(this.closed)return;
    if(release && this.process && !this.exit && !this.process.stdin.destroyed)this.process.stdin.end('release\n');
    let result;
    try {
      await until(async()=>this.exit,'native_reader_join_timeout',deadline?Math.min(65,Math.max(.001,(deadline-performance.now())/1000)):65);result=await this.exited;
      const armed=this.events.find(row=>row.event==='armed');
      const lost=this.helperLoss?.helper_joined_by_pidfd && this.helperLoss.signal===9 &&
        this.helperLoss.helper_pid===armed?.helper_pid && this.helperLoss.helper_birth===armed?.helper_birth;
      assert(result.code===0 || (allowKilled && lost && [137,255].includes(result.code)) || this.recoveryConfirmed,'native_reader_failed');
      const finishRemaining=deadline?Math.floor(deadline-performance.now()):70000;
      assert(finishRemaining>0,'native_recovery_observation_deadline');
      const receipt=await this.action('finish',{timeout:Math.min(70000,finishRemaining)});
      if(deadline)assert(performance.now()<=deadline,'native_recovery_observation_deadline');
      assert(receipt.completed && receipt.healthy && receipt.reference_unchanged && receipt.limits_nofile_restored);
      assert(Object.values(receipt.guard_states).every(row=>row.ActiveState==='inactive' && (!row.MainPID || row.MainPID==='0')));
      this.receipt=receipt;this.closed=true;
    } finally {
      this.campaign.observations.push({scenario:'native-reader',unit:this.unit,barrier:this.barrier,
        count:this.count,recovery_mode:this.recoveryMode,exit:this.exit,stderr_bytes:this.stderrBytes,events:this.events,helper_loss:this.helperLoss || null,receipt:this.receipt || null});
      await this.campaign.save();
    }
  }

  // @spec docs/BACKLOG.md#sls-122 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
  async observeRestoration(deadline,{requireSystemd=false}={}) {
    const armed=this.events.find(row=>row.event==='armed');assert(armed,'native_guard_identity_required');
    const observation={scenario:'native-restoration-observation',unit:this.unit,attempts:0,errors:[],errors_overflow:0,
      budget_from_launch_ms:125000,recovery_mode:this.recoveryMode};this.campaign.observations.push(observation);
    const receipt=await until(async()=>{
      observation.attempts++;
      const remaining=Math.floor(deadline-performance.now());assert(remaining>0,'native_recovery_observation_deadline');
      let value;
      try {value=await this.action('evidence',{timeout:Math.min(10000,remaining)});}
      catch(error){
        if(observation.errors.length<16)observation.errors.push(diagnosis(error));else observation.errors_overflow++;
        return null;
      }
      if(!value.completed){observation.last_incomplete_receipt=value;return null;}
      assert(performance.now()<=deadline,'native_recovery_observation_deadline');
      assert(value.unit===this.unit && value.pid===armed.process.pid && value.birth===armed.process.birth);
      assert(value.healthy && value.reference_unchanged && value.limits_nofile_restored);
      assert(value.threads.length && value.threads.every(row=>row.tracer_pid===0 && !['t','T'].includes(row.state)));
      if(requireSystemd) {
        assert(value.independent && value.helper_gone && value.restoration_origin==='systemd_guard');
        assert(value.restorer_systemd_unit===this.unit+'.service' && value.restorer_pid>1 && /^[0-9]+$/.test(value.restorer_birth));
      }
      return value;
    },'native_restoration_not_confirmed',Math.max(.001,(deadline-performance.now())/1000));
    this.campaign.observations.push({scenario:requireSystemd?'native-independent-guard-confirmed':'native-restoration-confirmed',
      unit:this.unit,receipt,elapsed_ms:performance.now()-this.startedMonotonic,qualified_groups:0});
    await this.campaign.save();return receipt;
  }

  // @spec docs/BACKLOG.md#sls-122 | docs/EXECUTION_LOGS.md#instrumentation-native-des-lectures
  async recover() {
    if(this.closed)return;
    assert(Number.isFinite(this.startedMonotonic),'native_owner_launch_time_required');
    const deadline=this.startedMonotonic+125000;
    const remaining=Math.floor(deadline-performance.now());assert(remaining>0,'native_recovery_observation_deadline');
    if(this.recoveryMode==='independent_guard')await this.observeRestoration(deadline,{requireSystemd:true});
    else {
      try {
        const receipt=await this.action('recover',{timeout:Math.min(70000,remaining)});
        assert(receipt.completed && receipt.healthy);
      } catch(error) {
        this.campaign.observations.push({scenario:'native-recovery-attempt-failed',unit:this.unit,...diagnosis(error)});
        await this.campaign.save();await this.observeRestoration(deadline);
      }
    }
    this.recoveryConfirmed=true;
    await this.close({release:false,allowKilled:true,deadline});
  }

}

export async function joinJournalSqlBarriers(campaign) {
  const errors=[];
  for(const owner of campaign.nativeSqlBarriers || []) {
    if(owner.closed)continue;
    try {await owner.recover();}catch(error){errors.push({unit:owner.unit,...diagnosis(error)});}
  }
  assert.equal(errors.length,0,'native_reader_cleanup_failed');
}

export class JournalControlCut {
  constructor(campaign,fn,image) {
    uuid(campaign.namespace.id);uuid(fn.id);assert.match(image,/^sha256:[0-9a-f]{64}$/);
    this.campaign=campaign;this.namespace=campaign.namespace.id;this.fn=fn.id;this.image=image;
    this.unit='serverless-restore-journal-cut-'+randomUUID().replaceAll('-','');
    this.events=[];this.closed=false;this.exit=null;
  }
  async start() {
    this.startedMonotonic=performance.now();this.deadline=this.startedMonotonic+235000;
    this.observation={scenario:'native-control-cut',unit:this.unit,stage:'intent',events:this.events,probes:[],qualified:false};
    this.campaign.observations.push(this.observation);await this.campaign.save();
    const command=['python3','-B',directory+'execution-journal-control-operator.py','arm',this.namespace,this.fn,this.image,this.unit].join(' ');
    this.process=spawn('ssh',[...connection,command],{stdio:['pipe','pipe','pipe']});
    this.stderrBytes=0;this.process.stderr.on('data',chunk=>{this.stderrBytes+=chunk.length;});
    const lines=createInterface({input:this.process.stdout});
    lines.on('line',line=>{try{const value=JSON.parse(line);assert.equal(value.unit,this.unit);this.events.push(value);}catch(error){this.failure=diagnosis(error);}});
    this.exited=new Promise(resolve=>{
      this.process.once('error',error=>{this.failure=diagnosis(error);});
      this.process.once('close',(code,signal)=>{lines.close();this.exit={code,signal};resolve(this.exit);});
    });
    this.campaign.nativeCuts??=[];this.campaign.nativeCuts.push(this);
    await this.event('armed');return this;
  }
  async event(name) {
    const deadline=Math.min(this.deadline,performance.now()+40000);
    try {
      while(performance.now()<deadline) {
        assert(!this.failure,'native_control_cut_message_invalid');
        const event=this.events.find(row=>row.event===name);
        if(event){this.observation.stage=name;return event;}
        assert(!this.exit,'native_control_cut_exited_before_'+name);await pauseForProbe(Math.min(100,deadline-performance.now()));
      }
      assert.fail('native_control_cut_event_missing_'+name);
    } catch(error) {this.observation.first_failure??=diagnosis(error);throw error;}
    finally {this.updateObservation();await this.campaign.save();}
  }
  updateObservation() {
    Object.assign(this.observation,{exit:this.exit,stderr_bytes:this.stderrBytes,helper_loss:this.helperLoss || null,
      message_failure:this.failure || null,elapsed_ms:performance.now()-this.startedMonotonic,closed:this.closed});
  }
  async action(mode,{deadline=this.deadline}={}) {
    assert(['evidence','finish','recover','kill-helper'].includes(mode));
    const command=['python3','-B',directory+'execution-journal-control-operator.py',mode,this.namespace,this.fn,this.unit].join(' ');
    const remaining=Math.floor(deadline-performance.now());assert(remaining>0,'native_cut_protocol_deadline');
    const timeout=Math.min(mode==='recover'?190000:10000,remaining),started=performance.now();
    const probe={mode,started_ms:started-this.startedMonotonic,timeout_ms:timeout};this.observation.probes.push(probe);
    try {
      const result=JSON.parse((await execute('ssh',[...connection,command],{timeout,maxBuffer:2*1024**2})).stdout);
      probe.event=result.event;probe.completed=result.completed ?? null;
      assert(performance.now()<=deadline,'native_cut_receipt_after_protocol_deadline');return result;
    } catch(error) {probe.failure=diagnosis(error);throw error;}
    finally {probe.finished_ms=performance.now()-this.startedMonotonic;}
  }
  async close({independent=false,recover=false}={}) {
    if(this.closed)return;
    // Cleanup has a separate bounded ownership recovery. It never substitutes
    // its receipt for a primary qualification that has already failed.
    const deadline=recover?performance.now()+235000:this.deadline;
    try {
      this.observation.stage=recover?'cleanup-recovery':'joining-primary';
      if(recover)this.observation.cleanup_receipt=await this.action('recover',{deadline});
      else if(independent)this.helperLoss=await this.action('kill-helper',{deadline});
      else if(!this.exit && !this.process.stdin.destroyed)this.process.stdin.end('restore\n');
      while(!this.exit) {
        const remaining=deadline-performance.now();assert(remaining>0,'native_control_cut_client_not_joined');
        await pauseForProbe(Math.min(100,remaining));
      }
      await this.exited;
      const armed=this.events.find(row=>row.event==='armed');
      const lost=this.helperLoss?.helper_joined_by_pidfd && this.helperLoss.signal===9 &&
        this.helperLoss.helper_pid===armed?.helper_pid && this.helperLoss.helper_birth===armed?.helper_birth;
      assert(this.exit.code===0 || (independent && lost && [137,255].includes(this.exit.code)) || recover,'native_control_cut_failed');
      let receipt;
      while(true) {
        receipt=await this.action('evidence',{deadline});
        if(receipt.event!=='pending')break;
        const remaining=deadline-performance.now();assert(remaining>0,'native_control_cut_restoration_missing');
        await pauseForProbe(Math.min(250,remaining));
      }
      assert(receipt.completed && receipt.healthy && receipt.reference_unchanged && receipt.stop_mutator_joined);
      assert.equal(receipt.container_id,armed?.container_id);assert.equal(receipt.image,this.image);
      if(independent)assert(receipt.independent && receipt.helper_gone);
      this.receipt=await this.action('finish',{deadline});
      assert(Object.values(this.receipt.guard_states).every(row=>row.ActiveState==='inactive' && (!row.MainPID || row.MainPID==='0')));
      assert(performance.now()<=deadline,'native_cut_finish_after_protocol_deadline');
      this.closed=true;
      if(recover)this.observation.cleanup_receipt=this.receipt;
      else {this.observation.primary_receipt=this.receipt;this.observation.qualified=!this.observation.first_failure;}
      return receipt;
    } catch(error) {
      if(recover)this.observation.cleanup_failure=diagnosis(error);
      else this.observation.first_failure??=diagnosis(error);
      throw error;
    } finally {this.updateObservation();await this.campaign.save();}
  }
}

export async function joinJournalCuts(campaign) {
  for(const cut of campaign.nativeCuts || [])if(!cut.closed)await cut.close({recover:true});
}
