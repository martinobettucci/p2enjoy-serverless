# @spec docs/BACKLOG.md#sls-030 | docs/DEPLOYMENT.md#outil-et-manifeste
# Parse deployment data only. No provider plugin, script or module is executed.
import math
import os
from pathlib import Path
import re
import stat

import yaml


class ManifestError(ValueError):
    pass


class UniqueLoader(yaml.SafeLoader):
    def construct_mapping(self,node,deep=False):
        result={}
        for key_node,value_node in node.value:
            key=self.construct_object(key_node,deep=deep)
            if not isinstance(key,str):raise ManifestError('Les clés YAML doivent être des chaînes.')
            if key in result:raise ManifestError('Clé YAML dupliquée, ligne '+str(key_node.start_mark.line+1)+'.')
            result[key]=self.construct_object(value_node,deep=deep)
        return result


# YAML 1.2 boolean spelling: names such as ON stay environment variable names.
UniqueLoader.yaml_implicit_resolvers={key:[entry for entry in entries if entry[0] not in
    ('tag:yaml.org,2002:bool','tag:yaml.org,2002:timestamp')] for key,entries in yaml.SafeLoader.yaml_implicit_resolvers.items()}
UniqueLoader.add_implicit_resolver('tag:yaml.org,2002:bool',re.compile(r'^(?:true|True|TRUE|false|False|FALSE)$'),list('tTfF'))


def mapping(value,where):
    if value is None:return {}
    if not isinstance(value,dict):raise ManifestError(where+' doit être un mapping.')
    return value


def fields(value,allowed,where):
    unknown=set(value)-set(allowed)
    if unknown:raise ManifestError(where+' : champs non pris en charge : '+', '.join(sorted(unknown)))


def alias(value,names,default=None):
    present=[name for name in names if name in value]
    if len(present)>1:raise ManifestError('Alias simultanés : '+', '.join(present))
    return value[present[0]] if present else default


def variables(value,where,resolve):
    result={}
    for key,item in mapping(value,where).items():
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,127}',key):raise ManifestError(where+' : nom de variable invalide.')
        if item is not None and not isinstance(item,str):raise ManifestError(where+'.'+key+' exige une chaîne ou null.')
        if item is not None:
            references=re.findall(r'\$\{([^}]+)\}',item)
            if '${' in re.sub(r'\$\{env:[A-Za-z_][A-Za-z0-9_]*\}','',item):
                raise ManifestError(where+'.'+key+' : référence incomplète ou non prise en charge.')
            for reference in references:
                if not re.fullmatch(r'env:[A-Za-z_][A-Za-z0-9_]{0,127}',reference):
                    raise ManifestError(where+'.'+key+' : seule la référence env:NOM est acceptée.')
                name=reference[4:]
                if resolve:
                    if name not in os.environ:raise ManifestError('Variable requise absente : '+name)
                    item=item.replace('${'+reference+'}',os.environ[name])
            if '\x00' in item or len(item.encode())>16384:raise ManifestError(where+'.'+key+' : valeur hors limites.')
        result[key]=item
    if len(result)>128:raise ManifestError(where+' dépasse 128 clés.')
    return result


def merged(base,local):
    result={**base,**local}
    return {key:value for key,value in result.items() if value is not None}


def number(value,name,low,high,integer=False):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or (isinstance(value,float) and not math.isfinite(value)) or not low<=value<=high:
        raise ManifestError(name+' hors limites.')
    if integer and not isinstance(value,int):raise ManifestError(name+' doit être entier.')
    return value


def timeout(value):
    if isinstance(value,str) and re.fullmatch(r'(?:\d+(?:\.\d+)?|\.\d+)s',value):value=float(value[:-1])
    return number(value,'timeout',.1,86400)


def handler(value):
    if not isinstance(value,str) or len(value)>256 or not re.fullmatch(r'[A-Za-z0-9_./-]+\.[A-Za-z_$][A-Za-z0-9_$]*',value):
        raise ManifestError('Handler attendu : chemin/module.export.')
    module=value.rsplit('.',1)[0]
    if module.startswith('/') or any(part in ('','.','..') for part in module.split('/')):
        raise ManifestError('Le handler doit rester dans le projet.')
    return value


def storage(value):
    value=mapping(value,'storage');fields(value,('data','cache','concurrency'),'storage')
    result={'concurrency':value.get('concurrency','exclusive')}
    if result['concurrency'] not in ('exclusive','shared'):raise ManifestError('Concurrence de stockage invalide.')
    for kind in ('data','cache'):
        volume=mapping(value.get(kind),kind);fields(volume,('enabled','quota_mib'),kind)
        enabled=volume.get('enabled',False)
        if not isinstance(enabled,bool):raise ManifestError(kind+'.enabled doit être booléen.')
        if enabled and 'quota_mib' not in volume:raise ManifestError(kind+' activé exige un quota_mib explicite.')
        result[kind]={'enabled':enabled,'quota_mib':number(volume.get('quota_mib',64),kind+'.quota_mib',1,65536,True)}
    return result


def config(provider,function):
    result={'handler':handler(function.get('handler')),'runtime':'node24','cpu':.25,
            'idle_seconds':60,'concurrency':1,'queue_timeout_seconds':10}
    result['memory_mib']=number(alias(function,('memorySize','memoryLimit'),alias(provider,('memorySize','memoryLimit'),256)),'memory',128,8192,True)
    result['timeout_seconds']=timeout(function.get('timeout',provider.get('timeout',30)))
    result['min_instances']=number(function.get('minScale',provider.get('minScale',0)),'minScale',0,32,True)
    result['max_instances']=number(function.get('maxScale',provider.get('maxScale',1)),'maxScale',1,32,True)
    extension={**mapping(provider.get('p2enjoy'),'provider.p2enjoy'),**mapping(function.get('p2enjoy'),'function.p2enjoy')}
    fields(extension,('cpu','idle_seconds','concurrency','queue_timeout_seconds','storage'),'p2enjoy')
    for key,low,high,integer in [('cpu',.05,1,False),('idle_seconds',0,86400,False),('concurrency',1,32,True),('queue_timeout_seconds',0,300,False)]:
        result[key]=number(extension.get(key,result[key]),key,low,high,integer)
    result['storage']=storage(extension.get('storage'))
    if result['min_instances']>result['max_instances'] or result['concurrency']>result['max_instances']:
        raise ManifestError('Les minimum/concurrence ne peuvent dépasser maxScale.')
    if result['storage']['data']['enabled'] and result['storage']['concurrency']=='exclusive' and result['concurrency']!=1:
        raise ManifestError('Les données exclusives imposent une concurrence de 1.')
    return result


def cron(value):
    if not isinstance(value,str) or len(value.split())!=5:raise ManifestError('Cron attendu : cinq champs numériques.')
    for part,(low,high) in zip(value.split(),[(0,59),(0,23),(1,31),(1,12),(0,7)]):
        for item in part.split(','):
            match=re.fullmatch(r'(\*|\d+(?:-\d+)?)(?:/(\d+))?',item)
            if not match:raise ManifestError('Champ cron non pris en charge.')
            base,step=match.groups()
            if step is not None and not 1<=int(step)<=high-low+1:raise ManifestError('Pas cron hors limites.')
            if base!='*':
                values=[int(n) for n in base.split('-')]
                if not all(low<=n<=high for n in values) or values[0]>values[-1]:raise ManifestError('Plage cron invalide.')
    return ' '.join(value.split())


def events(value,name):
    if value is None:value=[]
    if not isinstance(value,list) or len(value)>16:raise ManifestError('events doit être une liste de 16 entrées au maximum.')
    result={'http':[],'schedules':[]}
    methods=['GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS']
    for item in value:
        if not isinstance(item,dict) or len(item)!=1:raise ManifestError('Chaque événement doit avoir un type unique.')
        if 'http' in item:
            http=mapping(item['http'],'http');fields(http,('path','method'),'http')
            path=http.get('path',name);method=http.get('method','any')
            if not isinstance(path,str) or len(path)>256 or not re.fullmatch(r'[A-Za-z0-9_/-]+',path) or path.startswith('/') or any(p in ('','.','..') for p in path.split('/')):
                raise ManifestError('Chemin HTTP relatif exact requis.')
            if not isinstance(method,str) or method.upper() not in [*methods,'ANY']:raise ManifestError('Méthode HTTP non prise en charge.')
            result['http'].append({'path':path,'methods':methods if method.upper()=='ANY' else [method.upper()],'implicit':False})
        elif 'schedule' in item:
            schedule=mapping(item['schedule'],'schedule');fields(schedule,('rate','enabled'),'schedule')
            enabled=schedule.get('enabled',True)
            if not isinstance(enabled,bool):raise ManifestError('schedule.enabled doit être booléen.')
            result['schedules'].append({'cron':cron(schedule.get('rate')),'enabled':enabled,'timezone':'UTC'})
        else:raise ManifestError('Type d’événement non pris en charge.')
    if not result['http']:result['http']=[{'path':name,'methods':methods,'implicit':True}]
    return result


def patterns(value):
    value=mapping(value,'package');fields(value,('patterns',),'package')
    result=value.get('patterns',[])
    if not isinstance(result,list) or len(result)>256:raise ManifestError('package.patterns doit contenir au plus 256 motifs.')
    for pattern in result:
        if not isinstance(pattern,str) or not pattern or len(pattern)>512:raise ManifestError('Motif de packaging invalide.')
        clean=pattern.removeprefix('!')
        if not clean or clean.startswith('/') or any(part in ('.','..','') for part in clean.split('/')) or any(c in clean for c in '{}()\\\n\r\x00'):
            raise ManifestError('Motif de packaging hors du sous-ensemble glob pris en charge.')
        if any('**' in part and part!='**' for part in clean.split('/')):raise ManifestError('** doit occuper un segment complet du motif.')
    return result


def load(path,runtime_override=None,accept_provider_differences=False,resolve_environment=False):
    path=Path(path)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):raise ManifestError('Le manifeste doit être un fichier ordinaire.')
        raw=stream.read(1024*1024+1)
    if len(raw)>1024*1024:raise ManifestError('Manifeste supérieur à 1 Mio.')
    text=raw.decode('utf-8')
    try:
        for token in yaml.scan(text):
            if isinstance(token,(yaml.tokens.AnchorToken,yaml.tokens.AliasToken)):raise ManifestError('Ancres et alias YAML non pris en charge.')
        data=yaml.load(text,Loader=UniqueLoader)
    except ManifestError:raise
    except (yaml.YAMLError,ValueError) as error:
        mark=getattr(error,'problem_mark',None)
        raise ManifestError('YAML invalide'+(' à la ligne '+str(mark.line+1) if mark else '')+'.') from None
    data=mapping(data,'manifeste');fields(data,('service','provider','functions','package','plugins','custom','frameworkVersion','configValidationMode','org','app'),'manifeste')
    service=data.get('service')
    if not isinstance(service,str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,62}',service):raise ManifestError('Nom de service invalide.')
    provider=mapping(data.get('provider'),'provider')
    fields(provider,('name','runtime','env','environment','secret','memorySize','memoryLimit','timeout','minScale','maxScale','p2enjoy','architecture','scwToken','scwProject','scwRegion','region','stage'),'provider')
    if provider.get('name') not in ('p2enjoy','aws','scaleway'):raise ManifestError('Provider non pris en charge.')
    if provider.get('architecture','x86_64') not in ('x86_64','x64'):raise ManifestError('Architecture cible requise : Linux x64.')
    warnings=[]
    for key in ('plugins','custom','frameworkVersion','configValidationMode','org','app'):
        if key in data:warnings.append(key+' : non exécuté par l’adaptateur.')
    for key in ('scwToken','scwProject','scwRegion','region','stage'):
        if key in provider:warnings.append('provider.'+key+' : non transmis au fournisseur.')
    environment=variables(alias(provider,('environment','env')),'provider.environment',resolve_environment)
    secrets=variables(provider.get('secret'),'provider.secret',resolve_environment)
    functions=mapping(data.get('functions'),'functions')
    if not functions or len(functions)>256:raise ManifestError('Une à 256 fonctions sont requises.')
    result=[];global_patterns=patterns(data.get('package'))
    for name,function in functions.items():
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,62}',name):raise ManifestError('Nom de fonction invalide.')
        function=mapping(function,'functions.'+name)
        fields(function,('handler','runtime','env','environment','secret','memorySize','memoryLimit','timeout','minScale','maxScale','p2enjoy','events','package','httpOption','privacy','custom_domains'),'functions.'+name)
        runtime=function.get('runtime',provider.get('runtime'))
        if runtime not in ('node24','nodejs24','nodejs24.x'):
            if runtime not in ('node20','nodejs20','nodejs20.x','node22','nodejs22','nodejs22.x') or runtime_override!='node24':
                raise ManifestError(name+' : Node 24 requis ; conversion Node 20/22 avec --runtime node24 explicite.')
            warnings.append(name+' : conversion explicite vers Node 24, validation réelle requise au déploiement.')
        for key in ('httpOption','privacy','custom_domains'):
            if key in function:
                if not accept_provider_differences:raise ManifestError(name+'.'+key+' : --accept-provider-differences requis ; HTTPS et jeton plateforme font autorité, domaines configurés dans SPARK.')
                warnings.append(name+'.'+key+' : non appliqué ; HTTPS, jeton plateforme et route SPARK font autorité.')
        fn_env=merged(environment,variables(alias(function,('environment','env')),name+'.environment',resolve_environment))
        fn_secret=merged(secrets,variables(function.get('secret'),name+'.secret',resolve_environment))
        if len(fn_env)>128 or len(fn_secret)>128:raise ManifestError(name+' : configuration héritée supérieure à 128 clés.')
        if fn_env.keys()&fn_secret.keys():raise ManifestError(name+' : collision variable/secret.')
        result.append({'name':name,'config':config(provider,function),'configuration':{'environment':fn_env,'secrets':fn_secret},
                       'events':events(function.get('events'),name),'patterns':global_patterns+patterns(function.get('package'))})
    return {'service':service,'runtime':'node24','architecture':'linux-x64','functions':result,'warnings':warnings}


def public_plan(plan):
    return {**plan,'functions':[{key:value for key,value in function.items() if key!='configuration'}|
        {'environment_names':sorted(function['configuration']['environment']),'secret_names':sorted(function['configuration']['secrets'])}
        for function in plan['functions']]}
